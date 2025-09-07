import pytest


@pytest.fixture(scope="module")
def sid() -> str:
    return "test_sid"
