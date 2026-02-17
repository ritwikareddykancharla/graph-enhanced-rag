#!/usr/bin/env python
"""Run extraction evaluation against a labeled JSONL dataset."""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Tuple

from app.services.extraction import ExtractionService


def _norm(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _entity_key(entity: Dict[str, str]) -> Tuple[str, str]:
    return (_norm(entity.get("name", "")), _norm(entity.get("type", "")))


def _entity_name_key(entity: Dict[str, str]) -> str:
    return _norm(entity.get("name", ""))


def _relation_key(rel: Dict[str, str]) -> Tuple[str, str, str]:
    return (
        _norm(rel.get("source", "")),
        _norm(rel.get("target", "")),
        _norm(rel.get("relation_type", "")),
    )


def _precision_recall_f1(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    precision = tp / (tp + fp) if tp + fp > 0 else 0.0
    recall = tp / (tp + fn) if tp + fn > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall > 0
        else 0.0
    )
    return precision, recall, f1


def _score_sets(pred: set, gold: set) -> Tuple[int, int, int]:
    tp = len(pred & gold)
    fp = len(pred - gold)
    fn = len(gold - pred)
    return tp, fp, fn


async def _evaluate(dataset_path: Path, model: str | None) -> int:
    if not dataset_path.exists():
        print(f"Dataset not found: {dataset_path}")
        return 1

    service = ExtractionService(model=model)

    entity_strict = {"tp": 0, "fp": 0, "fn": 0}
    entity_name = {"tp": 0, "fp": 0, "fn": 0}
    relation_strict = {"tp": 0, "fp": 0, "fn": 0}

    samples = 0

    with dataset_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            samples += 1
            text = record["text"]

            prediction = await service.extract(text)

            pred_entities = [e.model_dump() for e in prediction.entities]
            pred_relations = [r.model_dump() for r in prediction.relations]

            gold_entities = record.get("entities", [])
            gold_relations = record.get("relations", [])

            pred_entity_set = {_entity_key(e) for e in pred_entities if e.get("name")}
            gold_entity_set = {_entity_key(e) for e in gold_entities if e.get("name")}

            pred_entity_name_set = {
                _entity_name_key(e) for e in pred_entities if e.get("name")
            }
            gold_entity_name_set = {
                _entity_name_key(e) for e in gold_entities if e.get("name")
            }

            pred_relation_set = {
                _relation_key(r)
                for r in pred_relations
                if r.get("source") and r.get("target")
            }
            gold_relation_set = {
                _relation_key(r)
                for r in gold_relations
                if r.get("source") and r.get("target")
            }

            tp, fp, fn = _score_sets(pred_entity_set, gold_entity_set)
            entity_strict["tp"] += tp
            entity_strict["fp"] += fp
            entity_strict["fn"] += fn

            tp, fp, fn = _score_sets(pred_entity_name_set, gold_entity_name_set)
            entity_name["tp"] += tp
            entity_name["fp"] += fp
            entity_name["fn"] += fn

            tp, fp, fn = _score_sets(pred_relation_set, gold_relation_set)
            relation_strict["tp"] += tp
            relation_strict["fp"] += fp
            relation_strict["fn"] += fn

            print(f"\nSample {record.get('id', samples)}")
            print(f"Text: {text}")
            print(f"Pred entities: {len(pred_entities)} | Gold entities: {len(gold_entities)}")
            print(
                f"Pred relations: {len(pred_relations)} | Gold relations: {len(gold_relations)}"
            )

    ep, er, ef = _precision_recall_f1(**entity_strict)
    enp, enr, enf = _precision_recall_f1(**entity_name)
    rp, rr, rf = _precision_recall_f1(**relation_strict)

    print("\n=== Aggregate Results ===")
    print(f"Samples: {samples}")
    print(
        "Entities (strict name+type)  P={:.3f} R={:.3f} F1={:.3f}".format(
            ep, er, ef
        )
    )
    print(
        "Entities (name only)         P={:.3f} R={:.3f} F1={:.3f}".format(
            enp, enr, enf
        )
    )
    print(
        "Relations (strict)           P={:.3f} R={:.3f} F1={:.3f}".format(
            rp, rr, rf
        )
    )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run extraction evaluation")
    parser.add_argument(
        "--dataset",
        default="backend/evals/dataset.jsonl",
        help="Path to JSONL dataset",
    )
    parser.add_argument("--model", default=None, help="LLM model override")
    args = parser.parse_args()

    return asyncio.run(_evaluate(Path(args.dataset), args.model))


if __name__ == "__main__":
    raise SystemExit(main())
