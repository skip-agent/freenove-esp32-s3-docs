## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying Python or JavaScript, run `graphify update .` to refresh AST relationships.
- Changes to lesson YAML, Markdown, packets, or generated course pages require a semantic re-extraction on the Mac mini; `graphify update .` does not index those formats completely. Follow `.codex/skills/esp32-project-coach/references/project-context.md`.
- Graphify is a navigation aid, not source-of-truth evidence. Verify claims in the lesson YAML, generated packet, current webpage, or learner screenshot.
- Store ESP32 project memories and its mental model in the existing `sam-personal` Hindsight bank. Never create a new Hindsight bank unless the user explicitly requests one.
- TinySkiff is only part of the current domain name, not the ESP32 project's name. Keep `TSK-...` and `tinyskiff.*` only where legacy compatibility requires them.
