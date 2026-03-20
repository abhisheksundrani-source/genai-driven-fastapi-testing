import os
import json
import subprocess
import requests
from datetime import datetime
from robot.api import ExecutionResult

def get_base_url():
    port = "8000"
    codespace = os.getenv("CODESPACE_NAME")
    if codespace:
        remote_url = f"https://{codespace}-{port}.app.github.dev"
        try:
            resp = requests.get(f"{remote_url}/health", timeout=3, verify=False)
            if resp.headers.get("content-type", "").startswith("application/json"):
                data = resp.json()
                if data.get("status") == "ok":
                    print(f"✅ Remote endpoint healthy at {remote_url}")
                    return remote_url
                else:
                    print(f"⚠️ Remote returned JSON but not healthy: {data}")
            else:
                print("⚠️ Remote returned non-JSON, falling back to localhost")
        except Exception as e:
            print(f"⚠️ Remote unreachable ({e}), falling back to localhost")
    local_url = f"http://localhost:{port}"
    print(f"✅ Using localhost endpoint {local_url}")
    return local_url

BASE_URL = get_base_url()

def run_robot():
    print(f"\n➡️ Running tests against: {BASE_URL}\n")
    subprocess.run([
        "robot",
        "--variable", f"BASE_URL:{BASE_URL}",
        "robot-tests/suites/generated.robot"
    ], check=True)

    result = ExecutionResult("output.xml")

    total_tests = result.statistics.total.total
    passed_tests = result.statistics.total.passed
    failed_tests = result.statistics.total.failed
    skipped_tests = result.statistics.total.skipped

    print("\n=== Test Summary ===")
    print(f"Total: {total_tests}, Passed: {passed_tests}, Failed: {failed_tests}, Skipped: {skipped_tests}")

    # Insights
    pass_rate = (passed_tests / total_tests * 100) if total_tests else 0
    fail_rate = (failed_tests / total_tests * 100) if total_tests else 0

    insights = {
        "total": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "skipped": skipped_tests,
        "pass_rate_percent": round(pass_rate, 2),
        "fail_rate_percent": round(fail_rate, 2),
        "endpoint": BASE_URL,
        "timestamp": datetime.now().isoformat(timespec="seconds")
    }

    return insights

if __name__ == "__main__":
    stats = run_robot()

    # Ensure results directory exists under robot-tests
    results_dir = os.path.join("robot-tests", "results")
    os.makedirs(results_dir, exist_ok=True)

    # Unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(results_dir, f"test_results_{timestamp}.json")

    with open(filename, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\n✅ Results exported to {filename}")