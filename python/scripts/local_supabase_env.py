#!/usr/bin/env python3
"""
Bootstrap environment variables for the docker compose local-supabase profile.

Generates JWT_SECRET (if missing) and Supabase-style service_role / anon JWTs,
then writes them to .env or .env.local-supabase without overwriting cloud credentials.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import hmac
import json
import re
import secrets
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_EXAMPLE = REPO_ROOT / ".env.example"
ENV_FILE = REPO_ROOT / ".env"
LOCAL_ENV_FILE = REPO_ROOT / ".env.local-supabase"

SUPABASE_URL_DOCKER = "http://supabase-kong:8000"
SUPABASE_URL_HOST = "http://localhost:8000"

JWT_ISS = "supabase"
JWT_IAT = 1_700_000_000
JWT_EXP = 2_000_000_000

LOCAL_SUPABASE_KEYS = (
	"STORAGE_BACKEND",
	"SUPABASE_URL",
	"SUPABASE_SERVICE_KEY",
	"SUPABASE_ANON_KEY",
	"SUPABASE_JWT_SECRET",
	"JWT_SECRET",
	"POSTGRES_USER",
	"POSTGRES_PASSWORD",
	"POSTGRES_DB",
	"POSTGRES_PORT",
	"SUPABASE_API_PORT",
)

ENV_LINE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def b64url_encode(data: bytes) -> str:
	return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(data: str) -> bytes:
	padding = "=" * (-len(data) % 4)
	return base64.urlsafe_b64decode(data + padding)


def mint_supabase_jwt(role: str, secret: str) -> str:
	"""Mint a Supabase-style HS256 JWT for the given role."""
	header = {"alg": "HS256", "typ": "JWT"}
	payload = {
		"role": role,
		"iss": JWT_ISS,
		"iat": JWT_IAT,
		"exp": JWT_EXP,
	}
	header_b64 = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
	payload_b64 = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
	signing_input = f"{header_b64}.{payload_b64}"
	signature = hmac.new(
		secret.encode("utf-8"),
		signing_input.encode("ascii"),
		hashlib.sha256,
	).digest()
	return f"{signing_input}.{b64url_encode(signature)}"


def decode_jwt_payload(token: str) -> dict:
	"""Decode a JWT payload without verifying the signature."""
	parts = token.split(".")
	if len(parts) != 3:
		raise ValueError("Invalid JWT format")
	return json.loads(b64url_decode(parts[1]))


def verify_jwt_signature(token: str, secret: str) -> bool:
	"""Verify HS256 JWT signature and return True when valid."""
	parts = token.split(".")
	if len(parts) != 3:
		return False
	signing_input = f"{parts[0]}.{parts[1]}"
	expected = hmac.new(
		secret.encode("utf-8"),
		signing_input.encode("ascii"),
		hashlib.sha256,
	).digest()
	try:
		actual = b64url_decode(parts[2])
	except (ValueError, binascii.Error):
		return False
	return hmac.compare_digest(expected, actual)


def parse_env_file(path: Path) -> dict[str, str]:
	"""Parse KEY=VALUE lines from an env file, ignoring comments and blanks."""
	if not path.exists():
		return {}

	values: dict[str, str] = {}
	for line in path.read_text(encoding="utf-8").splitlines():
		trimmed = line.strip()
		if not trimmed or trimmed.startswith("#"):
			continue
		match = ENV_LINE_RE.match(trimmed)
		if match:
			key, value = match.groups()
			values[key] = value.strip().strip('"').strip("'")
	return values


def is_cloud_supabase_url(url: str) -> bool:
	if not url:
		return False
	hostname = (urlparse(url).hostname or "").lower()
	return hostname.endswith(".supabase.co")


def generate_jwt_secret() -> str:
	"""Generate a URL-safe secret with at least 32 characters."""
	return secrets.token_urlsafe(32)


def resolve_jwt_secret(*sources: dict[str, str]) -> str:
	for source in sources:
		candidate = source.get("JWT_SECRET") or source.get("SUPABASE_JWT_SECRET") or ""
		if len(candidate) >= 32:
			return candidate
	return generate_jwt_secret()


def build_local_supabase_values(jwt_secret: str) -> dict[str, str]:
	return {
		"STORAGE_BACKEND": "supabase",
		"SUPABASE_URL": SUPABASE_URL_DOCKER,
		"SUPABASE_SERVICE_KEY": mint_supabase_jwt("service_role", jwt_secret),
		"SUPABASE_ANON_KEY": mint_supabase_jwt("anon", jwt_secret),
		"SUPABASE_JWT_SECRET": jwt_secret,
		"JWT_SECRET": jwt_secret,
		"POSTGRES_USER": "postgres",
		"POSTGRES_PASSWORD": "postgres",
		"POSTGRES_DB": "postgres",
		"POSTGRES_PORT": "5432",
		"SUPABASE_API_PORT": "8000",
	}


def apply_env_updates(content: str, updates: dict[str, str]) -> str:
	"""Merge updates into env file content, replacing existing keys or appending new ones."""
	lines = content.splitlines()
	seen: set[str] = set()
	updated_lines: list[str] = []

	for line in lines:
		trimmed = line.strip()
		if not trimmed or trimmed.startswith("#"):
			updated_lines.append(line)
			continue
		match = ENV_LINE_RE.match(trimmed)
		if not match:
			updated_lines.append(line)
			continue
		key = match.group(1)
		if key in updates:
			updated_lines.append(f"{key}={updates[key]}")
			seen.add(key)
		else:
			updated_lines.append(line)

	missing = [key for key in updates if key not in seen]
	if missing:
		if updated_lines and updated_lines[-1].strip():
			updated_lines.append("")
		updated_lines.append("# Local Supabase (generated by make local-supabase-env)")
		for key in missing:
			updated_lines.append(f"{key}={updates[key]}")

	return "\n".join(updated_lines).rstrip() + "\n"


def render_local_env_file(updates: dict[str, str], *, cloud_safe: bool) -> str:
	lines = [
		"# Local Supabase overrides (generated by make local-supabase-env)",
		"# Use with: docker compose --env-file .env --env-file .env.local-supabase --profile local-supabase up -d",
		"#",
		"# Docker services use SUPABASE_URL=http://supabase-kong:8000",
		"# Hybrid/host access from your machine: http://localhost:8000",
		"",
	]
	if cloud_safe:
		lines.insert(
			1,
			"# Cloud credentials in .env were left unchanged.",
		)
	for key in LOCAL_SUPABASE_KEYS:
		if key in updates:
			lines.append(f"{key}={updates[key]}")
	lines.append("")
	return "\n".join(lines)


def load_base_env_content(target: Path) -> str:
	if target.exists():
		return target.read_text(encoding="utf-8")
	if ENV_FILE.exists():
		return ENV_FILE.read_text(encoding="utf-8")
	if ENV_EXAMPLE.exists():
		return ENV_EXAMPLE.read_text(encoding="utf-8")
	return ""


def bootstrap_local_supabase_env(*, dry_run: bool = False) -> Path:
	existing_env = parse_env_file(ENV_FILE)
	cloud_detected = is_cloud_supabase_url(existing_env.get("SUPABASE_URL", ""))
	target = LOCAL_ENV_FILE if cloud_detected else ENV_FILE

	target_env = parse_env_file(target) if target.exists() else {}
	jwt_secret = resolve_jwt_secret(target_env, existing_env)
	updates = build_local_supabase_values(jwt_secret)

	if cloud_detected:
		content = render_local_env_file(updates, cloud_safe=True)
	else:
		base_content = load_base_env_content(target)
		content = apply_env_updates(base_content, updates)

	if not dry_run:
		target.write_text(content, encoding="utf-8")

	return target


def print_usage(target: Path, *, cloud_detected: bool) -> None:
	print(f"Wrote local Supabase env to: {target}")
	print("")
	print("Start the local Supabase stack:")
	if cloud_detected:
		print(
			"  docker compose --env-file .env --env-file .env.local-supabase "
			"--profile local-supabase up -d"
		)
		print("")
		print("Or use: make local-supabase")
	else:
		print("  docker compose --profile local-supabase up -d")
		print("")
		print("Or use: make local-supabase")
	print("")
	print("URLs:")
	print(f"  Inside Docker Compose network: {SUPABASE_URL_DOCKER}")
	print(f"  From host / hybrid dev:        {SUPABASE_URL_HOST}")


def main(argv: list[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description="Bootstrap local Supabase environment variables.")
	parser.add_argument(
		"--dry-run",
		action="store_true",
		help="Compute values without writing any env file.",
	)
	args = parser.parse_args(argv)

	existing_env = parse_env_file(ENV_FILE)
	cloud_detected = is_cloud_supabase_url(existing_env.get("SUPABASE_URL", ""))

	try:
		target = bootstrap_local_supabase_env(dry_run=args.dry_run)
	except OSError as exc:
		print(f"ERROR: Failed to write env file: {exc}", file=sys.stderr)
		return 1

	if args.dry_run:
		print("Dry run complete — no files were written.")
		target = LOCAL_ENV_FILE if cloud_detected else ENV_FILE

	print_usage(target, cloud_detected=cloud_detected)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
