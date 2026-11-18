import asyncio
import time
import httpx


async def call(client: httpx.AsyncClient, url: str) -> float:
    start = time.perf_counter()
    await client.get(url, timeout=30)
    return time.perf_counter() - start


async def main():
    async with httpx.AsyncClient() as client:
        for kind in ["slow-blocking", "slow-async"]:
            start = time.perf_counter()
            durations = await asyncio.gather(
                call(client, f"http://127.0.0.1:8000/{kind}/1"),
                call(client, f"http://127.0.0.1:8000/{kind}/2"),
            )
            total = time.perf_counter() - start
            print(
                f"{kind}: each {[round(d, 1) for d in durations]}s, total {total:.1f}s"
            )


asyncio.run(main())
