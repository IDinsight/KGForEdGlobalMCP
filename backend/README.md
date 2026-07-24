# Curriculum Knowledge Graph MCP backend

This package provides the curriculum-agnostic FastMCP application, immutable 
graph-package loading, deterministic catalog and retrieval services, resources, 
prompts, comparison evidence, local MCP Bundle packaging, and subprocess STDIO smoke 
coverage.

## Runtime contract

The server runs locally over STDIO and exposes the accepted fixed inventory:

- 8 tools;
- 1 fixed resource;
- 9 resource templates; and
- 6 prompts.

Application paths are supplied through process environment variables. The MCPB manifest
sets those paths explicitly because a desktop host does not inherit repository-local
shell configuration.

## Repository STDIO smoke

From the repository root:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke
```

The command launches a real locked subprocess, completes an MCP handshake, lists every
component family, verifies the exact inventory, and requires a clean shutdown. Protocol
traffic remains on stdout while framework logging remains on stderr.

## Build an MCP Bundle

Install the official MCPB CLI, then run:

```bash
npm install -g @anthropic-ai/mcpb
uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb
```

The build command stages the runtime source, locked Python metadata, all profiles, all
prompt configurations, and all accepted graph packages; invokes `mcpb validate` and
`mcpb pack`; and verifies the resulting ZIP-compatible `.mcpb` archive. The default
output is `dist/kgfegmcp-0.1.0.mcpb`.

To retain and smoke the exact staged bundle:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb --stage-output ./dist/kgfegmcp-stage
uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke --bundle-root ./dist/kgfegmcp-stage
```

The bundle uses the MCPB UV runtime. It does not include a virtual environment or 
vendored dependencies; the host resolves the locked project through `uv`.
