**XAVIER**
XAVIER receipts MVP
# 1) Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# 2) Generate a demo keypair (writes keys/ and pubkeys.json)
python generate_keys.py
# 3) Run verifier on the sample (schema + invariants only)
python verify.py --path test_vectors --skip-sig
# 4) (Optional) After you sign receipts, verify signatures too
# python verify.py --path test_vectors --pubkeys-file pubkeys.json
