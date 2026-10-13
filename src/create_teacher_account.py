"""Generate a PBKDF2 password hash for a teacher account configuration."""

import getpass
import hashlib
import json
import re
import secrets
import sys


ITERATIONS = 310_000
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def main() -> None:
    if len(sys.argv) != 2 or not USERNAME_PATTERN.fullmatch(sys.argv[1]):
        raise SystemExit(f"Usage: {sys.argv[0]} USERNAME (letters, digits, _ and - only)")

    password = getpass.getpass("Teacher password (12 characters minimum): ")
    confirmation = getpass.getpass("Confirm password: ")
    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), ITERATIONS
    ).hex()
    print(
        json.dumps(
            {
                "teachers": [
                    {
                        "username": sys.argv[1],
                        "password_hash": f"pbkdf2_sha256${ITERATIONS}${salt}${digest}",
                    }
                ]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
