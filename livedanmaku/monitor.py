#! /usr/bin/python3
from livedanmaku import danmaku
import sys

if len(sys.argv) < 2:
    print("No room number designated.")
    exit(0)
else:
    roomid=sys.argv[1]
client = danmaku.Danmaku()


@client.processor("DANMU_MSG")
def print_msg(msg):
    username = msg["info"][2][1]
    content = msg["info"][1]
    # print(" "*30, end="\r")
    print(f"\033[2K\r[\x1b[34m{username}\x1b[39m]: {content}")


@client.processor("INTERACT_WORD")
def process_interact_word(event):
    username = event["data"]["uname"]
    # print(" "*50, end="\r")
    print(f"\033[2K\r{username:8s} 进入了直播间。", end="")


@client.processor("NO_IMPL")
def process_no_impl(event):
    pass


client.connect(roomid)
# some code

client.wait()
