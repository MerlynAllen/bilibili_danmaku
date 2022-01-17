#! /usr/bin/python3
import livedanmaku

client = livedanmaku.Danmaku()
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

@client.processor("NOT_IMPL")
def process_not_impl(event):
    pass

# client.connect()