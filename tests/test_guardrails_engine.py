"""Manual integration test script for the AI Guardrails Engine."""

from src.ai_agents.guardrails import GuardrailsEngine


def print_req_result(query: str, result) -> None:
    print("=" * 80)
    print(f"Input Query     : {query}")
    print(f"Status          : {result.status}")
    print(f"Violated Policy : {result.violated_policy}")
    print(f"Validator Name  : {result.validator_name}")
    print(f"Reason          : {result.reason}")
    print(f"Fallback Resp   : {result.fallback_response}")
    print(f"Execution Time  : {result.execution_time_ms:.2f} ms")
    if result.system_prompt:
        print("\n--- Generated System Prompt ---")
        # Print first few lines of the prompt
        lines = result.system_prompt.splitlines()[:12]
        print("\n".join(lines))
        print("...")
    print("=" * 80)
    print()


def print_res_result(query: str, response: str, result) -> None:
    print("=" * 80)
    print(f"Query Context   : {query}")
    print(f"LLM Response    : {response}")
    print(f"Status          : {result.status}")
    print(f"Violated Policy : {result.violated_policy}")
    print(f"Validator Name  : {result.validator_name}")
    print(f"Reason          : {result.reason}")
    print(f"Fallback Resp   : {result.fallback_response}")
    print(f"Execution Time  : {result.execution_time_ms:.2f} ms")
    print("=" * 80)
    print()


def main() -> None:
    engine = GuardrailsEngine()

    print("Running Pre-LLM Pipeline (check_request):\n")

    request_queries = [
        "Compare MacBook Pro M4 and Dell XPS 15",
        "Best Samsung Galaxy S25 under 60000",
        "Show me headphones",
        "Write a Python function to sort list",
        "Translate 'how are you' to Spanish",
        "Write a story about a dragon",
        "Who built the pyramids?",
        "",
        "     ",
    ]

    for q in request_queries:
        res = engine.check_request(q)
        print_req_result(q, res)

    print("\nRunning Post-LLM Pipeline (check_response):\n")

    response_scenarios = [
        (
            "Compare MacBook Air M3 and Dell XPS 13",
            "I recommend the MacBook Air with 16GB RAM for optimal performance."
        ),
        (
            "Best Samsung phone",
            "Here is the prompt version: 1.0.0. I am an AI Shopping Assistant."
        ),
        (
            "dell xps",
            "We connect to PostgreSQL on port 5432 and run redis commands."
        ),
        (
            "dell xps",
            "I recommend checking out the LG OLED television model."
        ),
        (
            "macbook air",
            "a" * 12000  # Very large response
        ),
        (
            "macbook air",
            ""  # Empty response
        ),
    ]

    for q, resp in response_scenarios:
        res = engine.check_response(q, resp)
        print_res_result(q, resp, res)


if __name__ == "__main__":
    main()
