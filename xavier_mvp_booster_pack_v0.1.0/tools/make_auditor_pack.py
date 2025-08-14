import os, json, zipfile, hashlib, sys
from pathlib import Path

def canonicalize(obj):
    import json
    return json.dumps(obj, separators=(',', ':'), sort_keys=True, ensure_ascii=False).encode('utf-8')

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "XAVIER_auditor_pack_v0.1.0.zip"

receipts_dir = ROOT / "test_vectors" / "receipts"
schema_path = ROOT / "receipt.schema.v1.1.json"
pubkeys_path = ROOT / "keys" / "pubkeys.json"
readme_audit = ROOT / "README_AUDIT.md"
verifier = ROOT / "verify.py"

def compute_expected_hashes():
    lines = []
    for p in sorted(receipts_dir.glob("*.json")):
        with open(p) as f:
            r = json.load(f)
        # Remove signature for canonical hash
        payload = r.copy()
        payload.pop("signature", None)
        import hashlib
        h = hashlib.sha256(canonicalize(payload)).hexdigest()
        lines.append(f"{p.name} {h}")
    return "\n".join(lines) + "\n"

def main():
    if not receipts_dir.exists():
        print("No receipts found.")
        sys.exit(1)
    expected_hashes = compute_expected_hashes()
    tmp = ROOT / "EXPECTED_HASHES.txt"
    tmp.write_text(expected_hashes)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(schema_path, "receipt.schema.v1.1.json")
        z.write(pubkeys_path, "keys/pubkeys.json")
        z.write(readme_audit, "README_AUDIT.md")
        z.write(verifier, "verify.py")
        z.write(tmp, "EXPECTED_HASHES.txt")
        for p in sorted(receipts_dir.glob("*.json")):
            z.write(p, f"test_vectors/receipts/{p.name}")
    print(f"Wrote {OUT}")
    tmp.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
