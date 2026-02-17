"""Optional LLM-assisted canonicalization for entities and relations."""

from __future__ import annotations

from typing import Optional
from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI

from app.config import get_settings
from app.models.schemas import ExtractionResult, Entity, Relation
from app.utils.normalization import normalize_entity_type, normalize_relation_type

settings = get_settings()

CANONICALIZATION_PROMPT = """You are a data quality assistant for a knowledge graph system.
Given extracted entities and relations, normalize entity types and relation types to a
short, consistent vocabulary.

Return JSON ONLY with this schema:
{
  "entities": [{"name": "...", "type": "..."}],
  "relations": [{"source": "...", "target": "...", "relation_type": "..."}]
}

Rules:
- Keep entity names unchanged.
- Normalize entity types to coarse labels (service, api, database, cache, server, application, component, system, model, feature, pipeline, job, unknown).
- Normalize relation types to short snake_case verbs (depends_on, uses, calls, connects_to, reads_from, writes_to, publishes_to, consumes, queries, triggers, loads, hosted_on, runs, provides, owns, related_to).
- If uncertain, use "unknown" for type and "related_to" for relation_type.

Entities:
{entities}

Relations:
{relations}
"""


class CanonicalizationService:
    """LLM-assisted canonicalization."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.llm_model
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            if not self.api_key:
                raise ValueError("OpenAI API key is required for canonicalization")
            self._llm = ChatOpenAI(model=self.model, temperature=0, api_key=self.api_key)
        return self._llm

    async def canonicalize(self, extraction: ExtractionResult) -> ExtractionResult:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You normalize knowledge graph labels."),
                ("human", CANONICALIZATION_PROMPT),
            ]
        )
        chain = prompt | self.llm

        entities_payload = [
            {"name": e.name, "type": e.type} for e in extraction.entities
        ]
        relations_payload = [
            {"source": r.source, "target": r.target, "relation_type": r.relation_type}
            for r in extraction.relations
        ]

        response = await chain.ainvoke(
            {"entities": entities_payload, "relations": relations_payload}
        )

        try:
            import json

            data = json.loads(response.content)
        except Exception:
            # Fallback to deterministic normalization if LLM output fails
            return self._deterministic_fallback(extraction)

        entities = []
        for ent in data.get("entities", []):
            name = ent.get("name", "")
            ent_type = normalize_entity_type(ent.get("type", ""))
            if name:
                entities.append(Entity(name=name, type=ent_type, properties={}))

        relations = []
        for rel in data.get("relations", []):
            source = rel.get("source", "")
            target = rel.get("target", "")
            rel_type = normalize_relation_type(rel.get("relation_type", ""))
            if source and target:
                relations.append(
                    Relation(
                        source=source,
                        target=target,
                        relation_type=rel_type,
                        properties={},
                    )
                )

        return ExtractionResult(entities=entities, relations=relations)

    def _deterministic_fallback(self, extraction: ExtractionResult) -> ExtractionResult:
        entities = [
            Entity(
                name=e.name,
                type=normalize_entity_type(e.type),
                properties=e.properties or {},
            )
            for e in extraction.entities
            if e.name
        ]

        relations = [
            Relation(
                source=r.source,
                target=r.target,
                relation_type=normalize_relation_type(r.relation_type),
                properties=r.properties or {},
            )
            for r in extraction.relations
            if r.source and r.target
        ]

        return ExtractionResult(entities=entities, relations=relations)
