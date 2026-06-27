# Open Source Demand Analyzer

[![CI](https://github.com/pratikbajoria1991/opensource-demand-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/pratikbajoria1991/opensource-demand-analyzer/actions/workflows/ci.yml)
[![Weekly Analysis](https://github.com/pratikbajoria1991/opensource-demand-analyzer/actions/workflows/analyze.yml/badge.svg)](https://github.com/pratikbajoria1991/opensource-demand-analyzer/actions/workflows/analyze.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Analyze GitHub open source projects to answer two questions (6 categories including **memory-infra**):

1. **Which projects are most in demand?** — scored from stars, forks, open issues, recency, and engagement.
2. **Which projects are lacking features?** — inferred from README coverage, open enhancement issues, and category-specific expected capabilities.

Reports are generated as JSON and Markdown. A GitHub Actions workflow can publish fresh reports weekly.

## Quick start

```bash
git clone https://github.com/pratikbajoria1991/opensource-demand-analyzer.git
cd opensource-demand-analyzer
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -e .
os-analyzer
```

Set a GitHub token for higher API limits (recommended):

```bash
set GITHUB_TOKEN=ghp_your_token_here   # Windows
export GITHUB_TOKEN=ghp_your_token_here
os-analyzer --per-category 8
```

## CLI options

| Flag | Description |
|------|-------------|
| `--config` | Categories YAML (default: `config/categories.yaml`) |
| `--per-category` | Repos to scan per category (default: 5) |
| `--category` | Limit to specific category IDs (repeatable) |
| `--output-dir` | Report output folder (default: `reports/`) |

Example — analyze only AI agents:

```bash
os-analyzer --category ai-agents --per-category 10
```

## Output

- `reports/summary.json` — cross-category rankings
- `reports/by-category.json` — per-category detail
- `reports/REPORT.md` — human-readable report

## How demand scoring works

Each repository gets a 0–100 **demand score** from:

| Signal | Weight |
|--------|--------|
| Stars | 35% |
| Forks | 20% |
| Open issues | 15% |
| Recency (last push) | 15% |
| Watchers + forks engagement | 15% |

Tiers: `very_high` (75+), `high` (55+), `moderate` (35+), `emerging` (<35).

## How feature gaps are detected

For each category, expected features are defined in `config/categories.yaml`. The analyzer checks:

- Whether each feature appears in the README
- Whether open issues mention missing or requested capabilities
- Community reactions on enhancement / feature-request issues

Gap statuses:

- `likely_missing` — not documented and requested in issues
- `undocumented` — not in README, weak issue signal
- `requested_by_community` — documented but actively requested

## Customize categories

Edit `config/categories.yaml`:

```yaml
categories:
  - id: my-category
    name: My Category
    query: "topic:my-topic stars:>200"
    expected_features:
      - feature one
      - feature two
```

GitHub search query syntax: [docs](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories)

## Deploy to GitHub

1. Create a new public repository on GitHub.
2. Push this project:

```bash
git init
git add .
git commit -m "Initial commit: open source demand analyzer"
git branch -M main
git remote add origin https://github.com/pratikbajoria1991/opensource-demand-analyzer.git
git push -u origin main
```

3. Enable **Actions** in the repo settings. The weekly workflow publishes updated reports to `reports/`.

`GITHUB_TOKEN` is provided automatically in Actions (5000 requests/hour).

## Categories

| ID | Focus |
|----|-------|
| `ai-agents` | Agent orchestration, tools, streaming |
| `vector-databases` | Embeddings, hybrid search, tenancy |
| `local-llm` | Inference, quantization, caching |
| `developer-tools` | Plugins, CI/CD, self-hosted |
| `observability` | Tracing, metrics, cost attribution |
| `memory-infra` | Episodic/semantic memory, GDPR, context budget |

## Companion project

[agent-memory-gateway](../agent-memory-gateway) implements the memory-infra gaps this tool surfaces (tenancy, recall, GDPR erase, context budgeting).

## Limitations

- Analysis uses public GitHub API data only (no code parsing).
- Feature gaps are heuristic — validate before product decisions.
- Unauthenticated API: 60 requests/hour. Use `GITHUB_TOKEN` for production runs.

## License

MIT