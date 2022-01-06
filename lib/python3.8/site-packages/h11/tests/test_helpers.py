from .helpers import *


def test_normalize_data_events():
    assert normalize_data_events(
        [
            Data(data=bytearray(b"1")),
            Data(data=b"2"),
            Response(status_code=200, headers=[]),
            Data(data=b"3"),
            Data(data=b"4"),
            EndOfMessage(),
            Data(data=b"5"),
            Data(data=b"6"),
            Data(data=b"7"),
        ]
    ) == [
        Data(data=b"12"),
        Response(status_code=200, headers=[]),
        Data(data=b"34"),
        EndOfMessage(),
        Data(data=b"567"),
    ]
