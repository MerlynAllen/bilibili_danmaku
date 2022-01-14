#! /usr/bin/python3
import danmaku
import asyncio
import aiohttp
import logging as log


LOGLEVEL = log.INFO
log.basicConfig(
    level=LOGLEVEL, format="[%(asctime)s (%(levelname)s) line %(lineno)d in %(funcName)s]\n%(message)s\n----")
client = None
async def loop():
    global client
    while True:
        msg = client.get_message()
        if msg != None:
            print("[{username}]: {content}".format(**msg))
        await asyncio.sleep(0)
async def main():
    lp = asyncio.create_task(loop())
    cn = asyncio.create_task(client.connect())
    await asyncio.gather(cn, lp)
if __name__ == "__main__":
    roomid = input("Room ID: ")
    client = danmaku.Danmaku(roomid)
    asyncio.run(main())
