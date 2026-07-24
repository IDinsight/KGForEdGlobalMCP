# Knowledge Graph for Education Global MCP

<!-- Badges -->
<p align="center">
  <a href="https://github.com/econchick/interrogate">
    <img src="./interrogate_badge.svg" alt="Docstring coverage: interrogate">
  </a>
  &nbsp;
  <a href="https://github.com/pylint-dev/pylint">
    <img src="https://img.shields.io/badge/linting-pylint-yellowgreen" alt="Linting: pylint">
  </a>
</p>

KG for Education Global MCP is a FastMCP-based server for exploring and using 
curriculum knowledge graphs from countries, states, and educational organizations 
around the world. It provides a single interface for searching academic standards, 
navigating curriculum hierarchies, comparing frameworks and historical revisions, and 
supporting student, teacher, administrator, and curriculum-research workflows through 
clients such as Claude Desktop.

## Federated architecture

Each curriculum remains an independent, immutable, and versioned graph package. A 
shared catalog and common MCP services make those packages searchable and comparable 
through one interface without flattening them into a single source graph. This 
preserves framework identity, provenance, local terminology, and graph topology while 
enabling cross-country, cross-organization, and cross-version analysis.

## Current scope

The project currently focuses on Academic Standards knowledge graphs. Planned 
extensions include Learning Components, Learning Progressions, curriculum resources, 
assessments, and reviewed cross-framework alignments.

The implementation is designed to remain:

- curriculum-agnostic and configuration-driven;
- compatible with trees and multi-parent DAGs;
- auditable, provenance-aware, and versioned;
- extensible to additional frameworks and graph types; and
- deterministic at the server layer, with Claude handling user-facing reasoning and generation.

## Project status

The current local server exposes eight tools, one fixed resource, nine resource 
templates, and six prompts. 

## Local packaging and STDIO verification

Install the official MCPB CLI, then build the one-click local bundle:

```bash
npm install -g @anthropic-ai/mcpb
uv --directory backend run --locked --no-dev kgfegmcp-build-mcpb
```

Run the repository server through the real locked STDIO subprocess path:

```bash
uv --directory backend run --locked --no-dev kgfegmcp-stdio-smoke
```

Use `--stage-output` during the build and `--bundle-root` during the smoke command to
exercise the exact staged MCPB runtime before installation in a desktop host.

## License

See [LICENSE](./LICENSE).
