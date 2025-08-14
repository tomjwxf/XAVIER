#!/usr/bin/env python3
import base64, json, os
from nacl.signing import SigningKey

OUT_DIR = "keys"
PUBKEYS_JSON = "pubkeys.json"
REF = "coordinator_v1_ed25519"

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    sk = SigningKey.generate()
    vk = sk.verify_key

    sk_b64 = base64.b64encode(bytes(sk)).decode("ascii")
    vk_b64 = base64.b64encode(bytes(vk)).decode("ascii")

    with open(os.path.join(OUT_DIR, f"{REF}.secret"), "w") as f:
        f.write(sk_b64 + "\n")
    with open(os.path.join(OUT_DIR, f"{REF}.pub"), "w") as f:
        f.write(vk_b64 + "\n")

    # Write pubkeys.json for the verifier
    with open(PUBKEYS_JSON, "w") as f:
        json.dump({REF: vk_b64}, f, indent=2)
    print(f"Wrote keys/{REF}.secret (KEEP PRIVATE), keys/{REF}.pub, and {PUBKEYS_JSON}")

if __name__ == "__main__":
    main()
