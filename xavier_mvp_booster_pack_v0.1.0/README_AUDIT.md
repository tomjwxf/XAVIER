# Xavier Auditor Pack — How to Verify

## What this proves
- Schema correctness
- Signature authenticity (Ed25519) against `keys/pubkeys.json`
- Invariants: timestamp order, corridor enum, money integer units, fee bounds

## Quickstart
```bash
# 1) Optional: create and activate a venv
python3 -m venv .venv && source .venv/bin/activate

# 2) Install deps
pip install -r requirements.txt

# 3) Verify receipts
python verify.py --path test_vectors/receipts --pubkeys-file keys/pubkeys.json --strict --summary
```
Expected output is deterministic: `N valid, 0 invalid` and printed p95 emission.

## Spot-check hash anchors
- Each receipt includes `hash_anchor = sha256(canonical_json_without_signature)`
- See `EXPECTED_HASHES.txt` for a manifest you can compare.
