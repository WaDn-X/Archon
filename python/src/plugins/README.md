# Archon Plugin Allowlist

Extra Python plugins in this directory are **not** loaded automatically. Each plugin must be explicitly allowlisted by **name** and **SHA-256** hash of its source bytes.

Built-in Archon MCP tools (`rag_*`, `find_*`, `manage_*`) are first-party and do not require allowlist entries.

## Add a plugin

1. Create a plugin module in this directory (for example `my_plugin.py`).
2. Implement `register_tools(mcp)` if the plugin should register MCP tools.
3. Compute the SHA-256 hash of the plugin source file:

```bash
cd python
python -c "import hashlib, pathlib; p=pathlib.Path('src/plugins/my_plugin.py'); print(hashlib.sha256(p.read_bytes()).hexdigest())"
```

4. Add an entry to `src/server/config/plugin_allowlist.json` (or the path in `PLUGIN_ALLOWLIST_PATH`):

```json
{
  "plugins": [
    {
      "name": "my_plugin",
      "sha256": "<hash-from-step-3>",
      "enabled": true
    }
  ],
  "executors": []
}
```

5. Restart the MCP server (or Archon server) so allowlisted plugins are loaded.

## API

- `GET /api/plugins/allowlist` — read current allowlist
- `PUT /api/plugins/allowlist` — replace allowlist contents

## Agent Work Orders executors

Sandbox shell commands may only use first-party executors (`claude`, `git`, `gh`) or binaries listed under `executors` in the same allowlist file.

## Security model

- Empty `plugins` array = zero extra plugins loaded
- Hash mismatch or unknown name = load refused with a clear error
- `enabled: false` = entry ignored
- No import happens before the allowlist check
