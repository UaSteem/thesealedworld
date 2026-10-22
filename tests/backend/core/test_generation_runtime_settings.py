"""Runtime workers do not acquire API credentials through shared imports."""

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
AUTH_FIELDS = {"secret_key", "frontend_internal_service_key", "site_to_game_service_key"}


def _isolated_import(
    tmp_path, module: str, *, valid_auth: bool = False, worker_first: str | None = None, startup: bool = False
):
    environment = os.environ.copy()
    fields = set()
    for source in (ROOT / "src/backend/config").glob("*.py"):
        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                fields.add(node.target.id.upper())
    fields.update({"REDIS_URL", "REDIS_HOST", "REDIS_PORT", "REDIS_PASSWORD", "REDIS_TIMEOUT", "REDIS_MAX_CONNECTIONS"})
    for name in fields:
        environment.pop(name, None)
    environment.update(
        DEBUG="False",
        DATABASE_URL="postgresql+asyncpg://synthetic:synthetic@db.invalid/game",  # pragma: allowlist secret
        GAME_DATABASE_URL="postgresql+asyncpg://synthetic:synthetic@db.invalid/game",  # pragma: allowlist secret
        MONGO_URL="mongodb://mongo.invalid:27017",
        REDIS_URL="redis://cache.invalid:6379/0",
        PYTHONPATH=str(ROOT),
        TARGET_MODULE=module,
        WORKER_FIRST=worker_first or "",
        CHECK_STARTUP=str(startup),
        GEMINI_API_KEY="synthetic-gemini-key",  # pragma: allowlist secret
        GEMINI_MODEL="synthetic-gemini-model",
    )
    if valid_auth:
        environment.update(
            SECRET_KEY="synthetic-production-key",  # pragma: allowlist secret
            FRONTEND_INTERNAL_SERVICE_KEY="synthetic-service-key",  # pragma: allowlist secret
        )
    script = """
import importlib, os, socket, pydantic_settings, sys, asyncio
# Windows creates its internal event-loop self-pipe using a local socket pair.
# Create that loop before installing the guard; all application adapters stay guarded.
startup_loop = asyncio.new_event_loop() if os.environ['CHECK_STARTUP'] == 'True' else None
def forbidden(*a, **k): raise AssertionError('No network during settings test')
socket.socket.connect = forbidden
socket.socket.connect_ex = forbidden
socket.create_connection = forbidden
original = pydantic_settings.SettingsConfigDict
def without_dotenv(*a, **k):
    k['env_file'] = None
    return original(*a, **k)
pydantic_settings.SettingsConfigDict = without_dotenv
import src.shared.infrastructure.logging_config as logging_config
logging_config.setup_logging = lambda *a, **k: None
if os.environ['WORKER_FIRST']:
    importlib.import_module(os.environ['WORKER_FIRST'])
module = importlib.import_module(os.environ['TARGET_MODULE'])
if os.environ['TARGET_MODULE'].endswith('chat.workers.archive'):
    from src.backend.config.runtime import runtime_settings
    from src.backend.core.database import load_orm_models
    load_orm_models()
    assert 'src.backend.config.settings' not in sys.modules
    worker = module.ChatArchiveWorkerSettings
    assert worker.redis_settings.host == 'cache.invalid'
    assert worker.functions == [module.archive_chat_buffers]
    assert worker.max_jobs == 1
    assert len(worker.cron_jobs) == 1
    assert worker.cron_jobs[0].minute == {0,10,20,30,40,50}
    if os.environ['CHECK_STARTUP'] == 'True':
        from types import SimpleNamespace
        calls = []
        async def close(): calls.append('closed')
        client = SimpleNamespace(aclose=close)
        def from_url(url, **kwargs):
            calls.append((url, kwargs))
            return client
        module.aioredis.from_url = from_url
        async def exercise():
            ctx = {}
            await module.startup(ctx)
            assert ctx['redis'] is client
            await module.shutdown(ctx)
        try:
            startup_loop.run_until_complete(exercise())
        finally:
            startup_loop.close()
        assert calls == [(runtime_settings.effective_redis_url, {'decode_responses': True}), 'closed']
    assert 'src.backend.config.settings' not in sys.modules
is_system = os.environ['TARGET_MODULE'].endswith('system.workers.arq')
is_combat = os.environ['TARGET_MODULE'].endswith('combat.workers.arq')
is_simulation = os.environ['TARGET_MODULE'].endswith('combat.workers.ai_simulation_arq')
if is_system or is_combat or is_simulation or os.environ['TARGET_MODULE'].endswith('generation_ai.workers.arq'):
    from src.backend.config.runtime import RuntimeSettings, runtime_settings
    assert not {'secret_key','frontend_internal_service_key','site_to_game_service_key',
                'operator_read_key','operator_write_key','monster_catalog_read_key',
                'monster_catalog_write_key'} & RuntimeSettings.model_fields.keys()
    assert 'src.backend.config.settings' not in sys.modules
    assert runtime_settings.debug is False
    from src.backend.core.database import load_orm_models
    load_orm_models()
    assert 'src.backend.config.settings' not in sys.modules
    if os.environ['CHECK_STARTUP'] == 'True':
        import asyncio
        from types import SimpleNamespace
        import src.backend.core.arq as core_arq
        import src.backend.core.arq_container as container
        import src.backend.core.ai as ai
        calls = []
        async def platform_noop(ctx): pass
        async def close_noop(): pass
        core_arq.platform_base_startup = platform_noop
        core_arq.platform_base_shutdown = platform_noop
        fake_client = SimpleNamespace(aclose=close_noop)
        def from_url(url, **kwargs):
            calls.append(('redis', url, kwargs))
            return fake_client
        container.redis.from_url = from_url
        container.RedisService = lambda client: SimpleNamespace(client=client)
        class ConfigManager:
            def __init__(self, client): self.registered = []
            def register(self, config): self.registered.append(config)
            async def bootstrap(self): calls.append(('configs', len(self.registered)))
        container.GameConfigManager = ConfigManager
        managers = SimpleNamespace(**{name: object() for name in (
            'character_sessions','actor_commitments','scenario_sessions',
            'scenario_content','world_locations','expeditions')})
        container.build_redis_managers = lambda *a: managers
        container.StreamProducer = lambda client, name: SimpleNamespace(stream_name=name)
        class Provider:
            def __init__(self, **kwargs): calls.append(('gemini', kwargs))
        ai.GeminiProvider = Provider
        ctx = {}
        async def exercise():
            if is_combat:
                await module.combat_startup(ctx)
                assert ctx['arq_service'].queue_name == 'tbmmorpg:arq:combat'
                assert isinstance(ctx['combat_data_service'], module.CombatSessionIntegration)
                assert isinstance(ctx['combat_executor'], module.CombatExecutor)
                assert isinstance(ctx['ai_processor'], module.AiProcessor)
                assert ctx['combat_collector'].data_service is ctx['combat_data_service']
                assert ctx['turn_manager'].combat_sessions is ctx['combat_data_service']
                assert ctx['turn_manager'].arq is ctx['arq_service']
                assert ctx['turn_manager'].game_config is ctx['game_config']
                assert 'ai' not in ctx
            elif is_simulation:
                await module.combat_ai_simulation_startup(ctx)
                worker = module.CombatAiSimulationArqSettings
                assert worker.queue_name == 'tbmmorpg:arq:combat_ai_simulation'
                assert worker.max_jobs == 1 and worker.job_timeout == 2400
                assert worker.keep_result == 0
                assert {f.coroutine.__name__: (f.timeout_s, f.max_tries) for f in worker.functions} == {
                    'combat_ai_live_simulation_task': (180, 1),
                    'combat_family_pressure_task': (2400, 1),
                    'combat_ai_synthetic_training_task': (900, 1),
                    'combat_ai_battle_training_task': (2400, 1),
                }
                assert 'ai' not in ctx
            elif is_system:
                await module.system_startup(ctx)
                assert ctx['system_arq'].queue_name == 'tbmmorpg:arq:system'
                assert 'ai' not in ctx
            else:
                await module.generation_ai_startup(ctx)
                assert ctx['generation_ai_arq'].queue_name == 'tbmmorpg:arq:generation_ai'
                assert isinstance(ctx['ai'].provider, Provider)
            assert ctx['events']._producer.stream_name == runtime_settings.game_stream_name
            assert ctx['events']._maxlen == runtime_settings.game_stream_maxlen
            if is_combat:
                await module.combat_shutdown(ctx)
            elif is_simulation:
                await module.combat_ai_simulation_shutdown(ctx)
            elif is_system:
                await module.system_shutdown(ctx)
            else:
                await module.generation_ai_shutdown(ctx)
        try:
            startup_loop.run_until_complete(exercise())
        finally:
            startup_loop.close()
        assert ('redis', runtime_settings.effective_redis_url, {'decode_responses': True}) in calls
        if is_system or is_combat or is_simulation:
            assert not any(call[0] == 'gemini' for call in calls)
        else:
            assert ('gemini', {'api_key': 'synthetic-gemini-key', 'model': 'synthetic-gemini-model'}) in calls  # pragma: allowlist secret - synthetic fixture
        from src.backend.core.database.session import async_engine
        assert async_engine.url.host == 'db.invalid'
        from src.backend.infrastructure.mongo.client import get_mongo_provider
        assert get_mongo_provider().url == runtime_settings.mongo_url
        assert 'src.backend.config.settings' not in sys.modules
"""
    return subprocess.run(
        [sys.executable, "-c", script], env=environment, cwd=tmp_path, capture_output=True, text=True, timeout=45
    )


