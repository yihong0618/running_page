# A highish-level implementation of the HTTP/1.1 wire protocol (RFC 7230),
# containing no networking code at all, loosely modelled on hyper-h2's generic
# implementation of HTTP/2 (and in particular the h2.connection.H2Connection
# class). There's still a bunch of subtle details you need to get right if you
# want to make this actually useful, because it doesn't implement all the
# semantics to check that what you're asking to write to the wire is sensible,
# but at least it gets you out of dealing with the wire itself.

from ._connection import *
from ._events import *
from ._state import *
from ._util import LocalProtocolError, ProtocolError, RemoteProtocolError
from ._version import __version__

PRODUCT_ID = "python-h11/" + __version__


__all__ = ["ProtocolError", "LocalProtocolError", "RemoteProtocolError"]
__all__ += _events.__all__
__all__ += _connection.__all__
__all__ += _state.__all__
