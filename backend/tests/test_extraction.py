"""Tests for the extraction service"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.extraction import ExtractionService
from app.models.schemas import ExtractionResult, Entity, Relation


class TestExtractionService:
    """Tests for ExtractionService"""

    @pytest.mark.asyncio
    async def test_extract_entities_and_relations(self):
        """Test successful extraction of entities and relations"""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = """
        {
            "entities": [
                {"name": "Server A", "type": "server", "properties": {}},
                {"name": "Database B", "type": "database", "properties": {}}
            ],
            "relations": [
                {"source": "Server A", "target": "Database B", "relation_type": "depends_on", "properties": {}}
            ]
        }
        """

        service = ExtractionService.__new__(ExtractionService)
        service._llm = MagicMock()
        service._llm.ainvoke = AsyncMock(return_value=mock_response)

        # Create proper mock for chain
        with patch.object(service, "llm", service._llm):
            with patch("app.services.extraction.ChatPromptTemplate") as mock_template:
                mock_chain = MagicMock()
                mock_chain.ainvoke = AsyncMock(return_value=mock_response)
                mock_template.from_messages.return_value.__or__ = MagicMock(
                    return_value=mock_chain
                )

                result = await service.extract("Server A depends on Database B")

        assert isinstance(result, ExtractionResult)
        assert len(result.entities) == 2
        assert len(result.relations) == 1
        assert result.entities[0].name == "Server A"
        assert result.relations[0].relation_type == "depends_on"

    def test_parse_response_valid_json(self):
        """Test parsing valid JSON response"""
        service = ExtractionService.__new__(ExtractionService)

        content = """
        {
            "entities": [
                {"name": "Payment Service", "type": "service"},
                {"name": "Auth API", "type": "api"}
            ],
            "relations": [
                {"source": "Payment Service", "target": "Auth API", "relation_type": "uses"}
            ]
        }
        """

        result = service._parse_response(content)

        assert len(result.entities) == 2
        assert len(result.relations) == 1
        assert result.entities[0].name == "Payment Service"
        assert result.entities[1].type == "api"

    def test_parse_response_with_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks"""
        service = ExtractionService.__new__(ExtractionService)

        content = """
        ```json
        {
            "entities": [
                {"name": "Cache", "type": "service"}
            ],
            "relations": []
        }
        ```
        """

        result = service._parse_response(content)

        assert len(result.entities) == 1
        assert result.entities[0].name == "Cache"

    def test_parse_response_invalid_json(self):
        """Test handling invalid JSON"""
        service = ExtractionService.__new__(ExtractionService)

        content = "This is not valid JSON"

        result = service._parse_response(content)

        assert len(result.entities) == 0
        assert len(result.relations) == 0

    def test_parse_response_empty_entities(self):
        """Test handling empty entity name"""
        service = ExtractionService.__new__(ExtractionService)

        content = """
        {
            "entities": [
                {"name": "", "type": "server"},
                {"name": "Valid Entity", "type": "service"}
            ],
            "relations": []
        }
        """

        result = service._parse_response(content)

        # Empty name entities should be filtered out
        assert len(result.entities) == 1
        assert result.entities[0].name == "Valid Entity"
