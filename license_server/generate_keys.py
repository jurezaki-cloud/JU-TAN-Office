import secrets

from license_server.security import generate_signing_keys


if __name__ == "__main__":
    private_key, public_key = generate_signing_keys()
    print("JUTAN_LICENSE_SIGNING_KEY=" + private_key)
    print("JU_TAN_LICENSE_PUBLIC_KEY=" + public_key)
    print("JUTAN_LICENSE_PEPPER=" + secrets.token_urlsafe(48))
    print("JUTAN_LICENSE_ADMIN_TOKEN=" + secrets.token_urlsafe(48))
