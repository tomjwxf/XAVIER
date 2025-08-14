#!/usr/bin/env python3
import base64, json, os, glob, argparse
from nacl.signing import SigningKey

def canon(obj):
    return json.dumps(obj, separators=(",", ":"), sort_keys=True).encode("utf-8")

def load_secret(path):
    with open(path, "r", encoding="utf-8") as f:
        return base64.b64decode(f.read().strip())

def sign_file(path, sk: SigningKey):
    with open(path, "r", encoding="utf-8") as f:
        r = json.load(f)

    # Auto-calc receipt_emission_ms if timestamps exist
    ts = r.get("timestamps", {})
    if ts and "finality_at" in ts and "receipt_emitted_at" in ts and not r.get("receipt_emission_ms"):
        from datetime import datetime
        def to_ms(s): 
            return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp() * 1000)
        r["receipt_emission_ms"] = to_ms(ts["receipt_emitted_at"]) - to_ms(ts["finality_at"])

    to_sign = dict(r)
    to_sign.pop("sig", None)
    payload = canon(to_sign)
    sig = sk.sign(payload).signature
    r["sig"] = "ed25519:" + base64.b64encode(sig).decode("ascii")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(r, f, indent=2)
    print(f"Signed {os.path.basename(path)}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secret", default="keys/coordinator_v1_ed25519.secret", help="Path to base64 ed25519 secret key")
    ap.add_argument("--path", default="test_vectors", help="File or folder of receipts to sign")
    args = ap.parse_args()

    sk_bytes = load_secret(args.secret)
    sk = SigningKey(sk_bytes)

    paths = []
    if os.path.isdir(args.path):
        paths = sorted(glob.glob(os.path.join(args.path, "*.json")))
    else:
        paths = [args.path]

    for p in paths:
        sign_file(p, sk)

if __name__ == "__main__":
    main()
