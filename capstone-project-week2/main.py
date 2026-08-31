#!/usr/bin/env python3
"""AfyaPlus Enterprise RAG Agent System — CLI entry point."""

from __future__ import annotations

import argparse
import sys
import uuid

from src.agent.runner import clear_session_history
from src.pipeline import handle_inquiry
from src.rag.ingestion import verify_openai_connectivity


def run_single(question: str, session_id: str, verbose: bool) -> int:
    result = handle_inquiry(question, session_id=session_id, verbose=verbose)
    print(result.final_answer)
    return 0


def run_interactive(session_id: str, verbose: bool) -> int:
    print("AfyaPlus Agent (interactive). Type 'exit' or 'quit' to stop.\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break
        result = handle_inquiry(user_input, session_id=session_id, verbose=verbose)
        print(f"Agent: {result.final_answer}\n")
    return 0


def run_demo(verbose: bool) -> int:
    session_id = f"demo-{uuid.uuid4().hex[:8]}"
    clear_session_history(session_id)

    turns = [
        (
            "Hi, I'm David. My phone is 0712 345 678 and email is david@example.com. "
            "I'm on Silver tier — is a routine dental checkup covered?"
        ),
        (
            "Do you remember my name? Also calculate medication volume: "
            "500 mg amoxicillin twice daily for 7 days at 250 mg/mL concentration."
        ),
        "What are the best tourist beaches in Mombasa?",
    ]

    print(f"=== AfyaPlus Demo Session ({session_id}) ===\n")
    for index, question in enumerate(turns, start=1):
        print(f"--- Turn {index} ---")
        print(f"Patient: {question}")
        result = handle_inquiry(question, session_id=session_id, verbose=verbose)
        if verbose:
            print(f"[audit] vault tokens: {result.vault_tokens}")
        print(f"Agent: {result.final_answer}\n")

    clear_session_history(session_id)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AfyaPlus Enterprise RAG Agent System",
    )
    parser.add_argument("question", nargs="?", help="Single-turn inquiry text")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start a multi-turn interactive session",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a scripted demo proving memory, RAG, tools, and refusal",
    )
    parser.add_argument(
        "--session-id",
        default="patient-001",
        help="Session identifier for conversation memory",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print masked payloads and audit metadata",
    )
    parser.add_argument(
        "--verify-api",
        action="store_true",
        help="Verify OpenAI embedding connectivity and exit",
    )
    args = parser.parse_args(argv)

    if args.verify_api:
        verify_openai_connectivity()
        print("OpenAI embedding connectivity OK.")
        return 0

    if args.demo:
        return run_demo(verbose=args.verbose)
    if args.interactive:
        return run_interactive(session_id=args.session_id, verbose=args.verbose)
    if args.question:
        return run_single(args.question, session_id=args.session_id, verbose=args.verbose)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
