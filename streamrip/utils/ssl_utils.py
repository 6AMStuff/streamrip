"""Utility functions for SSL handling."""

import logging
import ssl
import sys

logger = logging.getLogger("streamrip")

try:
    import certifi

    HAS_CERTIFI = True
except ImportError:
    logger.debug("certifi not found, falling back to system certificates")
    HAS_CERTIFI = False


def create_ssl_context(verify=True):
    """Create an SSL context with the appropriate verification settings.

    Args:
        verify: Whether to verify SSL certificates

    Returns:
        An SSL context object with the specified verification settings
    """
    if not verify:
        # Disable verification entirely when requested
        logger.warning("SSL certificate verification disabled (less secure)")
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    # Use certifi for certificate verification if available
    if HAS_CERTIFI:
        return ssl.create_default_context(cafile=certifi.where())
    else:
        return ssl.create_default_context()


def get_httpx_verify_kwargs(verify_ssl: bool = True) -> dict:
    """Get keyword arguments for httpx2 clients with SSL settings.

    Args:
        verify_ssl: Whether to verify SSL certificates

    Returns:
        Dictionary of kwargs to pass to httpx2.AsyncClient
    """
    if not verify_ssl:
        return {"verify": False}

    return {"verify": create_ssl_context(verify=True)}


def is_certificate_error(exc: BaseException | None) -> bool:
    """Return True if an exception chain contains an SSL certificate error."""
    while exc is not None:
        if isinstance(exc, ssl.CertificateError):
            return True
        exc = exc.__cause__ or exc.__context__
    return False


def print_ssl_error_help():
    """Print helpful error message when SSL verification fails."""
    print("\nError: Cannot verify SSL certificate.")
    print("Options:")
    print("  1. Run again with the --no-ssl-verify flag (less secure)")
    print(
        '     Example: rip --no-ssl-verify url "https://tidal.com/browse/playlist/..."'
    )
    print()
    print("  2. Install certifi for better certificate handling:")
    print("     pip install certifi")
    print()
    print("  3. Update your certificates:")
    print("     pip install --upgrade certifi")
    sys.exit(1)
