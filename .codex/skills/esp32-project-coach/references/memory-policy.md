# ESP32 project Hindsight memory policy

## Existing system

- Hindsight 0.8.4 runs on the Mac mini at `http://127.0.0.1:8888`.
- Existing bank: `sam-personal`. All ESP32 project memories and the mental model live there.
- Never create a Hindsight memory bank unless the user explicitly asks for a new bank. A request for project memory, a strategy, isolation, tags, or a mental model is not permission to create one.
- Do not change `sam-personal`'s default ingestion mode. It remains chunk-based for other integrations.
- ESP32 lessons use named strategy `esp32-project-lessons` with concise extraction.
- ESP32 mental model: `esp32-project-learning-journey`.
- Hindsight 0.8.4 saved-model refresh currently uses a low reflection budget that returned no facts in a verified test. Automatic refresh is disabled to avoid empty, wasteful runs. Use `esp32_memory.py journey` for a grounded, strictly tagged recall view associated with the mental-model ID.

## Shapes worth retaining

- `concept`: a beginner concept the learner can now use.
- `setup`: a verified durable hardware/software configuration.
- `correction`: a lesson claim corrected against verified UI/source.
- `incident`: symptom, root cause, verified fix, and prevention guardrail.
- `preference`: stable instruction or learning preference.

Use tags: `esp32-project`, `learning`, `lesson:<CODE>`, `memory-shape:<shape>`.

## Quality rules

- Summarize only after the resolution is verified.
- Preserve exact UI labels, board/chip names, URLs, and versions when material.
- State uncertainty rather than smoothing over contradictions.
- Use a stable, unique `document_id` so a bad retain can be removed precisely.
- Recall from `sam-personal` with `tags_match=all_strict`; strict project tags are the scope boundary.
- Use `journey` for the current organized project view; use `recall --query` for a lesson-specific question.
- Do not bulk-clean or reorganize other `sam-personal` memories as part of lesson coaching.
- Do not call the project TinySkiff. That string is permitted only when referring to the domain name or legacy compatibility identifiers.

## Model policy

- Inherit the current Hindsight role split: `qwen3-coder:480b-cloud` for extraction and `gpt-oss:120b-cloud` for reflection.
- Do not swap to GLM 5.2 without a disposable-bank A/B evaluation for fidelity, durable filtering, duplicate rate, and schema validity.
- GPT-5.6 Luna is not an available Ollama model in the audited environment.
