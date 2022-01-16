import sys, os
import asyncio
import aioconsole
# sys.stdin.line_buffering = False
f = sys.stdin
# while True:
#     print(".", end="")
#     print(f.readline())
s = "."
async def read_from_stdin():
    stdin, _= await aioconsole.get_standard_streams()
    global s
    while True:
        line = await stdin.readline()
        s = line.decode("utf-8")
        await asyncio.sleep(0.1)

async def loop():
    while True:
        print(f"{s}", end="")
        await asyncio.sleep(0.1)
    pass

async def main():
    tasks = [
        asyncio.create_task(loop()),
        asyncio.create_task(read_from_stdin())
    ]
    await asyncio.gather(*tasks)

asyncio.run(main())