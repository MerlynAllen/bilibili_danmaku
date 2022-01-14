#!/bin/python3
import re
import aiohttp
import asyncio
from aiohttp import web
import json
import struct
import time
import brotli
import logging as log

HEADER_LEN = 16
DEFAULT_VER = 1
OP_USER_AUTH = 7
OP_HEARTBEAT = 2
OP_HEARTBEAT_ACK = 3
OP_CONN_SUCCESS = 8
OP_MSG = 5
DEFAULT_SEQ = 1
CONT_CMD = 0
CONT_INFO = 3

# Retrieve server info
LOGLEVEL = log.INFO

log.basicConfig(
    level=LOGLEVEL, format="[%(asctime)s (%(levelname)s) line %(lineno)d in %(funcName)s]\n%(message)s\n----")


async def get_info(room_id):
    api = "https://api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo"
    async with aiohttp.ClientSession() as session:
        async with session.get(api, params={"id": str(room_id), "type": "0"}) as resp:
            log.debug(
                f"Room {room_id}\nStatus {resp.status}\nInfo\n----\n{resp.text}")
            return await resp.json()
# Header generator


def header_gen(datalen, op, seq):
    header = [
        datalen + HEADER_LEN,
        HEADER_LEN,
        DEFAULT_VER,
        op,
        seq
    ]
    header = struct.pack(">ihhii", *header)
    log.debug(f"Created header {header}")
    return header

# Split messages from multiple packets
def split_msg(msg_raw):
    messages = []
    cur_ptr = 0
    while 1:
        msg_len = struct.unpack(">i", msg_raw[cur_ptr:cur_ptr + 4])[0]
        header_len = struct.unpack(">h", msg_raw[cur_ptr + 4:cur_ptr + 6])[0]
        messages.append(json.loads(msg_raw[cur_ptr + header_len:cur_ptr + msg_len]))
        cur_ptr += msg_len
        if cur_ptr >= len(msg_raw):
            break
    return messages


def parse_cmd():
    pass

# Event loop

MSG_BUFFER = []
async def loop(ws):
    while True:
        data = await ws.receive()
        if data.data is None:
            break
        op_type = struct.unpack(">i", data.data[8:12])[0]
        cont_type = struct.unpack(">h", data.data[6:8])[0]
        recv_len = len(data.data)
        recv_header_len = struct.unpack(">h", data.data[4:6])[0]
        header = data.data[:recv_header_len]
        payload = data.data[recv_header_len:]
        packet_type = None
        if_extended_header = False
        ext_header_len = 0
        ext_header = b''

        if op_type == OP_HEARTBEAT_ACK:
            packet_type = "heartbeat"
            if_extended_header = True
            ext_header = payload[:4]
            payload = payload[4:]
        elif op_type == OP_CONN_SUCCESS:
            packet_type = "conn_success_ack"
        else:
            if cont_type == CONT_CMD:
                packet_type = "command"
                # commands = split_cmd(payload)
                # payload = commands
            elif cont_type == CONT_INFO:
                payload = brotli.decompress(payload)
                packet_type = "info"
                messages = split_msg(payload)
                payload = messages
                for msg in messages:
                    if msg["cmd"] == "DANMU_MSG":
                        username = msg["info"][2][1]
                        content = msg["info"][1]
                        MSG_BUFFER.append({
                            "username": username,
                            "content": content
                        })

        log.debug(f"Received ({packet_type}) {recv_len} bytes\nHeader {recv_header_len} bytes:{header}\nExtHeader {ext_header_len} bytes: {ext_header}\nData {recv_len - recv_header_len - ext_header_len} bytes: {payload}")

# This is not included in the API
async def print_msg():
    while True:
        if len(MSG_BUFFER) > 0:
            msg = MSG_BUFFER.pop(0)
            print("[{username}] {content}".format(**msg))
        await asyncio.sleep(0)

