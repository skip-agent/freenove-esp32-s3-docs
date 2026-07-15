## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- Changes to lesson YAML, Markdown, packets, or generated course pages require semantic re-extraction on the Mac mini; follow `.codex/skills/esp32-project-coach/references/project-context.md`.
- Graphify is a navigation aid, not source-of-truth evidence. Verify claims in lesson YAML, generated packets, the current webpage, or learner screenshots.
- Store ESP32 project memory and its mental model in the existing `sam-personal` Hindsight bank. Never create a new project bank unless the user explicitly asks.
- TinySkiff is only part of the current domain name, not the ESP32 project name. Keep `TSK-...` and `tinyskiff.*` only where legacy compatibility requires them.
