# Bilibili Danmaku Resolver Python

A python library for resolving Bilibili Danmaku with Flask-style API. 

一个提供Flask-style API的Bilibili直播弹幕协议解析器。
[简体中文](https://github.com/MerlynAllen/bilibili_danmaku/blob/master/README_zh-CN.md/)
[English](https://github.com/MerlynAllen/bilibili_danmaku/blob/master/README.md/)

## Installation

### Git Clone

```sh
git clone https://github.com/MerlynAllen/bilibili_danmaku.git
cd bilibili_danmaku
pip3 install -r requirements.txt
```

Then copy `livedanmaku` directory into your working directory.

### Pip

```sh
pip3 install livedanmaku
```



## Requirements

Python Version >= 3.6  
Libraries: `aiohttp` `brotli` `aioconsole`

## Usage

### APIs at a glance

A sample client will look like this:

```python
#! /usr/bin/python3
from livedanmaku import danmaku
import logging as log


# LOGLEVEL = log.DEBUG
# log.basicConfig(
#     level=LOGLEVEL, format="[%(asctime)s (%(levelname)s) line %(lineno)d in %(funcName)s]\n%(message)s\n----")

client = danmaku.Danmaku()
client.set_cookie_file("cookie.txt")

@client.processor("DANMU_MSG")
def print_msg(msg):
    username = msg["info"][2][1]
    content = msg["info"][1]
    print(f"\033[2K\r[\x1b[34m{username}\x1b[39m]: {content}")
    if content == "Hello":
        client.send(f"@{username} hello!")
    # os.system(f"notify-send '[{username}]said:' '{content}' --app-name='Bilibili Danmaku Room {client.roomid}' -t 3000") 

@client.processor("INTERACT_WORD")
def process_interact_word(event):
    username = event["data"]["uname"]
    print(f"\033[2K\r{username} entered live room", end="")
    client.send(f"@{username} welcome to live room!")

@client.processor("NO_IMPL")
def process_no_impl(event):
    # write not implemeted type of data to log files.
    pass
try:
    client.connect(12345)
    #do some thing
    client.wait()
except KeyboardInterrupt:
    print("\rBye!")
    exit(0)
```

### Initializing

Import and create `Danmaku` object

```python
from livedanmaku import danmaku
client = danmaku.Danmaku(
	# roomid = None,
    # ua = None, 
    # cookie = None,
    # stdin = None
)
```

All parameters can be left unset. `cookie` and `roomid` can be set later by other functions. Default `ua` is  `User-Agent` of Firefox 96.0 on Linux (64-bits).

```python
client.set_cookie("xxxxxxx")
client.set_cookie_file("cookie.txt")
```

Reads cookie from either string or file.

### APIs

It provides a function decorator `processor` for user to implement. 

```python
@danmakuobject.processor(msg_type_name)
def func_name(event):
    pass
```



Bilibili live room danmaku transfers different types of messages distinguished by values of key `cmd` in json data. The decorator does not process json data, but simply passes original `json.loads` loaded dict object to function for user to implement aiming to preserve more data details. 

Sample dict data `event`

```json
{"cmd": "DANMU_MSG", "info": [[0, 1, 25, 16777215, 1642377825835, 0, 0, "c9f269af", 0, 0, 0, "", 0, "{}", "{}", {"mode": 0, "show_player_type": 0, "extra": "{'send_from_me':false,'mode':0,'color':16777215,'dm_type':0,'font_size':25,'player_mode':1,'show_player_type':0,'content':'didi','user_hash':'xxxx','emoticon_unique':'','direction':0,'pk_direction':0,'space_type':'','space_url':''}"}], "didi", [34571330, "xxxx", 0, 0, 0, 10000, 1, ""], [], [2, 0, 9868950, ">50000", 1], ["", ""], 0, 0, "None", {"ts": 1642377825, "ct": "1D32642E"}, 0, 0, "None", "None", 0, 210]}
```

`msg_type_name` specifies the implementation function when meets the value of key `cmd` in dict `event`.

### No Implemetation (I don't want to filter them!)

Unimplemented types of message will raise `NotImplemetedError`. Redirect them to `NO_IMPL`.

```python
@client.processor("NO_IMPL")
def func(e):
    # Write to logfile
    pass
```

### Connecting

Simply

```python
client.connect(roomid)
# do some thing
client.wait()
```

~~NOTICE: THIS WILL **BLOCK THE THREAD**!~~

~~Please use `multitasking` if needed.~~  
Now this method will no longer be blocking anymore(`>=0.0.4`). Asynchronous code will run in a seperate thread.

### Sending Danmaku

```
client.send(string_message)
```

Can be used in processor functions.

Standard input stream is read as manual input or file input and automatically send from `stdin`.(Asynchronous IO)

### Enabling Logging

```python
import logging as log
LOGLEVEL = log.DEBUG
log.basicConfig(level=LOGLEVEL, format="[%(asctime)s (%(levelname)s) line %(lineno)d in %(funcName)s]\n%(message)s\n----")
```
