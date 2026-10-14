"""
CapTax AI - Backend API
Owner: Anishka Jain (Backend & Data Lead)

FastAPI app that wraps the ingestion -> FIFO -> classification -> DTAA ->
disclosure pipeline and exposes it over HTTP for the frontend dashboard.

Run: uvicorn app:app --reload --port 8000   (from inside backend/)
Docs: http://localhost:8000/docs
"""

import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
AIML_DIR = PROJECT_DIR / "aiml"
DATA_DIR = BACKEND_DIR / "data"

app = FastAPI(title="CapTax AI API", version="0.1.0")

# Allow the frontend (served separately, e.g. via a dev server) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PIPELINE = [
    (BACKEND_DIR / "generate_datasets.py", "Anishka Jain"),
    (BACKEND_DIR / "ingest.py", "Anishka Jain"),
    (BACKEND_DIR / "corporate_actions_adjuster.py", "Anishka Jain"),
    (BACKEND_DIR / "fifo_matcher.py", "Anishka Jain"),
    (AIML_DIR / "tax_classifier.py", "Shraddha Singh"),
    (AIML_DIR / "dtaa_relief.py", "Shraddha Singh"),
    (AIML_DIR / "disclosure_generator.py", "Shraddha Singh"),
]


def _run_script(script_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=script_path.parent,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"{script_path.name} failed:\n{result.stdout}\n{result.stderr}",
        )


def _read_csv_as_records(filename: str):
    path = DATA_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found — run /pipeline/run first")
    df = pd.read_csv(path)
    return df.fillna("").to_dict(orient="records")


@app.get("/")
def root():
    return {"service": "CapTax AI API", "status": "ok", "endpoints": [
        "/pipeline/run", "/data/trades", "/data/tax-summary",
        "/data/dtaa-relief", "/data/disclosure-summary",
    ]}


@app.post("/pipeline/run")
def run_pipeline():
    """Runs every stage of the pipeline in order and returns a step log."""
    log = []
    for script_path, owner in PIPELINE:
        _run_script(script_path)
        log.append({"step": script_path.name, "owner": owner, "status": "completed"})
    return {"status": "completed", "steps": log}


@app.get("/data/trades")
def get_trades():
    return _read_csv_as_records("normalized_trades.csv")


@app.get("/data/realized-gains")
def get_realized_gains():
    return _read_csv_as_records("realized_gains.csv")


@app.get("/data/tax-summary")
def get_tax_summary():
    return _read_csv_as_records("tax_summary.csv")


@app.get("/data/dtaa-relief")
def get_dtaa_relief():
    return _read_csv_as_records("dtaa_relief.csv")


@app.get("/data/disclosure-summary")
def get_disclosure_summary():
    path = DATA_DIR / "disclosure_summary.txt"
    if not path.exists():
        raise HTTPException(status_code=404, detail="disclosure_summary.txt not found — run /pipeline/run first")
    return {"report": path.read_text()}