def test_generation_worker_imports_without_api_auth_settings(tmp_path):
    result = _isolated_import(tmp_path, "src.backend.features.generation_ai.workers.arq")
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "module",
    [
        "src.backend.config.settings",
        "src.backend.app",
        "src.backend.chat.app",
    ],
)
def test_authenticated_entrypoints_still_reject_missing_production_auth(tmp_path, module):
    result = _isolated_import(tmp_path, module)
    assert result.returncode != 0
    assert "Production settings cannot use default or development secret keys" in result.stderr


def test_backend_settings_still_accept_valid_production_auth(tmp_path):
    result = _isolated_import(tmp_path, "src.backend.config.settings", valid_auth=True)
    assert result.returncode == 0, result.stderr


def test_generation_runtime_startup_wiring_without_auth_or_external_io(tmp_path):
    result = _isolated_import(tmp_path, "src.backend.features.generation_ai.workers.arq", startup=True)
    assert result.returncode == 0, result.stderr


def test_generation_import_does_not_weaken_api_in_same_process(tmp_path):
    result = _isolated_import(
        tmp_path, "src.backend.app", worker_first="src.backend.features.generation_ai.workers.arq"
    )
    assert result.returncode != 0
    assert "Production settings cannot use default or development secret keys" in result.stderr


