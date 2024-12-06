# Certbot Regfish DNS Hooks

**Overview:**

- [Installation](#installation)
- [Usage](#usage)
- [Status](#status)

Pre and post validation hooks for Certbot to automate DNS-01 challenges using the
Regfish DNS API.

## Installation

1. Install via pip:

   ```bash
   pip install certbot-regfish-hooks
   ```

   See also
   [certbot installation via pip](https://certbot.eff.org/instructions?ws=other&os=pip).

2. Set up the Regfish API key:

   ```bash
   $ echo "your-regfish-key" > /etc/letsencrypt/regfish-api-key.txt
   $ chmod 600 /etc/letsencrypt/regfish-api-key.txt
   ```

## Usage

These Regfish DNS hooks can be used with
[Certbot's manual plugin](https://eff-certbot.readthedocs.io/en/stable/using.html#manual)
by specifying `certonly` and `--manual` on the command line:

```bash
$ certbot \
  --manual \
  --manual-auth-hook 'certbot-regfish-auth-hook --regfish-api-key-file /etc/letsencrypt/regfish-api-key.txt' \
  --manual-cleanup-hook 'certbot-regfish-cleanup-hook --regfish-api-key-file /etc/letsencrypt/regfish-api-key.txt' \
  --preferred-challenges dns-01 \
  certonly \
  <your other options>
```

Alternatively, use a
[global configuration file](https://eff-certbot.readthedocs.io/en/stable/using.html#configuration-file)
to apply your options:

```bash
$ certbot --config /etc/letsencrypt/regfish-example.ini certonly
```

`/etc/letsencrypt/regfish-example.ini`:

```ini
# register
email = your.email@example.com
no-eff-email = true
agree-tos = true

# authenticator
manual = true
manual-auth-hook = 'certbot-regfish-auth-hook --regfish-api-key-file /etc/letsencrypt/regfish-api-key.txt'
manual-cleanup-hook = 'certbot-regfish-cleanup-hook --regfish-api-key-file /etc/letsencrypt/regfish-api-key.txt'

# domain settings
domains = test.example.com,*.test.example.com

# NOTE: remove test-cert to use Let's Encrypt production endpoints
test-cert = true
preferred-challenges = dns-01
user-agent = 'autocrt/2.0'

# use ECC
key-type = ecdsa
elliptic-curve = secp384r1
```

## Status

### This is still in beta. What's missing for production?

The auth hooks have been tested as described above and this project will be deployed
across two servers shortly. Let's be honest though - a bit homework remains before I'd
consider this ready for production:

- [ ] Integration testing with a test domain
- [ ] Automated builds and releases to PyPI
- [x] Pre-commit hooks for linting/formatting
- [x] Automated dependency upgrades (Dependabot)

### If that's version 2, where's version 1?

In fact, this project started six years ago as the very first Python module one of my
closest friends hacked together for educational purposes. Certbot wasn't able to handle
DNS challenges back then, so he came up with a hand-rolled ACME implementation and web
scraping interface for Regfish. This tool, which has requested over 50 certificates for
our purposes by now, is what we named _autocrt-dns_.

It's been rock-solid until the day Regfish changed their DNS pad for the better and
_finally_ added an API to their product in November 2024. This public repository is a
complete rewrite of our first version, leaning towards Certbot's now well-established
ACME implementation and focusing on DNS authorization. None of the initial code survived
but for sentimental reasons, it still identifies itself with the user-agent _autocrt_,
now in version 2.
