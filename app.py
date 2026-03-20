# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import json
import subprocess
import csv
import shutil
from datetime import datetime
from robot.api import ExecutionResult
import random
import re
from typing import List, Optional

app = FastAPI(title="Test Generator with Auto Variations")

# -------------------------
# Backend endpoints
# -------------------------
@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello, {name}!"}

# -------------------------
# Variation generation utilities
# -------------------------
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9\-]{1,18}$")
BLACKLIST = {"admin", "root", "null", "undefined", "system"}

def deterministic_name(seed: int, idx: int, base_pool: List[str]) -> str:
    """Create a deterministic name from seed and index using base pool."""
    rnd = random.Random(seed + idx)
    base = rnd.choice(base_pool)
    suffix = rnd.randint(0, 999)
    return f"{base}{suffix}"

def filter_and_normalize(candidates: List[str]) -> List[str]:
    seen = set()
    out = []
    for c in candidates:
        c = c.strip()
        if not c:
            continue
        if c.lower() in BLACKLIST:
            continue
        if not NAME_RE.match(c):
            continue
        if c in seen:
            continue
        seen.add(c)
        out.append(c)
    return out

def generate_variations(seed: int, count: int, mode: str = "deterministic") -> List[str]:
    """
    Modes:
      - deterministic: deterministic_name using a small base pool
      - random: random choices (still seeded)
      - genai: placeholder to call an external GenAI to propose names (not implemented)
    """
    base_pool = ["Alice", "Bob", "Charlie", "Dana", "Eve", "Frank", "Grace", "Hector"]
    candidates = []
    if mode == "deterministic":
        for i in range(count * 3):
            candidates.append(deterministic_name(seed, i, base_pool))
    elif mode == "random":
        rnd = random.Random(seed)
        for _ in range(count * 5):
            name = rnd.choice(base_pool) + str(rnd.randint(0, 9999))
            candidates.append(name)
    elif mode == "genai":
        # Placeholder: integrate your GenAI model here to propose candidates.
        # Example: call_genai_propose(prompt, count) -> list[str]
        # For now, fallback to deterministic behavior.
        candidates = [deterministic_name(seed, i, base_pool) for i in range(count * 3)]
    else:
        raise ValueError("Unknown mode")
    filtered = filter_and_normalize(candidates)
    return filtered[:count]

# -------------------------
# API models
# -------------------------
class ProposeRequest(BaseModel):
    seed: Optional[int] = None
    count: int = 10
    mode: Optional[str] = "deterministic"  # deterministic | random | genai

class TestGenRequest(BaseModel):
    suite_name: str
    num_cases: int
    variations: Optional[List[str]] = None
    auto_generate: Optional[bool] = True
    seed: Optional[int] = None
    generation_mode: Optional[str] = "deterministic"  # deterministic | random | genai
    require_human_approval: Optional[bool] = False

