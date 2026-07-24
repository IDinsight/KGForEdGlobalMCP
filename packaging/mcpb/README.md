# MCP Bundle packaging

This directory contains the reviewed MCPB 0.4 manifest template and packing exclusions
for the local Curriculum Knowledge Graph MCP Server distribution.

The committed files are templates, not a complete bundle. The project packaging CLI
assembles a clean staging root containing generic runtime source, `pyproject.toml`,
`uv.lock`, FastMCP configuration, all six profiles, all six prompt configurations, and
all six accepted immutable graph packages. It then delegates validation and packing to
the official `mcpb` command and verifies the resulting archive.

Install the official CLI and build from the repository root:

```bash
npm install -g @anthropic-ai/mcpb
uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb
```

The generated archive is written to `dist/kgfegmcp-0.1.0.mcpb` by default. Override the
archive path with `--output PATH`.

Retain the assembled bundle directory for review or packaged-runtime smoke coverage:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb --stage-output ./dist/kgfegmcp-stage
uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke --bundle-root ./dist/kgfegmcp-stage
```

The manifest uses `server.type = "uv"` and an explicit `mcp_config` environment. The
bundle deliberately excludes virtual environments, bytecode, caches, build output, and
repository metadata.
