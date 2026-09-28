# QA Multi-Agent Pipeline

A Python pipeline and React dashboard for automated website QA. The crawler captures screenshots and rendered page HTML, Vision and Reason agents analyse the evidence, an LLM classifier assigns severity, and reporting produces Markdown and HTML reports. SQLite stores runs, findings, page records, traces, and human labels.

## Current application

- `api.py`: FastAPI endpoints for starting runs and retrieving results, screenshots, and reports.
- `pipeline_runner.py`: runs the pipeline in a background task and records unexpected failures.
- `orchestrator.py`: coordinates crawling, analysis, classification, storage, and reporting.
- `agents/`: Crawl, Vision, Reason, Classifier, and Report agents.
- `db.py`, `schemas.py`, `config.py`: storage, request models, settings, and application paths.
- `utils/`: HTML report generation.
- `frontend/`: React/Vite interface for starting runs and browsing results.

The current classifier is LLM-based. Saved DistilBERT models are retained as experiment evidence in `experiments/classifier/`.

## Model configuration

Each agent has a separate model setting in `config.py`. The current configuration uses GPT-4o for the Crawl, Vision, Reason and Classifier Agents, and GPT-4o-mini for the Report Agent. These settings allow models to be replaced independently. Historical evaluation results relate to the configurations described in the report.

## Starting the existing application

Run commands from this project’s root. With the required dependencies available in the existing environment, start the API in one terminal:

```
source venv/bin/activate
python -m uvicorn api:app --reload
```

First tima activation:

```
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install fastapi uvicorn
python -m playwright install chromium
```

Start the dashboard in a second terminal:

```
cd frontend
npm run dev
```

Open the local address printed by Vite. Its development proxy forwards `/api` requests to `http://127.0.0.1:8000`. The pipeline reads `OPENAI_API_KEY` from the local environment or `.env`.


## Files and evidence

| Location | Purpose |
| --- | --- |
| `qa_pipeline.db` | Active database |
| `screenshots/`, `dom/` | Captured screenshots and page HTML referenced by the application and stored runs. |
| `outputs/` | Saved HTML and Markdown reports. |
| `docs/` | Project map |
| `backups/` | Historical database snapshots|
| `experiments/classifier/` | Five saved DistilBERT experiment folders, including models, metrics, and charts. |
| `classifier_out/` | Existing baseline metrics and the training script’s default output location |
| `evaluation/results/` | Saved findings summaries, deduplication results, and classifier comparison output. |
| `logs/` | Historical console logs, including failed runs. |
| `archive/exports/` | Earlier notebook and source-code text exports. |

## Notes

The `test_*.py` files are manual checks. Some call AI services or websites, create captures, or write to the active database. 
