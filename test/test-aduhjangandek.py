import pytest
from main import attack

@pytest.mark.asyncio
async def test_attack_basic():
    assert callable(attack)