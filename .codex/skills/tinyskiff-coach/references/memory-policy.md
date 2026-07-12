# TinySkiff Hindsight memory policy

## Existing system

- Hindsight 0.8.4 runs on the Mac mini at `http://127.0.0.1:8888`.
- Dedicated Sam/TinySkiff bank: `sam-tinyskiff`. Isolation prevents unrelated global directives in `sam-personal` from leaking into the learning model.
- Do not change `sam-personal` or its global default ingestion mode. It remains chunk-based for other integrations.
- TinySkiff uses named strategy `tinyskiff-lessons` with concise extraction.
- TinySkiff mental model: `tinyskiff-learning-journey`.
- Hindsight 0.8.4 saved-model refresh currently uses a low reflection budget that returned no facts in a verified test. Automatic refresh is disabled to avoid empty, wasteful runs. Use `tinyskiff_memory.py journey`, which applies the same source query at the verified mid budget.

## Shapes worth retaining

- `concept`: a beginner concept the learner can now use.
- `setup`: a verified durable hardware/software configuration.
- `correction`: a lesson claim corrected against verified UI/source.
- `incident`: symptom, root cause, verified fix, and prevention guardrail.
- `preference`: stable instruction or learning preference.

Use tags: `tinyskiff`, `learning`, `lesson:<CODE>`, `memory-shape:<shape>`.

## Quality rules

- Summarize only after the resolution is verified.
- Preserve exact UI labels, board/chip names, URLs, and versions when material.
- State uncertainty rather than smoothing over contradictions.
- Use a stable, unique `document_id` so a bad retain can be removed precisely.
- Recall from the dedicated bank with `tags_match=all_strict`; bank isolation is the primary boundary and strict tags are a second boundary.
- Use `journey` for the current organized project view; use `recall --query` for a lesson-specific question.
- Do not bulk-clean existing Sam memories as part of lesson coaching.

## Model policy

- Inherit the current Hindsight role split: `qwen3-coder:480b-cloud` for extraction and `gpt-oss:120b-cloud` for reflection.
- Do not swap to GLM 5.2 without a disposable-bank A/B evaluation for fidelity, durable filtering, duplicate rate, and schema validity.
- GPT-5.6 Luna is not an available Ollama model in the audited environment.