# -------------------------
# Robot suite generation
# -------------------------
ROBOT_OUT_DIR = os.path.join("robot-tests", "generated")
RESULTS_DIR = os.path.join("robot-tests", "results")
os.makedirs(ROBOT_OUT_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

ROBOT_TEMPLATE = r"""*** Settings ***
Library    RequestsLibrary
Library    Collections

*** Test Cases ***
Hello API Generated Cases
    Create Session    api    ${BASE_URL}
    ${cases_list}=    Evaluate    (lambda j: j['cases'] if isinstance(j, dict) and 'cases' in j else j)(__import__('json').loads(open('${CURDIR}/__JSON_FILE__').read()))    json
    Log    ${cases_list}    console=True
    ${count}=    Evaluate    len(${cases_list})    json
    FOR    ${i}    IN RANGE    0    ${count}
        ${case}=    Get From List    ${cases_list}    ${i}
        ${name}=    Get From Dictionary    ${case}    name
        ${expected}=    Get From Dictionary    ${case}    expected_message
        ${ok}    ${resp}=    Run Keyword And Ignore Error    GET On Session    api    /hello/${name}
        Run Keyword If    '${ok}' == 'FAIL'    Log    HTTP request failed for /hello/${name}: ${resp}    console=True
        Run Keyword If    '${ok}' == 'FAIL'    Fail    HTTP request failed for /hello/${name}
        ${json}=    Set Variable    ${resp.json()}
        Log    ${json}    console=True
        Should Be Equal As Strings    ${resp.status_code}    200
        Should Be Equal As Strings    ${json["message"]}    ${expected}
    END
"""

def write_suite_and_json(suite_name: str, cases: List[dict]) -> dict:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = f"{suite_name}_{ts}_cases.json"
    robot_file = f"{suite_name}_{ts}.robot"
    json_path = os.path.join(ROBOT_OUT_DIR, json_file)
    robot_path = os.path.join(ROBOT_OUT_DIR, robot_file)
    with open(json_path, "w") as f:
        json.dump({"cases": cases, "metadata": {"generated_at": ts}}, f, indent=2)
    content = ROBOT_TEMPLATE.replace("__JSON_FILE__", json_file)
    with open(robot_path, "w") as f:
        f.write(content)
    return {"json_path": json_path, "robot_path": robot_path, "json_file": json_file, "robot_file": robot_file, "timestamp": ts}

def run_robot(robot_path: str, base_url: str = "http://localhost:8000") -> dict:
    if not shutil.which("robot"):
        raise RuntimeError("'robot' executable not found in PATH. Install Robot Framework.")
    robot_dir = os.path.dirname(robot_path) or "."
    cmd = ["robot", "--variable", f"BASE_URL:{base_url}", os.path.basename(robot_path)]
    try:
        subprocess.run(cmd, check=True, cwd=robot_dir, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        out = e.stdout or ""
        err = e.stderr or ""
        raise RuntimeError(f"Robot failed (exit {e.returncode}). stdout:\n{out}\n\nstderr:\n{err}")
    output_xml = os.path.join(robot_dir, "output.xml")
    if not os.path.exists(output_xml):
        raise RuntimeError("Robot did not produce output.xml")
    result = ExecutionResult(output_xml)
    stats = {
        "total": result.statistics.total.total,
        "passed": result.statistics.total.passed,
        "failed": result.statistics.total.failed,
        "skipped": result.statistics.total.skipped,
        "pass_rate_percent": round((result.statistics.total.passed / result.statistics.total.total * 100), 2)
            if result.statistics.total.total else 0
    }
    return stats

# -------------------------
# Endpoints: propose and generate
# -------------------------
@app.post("/propose-variations")
def propose_variations(req: ProposeRequest):
    seed = req.seed if req.seed is not None else random_seed = random_seed = random_seed = int(datetime.utcnow().timestamp())
    # Use deterministic generator or placeholder GenAI
    try:
        candidates = generate_variations(seed, req.count, mode=req.mode)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"seed": seed, "mode": req.mode, "candidates": candidates}

@app.post("/generate-tests")
def generate_tests(req: TestGenRequest):
    # Determine variations
    seed = req.seed if req.seed is not None else int(datetime.utcnow().timestamp())
    if req.variations and len(req.variations) > 0:
        variations = filter_and_normalize(req.variations)
    elif req.auto_generate:
        variations = generate_variations(seed, req.num_cases, mode=req.generation_mode)
    else:
        raise HTTPException(status_code=400, detail="No variations provided and auto_generate is false")

    if len(variations) < req.num_cases:
        # If not enough unique valid variations, expand generation
        extra = generate_variations(seed + 1, req.num_cases - len(variations), mode=req.generation_mode)
        variations += [v for v in extra if v not in variations]
    variations = variations[:req.num_cases]

    # If human approval required, return proposed list and metadata instead of running
    if req.require_human_approval:
        return {
            "suite_name": req.suite_name,
            "seed": seed,
            "generation_mode": req.generation_mode,
            "proposed_variations": variations,
            "message": "Human approval required. Re-submit without require_human_approval to run tests."
        }

    # Build cases
    cases = [{"name": v, "expected_message": f"Hello, {v}!"} for v in variations]
    gen_info = write_suite_and_json(req.suite_name, cases)

    # Run Robot
    try:
        stats = run_robot(gen_info["robot_path"], base_url="http://localhost:8000")
    except RuntimeError as e:
        return {"error": str(e)}

    # Persist results summary
    results_file = os.path.join(RESULTS_DIR, f"{req.suite_name}_results_{gen_info['timestamp']}.json")
    export_data = {
        "suite_name": req.suite_name,
        "cases_created": len(cases),
        "variations": variations,
        "results": stats,
        "json_file": gen_info["json_file"],
        "robot_file": gen_info["robot_file"],
        "seed": seed,
        "generation_mode": req.generation_mode
    }
    with open(results_file, "w") as f:
        json.dump(export_data, f, indent=2)

    # Append to CSV log
    csv_file = os.path.join(RESULTS_DIR, "test_results_log.csv")
    write_header = not os.path.exists(csv_file)
    with open(csv_file, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow([
                "timestamp", "suite_name", "cases_created", "generation_mode", "seed",
                "total", "passed", "failed", "skipped", "pass_rate_percent", "json_file", "robot_file"
            ])
        writer.writerow([
            gen_info["timestamp"], req.suite_name, len(cases), req.generation_mode, seed,
            stats["total"], stats["passed"], stats["failed"], stats["skipped"], stats["pass_rate_percent"],
            gen_info["json_file"], gen_info["robot_file"]
        ])

    return export_data

# -------------------------
# Notes on GenAI integration
# -------------------------
# To integrate a real GenAI model for proposing variations:
# - Implement call_genai_propose(prompt, count, constraints) that calls your model and returns a list[str].
# - Replace the 'genai' branch in generate_variations with a call to that function.
# - Always post-filter GenAI outputs with filter_and_normalize and record the seed/metadata.
#
# Security and reproducibility:
# - Record seed, mode, and filters in generated JSON.
# - Require human approval for any GenAI-proposed lists before using them in production tests.
#
# Run instructions:
# 1. pip install fastapi uvicorn robotframework robotframework-requests
# 2. uvicorn app:app --reload --host 0.0.0.0 --port 8000
# 3. POST /propose-variations or /generate-tests as needed.