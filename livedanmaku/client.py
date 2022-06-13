#! /usr/bin/python3
from livedanmaku import danmaku
import logging as log
import os
import sys

if len(sys.argv) < 3:
    print("Usage: python -m livedanmaku.client <roomid> <cookie_path>")
    exit(0)
else:
    roomid=sys.argv[1]
    cookie_path=sys.argv[2]


LOGLEVEL = log.DEBUG
log.basicConfig(
    level=LOGLEVEL, format="[%(asctime)s (%(levelname)s) line %(lineno)d in %(funcName)s]\n%(message)s\n----")

client = danmaku.Danmaku()


@client.processor("DANMU_MSG")
def print_msg(msg):
    username = msg["info"][2][1]
    content = msg["info"][1]
    print(f"\033[2K\r[\x1b[34m{username}\x1b[39m]: {content}")
    if content == "哈喽":
        client.send(f"@{username} qwq")
    # os.system(f"notify-send '[{username}]说:' '{content}' --app-name='Bilibili Danmaku Room {client.roomid}' -t 3000")


@client.processor("INTERACT_WORD")
def process_interact_word(event):
    username = event["data"]["uname"]
    print(f"\033[2K\r{username} 进入了直播间。", end="")
    client.send(f"@{username} 欢迎进入直播间!")


@client.processor("NO_IMPL")
def process_no_impl(event):
    # 可以加Logfile， 以便记录未实现的事件
    pass


try:
    client.set_cookie_file(cookie_path)
    client.connect(roomid)
    # do some thing
    client.wait()
except KeyboardInterrupt:
    print("\rBye!")
    exit(0)
