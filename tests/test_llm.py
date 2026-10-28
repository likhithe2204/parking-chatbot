import pytest
from langchain_openai import AzureChatOpenAI

from app.llm import get_llm

SETTINGS = ["DIAL_API_KEY", "DIAL_ENDPOINT", "DIAL_API_VERSION", "DIAL_DEPLOYMENT"]


def test_get_llm_fails_without_settings(monkeypatch):
    for name in SETTINGS:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(KeyError):
        get_llm()


def test_get_llm_builds_client_from_environment(monkeypatch):
    monkeypatch.setenv("DIAL_API_KEY", "test-key")
    monkeypatch.setenv("DIAL_ENDPOINT", "https://example.invalid")
    monkeypatch.setenv("DIAL_API_VERSION", "2024-02-01")
    monkeypatch.setenv("DIAL_DEPLOYMENT", "test-deployment")
    llm = get_llm()
    assert isinstance(llm, AzureChatOpenAI)
    assert llm.deployment_name == "test-deployment"