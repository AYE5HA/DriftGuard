"""Fuzzy column-name matching for likely schema renames."""

from __future__ import annotations

from typing import Iterable

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover - useful for tiny local demos.
    from difflib import SequenceMatcher

    class _DifflibFuzz:
        @staticmethod
        def ratio(left: str, right: str) -> float:
            return SequenceMatcher(None, left, right).ratio() * 100

    fuzz = _DifflibFuzz()


def find_likely_renames(
    missing_columns: Iterable[str],
    added_columns: Iterable[str],
    threshold: int = 80,
) -> list[dict[str, float | str]]:
    """Match missing columns to new columns when names are semantically close."""
    matches: list[dict[str, float | str]] = []
    used_new_columns: set[str] = set()

    for old_column in sorted(missing_columns):
        best_new_column = None
        best_score = 0.0

        for new_column in sorted(added_columns):
            if new_column in used_new_columns:
                continue

            score = max(
                fuzz.ratio(_normalize(old_column), _normalize(new_column)),
                fuzz.ratio(_tokenize(old_column), _tokenize(new_column)),
            )
            if score > best_score:
                best_score = score
                best_new_column = new_column

        if best_new_column and best_score >= threshold:
            used_new_columns.add(best_new_column)
            matches.append(
                {
                    "old_column": old_column,
                    "new_column": best_new_column,
                    "score": float(best_score),
                }
            )

    return matches


def _normalize(column_name: str) -> str:
    return "".join(character.lower() for character in column_name if character.isalnum())


def _tokenize(column_name: str) -> str:
    tokens: list[str] = []
    current = ""

    for character in column_name:
        if character in {"_", "-", ".", " "}:
            if current:
                tokens.append(current.lower())
                current = ""
            continue

        if character.isupper() and current:
            tokens.append(current.lower())
            current = character
        else:
            current += character

    if current:
        tokens.append(current.lower())

    return " ".join(tokens)
