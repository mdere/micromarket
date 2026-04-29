from app.core.config import Settings


def test_settings_can_load_services_api_env_file_from_repo_root(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / "services" / "api" / ".env"
    env_file.parent.mkdir(parents=True)
    env_file.write_text(
        "\n".join(
            [
                "MICROMARKET_ENV=test-env-file",
                "SENTIMENT_PROVIDER=ollama",
                "OLLAMA_SENTIMENT_MODEL=test-model:latest",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    settings = Settings()

    assert settings.environment == "test-env-file"
    assert settings.sentiment_provider == "ollama"
    assert settings.ollama_sentiment_model == "test-model:latest"
