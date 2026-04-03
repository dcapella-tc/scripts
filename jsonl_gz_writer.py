from __future__ import annotations

import gzip
import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, TextIO


class _CompressedJsonlWriter:
    def __init__(self, fileobj: TextIO) -> None:
        self._fileobj = fileobj

    def write(self, obj: dict[str, Any]) -> None:
        line = json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n"
        self._fileobj.write(line)

    def flush(self) -> None:
        self._fileobj.flush()


@contextmanager
def compressed_jsonl_writer(path: Path | str, *, compresslevel: int = 6) -> Iterator[_CompressedJsonlWriter]:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(p, "wt", encoding="utf-8", compresslevel=compresslevel, newline="\n") as f:
        yield _CompressedJsonlWriter(f)
