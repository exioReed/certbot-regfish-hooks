"""Implementations of Regfish Pre and Post Validation Hooks for Certbot.

This module provides hook functions for Certbot's DNS-01 challenge validation process
using the Regfish DNS API. It implements two main functions:
- An authentication hook that creates required DNS TXT records
- A cleanup hook that removes the DNS TXT records after validation

The hooks are designed to be used with Certbot's --manual-auth-hook and
--manual-cleanup-hook parameters when requesting certificates using DNS-01
challenge validation.

Environment Variables:
    The following environment variables are supported and can be used instead
    of command line arguments:
    - CERTBOT_DOMAIN: Domain being authenticated
    - CERTBOT_VALIDATION: Validation string to be placed in DNS TXT record
    - CERTBOT_REMAINING_CHALLENGES: Number of remaining challenges
    - CERTBOT_ALL_DOMAINS: Comma-separated list of all domains being validated
    - CERTBOT_AUTH_OUTPUT: Output from the auth hook (used by cleanup hook)
    - REGFISH_API_KEY: Regfish API key
    - REGFISH_API_KEY_FILE: Path to file containing Regfish API key
"""

import argparse
import datetime
import re
import time

from certbot_regfish_hooks.api import RegfishClient

RRID_RE = re.compile(r"[0-9]+")


def regfish_auth_hook(args: argparse.Namespace):
    """Create a DNS TXT record for Certbot DNS-01 challenge validation.

    This function creates a TXT record named '_acme-challenge.<domain>' with
    the validation string provided by Certbot. After creating the record,
    it will sleep for the TTL duration plus 30 seconds if this is the last
    remaining challenge, allowing DNS propagation to complete.

    Parameters
    ----------
    args : argparse.Namespace
        Command line arguments containing:
        - regfish_api_key : str
            The Regfish API key for authentication
        - certbot_domain : str
            The domain being validated
        - certbot_validation : str
            The validation string to be placed in the TXT record
        - ttl : int
            Time-to-live in seconds for the DNS record (60-604800)
        - certbot_remaining_challenges : int
            Number of remaining challenges after this one

    Notes
    -----
    The function prints the record ID (rrid) to stdout, which will be
    captured by Certbot and passed to the cleanup hook via CERTBOT_AUTH_OUTPUT.
    """
    client = RegfishClient(api_key=args.regfish_api_key)
    rr = client.create_record(
        type_="TXT",
        name=f"_acme-challenge.{args.certbot_domain}.",
        data=args.certbot_validation,
        ttl=args.ttl,
        annotation=f"certbook-regfish-hook on {datetime.datetime.utcnow().isoformat()}",
    )

    # Record id is printed to standard output to be used in cleanup hook as
    # CERTBOT_AUTH_OUTPUT
    print(rr.rrid)

    # If this is the last remaining challenge (certbot_remaining_challenges == 0),
    # sleep for longer than the TTL. There is no cache; assumes TTL is consistent
    # across a series of challenges.
    if not args.certbot_remaining_challenges:
        time.sleep(args.ttl + 30)


def regfish_cleanup_hook(args: argparse.Namespace):
    """Remove DNS TXT records created during the authentication process.

    This function deletes all TXT records created by the authentication hook.
    It parses the record IDs from the auth hook's output (CERTBOT_AUTH_OUTPUT)
    and deletes each record using the Regfish API.

    Parameters
    ----------
    args : argparse.Namespace
        Command line arguments containing:
        - regfish_api_key : str
            The Regfish API key for authentication
        - certbot_auth_output : str
            Newline-separated string of record IDs created by the auth hook

    Notes
    -----
    The function expects record IDs to be integers and will ignore any
    non-numeric content in the auth output. Multiple record IDs should
    be separated by newlines in the certbot_auth_output.
    """
    client = RegfishClient(api_key=args.regfish_api_key)
    for rrid in [
        # CANDO: Use RRID_RE to parse rrid from CERTBOT_AUTH_OUTPUT
        int(rrid_str.strip())
        for rrid_str in args.certbot_auth_output.split("\n")
        if RRID_RE.search(rrid_str)
    ]:
        client.delete_record(rrid)
