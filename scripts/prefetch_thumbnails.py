import asyncio
import aiohttp
import os

API_BASE = os.environ.get("NEXUS_API_BASE", "http://127.0.0.1:8000")

async def prefetch_for_ids(content_ids):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for cid in content_ids:
            url = f"{API_BASE}/api/v1/content/thumbnail/{cid}"
            tasks.append(session.get(url))
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for cid, resp in zip(content_ids, responses):
            if isinstance(resp, Exception):
                print(f"❌ thumbnail prefetch failed for {cid}: {resp}")
            else:
                try:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"✅ {cid} -> {data.get('picture_url')}")
                    else:
                        print(f"⚠️ {cid} -> status {resp.status}")
                finally:
                    await resp.release()

async def main():
    # Accept IDs via env var or fallback sample range
    ids_env = os.environ.get("NEXUS_THUMBNAIL_IDS")
    if ids_env:
        ids = [int(x) for x in ids_env.split(",") if x.strip().isdigit()]
    else:
        # Fallback: recent sample range; adjust as needed
        ids = list(range(2100, 2180))
    await prefetch_for_ids(ids)

if __name__ == "__main__":
    asyncio.run(main())
