import argparse

import garth

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
    if options.is_cn:
        garth.configure(domain="garmin.cn", ssl_verify=False)
    garth.login(options.email, options.password)
    secret_string = garth.client.dumps()
    print(secret_string)
