from io import (
    BufferedIOBase,
    RawIOBase,
    TextIOBase,
    TextIOWrapper,
)
from mmap import mmap
from os import PathLike
from typing import (
    IO,
    TYPE_CHECKING,
    AnyStr,
    Union,
)

# To prevent import cycles place any internal imports in the branch below
# and use a string literal forward reference to it in subsequent types
# https://mypy.readthedocs.io/en/latest/common_issues.html#import-cycles
if TYPE_CHECKING:
    from typing import (
        Literal,
        TypedDict,
        final,
    )

    from pandas._libs import (
        Period,
        Timedelta,
        Timestamp,
    )

# filenames and file-like-objects
Buffer = Union[IO[AnyStr], RawIOBase, BufferedIOBase, TextIOBase, TextIOWrapper, mmap]
FileOrBuffer = Union[str, Buffer[AnyStr]]
FilePathOrBuffer = Union["PathLike[str]", FileOrBuffer[AnyStr]]