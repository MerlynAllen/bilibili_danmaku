from http import client
import danmaku
import asyncio
import aiohttp
import logging as log


LOGLEVEL = log.INFO
log.basicConfig(
    level=LOGLEVEL, format="[%(asctime)s (%(levelname)s) line %(lineno)d in %(funcName)s]\n%(message)s\n----")

async def loop():
    global client
    while True:
        msg = client.get_message()
        if msg != None:
            print("[{username}]: {content}".format(**msg))
        await asyncio.sleep(1)
async def main():
    roomid = input("Room ID: ")
    client = danmaku.Danmaku(roomid)
    lp = asyncio.create_task(loop())
    cn = asyncio.create_task(client.connect())
    await asyncio.gather(cn, lp)
asyncio.run(main())