"""Request origin checks for local-only write endpoints."""

from fastapi import Request


def is_internal_request(request: Request) -> bool:
	"""Return True when the request originates from localhost or Docker internal networks."""
	client_host = request.client.host if request.client else None

	if not client_host:
		return False

	if client_host.startswith("172."):
		parts = client_host.split(".")
		if len(parts) == 4:
			second_octet = int(parts[1])
			if 16 <= second_octet <= 31:
				return True

	return client_host in {"127.0.0.1", "::1", "localhost"}
