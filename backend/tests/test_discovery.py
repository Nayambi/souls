import pytest
from app.core.discovery import discover_topics

@pytest.mark.asyncio
async def test_discover_topics_returns_list():
    topics = await discover_topics()
    assert isinstance(topics, list)