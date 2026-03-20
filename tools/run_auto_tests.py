import os, json, random, string, subprocess
from robot.api import ExecutionResult

BASE_URL = os.getenv("BASE_URL") or get_base_url()

def random_string(length=20):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def get_base_url():
    # Try to auto-detect Codespaces proxy
    codespace = os.getenv("CODESPACE_NAME")
    port = "8000"
    if codespace:
        return f"https://{codespace}-{port}.app.github.dev"
    # Allow manual override via BASE_URL env var
    if os.getenv("BASE_URL"):
        return os.getenv("BASE_URL")
    # Fallback to localhost
    return f"http://localhost:{port}"

def generate_cases(extend=True):
    new_cases = [
        {"name": "Alice", "expected_message": "Hello, Alice!"},
        {"name": "Bob", "expected_message": "Hello, Bob!"},
        {"name": "", "expected_message": "Hello, !"},
        {"name": "@#$%^&*", "expected_message": "Hello, @#$%^&*!"},
        {"name": random_string(), "expected_message": f"Hello, {random_string()}!"}
    ]
    path = "robot-tests/data/generated_cases.json"
    if extend and os.path.exists(path):
        existing = json.load(open(path))
        cases = existing["cases"] + new_cases
    else:
        cases = new_cases
    json.dump({"cases": cases}, open(path, "w"), indent=2)
    return cases

def ensure_suite():
    suite_path = "robot-tests/suites/generated.robot"
    os.makedirs(os.path.dirname(suite_path), exist_ok=True)
    with open(suite_path, "w") as f:
        f.write(f"""*** Settings ***
Library    RequestsLibrary
Variables  ../data/generated_cases.json

*** Test Cases ***
Hello API Generated Cases
    Create Session    api    {BASE_URL}
    FOR    ${{case}}    IN    @{cases}
        ${{resp}}=    GET On Session    api    /hello/${{case["name"]}}
        Should Be Equal As Strings    ${{resp.json()["message"]}}    ${{case["expected_message"]}}
    END
""")

def run_robot():
    print(f"\n➡️ Running tests against: {BASE_URL}\n")
    subprocess.run(["robot", "robot-tests/suites/generated.robot"], check=True)
    result = ExecutionResult("output.xml")
    stats = {
        "total": result.suite.statistics.total.all,
        "passed": result.suite.statistics.total.passed,
        "failed": result.suite.statistics.total.failed
    }
    return stats

if __name__ == "__main__":
    choice = input("Extend existing suite (y/n)? ").lower().startswith("y")
    cases = generate_cases(extend=choice)
    ensure_suite()
    stats = run_robot()
    print(f"\nGenerated {len(cases)} cases.")
    print(f"Results: {stats['passed']} passed / {stats['failed']} failed / {stats['total']} total")
    if stats["failed"] > 0:
        print("Insights: Some edge cases failed — API may need stronger input validation.")
    else:
        print("Insights: All cases passed — API handled tested variations well.")