import aiohttp
import asyncio
import json
import requests

api = "https://api.live.bilibili.com/msg/send"
header = {
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://live.bilibili.com",
    "DNT": "1",
    "Connection": "keep-alive, Upgrade",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "TE": "trailers",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

from cookie import cookie
token = cookie["bili_jct"]
cookie_str = "".join([f"{k}={v};" for k, v in cookie.items()])
msg = "开门！！"
data = {
    "data": 0,
    "msg": msg,
    "color": "16777215",
    "fontsize": 25,
    "mode": 1,
    "rnd": 0,
    "roomid": "3645373",
    "csrf": token,
    "csrf_token": token
}
header["Cookie"] = cookie_str
async def main():
    async with aiohttp.ClientSession(headers=header) as session:
        while True:
            async with session.post(api, data=data) as resp:
                print(await resp.text())
            await asyncio.sleep(5)

asyncio.run(main())
# r = requests.post(api, data=data, headers=header, cookies=cookie)
# print(r.text)
