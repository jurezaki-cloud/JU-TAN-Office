# Production Ed25519 PUBLIC verification keys for JU-TAN Office update manifests.
#
# Place one file per key id:  <key_id>.pub
# Contents: base64 or hex encoding of the raw 32-byte Ed25519 public key.
#
# NEVER place private signing keys in this directory.
# NEVER commit private keys.
# Private keys are supplied only to scripts/generate_update_manifest.py via
#   JU_TAN_UPDATE_SIGNING_KEY_FILE  or  JU_TAN_UPDATE_SIGNING_KEY
#
# Until a production key is issued and installed here, signature verification
# fails closed (unknown key_id).
