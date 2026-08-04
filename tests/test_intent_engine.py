"""Manual integration test script for the Intent Classification Engine."""

from src.ai_agents.intent import IntentEngine


def print_result(query: str, result) -> None:
    print("=" * 80)
    print(f"Input Query   : {query}")
    print(f"Primary Intent: {result.primary_intent}")
    print(f"Confidence    : {result.confidence:.4f}")
    print(f"Entities      : {result.entities}")
    print("=" * 80)
    print()


def main() -> None:
    engine = IntentEngine()

    print("Running Intent Classification & Entity Extraction Scenarios:\n")

    test_queries = [
        "Compare Dell vs HP under ₹70,000",
        "Best gaming laptop under ₹80,000",
        "Show Apple laptops with OLED display",
        "Compare Samsung phones with good battery",
        "Price drop history of Asus Zenbook with 16GB RAM",
        "Is the iPhone 15 Pro in stock in midnight color?",
        "recommend a laptop with Intel Core i7 processor and Windows operating system",
        "blah blah widgets",
        "hello there",
    ]

    for q in test_queries:
        res = engine.classify_intent(q)
        print_result(q, res)


if __name__ == "__main__":
    main()
