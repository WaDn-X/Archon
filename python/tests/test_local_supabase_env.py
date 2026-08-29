"""Unit tests for local Supabase env bootstrap JWT helpers."""

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
SCRIPT_PATH = SCRIPTS_DIR / "local_supabase_env.py"


def load_local_supabase_env_module():
	spec = importlib.util.spec_from_file_location("local_supabase_env", SCRIPT_PATH)
	if spec is None or spec.loader is None:
		raise RuntimeError(f"Unable to load module from {SCRIPT_PATH}")
	module = importlib.util.module_from_spec(spec)
	sys.modules["local_supabase_env"] = module
	spec.loader.exec_module(module)
	return module


local_supabase_env = load_local_supabase_env_module()


@pytest.mark.parametrize(
	("role", "expected_valid"),
	[
		("service_role", True),
		("anon", False),
	],
)
def test_mint_supabase_jwt_role_claim(role: str, expected_valid: bool) -> None:
	secret = "a" * 32
	token = local_supabase_env.mint_supabase_jwt(role, secret)

	payload = local_supabase_env.decode_jwt_payload(token)
	assert payload["role"] == role
	assert payload["iss"] == "supabase"
	assert "iat" in payload
	assert "exp" in payload
	assert local_supabase_env.verify_jwt_signature(token, secret) is True
	assert local_supabase_env.verify_jwt_signature(token, "wrong-secret" * 3) is False

	from src.server.config.config import validate_supabase_key

	is_valid, _ = validate_supabase_key(token)
	assert is_valid is expected_valid


def test_generate_jwt_secret_meets_minimum_length() -> None:
	secret = local_supabase_env.generate_jwt_secret()
	assert len(secret) >= 32


def test_is_cloud_supabase_url() -> None:
	assert local_supabase_env.is_cloud_supabase_url("https://abc.supabase.co") is True
	assert local_supabase_env.is_cloud_supabase_url("http://supabase-kong:8000") is False
	assert local_supabase_env.is_cloud_supabase_url("") is False


def test_apply_env_updates_replaces_and_appends(tmp_path: Path) -> None:
	env_path = tmp_path / ".env"
	env_path.write_text(
		"HOST=localhost\nSUPABASE_URL=\nLOG_LEVEL=INFO\n",
		encoding="utf-8",
	)
	updates = {
		"SUPABASE_URL": "http://supabase-kong:8000",
		"JWT_SECRET": "x" * 32,
	}
	updated = local_supabase_env.apply_env_updates(env_path.read_text(encoding="utf-8"), updates)

	assert "SUPABASE_URL=http://supabase-kong:8000" in updated
	assert "HOST=localhost" in updated
	assert "JWT_SECRET=" + ("x" * 32) in updated


def test_bootstrap_writes_separate_file_for_cloud_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(local_supabase_env, "REPO_ROOT", tmp_path)
	monkeypatch.setattr(local_supabase_env, "ENV_FILE", tmp_path / ".env")
	monkeypatch.setattr(local_supabase_env, "LOCAL_ENV_FILE", tmp_path / ".env.local-supabase")
	monkeypatch.setattr(local_supabase_env, "ENV_EXAMPLE", tmp_path / ".env.example")

	(tmp_path / ".env").write_text(
		"SUPABASE_URL=https://my-project.supabase.co\nSUPABASE_SERVICE_KEY=cloud-key\n",
		encoding="utf-8",
	)

	target = local_supabase_env.bootstrap_local_supabase_env()
	assert target == tmp_path / ".env.local-supabase"
	assert (tmp_path / ".env.local-supabase").exists()
	cloud_env = (tmp_path / ".env").read_text(encoding="utf-8")
	assert "https://my-project.supabase.co" in cloud_env
	assert "cloud-key" in cloud_env

	local_env = local_supabase_env.parse_env_file(tmp_path / ".env.local-supabase")
	assert local_env["SUPABASE_URL"] == "http://supabase-kong:8000"
	assert local_env["STORAGE_BACKEND"] == "supabase"
	assert local_supabase_env.verify_jwt_signature(local_env["SUPABASE_SERVICE_KEY"], local_env["JWT_SECRET"])


def test_bootstrap_updates_env_in_place_for_local_setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(local_supabase_env, "REPO_ROOT", tmp_path)
	monkeypatch.setattr(local_supabase_env, "ENV_FILE", tmp_path / ".env")
	monkeypatch.setattr(local_supabase_env, "LOCAL_ENV_FILE", tmp_path / ".env.local-supabase")
	monkeypatch.setattr(local_supabase_env, "ENV_EXAMPLE", tmp_path / ".env.example")

	(tmp_path / ".env").write_text("HOST=localhost\nSUPABASE_URL=\n", encoding="utf-8")

	target = local_supabase_env.bootstrap_local_supabase_env()
	assert target == tmp_path / ".env"
	content = (tmp_path / ".env").read_text(encoding="utf-8")
	assert "HOST=localhost" in content
	assert "SUPABASE_URL=http://supabase-kong:8000" in content
