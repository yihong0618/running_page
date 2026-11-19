import argparse
import getpass

import garminconnect

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("email", nargs="?", help="email of garmin")
    parser.add_argument("password", nargs="?", help="password of garmin")
    parser.add_argument(
        "--is-cn",
        dest="is_cn",
        action="store_true",
        help="if garmin account is cn",
    )
    options = parser.parse_args()
    email = options.email or input("Garmin email: ")
    password = options.password or getpass.getpass("Garmin password: ")
    garmin = garminconnect.Garmin(
        email,
        password,
        is_cn=options.is_cn,
        prompt_mfa=lambda: input("MFA code: ").strip(),
    )
    garmin.login()
    secret_string = garmin.client.dumps()
    print(secret_string)
