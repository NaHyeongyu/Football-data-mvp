from __future__ import annotations

from collections.abc import Mapping
from difflib import get_close_matches
import re
from typing import Any

import psycopg


SQL_TABLE_REF_PATTERN = re.compile(
    r"\b(?:from|join)\s+(?:lateral\s+)?([a-zA-Z_][\w.]*)\s*(?:as\s+)?([a-zA-Z_][\w]*)?",
    flags=re.IGNORECASE,
)
SQL_CTE_NAME_PATTERN = re.compile(
    r"(?:\bwith\b|,)\s*([a-zA-Z_][\w]*)\s*(?:\([^)]*\))?\s+as\s*\(",
    flags=re.IGNORECASE,
)
QUALIFIED_IDENTIFIER_PATTERN = re.compile(r"\b([a-zA-Z_][\w]*)\.([a-zA-Z_][\w]*)\b")
IDENTIFIER_PATTERN = re.compile(r"\b([a-zA-Z_][\w]*)\b")
SQL_STRING_PATTERN = re.compile(r"'(?:''|[^'])*'")
SQL_AS_ALIAS_PATTERN = re.compile(r"\bas\s+([a-zA-Z_][\w]*)\b", flags=re.IGNORECASE)


def _normalize_sql_error(error: psycopg.Error, *, sql_query: str | None = None) -> str:
    primary = getattr(error, "diag", None)
    message = getattr(primary, "message_primary", None)
    detail = getattr(primary, "message_detail", None)

    parts = [str(part).strip() for part in (message, detail) if part]
    if sql_query and re.search(r"\)\s+as\s+\w+\s+as\s+\w+\b", sql_query, flags=re.IGNORECASE):
        parts.append("A derived table or subquery may only have one alias. Use a single `AS alias` after the closing parenthesis.")
    if parts:
        return " ".join(parts)
    return str(error).strip() or "SQL execution failed."


def _extract_referenced_objects(
    sql_query: str,
    schema_catalog: dict[str, dict[str, Any]],
    *,
    cte_names: set[str],
) -> tuple[dict[str, str | None], set[str], list[str]]:
    alias_map: dict[str, str | None] = {}
    referenced_names: set[str] = set()
    unknown_object_names: list[str] = []

    for match in SQL_TABLE_REF_PATTERN.finditer(sql_query):
        raw_name = match.group(1)
        alias = match.group(2)
        normalized_raw_name = raw_name.lower()
        if normalized_raw_name in {"select", "values"}:
            continue
        if _is_function_call(sql_query, match.end(1)):
            continue

        resolved_name = _resolve_schema_object_name(normalized_raw_name, schema_catalog)
        alias_name = (alias or normalized_raw_name.rsplit(".", 1)[-1]).lower()

        if not resolved_name and normalized_raw_name not in cte_names:
            unknown_object_names.append(normalized_raw_name)

        alias_map[alias_name] = resolved_name
        referenced_names.add(alias_name)
        referenced_names.add(normalized_raw_name.rsplit(".", 1)[-1])
        if resolved_name:
            referenced_names.add(resolved_name.rsplit(".", 1)[-1])

    return alias_map, referenced_names, unknown_object_names


def _resolve_schema_object_name(
    raw_name: str,
    schema_catalog: dict[str, dict[str, Any]],
) -> str | None:
    if raw_name in schema_catalog:
        return raw_name

    prefixed_name = f"football.{raw_name}"
    if prefixed_name in schema_catalog:
        return prefixed_name

    return None


def _extract_as_aliases(sql_query: str) -> set[str]:
    return {match.group(1).lower() for match in SQL_AS_ALIAS_PATTERN.finditer(sql_query)}


def _extract_cte_names(sql_query: str) -> set[str]:
    return {match.group(1).lower() for match in SQL_CTE_NAME_PATTERN.finditer(sql_query)}


def _is_function_call(sql_query: str, token_end: int) -> bool:
    return sql_query[token_end:].lstrip().startswith("(")


def _format_unknown_column_error(
    column_name: str,
    *,
    referenced_objects: set[str],
    schema_catalog: dict[str, dict[str, Any]],
) -> str:
    close_matches_in_context = []
    for object_name in sorted(referenced_objects):
        suggestions = get_close_matches(
            column_name,
            sorted(schema_catalog[object_name]["column_names_lower"]),
            n=2,
            cutoff=0.45,
        )
        close_matches_in_context.extend(f"{object_name}.{suggestion}" for suggestion in suggestions)

    if close_matches_in_context:
        suggestion_text = ", ".join(dict.fromkeys(close_matches_in_context))
        current_objects = ", ".join(sorted(referenced_objects))
        return (
            f"Column '{column_name}' is not present in the referenced tables/views ({current_objects}). "
            f"Close matches in the current query context: {suggestion_text}. Use the exact listed column name."
        )

    matching_objects = sorted(
        object_name
        for object_name, details in schema_catalog.items()
        if column_name in details["column_names_lower"]
    )

    if matching_objects:
        preview = ", ".join(matching_objects[:3])
        if referenced_objects:
            current_objects = ", ".join(sorted(referenced_objects))
            return (
                f"Column '{column_name}' is not present in the referenced tables/views "
                f"({current_objects}). It exists on {preview}. Join the correct object or use a curated view."
            )

        return (
            f"Column '{column_name}' is not available in the current query context. "
            f"It exists on {preview}. Join the correct object first."
        )

    return (
        f"Column '{column_name}' does not exist in the known football schema catalog. "
        "Use only listed columns from the relevant objects."
    )


def _format_unknown_object_error(
    object_name: str,
    *,
    schema_catalog: dict[str, dict[str, Any]],
) -> str:
    catalog_names = sorted(schema_catalog.keys())
    suggestion_pool = set(catalog_names)
    suggestion_pool.update(name.rsplit(".", 1)[-1] for name in catalog_names)
    suggestions = get_close_matches(object_name, sorted(suggestion_pool), n=3, cutoff=0.6)

    if suggestions:
        suggestion_text = ", ".join(suggestions[:3])
        return (
            f"Table/view '{object_name}' is not present in the known football schema catalog. "
            f"Use one of the listed objects instead, for example: {suggestion_text}."
        )

    return (
        f"Table/view '{object_name}' is not present in the known football schema catalog. "
        "Use only listed football tables or curated views."
    )
