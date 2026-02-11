#!/usr/bin/env python3
"""
Manual test script for Epic 2.3, 2.4, 2.5
This runs the ingestion pipeline with mock data (no Google API needed)
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the app directory to path
sys.path.insert(0, "/app")

from app.pipelines.ingestion import RunInput, ingest_run, build_run_inputs
from app.schemas.results import SearchResultItem


class MockSearchClient:
    """Mock search client that returns fake results"""
    def __init__(self):
        self.calls = []
    
    def search(self, *, run_id: str, search_query: str):
        self.calls.append((run_id, search_query))
        print(f"🔍 Mock search: {search_query}")
        
        # Return mock results based on domain
        if "greenhouse.io" in search_query:
            return [
                SearchResultItem(
                    title="Senior Backend Engineer",
                    snippet="Join our team as a Senior Backend Engineer...",
                    link="https://boards.greenhouse.io/example/jobs/123",
                    display_link="greenhouse.io"
                ),
                SearchResultItem(
                    title="Staff Backend Developer",
                    snippet="Looking for a Staff Backend Developer...",
                    link="https://boards.greenhouse.io/example/jobs/456",
                    display_link="greenhouse.io"
                ),
            ]
        return []


class MockUrlResolver:
    """Mock URL resolver that simulates HTTP requests"""
    def __init__(self):
        self.calls = []
    
    def resolve(self, url: str):
        self.calls.append(url)
        
        # Simulate 404 for specific URLs to test Story 2.3
        if "404" in url or "not-found" in url:
            print(f"   ⚠️  404 for: {url}")
            return type("Resolved", (), {
                "status_code": 404, 
                "final_url": None, 
                "redirected": False
            })()
        
        print(f"   ✓ Resolved: {url}")
        return type("Resolved", (), {
            "status_code": 200, 
            "final_url": url, 
            "redirected": False
        })()


def test_stories_2_3_to_2_5(run_id: str = None):
    """
    Test Stories:
    - 2.3: Fetch Search Results and Persist Metadata
    - 2.4: Capture Raw HTML and Visible Text  
    - 2.5: Cache Results and Revisit Throttling
    """
    run_id = run_id or f"test-run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    
    print("=" * 60)
    print(f"🚀 Testing Stories 2.3, 2.4, 2.5")
    print(f"   Run ID: {run_id}")
    print("=" * 60)
    
    # Build run inputs from config
    print("\n📋 Building run inputs from config...")
    config_dir = Path(os.getenv("CONFIG_DIR", "/app/config"))
    run_inputs = build_run_inputs(config_dir=config_dir)
    print(f"   Found {len(run_inputs)} query/domain combinations")
    
    if not run_inputs:
        print("   ❌ No enabled queries or domains found!")
        print("   Make sure you have enabled queries and allowlists in config/")
        return
    
    for ri in run_inputs:
        print(f"   - {ri.search_query}")
    
    # Run ingestion with mocks
    print("\n🔬 Running ingestion pipeline...")
    search_client = MockSearchClient()
    resolver = MockUrlResolver()
    data_dir = Path(os.getenv("DATA_DIR", "/app/data"))
    
    outcome = ingest_run(
        run_id=run_id,
        run_inputs=run_inputs,
        search_client=search_client,
        url_resolver=resolver,
        now=datetime.now(timezone.utc),
        data_dir=data_dir
    )
    
    # Results
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)
    print(f"   Search calls issued: {outcome.issued_calls}")
    print(f"   Results persisted: {outcome.persisted_results}")
    print(f"   404s skipped: {outcome.skipped_404}")
    
    # Check database
    db_path = data_dir / "db" / "runs" / f"{run_id}.db"
    print(f"\n💾 Database: {db_path}")
    if db_path.exists():
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check run_items table
        cursor.execute("SELECT COUNT(*) FROM run_items")
        count = cursor.fetchone()[0]
        print(f"   Run items in DB: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT title, domain, raw_url, final_url, raw_html_path, visible_text 
                FROM run_items LIMIT 3
            """)
            rows = cursor.fetchall()
            print("\n   Sample data:")
            for row in rows:
                print(f"   - Title: {row[0]}")
                print(f"     Domain: {row[1]}")
                print(f"     URL: {row[3]}")
                print(f"     HTML Path: {row[4]}")
                print(f"     Visible Text Preview: {str(row[5])[:100]}..." if row[5] else "     Visible Text: None")
                print()
        
        conn.close()
    
    # Check HTML files (Story 2.4)
    html_dir = data_dir / "html" / "raw"
    if html_dir.exists():
        html_files = list(html_dir.glob("*.html"))
        print(f"\n🌐 HTML files captured: {len(html_files)}")
        for f in html_files[:3]:
            print(f"   - {f.name} ({f.stat().st_size} bytes)")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test Epic 2.3-2.5 ingestion pipeline")
    parser.add_argument("--run-id", help="Custom run ID (optional)")
    args = parser.parse_args()
    
    test_stories_2_3_to_2_5(run_id=args.run_id)
