from datetime import datetime, timezone

from app.pipelines.ingestion import RunInput, build_run_inputs, ingest_run


def test_build_run_inputs_loads_enabled_queries_and_domains(tmp_path):
    queries_path = tmp_path / "queries.yaml"
    allowlists_path = tmp_path / "allowlists.yaml"

    queries_path.write_text(
        "\n".join(
            [
                "queries:",
                "- {id: q1, text: Backend Remote, enabled: true, createdAt: '2026-02-01T00:00:00Z', updatedAt: '2026-02-01T00:00:00Z'}",
                "- {id: q2, text: backend remote, enabled: true, createdAt: '2026-02-02T00:00:00Z', updatedAt: '2026-02-02T00:00:00Z'}",
                "- {id: q3, text: disabled, enabled: false, createdAt: '2026-02-02T00:00:00Z', updatedAt: '2026-02-02T00:00:00Z'}",
                "",
            ]
        )
    )
    allowlists_path.write_text(
        "\n".join(
            [
                "allowlists:",
                "- domain: Example.COM",
                "  enabled: true",
                "- domain: example.com",
                "  enabled: true",
                "- domain: disabled.com",
                "  enabled: false",
                "",
            ]
        )
    )

    run_inputs = build_run_inputs(config_dir=tmp_path)

    assert len(run_inputs) == 1
    run_input = run_inputs[0]
    assert run_input.query_text == "Backend Remote"
    assert run_input.domain == "example.com"
    assert run_input.search_query == "site:example.com Backend Remote"


def test_ingest_run_calls_search_for_each_input_with_run_id():
    run_inputs = [
        RunInput(
            query_id="q1",
            query_text="Backend Remote",
            domain="example.com",
            search_query="site:example.com Backend Remote",
        ),
        RunInput(
            query_id="q2",
            query_text="Python Remote",
            domain="jobs.example.com",
            search_query="site:jobs.example.com Python Remote",
        ),
    ]

    class StubSearchClient:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str]] = []

        def search(self, *, run_id: str, search_query: str):
            self.calls.append((run_id, search_query))
            return []

    class StubResolver:
        def resolve(self, url: str):
            return type("Resolved", (), {"status_code": 200, "final_url": url, "redirected": False})()

    class StubWriter:
        def __init__(self) -> None:
            self.results = []

        def write_all(self, results):
            self.results.extend(list(results))
            return len(self.results)

    search_client = StubSearchClient()
    resolver = StubResolver()
    writer = StubWriter()

    outcome = ingest_run(
        run_id="run-123",
        run_inputs=run_inputs,
        search_client=search_client,
        url_resolver=resolver,
        result_writer=writer,
        now=datetime(2026, 2, 8, 12, 0, tzinfo=timezone.utc),
    )

    assert len(search_client.calls) == len(run_inputs)
    assert all(run_id == "run-123" for run_id, _ in search_client.calls)
    assert outcome.issued_calls == len(run_inputs)
    assert writer.results == []
