"""Normalization utilities for entity and relation canonicalization."""

from __future__ import annotations

import re
from typing import Dict

ENTITY_TYPE_MAP: Dict[str, str] = {
    "svc": "service",
    "service": "service",
    "api": "api",
    "app": "application",
    "application": "application",
    "db": "database",
    "database": "database",
    "datastore": "database",
    "cache": "cache",
    "redis": "cache",
    "server": "server",
    "host": "server",
    "component": "component",
    "module": "component",
    "pipeline": "pipeline",
    "job": "job",
    "system": "system",
    "platform": "system",
    "model": "model",
    "feature": "feature",
}

RELATION_TYPE_MAP: Dict[str, str] = {
    "depends_on": "depends_on",
    "dependson": "depends_on",
    "depends": "depends_on",
    "uses": "uses",
    "use": "uses",
    "calls": "calls",
    "invokes": "calls",
    "connects_to": "connects_to",
    "connects": "connects_to",
    "connected_to": "connects_to",
    "reads_from": "reads_from",
    "writes_to": "writes_to",
    "publishes_to": "publishes_to",
    "consumes": "consumes",
    "queries": "queries",
    "triggers": "triggers",
    "loads": "loads",
    "hosted_on": "hosted_on",
    "runs": "runs",
    "provides": "provides",
    "owns": "owns",
}


def normalize_text(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\s_-]", " ", value)
    value = re.sub(r"[_-]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_entity_name(name: str) -> str:
    return normalize_text(name)


def normalize_entity_type(entity_type: str) -> str:
    if not entity_type:
        return "unknown"
    key = normalize_text(entity_type)
    return ENTITY_TYPE_MAP.get(key, key)


def normalize_relation_type(relation_type: str) -> str:
    if not relation_type:
        return "related_to"
    key = normalize_text(relation_type).replace(" ", "_")
    return RELATION_TYPE_MAP.get(key, key)
