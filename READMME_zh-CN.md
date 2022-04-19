# Bilibili Danmaku Resolver Python

A python library for resolving Bilibili Danmaku with Flask-style API. 

一个提供Flask-style API的Bilibili直播弹幕协议解析器。
[简体中文](https://github.com/MerlynAllen/bilibili_danmaku/blob/master/README_zh-CN.md/)
[English](https://github.com/MerlynAllen/bilibili_danmaku/blob/master/README.md/)

## 安装

### Git Clone

```sh
git clone https://github.com/MerlynAllen/bilibili_danmaku.git
cd bilibili_danmaku
pip3 install -r requirements.txt
```

然后将`livedanmaku`目录复制到工作目录中。

### Pip

```sh
pip3 install livedanmaku
```



## 依赖

Python 版本 >= 3.6  
Python库: `aiohttp` `brotli` `aioconsole`

## Usage

### 示例

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

### 创建对象

导入 `Danmaku` object

```python
from livedanmaku import danmaku
client = danmaku.Danmaku(
	# roomid = None,
    # ua = None, 
    # cookie = None,
    # stdin = None
)
```

参数都可以为空。默认值会自动填充。 `cookie` 和 `roomid` 可以在稍后设置。 默认的 `ua` 使用 Firefox 96.0 on Linux (64-bits)的User-Agent。

```python
client.set_cookie("xxxxxxx")
client.set_cookie_file("cookie.txt")
```

可以从字符串或者文件中读取cookie。

### API

提供了函数装饰器 `processor`以便用户实现。

```python
@danmakuobject.processor(msg_type_name)
def func_name(event):
    pass
```



哔哩哔哩直播间弹幕通过json数据中键 `cmd` 的值来区分传输不同类型的消息。装饰器不处理json数据，只是将原始 `json.loads` 加载的 dict 对象传递给函数，供用户实现，旨在保留更多数据细节。

示例 `event`字典值

```json
{"cmd": "DANMU_MSG", "info": [[0, 1, 25, 16777215, 1642377825835, 0, 0, "c9f269af", 0, 0, 0, "", 0, "{}", "{}", {"mode": 0, "show_player_type": 0, "extra": "{'send_from_me':false,'mode':0,'color':16777215,'dm_type':0,'font_size':25,'player_mode':1,'show_player_type':0,'content':'didi','user_hash':'xxxx','emoticon_unique':'','direction':0,'pk_direction':0,'space_type':'','space_url':''}"}], "didi", [34571330, "xxxx", 0, 0, 0, 10000, 1, ""], [], [2, 0, 9868950, ">50000", 1], ["", ""], 0, 0, "None", {"ts": 1642377825, "ct": "1D32642E"}, 0, 0, "None", "None", 0, 210]}
```

`msg_type_name` 指定了字典`cmd`键所对应的值。装饰器将会把函数注册为对应键值对应的处理函数。当遇到指定的`cmd`值时将会调用该方法。
典型的消息类型在`Danmaku.TYPICAL_EVENTS`中定义。

### 不对消息分流

未实现处理函数的消息类型将会默认raise一个`NotImplementedError`.  
`NO_IMPL`是为这种情况设计的内置消息类型。当实现该类型消息时，所有未实现的消息类型都会重定向到此函数中（即定义默认行为）。可以只实现该类型以对所有消息均不分流。也可以在此处添加logging记录未实现的类型消息，方便后期改添加函数。

```python
@client.processor("NO_IMPL")
def func(e):
    # Write to logfile
    pass
```

### 连接

只需要

```python
client.connect(roomid)
# do some thing
client.wait()
```

~~注: 这将**阻塞线程**!~~

~~如果不想被`connect()`阻塞，请使用`threading`模块~~  
现在该方法不再会阻塞线程了(`>=0.0.4`).  
会使用独立的线程调用异步代码。

### 发送弹幕

```
client.send(string_message)
```

可以在任何位置调用。包括处理器函数中。此方法将会把消息送进缓冲区，等待消息发送协程发送。消息发送协程的发送间歇为`3s`。可以在`Danmaku.send_delay`中修改。

标准输入流可以作为手动输入的消息的源（异步IO）。如果设置`stdin`为`None`将会禁用这一行为。

### 开启日志

```python
import logging as log
LOGLEVEL = log.DEBUG
log.basicConfig(level=LOGLEVEL, format="[%(asctime)s (%(levelname)s) line %(lineno)d in %(funcName)s]\n%(message)s\n----")
```
