"""
Rewrite danmaku.py in Class
"""
import aiohttp
import asyncio
from aiohttp import web
import json
import struct
import time
import brotli
import re
import logging as log


class Danmaku():
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

    MSG_BUFFER = []

    async def get_real_roomid(self, roomid):
        api = "https://api.live.bilibili.com/room/v1/Room/room_init"
        async with aiohttp.ClientSession() as session:
            async with session.get(api, params={"id": str(roomid)}) as resp:
                real_roomid = (await resp.json())['data']['room_id']
                log.debug(f"Get real roomid {real_roomid}")
                return real_roomid

    async def get_info(self, room_id):
        api = "https://api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo"
        async with aiohttp.ClientSession() as session:
            async with session.get(api, params={"id": str(room_id), "type": "0"}) as resp:
                log.debug(
                    f"Room {room_id}\nStatus {resp.status}\nInfo\n----\n{await resp.text()}")
                return await resp.json()

    def server_selection(self):
        raise NotImplementedError

    def __init__(self, roomid) -> None:
        self.roomid = roomid
        log.debug(f"Room ID set to {roomid}")

    def header_gen(self, datalen, op, seq):
        header = [
            datalen + self.HEADER_LEN,
            self.HEADER_LEN,
            self.DEFAULT_VER,
            op,
            seq
        ]
        header = struct.pack(">ihhii", *header)
        log.debug(f"Created header {header}")
        return header

    def split_msg(self, msg_raw):
        messages = []
        cur_ptr = 0
        while 1:
            msg_len = struct.unpack(">i", msg_raw[cur_ptr:cur_ptr + 4])[0]
            header_len = struct.unpack(
                ">h", msg_raw[cur_ptr + 4:cur_ptr + 6])[0]
            messages.append(json.loads(
                msg_raw[cur_ptr + header_len:cur_ptr + msg_len]))
            cur_ptr += msg_len
            if cur_ptr >= len(msg_raw):
                break
        return messages
    def get_message(self):
        if len(self.MSG_BUFFER) > 0:
            return self.MSG_BUFFER.pop(0)
        else:
            return None
    async def loop(self, ws):
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

            if op_type == self.OP_HEARTBEAT_ACK:
                packet_type = "heartbeat"
                if_extended_header = True
                ext_header = payload[:4]
                payload = payload[4:]
            elif op_type == self.OP_CONN_SUCCESS:
                packet_type = "conn_success_ack"
            else:
                if cont_type == self.CONT_CMD:
                    packet_type = "command"
                    # commands = split_cmd(payload)
                    # payload = commands
                elif cont_type == self.CONT_INFO:
                    payload = brotli.decompress(payload)
                    packet_type = "info"
                    messages = self.split_msg(payload)
                    payload = messages
                    for msg in messages:
                        if msg["cmd"] == "DANMU_MSG":
                            username = msg["info"][2][1]
                            content = msg["info"][1]
                            self.MSG_BUFFER.append({
                                "username": username,
                                "content": content
                            })

            log.debug(f"Received ({packet_type}) {recv_len} bytes\nHeader {recv_header_len} bytes:{header}\nExtHeader {ext_header_len} bytes: {ext_header}\nData {recv_len - recv_header_len - ext_header_len} bytes: {payload}")

    async def heartbeat(self, ws):
        obj = "[object Object]"
        while True:
            await ws.send_bytes(
                self.header_gen(len(obj), self.OP_HEARTBEAT, self.DEFAULT_SEQ) +
                obj.encode("utf-8")
            )
            log.debug("Sent heartbeat")
            await asyncio.sleep(30)
    # def connect(self):
    #     asyncio.run(self._connect())
    async def connect(self, server_autoselect=True):
        self.real_roomid = await self.get_real_roomid(self.roomid)
        self.server_info = await self.get_info(self.real_roomid)
        self.token = self.server_info['data']['token']
        self.server_list = self.server_info['data']['host_list']
        if server_autoselect:
            self.server = self.server_list[0]
        else:
            self.server = None
        log.debug(f"Got token {self.token}")
        log.debug(f"Got server {self.server_list}")
        self.header = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate, br",
            # "Sec-WebSocket-Version": "13",
            "Origin": "https://live.bilibili.com",
            "DNT": "1",
            "Connection": "keep-alive, Upgrade",
            # "Cookie": "b_ut=5; i-wanna-go-back=-1; _uuid=D4543696-6DD9-BBE5-88B1-29B7F76DE76B79508infoc; sid=bkzvod6m; fingerprint=2d4d930b6fd1fbaea36c5817ed4e4276; DedeUserID=34571330; DedeUserID__ckMd5=994798d0b387867e; SESSDATA=522eb1f3%2C1647486690%2Cd9dc8*91; bili_jct=c674567fe1ceb43b54740842153ba915; fingerprint3=75a924074f058eb3f4226db19ce4f289; fingerprint_s=0adcbfdcac6dc2d86406677fe754a609; CURRENT_BLACKGAP=0; CURRENT_FNVAL=80; CURRENT_QUALITY=0; rpdid=|(u)YJmmlmRR0J'uYJumJR)~m; buvid3=FA0FAEFC-DE12-8132-FF02-8BD6187C340113786infoc; blackside_state=0; PVID=8; video_page_version=v_old_home_20; buvid_fp=FA0FAEFC-DE12-8132-FF02-8BD6187C340113786infoc; bp_video_offset_34571330=615042851549059800; bp_t_offset_34571330=607724102725730626; LIVE_BUVID=AUTO6916399984256327; bp_article_offset_34571330=608551506695003800; innersign=0; b_lsid=28E834A8_17E5167DE82; _dfcaptcha=3956db1260cb87ba0579faa08e4acd95",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "Upgrade": "websocket"
        }
        log.info(f"Entering room {self.real_roomid}")
        async with aiohttp.ClientSession() as self.session:
            log.debug(f"Initialized Danmaku object for room {self.real_roomid}")
            log.debug(
                f"Connecting to server {self.server['host']}:{self.server['wss_port']}")
            async with self.session.ws_connect(f"wss://{self.server['host']}:{self.server['wss_port']}/sub", headers=self.header, timeout=0) as ws:
                log.debug(f"Connected")
                subsc = json.dumps({
                    "uid": 0,
                    "roomid": self.real_roomid,
                    "protover": 3,
                    "platform": "web",
                    "type": 2,
                    "key": self.token
                })
                ws_header = self.header_gen(
                    len(subsc), self.OP_USER_AUTH, self.DEFAULT_SEQ)
                await ws.send_bytes(
                    ws_header + subsc.encode("utf-8")
                )
                tasks = [
                    self.loop(ws),
                    self.heartbeat(ws)
                ]
                await asyncio.gather(*tasks)
