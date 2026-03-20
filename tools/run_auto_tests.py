import json, random, string, subprocess
from robot.api import ExecutionResult

def random_string(length=20):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_cases(extend=True):
    cases = [
        {"name": "Alice", "expected_message": "Hello, Alice!"},
        {"name": "Bob", "expected_message": "Hello, Bob!"},
        {"name": "", "expected_message": "Hello, !"},
        {"name": "@#$%^&*", "expected_message": "Hello, @#$%^&*!"},
        {"name": random_string(), "expected_message": f"Hello, {random_string()}!"}
    ]
    path = "robot-tests/data/generated_cases.json"
    if extend:
        try:
            existing = json.load(open(path))
            cases = existing + cases
        except FileNotFoundError:
            pass
    json.dump(cases, open(path, "w"), indent=2)
    return cases

def run_robot():
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
    stats = run_robot()
    print(f"\nGenerated {len(cases)} cases.")
    print(f"Results: {stats['passed']} passed / {stats['failed']} failed / {stats['total']} total")
    print("Insights:")
    if stats["failed"] > 0:
        print("- Some edge cases failed, check API handling for special inputs.")
    else:
        print("- All cases passed, API is resilient to tested variations.")