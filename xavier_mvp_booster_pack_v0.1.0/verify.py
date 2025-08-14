import argparse, json, os, sys, base64, statistics
from pathlib import Path
from jsonschema import Draft202012Validator
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

from canonical_json import canonicalize, sha256_hexdigest

def load_json(p):
    with open(p) as f:
        return json.load(f)

def rfc3339_to_epoch(s):
    # assuming 'Z' suffix
    from datetime import datetime, timezone
    return int(datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).timestamp())

def verify_one(receipt, pubkeys, strict=True):
    # 1) Schema
    schema = load_json('receipt.schema.v1.1.json') if os.path.exists('receipt.schema.v1.1.json') else load_json('receipt.schema.json')
    Draft202012Validator(schema).validate(receipt)

    # 2) Invariants
    ts = receipt['timestamps']
    t_obs = rfc3339_to_epoch(ts['observed_at'])
    t_fin = rfc3339_to_epoch(ts['finality_at'])
    t_emit = rfc3339_to_epoch(ts['receipt_emitted_at'])
    assert t_obs <= t_fin <= t_emit, 'timestamp order invalid'

    assert receipt['corridor'] in ['USDC-Base↔USDC-Base'], 'unexpected corridor'
    parts = receipt['participants']
    assert len(parts) == 2, 'participants must be length=2'
    assert parts[0]['entity_id'] != parts[1]['entity_id'], 'entity_ids must differ'
    for p in parts:
        assert isinstance(p['notional_cents'], int) and p['notional_cents'] >= 0, 'notional_cents must be integer >= 0'
        assert 0.0 <= float(p['fee_bps']) <= 100.0, 'fee_bps out of range'

    if strict:
        # 3) Check hash_anchor recomputation without signature
        payload = receipt.copy()
        payload.pop('signature', None)
        calc = sha256_hexdigest(canonicalize(payload))
        assert calc == receipt['hash_anchor'], 'hash_anchor mismatch'

        # 4) Signature
        sigenv = receipt['signature']
        assert sigenv['alg'] == 'ed25519', 'unsupported alg'
        pubref = sigenv['pubkey_ref']
        key_b64 = pubkeys.get(pubref)
        assert key_b64, f'pubkey_ref {pubref} not found'
        sig = base64.b64decode(sigenv['sig'])
        vk = VerifyKey(base64.b64decode(key_b64))
        vk.verify(canonicalize(payload), sig)

        # 5) Emission SLO (p95 checked at summary level)
        assert receipt['receipt_emission_ms'] >= 0

    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--path', required=True, help='Folder with receipt JSON files')
    ap.add_argument('--pubkeys-file', help='JSON map of pubkey_ref -> base64(ed25519-pubkey)')
    ap.add_argument('--strict', action='store_true', help='Enable signature/hash checks')
    ap.add_argument('--expect', type=int, default=None, help='Expected count of receipts')
    ap.add_argument('--summary', action='store_true', help='Print counts and p95 latency')
    args = ap.parse_args()

    pubkeys = {}
    if args.pubkeys_file:
        pubkeys = load_json(args.pubkeys_file)

    files = sorted([p for p in Path(args.path).glob('*.json')])
    assert files, f'No receipts found in {args.path}'

    valid = 0
    latencies = []
    for p in files:
        r = load_json(p)
        try:
            verify_one(r, pubkeys, strict=args.strict)
            valid += 1
            if isinstance(r.get('receipt_emission_ms'), int):
                latencies.append(r['receipt_emission_ms'])
        except Exception as e:
            print(f'INVALID {p.name}: {e}', file=sys.stderr)

    if args.expect is not None:
        assert valid == args.expect, f'expected {args.expect} valid receipts, got {valid}'
    if args.summary:
        p95 = int(statistics.quantiles(latencies, n=100)[94]) if len(latencies) >= 20 else (sorted(latencies)[int(0.95*len(latencies))-1] if latencies else 0)
        print(f'{valid} valid, {len(files)-valid} invalid; p95_emission_ms={p95}')

if __name__ == '__main__':
    main()