# Heartbeat loop
async def heartbeat(ws):
    obj = "[object Object]"
    while True:
        await ws.send_bytes(
            header_gen(len(obj), OP_HEARTBEAT, DEFAULT_SEQ) +
            obj.encode("utf-8")
        )
        log.debug("Sent heartbeat")
        await asyncio.sleep(30)
# Main loop

async def get_real_roomid(roomid):
    api = "https://api.live.bilibili.com/room/v1/Room/room_init"
    async with aiohttp.ClientSession() as session:
        async with session.get(api, params={"id": str(roomid)}) as resp:
            real_roomid = (await resp.json())['data']['room_id']
            log.debug(f"Get real roomid {real_roomid}")
            return real_roomid

async def main():
    roomid = input("Room ID: ")
    roomid = await get_real_roomid(roomid)
    server_info = await get_info(room_id=roomid)
    token = server_info["data"]["token"]
    server_lists = server_info["data"]["host_list"]
    # Select server
    sample_server = server_lists[1]
    server = sample_server
    port = 443
    log.debug(f"Got token {token}")
    log.debug(f"Got server {server_lists}")
    header = \
        "User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0"
    "Accept: */*"
    "Accept-Language: zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2"
    "Accept-Encoding: gzip, deflate, br"
    "Sec-WebSocket-Version: 13"
    "Origin: https://live.bilibili.com"
    "DNT: 1"
    "Connection: keep-alive, Upgrade"
    "Cookie: b_ut=5; i-wanna-go-back=-1; _uuid=D4543696-6DD9-BBE5-88B1-29B7F76DE76B79508infoc; sid=bkzvod6m; fingerprint=2d4d930b6fd1fbaea36c5817ed4e4276; DedeUserID=34571330; DedeUserID__ckMd5=994798d0b387867e; SESSDATA=522eb1f3%2C1647486690%2Cd9dc8*91; bili_jct=c674567fe1ceb43b54740842153ba915; fingerprint3=75a924074f058eb3f4226db19ce4f289; fingerprint_s=0adcbfdcac6dc2d86406677fe754a609; CURRENT_BLACKGAP=0; CURRENT_FNVAL=80; CURRENT_QUALITY=0; rpdid=|(u)YJmmlmRR0J'uYJumJR)~m; buvid3=FA0FAEFC-DE12-8132-FF02-8BD6187C340113786infoc; blackside_state=0; PVID=8; video_page_version=v_old_home_20; buvid_fp=FA0FAEFC-DE12-8132-FF02-8BD6187C340113786infoc; bp_video_offset_34571330=615042851549059800; bp_t_offset_34571330=607724102725730626; LIVE_BUVID=AUTO6916399984256327; bp_article_offset_34571330=608551506695003800; innersign=0; b_lsid=28E834A8_17E5167DE82; _dfcaptcha=3956db1260cb87ba0579faa08e4acd95"
    "Pragma: no-cache"
    "Cache-Control: no-cache"
    "Upgrade: websocket"
    header = header.split("\n")
    header = dict(map(lambda x: x.split(": "), header))
    log.info(f"Entering room {roomid}")
    async with aiohttp.ClientSession() as session:
        log.debug(f"Connecting to server {server['host']}:{port}")
        async with session.ws_connect(f"wss://{server['host']}:{port}/sub", headers=header, timeout=0) as ws:
            log.debug(f"Connected")
            subsc = json.dumps({
                "uid": 0,
                "roomid": roomid,
                "protover": 3,
                "platform": "web",
                "type": 2,
                "key": token
            })
            ws_header = header_gen(len(subsc), OP_USER_AUTH, DEFAULT_SEQ)
            await ws.send_bytes(
                ws_header + subsc.encode("utf-8")
            )
            tasks = [
                loop(ws),
                heartbeat(ws),
                print_msg()
            ]
            await asyncio.gather(*tasks)

asyncio.run(main())
