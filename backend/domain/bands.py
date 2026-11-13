"""Пошук категорії за нижніми межами (G1–G5, ступені анемії)."""
from typing import Protocol, Sequence


class Band(Protocol):
    code: str
    lower_bound: float  # межа входить у категорію


def band_code(value: float, bands: Sequence[Band]) -> str:
    """Код категорії з найбільшою нижньою межею, яка не перевищує value."""
    for band in sorted(bands, key=lambda candidate: candidate.lower_bound, reverse=True):
        if value >= band.lower_bound:
            return band.code
    raise ValueError(f"Значення {value:g} нижче за всі межі категорій")
