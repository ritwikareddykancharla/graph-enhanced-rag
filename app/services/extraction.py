"""Entity and Relation Extraction Service using LangChain"""

import json
from typing import List, Optional
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_community.chat_models import ChatOpenAI

from app.config import get_settings
from app.models.schemas import Entity, Relation, ExtractionResult

settings = get_settings()

# System prompt for entity/relation extraction
EXTRACTION_PROMPT = """You are a knowledge graph expert. Your task is to extract entities and their relationships from the given text.

Instructions:
1. Identify all important entities (servers, databases, services, APIs, systems, components, etc.)
2. For each entity, determine its type (e.g., 'server', 'database', 'service', 'api', 'component', 'system', 'feature', 'module')
3. Identify all relationships between entities
4. Use descriptive relationship types (e.g., 'depends_on', 'connects_to', 'uses', 'calls', 'hosts', 'contains', 'provides', 'consumes')

Text to analyze:
{text}

{format_instructions}

Important: Return ONLY valid JSON. No additional text or explanation."""

# Alternative prompt for more structured extraction
STRUCTURED_EXTRACTION_PROMPT = """Extract entities and relationships from the following text to build a knowledge graph.

Text:
{text}

Extract:
1. Entities with their names and types (server, database, service, api, component, etc.)
2. Relationships showing how entities are connected (depends_on, connects_to, uses, calls, etc.)

Respond in the following JSON format:
{{
  "entities": [
    {{"name": "Entity Name", "type": "entity_type", "properties": {{}}}}
  ],
  "relations": [
    {{"source": "Source Entity", "target": "Target Entity", "relation_type": "relation_type", "properties": {{}}}}
  ]
}}

JSON Response:"""


class ExtractionService:
    """Service for extracting entities and relations from text using LLM"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize extraction service.

        Args:
            api_key: OpenAI API key (defaults to settings)
            model: LLM model to use (defaults to settings)
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.llm_model

        if not self.api_key:
            raise ValueError("OpenAI API key is required for extraction")

        self._llm = None
        self._parser = PydanticOutputParser(pydantic_object=ExtractionResult)

    @property
    def llm(self):
        """Lazy-load LLM instance"""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.model,
                temperature=0,
                api_key=self.api_key,
            )
        return self._llm

    async def extract(self, text: str) -> ExtractionResult:
        """
        Extract entities and relations from text.

        Args:
            text: Text to extract from

        Returns:
            ExtractionResult containing entities and relations
        """
        # Use structured prompt for better results
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a knowledge graph expert. Extract entities and relationships from text.",
                ),
                ("human", STRUCTURED_EXTRACTION_PROMPT),
            ]
        )

        chain = prompt | self.llm

        try:
            response = await chain.ainvoke({"text": text})
            result = self._parse_response(response.content)
            return result
        except Exception as e:
            # Fallback: try simpler extraction
            return await self._fallback_extract(text, str(e))

    async def _fallback_extract(
        self, text: str, original_error: str
    ) -> ExtractionResult:
        """
        Fallback extraction method if primary fails.

        Args:
            text: Text to extract from
            original_error: Error from primary extraction

        Returns:
            ExtractionResult with basic extraction or empty result
        """
        try:
            # Try with format instructions
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a knowledge graph expert. Extract entities and relationships.",
                    ),
                    ("human", EXTRACTION_PROMPT),
                ]
            )

            chain = prompt | self.llm

            response = await chain.ainvoke(
                {
                    "text": text,
                    "format_instructions": self._parser.get_format_instructions(),
                }
            )

            return self._parse_response(response.content)
        except Exception:
            # Return empty result if all fails
            return ExtractionResult(entities=[], relations=[])

    def _parse_response(self, content: str) -> ExtractionResult:
        """
        Parse LLM response into ExtractionResult.

        Args:
            content: Raw LLM response content

        Returns:
            Parsed ExtractionResult
        """
        # Clean up the response
        content = content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re

            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                except json.JSONDecodeError:
                    return ExtractionResult(entities=[], relations=[])
            else:
                return ExtractionResult(entities=[], relations=[])

        # Parse entities
        entities = []
        for entity_data in data.get("entities", []):
            try:
                entity = Entity(
                    name=entity_data.get("name", ""),
                    type=entity_data.get("type", "unknown"),
                    properties=entity_data.get("properties", {}),
                )
                if entity.name:  # Only add if name is not empty
                    entities.append(entity)
            except Exception:
                continue

        # Parse relations
        relations = []
        for relation_data in data.get("relations", []):
            try:
                relation = Relation(
                    source=relation_data.get("source", ""),
                    target=relation_data.get("target", ""),
                    relation_type=relation_data.get("relation_type", "related_to"),
                    properties=relation_data.get("properties", {}),
                )
                if (
                    relation.source and relation.target
                ):  # Only add if both endpoints exist
                    relations.append(relation)
            except Exception:
                continue

        return ExtractionResult(entities=entities, relations=relations)

    async def extract_batch(self, texts: List[str]) -> List[ExtractionResult]:
        """
        Extract entities and relations from multiple texts.

        Args:
            texts: List of texts to process

        Returns:
            List of ExtractionResults
        """
        results = []
        for text in texts:
            result = await self.extract(text)
            results.append(result)
        return results
