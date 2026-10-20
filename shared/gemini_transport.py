"""TLS verificado con los certificados del sistema (incluye Windows)."""
from functools import lru_cache
import ssl


@lru_cache(maxsize=1)
def _ssl_context():
    return ssl.create_default_context()


def gemini_client_args():
    return {"verify": _ssl_context(), "timeout": 60.0}
