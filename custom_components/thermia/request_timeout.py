"""Apply an HTTP request timeout to the ThermiaOnlineAPI session.

ThermiaOnlineAPI (<= 6.3.1) sends requests without a timeout and retries up
to 20 times, so a silently dropped connection can block the update forever
and freeze all entities until the integration is reloaded.

This is a stopgap until the library sets a timeout itself: it mounts an
adapter with a default timeout and fewer retries on the library's private
requests session. If the library changes and the session cannot be found,
nothing is patched.
"""

from __future__ import annotations

import logging

from requests import Session
from requests.adapters import HTTPAdapter, Retry
from ThermiaOnlineAPI import Thermia

_LOGGER = logging.getLogger(__name__)

# (connect timeout, read timeout) in seconds
DEFAULT_REQUEST_TIMEOUT = (10, 30)


class TimeoutHTTPAdapter(HTTPAdapter):
    """HTTPAdapter that applies a default timeout when none is given."""

    def __init__(self, *args, timeout=DEFAULT_REQUEST_TIMEOUT, **kwargs):
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


def apply_request_timeout(thermia: Thermia) -> bool:
    """Mount a timeout adapter on the library's session. Return True if applied."""
    session = getattr(
        getattr(thermia, "api_interface", None), "_ThermiaAPI__session", None
    )

    if not isinstance(session, Session):
        _LOGGER.warning(
            "Could not find the ThermiaOnlineAPI HTTP session; "
            "requests will run without a timeout"
        )
        return False

    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    session.mount("https://", TimeoutHTTPAdapter(max_retries=retry))

    _LOGGER.debug("Applied request timeout %s to ThermiaOnlineAPI session", DEFAULT_REQUEST_TIMEOUT)
    return True