def test_system_worker_imports_without_api_auth_settings(tmp_path):
    result = _isolated_import(tmp_path, "src.backend.features.system.workers.arq")
    assert result.returncode == 0, result.stderr


def test_system_runtime_startup_wiring_without_auth_or_external_io(tmp_path):
    result = _isolated_import(tmp_path, "src.backend.features.system.workers.arq", startup=True)
    assert result.returncode == 0, result.stderr


def test_system_import_does_not_weaken_api_in_same_process(tmp_path):
    result = _isolated_import(tmp_path, "src.backend.app", worker_first="src.backend.features.system.workers.arq")
    assert result.returncode != 0
    assert "Production settings cannot use default or development secret keys" in result.stderr


def test_combat_worker_imports_without_api_auth_settings(tmp_path):
    result = _isolated_import(tmp_path, "src.backend.features.combat.workers.arq")
    assert result.returncode == 0, result.stderr


def test_combat_runtime_startup_wiring_without_auth_or_external_io(tmp_path):
    result = _isolated_import(tmp_path, "src.backend.features.combat.workers.arq", startup=True)
    assert result.returncode == 0, result.stderr


def test_combat_import_does_not_weaken_api_in_same_process(tmp_path):
    result = _isolated_import(tmp_path, "src.backend.app", worker_first="src.backend.features.combat.workers.arq")
    assert result.returncode != 0
    assert "Production settings cannot use default or development secret keys" in result.stderr


def test_simulation_worker_imports_without_api_auth_settings(tmp_path):
    result = _isolated_import(tmp_path, "src.backend.features.combat.workers.ai_simulation_arq")
    assert result.returncode == 0, result.stderr


def test_simulation_runtime_startup_wiring_without_auth_or_external_io(tmp_path):
    result = _isolated_import(tmp_path, "src.backend.features.combat.workers.ai_simulation_arq", startup=True)
    assert result.returncode == 0, result.stderr


def test_simulation_import_does_not_weaken_api_in_same_process(tmp_path):
    result = _isolated_import(
        tmp_path, "src.backend.app", worker_first="src.backend.features.combat.workers.ai_simulation_arq"
    )
    assert result.returncode != 0
    assert "Production settings cannot use default or development secret keys" in result.stderr


def test_archive_worker_imports_without_api_auth_settings(tmp_path):
    result = _isolated_import(tmp_path, "src.backend.chat.workers.archive")
    assert result.returncode == 0, result.stderr


def test_archive_runtime_startup_wiring_without_auth_or_external_io(tmp_path):
    result = _isolated_import(tmp_path, "src.backend.chat.workers.archive", startup=True)
    assert result.returncode == 0, result.stderr


def test_archive_import_does_not_weaken_api_in_same_process(tmp_path):
    result = _isolated_import(tmp_path, "src.backend.app", worker_first="src.backend.chat.workers.archive")
    assert result.returncode != 0
    assert "Production settings cannot use default or development secret keys" in result.stderr


def test_backend_migration_management_imports_without_api_auth(tmp_path):
    result = _isolated_import(tmp_path, "src.backend.manage")
    assert result.returncode == 0, result.stderr


def test_management_import_does_not_weaken_api_in_same_process(tmp_path):
    result = _isolated_import(tmp_path, "src.backend.app", worker_first="src.backend.manage")
    assert result.returncode != 0
    assert "Production settings cannot use default or development secret keys" in result.stderr
