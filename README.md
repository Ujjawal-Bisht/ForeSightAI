# ForeSightAI

ForeSightAI is a data-driven AI project focused on software review simulation, data processing, embedding-based feature extraction, and evaluation workflows. The repository is organized to support experimentation, backend services, and modular ML/data engineering components.

## Repository Structure

```text
ForeSightAI/
├── .env
├── .env.example
├── .gitignore
├── .github/
│   └── workflows/
│       └── .gitkeep
├── backend/
│   ├── db.sqlite3
│   ├── manage.py
│   └── foreSightAI/
│       ├── __init__.py
│       ├── asgi.py
│       ├── settings.py
│       ├── urls.py
│       ├── wsgi.py
│       └── __pycache__/
├── config/
│   └── config.yaml
├── data/
│   ├── demo/
│   │   ├── dataset_12k.json
│   │   ├── dataset_25k.json
│   │   └── dataset_50k.json
│   ├── processed/
│   │   ├── .gitkeep
│   │   └── software_clean.jsonl
│   └── raw/
│       ├── .gitkeep
│       └── Software.jsonl
├── docs/
│   ├── architecture.md
│   ├── design.md
│   ├── memory.md
│   ├── PRD.md
│   ├── rules.md
│   └── tasks.md
├── logs/
├── notebooks/
│   ├── break_dataset.ipynb
│   ├── trials.ipynb
│   └── ingestion/
│       ├── 01_data_exploration.ipynb
│       ├── 02_data_preprocessing.ipynb
│       ├── 03_pipeline_validation.ipynb
│       └── 04_optimizing_workflow.ipynb
├── prompts/
├── reports/
│   ├── 01_data_exploration_report.md
│   └── 02_data_preprocessing_report.md
├── src/
│   └── foresightai/
│       ├── __init__.py
│       ├── __pycache__/
│       ├── config/
│       │   ├── __init__.py
│       │   ├── configuration.py
│       │   └── __pycache__/
│       ├── constants/
│       │   └── __init__.py
│       ├── database/
│       │   ├── __init__.py
│       │   ├── connection.py
│       │   ├── __pycache__/
│       │   └── repositories/
│       │       ├── __init__.py
│       │       ├── review_hash_repository.py
│       │       └── __pycache__/
│       ├── feature_extraction/
│       │   ├── __init__.py
│       │   ├── embeddings.py
│       │   ├── llm_extractor.py
│       │   └── __pycache__/
│       ├── ingestion/
│       │   ├── __init__.py
│       │   ├── preprocessing.py
│       │   └── __pycache__/
│       ├── personas/
│       │   ├── __init__.py
│       │   ├── clustering.py
│       │   └── __pycache__/
│       ├── pipeline/
│       │   └── __init__.py
│       ├── simulation/
│       │   ├── __init__.py
│       │   ├── agents.py
│       │   ├── orchestrator.py
│       │   └── __pycache__/
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── common.py
│       │   ├── logger.py
│       │   └── __pycache__/
│       ├── validation/
│       │   ├── __init__.py
│       │   ├── evaluator.py
│       │   └── __pycache__/
│       └── foresightai.egg-info/
│           ├── dependency_links.txt
│           ├── PKG-INFO
│           ├── requires.txt
│           ├── SOURCES.txt
│           └── top_level.txt
├── checklist.md
├── params.yaml
├── README.md
├── requirements.txt
├── setup.py
├── template.py
└── .venv/
```

## Project Areas

- Backend: Django-based application under `backend/`
- Core source code: Python modules under `src/foresightai/`
- Data assets: raw, processed, and demo datasets under `data/`
- Documentation: product and technical specs under `docs/`
- Notebooks: experimentation and pipeline notebooks under `notebooks/`
- Reports: analysis summaries and validation reports under `reports/`

## Notes

The repository is organized for experimentation, preprocessing, simulation, and evaluation, with supporting backend and documentation files for project delivery.
