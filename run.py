#!/usr/bin/env python3
from my_agent.main import AIAgent
import json


def main():
    print("Initializing AI Agent...")
    agent = AIAgent("config/config.yaml")
    agent.initialize()

    print("AI Agent ready. Enter your questions (or 'exit' to quit)")

    while True:
        question = input("\nYour question: ")
        if question.lower() in ["exit", "quit"]:
            break

        # Process the query
        result = agent.query(question)

        # Display the answer
        print("\nAnswer:")
        print(result["answer"])

        # Display sources
        if result["sources"]:
            print("\nSources:")
            for i, source in enumerate(result["sources"]):
                if "path" in source:
                    print(f"  {i + 1}. {source['type']}: {source['path']}")
                elif "url" in source:
                    print(f"  {i + 1}. {source['type']}: {source['url']}")


if __name__ == "__main__":
    main()