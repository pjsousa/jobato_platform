#!/usr/bin/env python3
"""
Standalone demo script to showcase Brave Search API functionality.

Usage:
    cd ml && python demo/brave_search_demo.py

Requirements:
    - BRAVE_SEARCH_API_KEY environment variable must be set
"""

from __future__ import annotations

import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.brave_search import BraveSearchClient, BraveSearchConfig, SearchServiceError


def main() -> int:
    api_key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
    if not api_key:
        print("ERROR: BRAVE_SEARCH_API_KEY environment variable is not set")
        print("Get your API key at: https://brave.com/search/api/")
        return 1

    config = BraveSearchConfig(api_key=api_key, freshness="pw", count=20)
    client = BraveSearchClient(config)

    queries = [
        "engineer AND remote",
    ]

    print("=" * 60)
    print("BRAVE SEARCH DEMO")
    print("=" * 60)
    print()

    for query in queries:
        print(f"Query: {query}")
        print("-" * 40)

        try:
            results = client.search(run_id=str(uuid.uuid4()), search_query=query)
            print(f"Found {len(results)} results:\n")

            for i, result in enumerate(results[:10], 1):
                print(f"  [{i}] {result.title}")
                print(f"      URL: {result.link}")
                print(f"      Site: {result.display_link}")
                print(
                    f"      Snippet: {result.snippet[:100]}..."
                    if len(result.snippet) > 100
                    else f"      Snippet: {result.snippet}"
                )
                print()

        except SearchServiceError as e:
            print(f"  ERROR: {e}")
            return 1

        print()

    print("=" * 60)
    print("Brave Search is working correctly!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
