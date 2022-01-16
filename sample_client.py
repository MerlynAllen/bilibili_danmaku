#! /usr/bin/python3
from pydoc import cli
import danmaku
import logging as log
import os


# LOGLEVEL = log.DEBUG
# log.basicConfig(
#     level=LOGLEVEL, format="[%(asctime)s (%(levelname)s) line %(lineno)d in %(funcName)s]\n%(message)s\n----")

client = danmaku.Danmaku()
client.set_cookie_file("cookie.txt")

@client.processor("DANMU_MSG")
def print_msg(msg):
    username = msg["info"][2][1]
    content = msg["info"][1]
    print(f"[\x1b[34m{username}\x1b[39m]: {content}")
    os.system(f"notify-send '[{username}]说:' '{content}' --app-name='Bilibili Danmaku Room {client.roomid}' -t 3000") 

@client.processor("INTERACT_WORD")
def process_interact_word(event):
    username = event["data"]["uname"]
    print(f"{username} 进入了直播间。", end="\r")
    client.send(f"@{username} 哈喽！")

@client.processor("NOT_IMPL")
def process_not_impl(event):
    pass

client.connect(3278551)
