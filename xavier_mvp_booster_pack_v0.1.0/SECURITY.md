# Security & Ops Overview (MVP)

- **Key generation:** Ed25519 keys generated locally; private keys never committed. Store in password manager or HSM later.
- **Key rotation:** Maintain `keys/pubkeys.json` with `key_id`, `alg`, `created_at`, `rotated_at` (nullable), `revoked_at` (nullable).
- **Revocation list:** Publish `keys/rl.json`. Each receipt references this URL as `revocation_list_ref`.
- **Disaster recovery:** Keep an offline backup of signing key (RTO/RPO TBD).

**Important:** This booster pack includes *sample* signatures for demonstration only. Generate your own keys before any public demo.
