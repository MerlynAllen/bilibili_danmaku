from os import times
import aiohttp
import asyncio
import base64
import json
import time

doh = "https://dns.google/resolve"

async def heartbeat(sess):
    while True:
        res = await sess.get("http://localhost:8080")
        print(f"{time.strftime('%X')} sent {res.status}")
        await asyncio.sleep(5)


async def main():
    async with aiohttp.ClientSession() as session:
        hb = asyncio.create_task(heartbeat(session))
        print("Created tasks")
        await hb
        while 1:
            print(f"{time.strftime('%X')} heartbeat")
            await asyncio.sleep(1)
asyncio.run(main())