# Evaluation Dataset

This folder contains labeled examples for entity and relation extraction evaluation.

## Format

`dataset.jsonl` uses one JSON object per line:

```
{
  "id": "sample_01",
  "text": "...",
  "entities": [{"name": "Service A", "type": "service"}],
  "relations": [{"source": "Service A", "target": "Database B", "relation_type": "depends_on"}]
}
```

## Notes

- Keep labels consistent and concise.
- Types are coarse on purpose to avoid overfitting to ontology.
- Relations should use the canonical verb phrase used by the system prompt (e.g., `depends_on`, `uses`, `calls`).
