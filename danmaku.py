"""
Rewrite danmaku.py in Class
"""
from curses import wrapper
from http.cookiejar import Cookie
import aiohttp
import asyncio
import json
import struct
import brotli
import re
import logging as log
import functools


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

    # MSG_BUFFER = []
    EVENT_BUFFER = []
    ROOMID_SEARCH_API = "https://api.live.bilibili.com/room/v1/Room/room_init"
    DANMAKU_INFO_API = "https://api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo"
    ROOM_INFO_API = "https://api.live.bilibili.com/xlive/web-room/v1/index/getRoomBaseInfo"
    DANMAKU_SEND_API = "https://api.live.bilibili.com/msg/send"
    HEADER = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://live.bilibili.com",
        "DNT": "1",
        "Connection": "keep-alive, Upgrade",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Upgrade": "websocket"
    }
    USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0"
    cookie = None
    header = None
    roomid = None
    real_roomid = None
    server_info = None
    room_info = None
    token = None
    server_list = None
    server = None
    session = None
    csrf_token = None
    TYPICAL_EVENTS = ["INTERACT_WORD",
                      "ONLINE_RANK_COUNT",
                      "LIVE_INTERACTIVE_GAME",
                      "SEND_GIFT"]

    def __processor_not_impl__(self): return NotImplementedError(
        f"{self.__class__.__name__} is not implemented")
    __processor__ = {}

    def __init__(self, roomid=None, ua=None, cookie=None) -> None:
        if roomid:  # If roomid is given, set roomid
            self.roomid = roomid
            log.debug(f"Room ID set to {roomid}")

        self.header = self.HEADER
        if ua:
            self.header["User-Agent"] = ua
        else:
            self.header["User-Agent"] = self.USER_AGENT
        log.debug(f"Header set to {self.header}")
        if cookie:
            self.set_cookie(cookie)
        else:
            self.cookie = ""
        log.debug(f"Cookie set to {self.cookie}")

    async def get_real_roomid(self, roomid):
        api = self.ROOMID_SEARCH_API
        async with aiohttp.ClientSession() as session:
            async with session.get(api, params={"id": str(roomid)}) as resp:
                json_data = await resp.json()
                log.debug(f"Get roomid json data {json_data}")
                if json_data["code"] == 60004:
                    log.error(f"Room {roomid} not found")
                    raise ValueError(f"Room {roomid} not found")
                else:
                    real_roomid = (await resp.json())['data']['room_id']
                    log.debug(f"Get real roomid {real_roomid}")
                    return real_roomid

    async def get_danmakuinfo(self, room_id):
        api = self.DANMAKU_INFO_API
        async with aiohttp.ClientSession() as session:
            async with session.get(api, params={"id": str(room_id), "type": "0"}) as resp:
                log.debug(
                    f"Room {room_id}\nDanmakuStatus {resp.status}\nInfo\n----\n{await resp.text()}")
                return await resp.json()

    async def get_roominfo(self, roomid):
        api = self.ROOM_INFO_API
        async with aiohttp.ClientSession() as session:
            async with session.get(api, params={"room_ids": str(roomid), "req_biz": "web_room_componet"}) as resp:
                log.debug(
                    f"Room {roomid}\nRoomStatus {resp.status}\nInfo\n----\n{await resp.text()}")
                return await resp.json()

    def server_select(self):
        raise NotImplementedError

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

    # Event getter
    def get_active_event(self):
        if len(self.EVENT_BUFFER) > 0:
            return self.EVENT_BUFFER.pop(0)
        else:
            return None

    # Message getter.

    # def get_message(self):
    #     if len(self.MSG_BUFFER) > 0:
    #         return self.MSG_BUFFER.pop(0)
    #     else:
    #         return None

    # Set cookies. Set csrf_token at the same time.
    def set_cookie(self, cookie):
        if isinstance(cookie, str):
            self.cookie = cookie
            matches = re.findall(r"bili_jct=([0-9 abcdef]+?);", cookie)
            self.token = matches[0]
        else:
            raise TypeError("Cookie must be a string")

    # Set cookies from file.
    def set_cookie_file(self, cookie_file):
        if isinstance(cookie_file, str):
            self.cookie_file = cookie_file
        else:
            raise TypeError("Cookie file path must be a string")
        try:
            with open("cookie.txt", "r") as f:
                self.set_cookie(f.read())
        except:
            raise FileNotFoundError("Cookie file not found")

    # Send message.
    async def send(self, content):
        api = self.DANMAKU_SEND_API
        data = {
            "data": 0,
            "color": "16777215",
            "fontsize": 25,
            "mode": 1,
            "rnd": 0
        }
        data["msg"] = content
        data["csrf_token"] = self.csrf_token
        data["csrf"] = self.csrf_token
        data["roomid"] = self.real_roomid
        async with aiohttp.ClientSession(headers=self.header) as session:
            async with session.post(api, data=data) as resp:
                print(await resp.text())

    # Print handler which runs print functions that user defined.
    # Going to be discarded and merging into process handler.
    # async def print_handler(self):
    #     while True:
    #         msg = self.get_message()
    #         # log.debug(f"Printing {msg}")
    #         if msg:
    #             self.__processor_msg__(msg)
    #         await asyncio.sleep(0)
    # Event processing handler which runs event processing functions that user defined.
    async def process_handler(self):
        while True:
            event = self.get_active_event()
            if event:
                log.debug(f"Processing {event}")
                etype = event["cmd"]
                if etype in self.__processor__.keys():
                    self.__processor__[etype](event)
                else:
                    self.__processor_not_impl__(event)
            await asyncio.sleep(0)

    # Interfaces
    # Wrapper of printer
    # def printer(self, func):
    #     @functools.wraps(func)
    #     def wrapper(msg):
    #         return func(msg)
    #     self.__processor_msg__ = wrapper
    # Wrapper of processor
    def processor(self, event_name):
        def wrapper_(func):
            @functools.wraps(func)
            def wrapper(event):
                return func(event)
            # Registry user functions to different event handlers.
            if event_name == "NOT_IMPL": 
                self.__processor_not_impl__ = wrapper
            else:
                self.__processor__[event_name] = wrapper
            log.debug(f"Registered {event_name} event handler")
        return wrapper_

    # Heartbeat function

    async def heartbeat(self, ws):
        obj = "[object Object]"
        while True:
            await ws.send_bytes(
                self.header_gen(len(obj), self.OP_HEARTBEAT, self.DEFAULT_SEQ) +
                obj.encode("utf-8")
            )
            log.debug("Sent heartbeat")
            await asyncio.sleep(30)

    # Main loop
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
            ext_header_len = 0
            ext_header = b''

            if op_type == self.OP_HEARTBEAT_ACK:
                packet_type = "heartbeat"
                ext_header = payload[:4]
                payload = payload[4:]
            elif op_type == self.OP_CONN_SUCCESS:
                packet_type = "conn_success_ack"
            else:
                if cont_type == self.CONT_CMD:
                    packet_type = "command"
                elif cont_type == self.CONT_INFO:
                    payload = brotli.decompress(payload)
                    packet_type = "info"
                    messages = self.split_msg(payload)
                    payload = messages
                    for msg in messages:
                        self.EVENT_BUFFER.append(msg)
            log.debug(f"Received ({packet_type}) {recv_len} bytes\nHeader {recv_header_len} bytes:{header}\nExtHeader {ext_header_len} bytes: {ext_header}\nData {recv_len - recv_header_len - ext_header_len} bytes: {payload}")

    # Main function
    # Initializes connection and start loops.
    async def connect(self, roomid=None, server_autoselect=True):
        if roomid:
            self.roomid = roomid
        elif self.roomid is None:
            raise ValueError("Room ID not set")

        self.real_roomid = await self.get_real_roomid(self.roomid)
        self.server_info = await self.get_danmakuinfo(self.real_roomid)
        self.room_info = (await self.get_roominfo(self.real_roomid))["data"]["by_room_ids"][str(self.real_roomid)]
        self.token = self.server_info['data']['token']
        self.server_list = self.server_info['data']['host_list']
        if server_autoselect:
            self.server = self.server_list[0]
        else:
            self.server = None
        log.debug(f"Got token {self.token}")
        log.debug(f"Got server {self.server_list}")
        log.info(
            f"Entering room {self.room_info['title']}\nUser {self.room_info['uname']}\nDescription {self.room_info['description']}\nRoomID {self.roomid}\nReal RoomID {self.real_roomid}")
        async with aiohttp.ClientSession() as self.session:
            log.debug(
                f"Initialized Danmaku object for room {self.real_roomid}")
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
                    self.heartbeat(ws),
                    # self.print_handler(),
                    self.process_handler()
                ]
                await asyncio.gather(*tasks)
