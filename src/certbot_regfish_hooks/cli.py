"""Command Line Interface for Regfish Pre and Post Validation Hooks for Certbot.

This module provides the command-line interface for managing Certbot DNS-01 challenge
validations using the Regfish DNS API. It supports two main operations:
- Authentication: Creating DNS TXT records for domain validation
- Cleanup: Removing DNS TXT records after validation

The CLI can be invoked either directly or through entry points that automatically
select the appropriate hook operation. All parameters can be specified either as
command-line arguments or through environment variables.
"""

import argparse
import os
import sys
from io import TextIOWrapper

from certbot_regfish_hooks.__version__ import version
from certbot_regfish_hooks.hooks import regfish_auth_hook, regfish_cleanup_hook


def get_common_args_parser() -> argparse.ArgumentParser:
    """Create an argument parser with common arguments for both hooks.

    This function creates an ArgumentParser with arguments that are common to both
    the authentication and cleanup hooks.

    Returns
    -------
    argparse.ArgumentParser
        Parser configured with common arguments for domain validation hooks.

    Notes
    -----
    The following arguments are supported:
    - --certbot-domain : Domain being validated (env: CERTBOT_DOMAIN)
    - --certbot-validation : Validation string (env: CERTBOT_VALIDATION)
    - --certbot-remaining-challenges : Number of remaining challenges
      (env: CERTBOT_REMAINING_CHALLENGES)
    - --certbot-all-domains : All domains being validated (env: CERTBOT_ALL_DOMAINS)
    - --regfish-api-key : API key (env: REGFISH_API_KEY)
    - --regfish-api-key-file : File containing API key (env: REGFISH_API_KEY_FILE)
    """
    common_args_parser = argparse.ArgumentParser(add_help=False)
    common_args_parser.add_argument(
        "--certbot-domain",
        default=os.getenv("CERTBOT_DOMAIN"),
        help="The domain being authenticated",
    )
    common_args_parser.add_argument(
        "--certbot-validation",
        default=os.getenv("CERTBOT_VALIDATION"),
        help="The validation string",
    )
    common_args_parser.add_argument(
        "--certbot-remaining-challenges",
        type=int,
        default=os.getenv("CERTBOT_REMAINING_CHALLENGES"),
        help="Number of challenges remaining after the current challenge",
    )
    common_args_parser.add_argument(
        "--certbot-all-domains",
        default=os.getenv("CERTBOT_ALL_DOMAINS"),
        help="A comma-separated list of all domains challenged for the current certificate",
    )
    api_key_group = common_args_parser.add_mutually_exclusive_group()
    api_key_group.add_argument(
        "--regfish-api-key-file",
        dest="regfish_api_key",
        type=argparse.FileType(mode="r"),
        default=os.getenv("REGFISH_API_KEY_FILE"),
        help="Read Regfish API key from this file",
    )
    api_key_group.add_argument(
        "--regfish-api-key",
        dest="regfish_api_key",
        default=os.getenv("REGFISH_API_KEY"),
        help="Regfish API key",
    )

    return common_args_parser


def get_root_parser() -> argparse.ArgumentParser:
    """Create the root argument parser for the CLI.

    This function creates the main ArgumentParser that serves as the entry point
    for the command-line interface.

    Returns
    -------
    argparse.ArgumentParser
        The configured root parser for the CLI.
    """
    root_parser = argparse.ArgumentParser(
        prog="certbot-regfish-hooks",
        description="Regfish Pre and Post Validation Hooks for Certbot",
    )

    root_parser.add_argument(
        "--version", "-v", action="version", version=version, help="print version"
    )
    return root_parser


def main():
    """Main entry point for the CLI."""
    root_parser = get_root_parser()
    common_args_parser = get_common_args_parser()
    hooks_parser = root_parser.add_subparsers(title="pre and post validation hooks")

    auth_command_parser = hooks_parser.add_parser(
        "auth", help="auth hook for certboot", parents=[common_args_parser]
    )
    auth_command_parser.set_defaults(func=regfish_auth_hook)
    auth_command_parser.add_argument(
        "--ttl",
        type=int,
        default=60,
        help="time-to-live in seconds. must be between 60 and 604800. defaults to 60",
    )

    cleanup_command_parser = hooks_parser.add_parser(
        "cleanup", help="cleanup hook for certbot", parents=[common_args_parser]
    )
    cleanup_command_parser.set_defaults(func=regfish_cleanup_hook)
    cleanup_command_parser.add_argument(
        "--certbot-auth-output",
        default=os.getenv("CERTBOT_AUTH_OUTPUT"),
        help="whatever the auth script wrote to stdout",
    )

    args = root_parser.parse_args()

    if isinstance(args.regfish_api_key, TextIOWrapper):
        args.regfish_api_key = args.regfish_api_key.read().strip()

    args.func(args)


def auth_hook():
    """Entry point for the authentication hook of certbot's manual plugin."""
    sys.argv.insert(1, "auth")
    main()


def cleanup_hook():
    """Entry point for the cleanup hook of cerbot's manual plugin."""
    sys.argv.insert(1, "cleanup")
    main()


if __name__ == "__main__":
    main()
