# Market Signal Extraction System — agenti

CLI-based test of the two-layer extraction + orchestration architecture using Claude API.

## Setup

```bash
# From project root — use Python 3.11
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Set Claude API key (required)
export ANTHROPIC_API_KEY=sk-ant-...
# Or add to .env: ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

### Full pipeline (recommended for testing)

```bash
python3.11 -m agenti.cli run --dataset datasets/24h_accrued --commentators 3 --save-extractions
```

- `--dataset`: Path to 24h_accrued-style folder (tweets_*_24h_*.json + conversation_parents.json). `conversation_parents.json` maps parent tweet IDs (inReplyToId) → full parent tweet objects, so when a commentator replies we can show what they were replying to.
- `--commentators`: Max commentators to process (default 5)
- `--output`: Output path for positioning plan (default: agenti/output/positioning_plan.json)
- `--save-extractions`: Save per-commentator extraction JSONs
- `--continue-on-error`: Skip failed extractions instead of failing

### Extract only (single commentator)

```bash
python3.11 -m agenti.cli extract --dataset datasets/24h_accrued --handle clkleinmonaco --output agenti/output/extract_clkleinmonaco.json
```

### Orchestrate only (from existing extractions)

```bash
python3.11 -m agenti.cli orchestrate --extractions agenti/output/extract_*.json --output agenti/output/plan.json
```

## Models

- **Extraction**: `claude-sonnet-4-20250514` (fast, cheap)
- **Orchestrator**: `claude-opus-4-20250514` (deeper synthesis)

## Output

- `positioning_plan.json`: Full orchestrator output (theme_map, convergence_matrix, positioning_plan, tail_risk_register, daily_briefing)
- `extract_<handle>.json`: Per-commentator extraction (signals, risk_flags, macro_thesis, etc.)
