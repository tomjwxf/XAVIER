#!/usr/bin/env python3
import argparse, base64, glob, json, os, sys
from datetime import datetime, timezone
from jsonschema import Draft7Validator
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "receipt.schema.json")

def iso_to_epoch_ms(s: str) -> int:
    # Accepts ISO8601 with trailing Z
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1000)

def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def canon_dumps(obj: dict) -> bytes:
    # Deterministic JSON encoding (RFC8259 subset)
    return json.dumps(obj, separators=(",", ":"), sort_keys=True).encode("utf-8")

def validate_schema(receipt: dict, schema: dict):
    Draft7Validator(schema).validate(receipt)

def check_invariants(receipt: dict):
    t_obs = iso_to_epoch_ms(receipt["timestamps"]["observed_at"])
    t_fin = iso_to_epoch_ms(receipt["timestamps"]["finality_at"])
    t_emit = iso_to_epoch_ms(receipt["timestamps"]["receipt_emitted_at"])
    assert t_obs <= t_fin <= t_emit, "timestamp order invalid"

    corridor = receipt["corridor"]
    assert "↔" in corridor, "corridor must contain ↔"
    # Example guard for demo corridor
    # assert corridor == "USDC-Base↔USDC-Base", "unexpected corridor"

    fees = [p.get("fee_bps", 0.0) for p in receipt["participants"]]
    assert 0.0 <= max(fees) <= 100.0, "fee_bps out of range"

    emission_ms = receipt.get("receipt_emission_ms")
    if emission_ms is not None:
        assert emission_ms >= 0, "receipt_emission_ms negative"
        # Optional SLO demo check
        assert emission_ms < 10000, "p95 emission SLO breached (>= 10s)"

def verify_signature(receipt: dict, pubkey_b64: str):
    to_sign = dict(receipt)  # shallow copy
    sig_field = to_sign.pop("sig", None)
    if not sig_field or not sig_field.startswith("ed25519:"):
        raise AssertionError("missing or malformed sig field")

    payload = canon_dumps(to_sign)
    sig = base64.b64decode(sig_field.split(":", 1)[1])
    vk = VerifyKey(base64.b64decode(pubkey_b64))
    try:
        vk.verify(payload, sig)
    except BadSignatureError as e:
        raise AssertionError("signature invalid") from e

def load_pubkey_for_ref(pubkeys_path: str, pubkey_ref: str) -> str:
    with open(pubkeys_path, "r", encoding="utf-8") as f:
        m = json.load(f)
    if pubkey_ref not in m:
        raise KeyError(f"pubkey_ref {pubkey_ref} not found in {pubkeys_path}")
    return m[pubkey_ref]

def verify_file(path: str, schema: dict, pubkey_b64: str = None, pubkeys_path: str = None, skip_sig: bool = False) -> tuple[bool, str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            receipt = json.load(f)

        validate_schema(receipt, schema)
        check_invariants(receipt)

        if not skip_sig:
            if pubkey_b64 is None and pubkeys_path is None:
                raise AssertionError("no pubkey provided; use --pubkey or --pubkeys-file or --skip-sig")
            if pubkey_b64 is None:
                pubkey_b64 = load_pubkey_for_ref(pubkeys_path, receipt["pubkey_ref"])
            verify_signature(receipt, pubkey_b64)

        return True, "OK"
    except Exception as e:
        return False, str(e)

def main():
    ap = argparse.ArgumentParser(description="Xavier Receipt Verifier (v1.1)")
    ap.add_argument("--path", required=True, help="Path to a receipt .json file or a directory of receipts")
    ap.add_argument("--pubkey", help="Base64 Ed25519 public key to verify signatures")
    ap.add_argument("--pubkeys-file", help="JSON mapping of pubkey_ref -> base64 public key")
    ap.add_argument("--skip-sig", action="store_true", help="Skip signature verification (schema + invariants only)")
    args = ap.parse_args()

    schema = load_schema()
    paths = []
    if os.path.isdir(args.path):
        paths = sorted(glob.glob(os.path.join(args.path, "*.json")))
    else:
        paths = [args.path]

    ok = 0
    for p in paths:
        success, msg = verify_file(p, schema, pubkey_b64=args.pubkey, pubkeys_path=args.pubkeys_file, skip_sig=args.skip_sig)
        status = "OK" if success else "FAIL"
        print(f"{status}: {os.path.basename(p)} - {msg}")
        if success:
            ok += 1

    total = len(paths)
    print(f"\nSummary: {ok}/{total} valid")
    sys.exit(0 if ok == total else 1)

if __name__ == "__main__":
    main()
