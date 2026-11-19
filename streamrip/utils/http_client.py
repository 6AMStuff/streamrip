"""Central construction of httpx2 clients with streamrip's defaults."""

import httpx2

from . import ssl_utils

# aiohttp (the previous client) followed redirects and allowed ~5 minutes per
# read. httpx2 defaults to no redirects and a 5s timeout, which breaks short
# links and stalls slow downloads, so set the behaviour explicitly here.
DEFAULT_TIMEOUT = httpx2.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)


def create_client(
    *, headers: dict | None = None, verify_ssl: bool = True
) -> httpx2.AsyncClient:
    """Create an AsyncClient that follows redirects with generous timeouts."""
    return httpx2.AsyncClient(
        headers=headers,
        follow_redirects=True,
        timeout=DEFAULT_TIMEOUT,
        **ssl_utils.get_httpx_verify_kwargs(verify_ssl=verify_ssl),
    )
