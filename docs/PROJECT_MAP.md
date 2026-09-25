# Project map

A guide to the main files and folders, what they do, and where the earlier work is saved.

## How the application works

The React dashboard sends a test request to `api.py`. This starts `pipeline_runner.py`, which calls the orchestrator.

`orchestrator.py` runs the pipeline in order:

1. Crawl the website and capture screenshots and DOM snapshots.
2. Analyse the captured pages with the Vision and Reason agents.
3. Assign severity using the Classifier Agent.
4. Group repeated findings and generate the reports.

`db.py` handles storing the run data and results. The dashboard gets the saved runs, findings, screenshots, and Markdown reports through the API.

## Supporting scripts

| File | What it does |
| --- | --- |
| `inspect_run.py` | Reads a saved run from the database and prints its summary. |
| `generate_report_from_db.py` | Regenerates reports from saved findings. This is an older helper and needs updating because the report functions now require `target_url`. |
| `dedup_findings.py` | Uses an LLM to group findings that describe the same issue, then prints the results. |
| `run_all_users.py` | Runs the pipeline for the SauceDemo test users to collect a dataset. |
| `label_findings.py` | Saves manual severity labels in the database. |
| `reclassify.py` | Runs the classifier on saved findings and compares its results with the manual labels. |
| `train_classifier.py` | Trains and evaluates DistilBERT. Results go to `classifier_out/` by default, or to the folder passed with `--out`. |
| `ground_truth.py` | Stores the reference SauceDemo bugs and notes on which ones the tool can detect. |
| `score_runs.py` | Checks saved findings against the reference bugs using text-matching rules. |
| `test_crawl.py` | Runs the crawler on its own. It still expects two return values, but the current crawler returns three, so this needs updating. |
| `test_decide.py`, `test_execute.py` | Check how the crawler chooses and performs actions on a page. |
| `test_reason.py`, `test_vision.py` | Test the analysis agents using saved DOM files and screenshots, including the `999_` captures. |
| `test_storage.py` | Writes sample data to the configured database and reads it back to check storage. |

The test files are manual checks. Some make API calls, open a browser, save captures, or write to the database. They were not run during the folder reorganization.

## Development notes and notebooks

- `docs/IMPLEMENTATION_LOG.md`: notes on how the pipeline was built, decisions made, problems found, and evaluation results. It also includes terminal output. Some progress notes and next steps are from earlier stages and are now out of date.
- `qa_pipeline.ipynb`: the original prototype, with database setup, crawling, visual analysis, and report generation in one notebook.
- `qa_demo.ipynb`: an earlier demonstration and evaluation notebook with saved results. It uses older pipeline calls and includes a step that deletes `qa_pipeline.db` before running, so it needs reviewing before reuse.
- `archive/exports/demo_file.txt`: a notebook saved as JSON in a text file.
- `archive/exports/exported_files.txt`: a notebook export followed by copies of earlier code.

## Classifier experiments

`experiments/classifier/` contains the saved DistilBERT experiments. Each folder keeps the model, tokenizer, settings, metrics, and confusion matrix chart together.

The current pipeline uses the LLM-based Classifier Agent. These DistilBERT models are kept to document the experiments and their results.

| Folder | Experiment |
| --- | --- |
| `out_2class/` | Two-class severity classification, seed 42. |
| `out_2class_s1/` | Two-class severity classification, seed 1. |
| `out_2class_s7/` | Two-class severity classification, seed 7. |
| `out_e8/` | Classification with `not_a_bug`, `low`, and `high`, seed 42. |
| `out_s42/` | Another experiment with `not_a_bug`, `low`, and `high`, seed 42. |

`classifier_out/` It currently contains baseline metrics. Commands that refer to the moved experiments need to use their new paths under `experiments/classifier/`.

## Evaluation results and logs

`evaluation/results/` contains the saved summaries and comparisons:

| File | Saved result |
| --- | --- |
| `run5_summary.txt` | Run 5 summary. |
| `problem_findings.txt` | Run 7 summary. |
| `problem_findings_v2.txt` | Run 8 summary. |
| `problem_findings_final.txt` | Run 10 summary. |
| `dedup_run10.txt` | Results from grouping repeated findings in run 10. |
| `classifier_results_final.txt` | Comparison of agent and classifier severity against the manual labels. |

`logs/` contains the seven saved console logs, including failed runs. These help show what happened during development. 

## Database backups and captured files

`backups/` contains the eight `qa_pipeline_backup_*.db` files. They are snapshots from different stages, such as dataset collection, evaluation runs, and changes to labels or classification. Their original names and contents were kept.

The files used by the application are still in the main folder:

- `qa_pipeline.db`: the active database.
- `screenshots/`: captured screenshots.
- `dom/`: captured page HTML.
- `outputs/`: generated Markdown and HTML reports.