# Data Collection Tools

Invoke the `data-collection-tools` skill to generate data collection instruments, scripts, and templates based on a confirmed study protocol.

## Type Router

| Research type | Tools generated |
|--------------|----------------|
| AI/ML Benchmark (VLM/LLM) | Prompt templates + inference script + annotation template + scoring template + analysis pipeline |
| AI Diagnostic / Prediction | Data extraction form + annotation template + data split script + evaluation script |
| Clinical (RCT / cohort) | CRF (case report form) + data dictionary + screening log + randomization script |
| Basic science | Experiment log + image acquisition protocol + data entry template |
| Systematic review / Meta | Data extraction form + risk of bias table + PRISMA template + dual screening log |

## Prerequisite

**Requires `study-protocol.md`** — run `study-design` first.

## Output

- `tools/README.md` — usage guide for all generated tools
- `tools/` — all instruments, scripts, and templates
- `data/` — standardized project directory structure

## Mandatory next step
After tools are ready and data collected → `statistical-analysis`.
