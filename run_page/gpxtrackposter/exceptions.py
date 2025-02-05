# Copyright 2016-2019 Florian Pigorsch & Contributors. All rights reserved.
#
# Use of this source code is governed by a MIT-style
# license that can be found in the LICENSE file.


class PosterError(Exception):
    "Base class for all errors"

    pass


class TrackLoadError(PosterError):
    "Something went wrong when loading a track file, we just ignore this file and continue"

    pass


class ParameterError(PosterError):
    "Something's wrong with user supplied parameters"

    pass
