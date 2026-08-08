import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s]: %(message)s:')

project_name = "foresightai"

list_of_files = [
    ".github/workflows/.gitkeep",

    # Core library package — used by both the Django backend and notebooks
    f"src/{project_name}/__init__.py",

    # One component per methodology stage
    f"src/{project_name}/ingestion/__init__.py",
    f"src/{project_name}/ingestion/preprocessing.py",

    f"src/{project_name}/feature_extraction/__init__.py",
    f"src/{project_name}/feature_extraction/llm_extractor.py",
    f"src/{project_name}/feature_extraction/embeddings.py",

    f"src/{project_name}/personas/__init__.py",
    f"src/{project_name}/personas/clustering.py",

    f"src/{project_name}/simulation/__init__.py",
    f"src/{project_name}/simulation/agents.py",
    f"src/{project_name}/simulation/orchestrator.py",

    f"src/{project_name}/validation/__init__.py",
    f"src/{project_name}/validation/evaluator.py",

    # Shared utilities across stages
    f"src/{project_name}/utils/__init__.py",
    f"src/{project_name}/utils/common.py",
    f"src/{project_name}/utils/logger.py", 

    # Config loading + constants (paths, k-range, LLM model name, etc.)
    f"src/{project_name}/config/__init__.py",
    f"src/{project_name}/config/configuration.py",
    f"src/{project_name}/constants/__init__.py",

    # Pipeline entry points (e.g. run_ingestion.py, run_k_sweep.py)
    f"src/{project_name}/pipeline/__init__.py",

    "config/config.yaml",
    "params.yaml",
    "requirements.txt",
    "setup.py",

    "notebooks/trials.ipynb",

    "data/raw/.gitkeep",
    "data/processed/.gitkeep",
     
]

for filePath in list_of_files:
    filePath = Path(filePath)

    fileDir, fileName = os.path.split(filePath)

    if fileDir != "":
        os.makedirs(fileDir, exist_ok=True)
        logging.info(f"Creating Directory: {fileDir} for {fileName}.")

    if (not os.path.exists(filePath)) or (os.path.getsize(filePath) == 0):
        with open(filePath, 'w') as f:
            pass
        logging.info(f"Creating empty file: {filePath}.")

    else:
        logging.info(f"{fileName} already exists.")