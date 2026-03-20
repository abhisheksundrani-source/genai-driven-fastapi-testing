import json
import random
import string


def random_string(length=20):
    """Generate a random alphanumeric string for fuzz testing."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_cases():
    cases = [
        {"name": "Alice", "expected_message": "Hello, Alice!"},
        {"name": "Bob", "expected_message": "Hello, Bob!"},
        {"name": "", "expected_message": "Hello, !"},  # Empty string
        {"name": "John_Doe_123", "expected_message": "Hello, John_Doe_123!"},
        {"name": "@#$%^&*", "expected_message": "Hello, @#$%^&*!"},
        {
            "name": "ThisIsAVeryLongNameThatExceedsNormalLengthExpectations",
            "expected_message": "Hello, ThisIsAVeryLongNameThatExceedsNormalLengthExpectations!",
        },
        {"name": "null", "expected_message": "Hello, null!"},
        {"name": "测试", "expected_message": "Hello, 测试!"},
        {"name": "   ", "expected_message": "Hello,    !"},  # Whitespace
        {
            "name": random_string(),
            "expected_message": f"Hello, {random_string()}!",
        },  # Fuzzed input
    ]
    return cases


if __name__ == "__main__":
    cases = generate_cases()
    output_path = "robot-tests/data/generated_cases.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2, ensure_ascii=False)
    print(f"Generated {len(cases)} test cases in {output_path}")