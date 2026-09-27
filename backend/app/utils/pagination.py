"""Pagination helpers shared by list endpoints."""
from __future__ import annotations

import math
from typing import Any, Sequence


def clamp(page: int, page_size: int, max_size: int = 200) -> tuple[int, int]:
    return max(1, page), min(max(1, page_size), max_size)


def meta(page: int, page_size: int, total: int) -> dict[str, Any]:
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": max(1, math.ceil(total / page_size)) if total else 0,
    }


def paginate(items: Sequence[Any], page: int, page_size: int) -> tuple[Sequence[Any], dict]:
    return items, meta(page, page_size, len(items))
