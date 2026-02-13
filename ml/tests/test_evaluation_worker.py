import asyncio

from app.services.evaluation_worker import run_worker_pool


def test_worker_pool_respects_concurrency_cap() -> None:
    async def run_case() -> int:
        max_running = 0
        running = 0
        lock = asyncio.Lock()

        async def worker_fn(job: int) -> None:
            nonlocal running, max_running
            async with lock:
                running += 1
                max_running = max(max_running, running)
            await asyncio.sleep(0.03)
            async with lock:
                running -= 1

        await run_worker_pool(range(8), worker_count=3, worker_fn=worker_fn)
        return max_running

    max_running = asyncio.run(run_case())
    assert max_running <= 3


def test_worker_pool_continues_when_job_fails() -> None:
    async def run_case() -> list[int]:
        processed: list[int] = []

        async def worker_fn(job: int) -> None:
            processed.append(job)
            if job == 2:
                raise RuntimeError("boom")

        try:
            await run_worker_pool([0, 1, 2, 3], worker_count=2, worker_fn=worker_fn)
        except RuntimeError:
            pass
        return processed

    processed = asyncio.run(run_case())
    assert set(processed) == {0, 1, 2, 3}
