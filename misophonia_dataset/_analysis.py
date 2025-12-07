from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import pandas as pd
import pydantic


def models_to_df(
    models: Iterable[pydantic.BaseModel],
    *,
    model_col: str = "_model",
    flatten: bool = False,
) -> pd.DataFrame:
    """
    Convert an iterable of Pydantic models into a pandas DataFrame.

    Args:
        models:
            Iterable of BaseModel instances.
        model_col:
            Column name in which to store the original model objects.
        flatten:
            Whether to flatten nested structures in the resulting DataFrame.
            - Iterables (lists, tuples) become columns like `col[0]`, `col[1]`, ...
            - Dicts become columns like `col[key]`.
            - Nested combinations become e.g. `col[0][subkey]`.

            Additionally, for each top-level iterable field (excluding strings and mappings),
            a companion column `len(field_name)` is added to make sorting/filtering easier.

    Returns:
        DataFrame containing the models' fields and optionally the original objects.
    """
    rows: list[dict[str, Any]] = []
    for m in models:
        # Dump to plain Python structures; submodels become dicts here
        row = m.model_dump()
        # Preserve original model instance
        row[model_col] = m

        rows.append(row)

    if flatten:
        rows = [_flatten_row(row) for row in rows]

    df = pd.DataFrame(rows)
    return df


def _is_sequence_but_not_str(obj: Any) -> bool:  # noqa: ANN401
    return isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray))


def _flatten_value(prefix: str, value: Any, out: dict[str, Any]) -> None:  # noqa: ANN401
    """
    Recursively flatten `value` into `out`, using `prefix` as the column name root.
    Also adds recursive `len(...)` columns for any non-string sequence encountered.
    """
    if isinstance(value, Mapping):
        # Dict-like: recurse into keys
        for k, v in value.items():
            key_str = str(k)
            new_prefix = f"{prefix}[{key_str}]"
            _flatten_value(new_prefix, v, out)
    elif _is_sequence_but_not_str(value):
        # Add length column for this sequence
        len_key = f"len({prefix})"
        if len_key not in out:
            out[len_key] = len(value)

        # List/tuple/etc: index each element
        for idx, v in enumerate(value):
            new_prefix = f"{prefix}[{idx}]"
            _flatten_value(new_prefix, v, out)
    else:
        # Atomic value: assign directly
        if prefix in out:
            raise ValueError(f"Key collision when flattening: {prefix!r}")
        out[prefix] = value


def _flatten_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """
    Flatten a single row dict into a flat dict with bracketed keys.
    """
    flat: dict[str, Any] = {}
    for key, value in row.items():
        # Top-level keys stay as-is, nested structure goes into brackets
        key_str = str(key)
        _flatten_value(key_str, value, flat)
    return flat
