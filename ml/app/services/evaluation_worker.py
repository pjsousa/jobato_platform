from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable
from typing import TypeVar


T = TypeVar("T")


async def run_worker_pool(
    jobs: Iterable[T],
    *,
    worker_count: int,
    worker_fn: Callable[[T], Awaitable[None]],
) -> None:
    if worker_count < 1:
        raise ValueError("worker_count must be >= 1")

    queue: asyncio.Queue[T | None] = asyncio.Queue()
    job_list = list(jobs)
    for job in job_list:
        queue.put_nowait(job)

    active_workers = min(worker_count, max(len(job_list), 1))
    for _ in range(active_workers):
        queue.put_nowait(None)

    async def worker() -> None:
        while True:
            job = await queue.get()
            try:
                if job is None:
                    return
                try:
                    await worker_fn(job)
                except Exception:
                    continue
            finally:
                queue.task_done()

    workers = [asyncio.create_task(worker()) for _ in range(active_workers)]
    await queue.join()
    await asyncio.gather(*workers)
