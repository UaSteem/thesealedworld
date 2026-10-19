import pytest
from pydantic import ValidationError

from src.backend.config.settings import BackendSettings
from src.frontend.config.settings import FrontendSettings


@pytest.mark.parametrize(
    "settings_type,key_field",
    [(BackendSettings, "frontend_internal_service_key"), (FrontendSettings, "backend_internal_service_key")],
)
@pytest.mark.parametrize("invalid", ["", "   ", "change-me-example", "dev-example"])
@pytest.mark.parametrize("field", ["secret_key", "service_key"])
def test_production_rejects_unconfigured_keys(settings_type, key_field, invalid, field):
    values = {"debug": False, "secret_key": "test-production-signing-key", key_field: "test-production-service-key"}  # pragma: allowlist secret
    values["secret_key" if field == "secret_key" else key_field] = invalid
    with pytest.raises(ValidationError, match="Production settings"):
        settings_type(_env_file=None, **values)


@pytest.mark.parametrize(
    "settings_type,key_field",
    [(BackendSettings, "frontend_internal_service_key"), (FrontendSettings, "backend_internal_service_key")],
)
def test_explicit_production_keys_and_debug_defaults(settings_type, key_field):
    assert settings_type(_env_file=None, debug=True).debug
    assert not settings_type(
        _env_file=None,
        debug=False,
        secret_key="test-production-signing-key",  # pragma: allowlist secret
        **{key_field: "test-production-service-key"},
    ).debug


@pytest.mark.parametrize("primary", [None, ""])
def test_backend_legacy_fallback_requires_explicitly_empty_primary(primary):
    result = BackendSettings(
        _env_file=None,
        debug=False,
        secret_key="test-production-signing-key",  # pragma: allowlist secret
        frontend_internal_service_key=primary,
        site_to_game_service_key="test-production-fallback",  # pragma: allowlist secret
    )
    assert result.frontend_internal_service_key == primary
    # A configured primary always wins; do not silently substitute the legacy key.
    with pytest.raises(ValidationError, match="Production settings"):
        BackendSettings(
            _env_file=None,
            debug=False,
            secret_key="test-production-signing-key",  # pragma: allowlist secret
            frontend_internal_service_key="dev-invalid",  # pragma: allowlist secret
            site_to_game_service_key="test-production-fallback",  # pragma: allowlist secret
        )
