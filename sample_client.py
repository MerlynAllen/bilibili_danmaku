#! /usr/bin/python3
import danmaku
import asyncio
import logging as log
import os


# LOGLEVEL = log.DEBUG
# log.basicConfig(
#     level=LOGLEVEL, format="[%(asctime)s (%(levelname)s) line %(lineno)d in %(funcName)s]\n%(message)s\n----")
#==========
# client = None
# async def loop():
#     global client
#     while True:
#         msg = client.get_message()
#         if msg != None:
#             print("[\x1b[34m{username}\x1b[39m]: {content}".format(**msg))
#             os.system(f"notify-send '[{msg['username']}]说:' '{msg['content']}' --app-name='Bilibili Danmaku Room {roomid}' -t 3000")
#         await asyncio.sleep(0)
# async def main():
#     lp = asyncio.create_task(loop())
#     cn = asyncio.create_task(client.connect())
#     await asyncio.gather(cn, lp)
# if __name__ == "__main__":
#     roomid = input("Room ID: ")
#     client = danmaku.Danmaku(roomid)
#     asyncio.run(main())

client = danmaku.Danmaku()

@client.processor("DANMU_MSG")
def print_msg(msg):
    username = msg["info"][2][1]
    content = msg["info"][1]
    print(f"[\x1b[34m{username}\x1b[39m]: {content}")
    os.system(f"notify-send '[{username}]说:' '{content}' --app-name='Bilibili Danmaku Room {client.roomid}' -t 3000") 

# @client.processor("ALL")
# def process_all(event):
#     print(event)

# @client.processor("INTERACT_WORD")
# def process_interact_word(event):
#     print(event)

# @client.processor("SEND_GIFT")
# def process_send_gift(event):
#     print(event)

# @client.processor("LIVE_INTERACTIVE_GAME")
# def process_live_interactive_game(event):
#     print(event)

# @client.processor("ONLINE_RANK_COUNT")
# def process_online_rank_count(event):
#     print(event)

@client.processor("NOT_IMPL")
def process_not_impl(event):
    print(event["cmd"])


roomid = input("Room ID: ")
asyncio.run(client.connect(roomid))

# INTERACT_WORD
# ONLINE_RANK_COUNT
# LIVE_INTERACTIVE_GAME
# SEND_GIFT
