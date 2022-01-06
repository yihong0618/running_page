"""Async executor versions of file functions from the os.path module."""

from .os import wrap
from os import path

exists = wrap(path.exists)
isfile = wrap(path.isfile)
isdir = wrap(path.isdir)
getsize = wrap(path.getsize)
getmtime = wrap(path.getmtime)
getatime = wrap(path.getatime)
getctime = wrap(path.getctime)
samefile = wrap(path.samefile)
sameopenfile = wrap(path.sameopenfile)
