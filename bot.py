"""
MIT License

Copyright (c) 2022 boobfuck

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from pyrogram import Client, filters

import re
import asyncio
import aiohttp
from urllib.parse import quote

from . import config


# --- Initialize Client --- #
class JavInfoClient(Client):
    async def start(self):
        await super().start()
        self.me = await self.get_me()

bot = JavInfoClient(
    'javinfo',
    api_id = config.api_id,
    api_hash = config.api_hash,
    bot_token = config.bot_token
)
# --- #


# --- Helper Funtions --- #
async def get_html(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise Exception(f'Service responded with status code {resp.status}')
            
            html = await resp.text()
            return html

def parse(regex: re.Pattern, html: str):
    return (re.search(regex, html))
# --- #


# --- VARS --- #
P = filters.private

MAIN_URL_RE = re.compile(r'href="(?P<url>https://www.javdatabase.com/movies/\S.*?)/"')
TITLE_RE   = re.compile(r'<td class="tablevalue">(?P<title>\S.+?)</td>')
STUDIO_RE  = re.compile(r'href="https://www.javdatabase.com/studios/(?P<studio>\S+?)/')
DVD_RE     = re.compile(r'DVD ID:.*?"tablevalue">(?P<dvd>\S+?)</td>', flags=re.DOTALL)
DATE_RE    = re.compile(r'Release Date.+?">(?P<date>\S+)</', flags=re.DOTALL)
RUNTIME_RE = re.compile(r'Runtime.+?">(?P<runtime>\S.+?)<', flags=re.DOTALL)
TRAILER_RE = re.compile(r"<source data-fluid-hd src='(?P<trailer>\S.+?)'", flags=re.DOTALL)
POSTER_RE  = re.compile(r"posterImage: '(?P<poster>\S.+?)'")
# --- #


@bot.on_message(filters.command('start') & P)
async def start(bot, ctx):
    msg = f"""
Hi @{ctx.from_user.username}!

Send me a JAV movie ID and I will give you some information about it.

Try sending `pppd-964` to test.

If the bot doesn't work, wait for it to get fixed.
"""
    await ctx.reply(msg)

@bot.on_message(P)
async def main(bot, ctx):
    if ctx.from_user.id == bot.me.id:
        return
    if ctx.from_user.username == bot.me.username:
        return

    uinput = quote(ctx.text)
    try:
        init_html = await get_html(f'https://www.javdatabase.com/?s={uinput}')
    except Exception as e:
        return await ctx.reply(f'{e}. Please try again later.')

    pw = await ctx.reply('Please wait...')

    try:
        murl = parse(MAIN_URL_RE, init_html).group(1)
    except AttributeError as e:
        print(e)
        await ctx.reply(f'Could not fetch information. Make sure you enter the proper movie ID.\n\nErr:\n{e}')

    html = await get_html(murl)
    info = {}
    
    title, studio, dvd, date, runtime, trailer, poster = parse(TITLE_RE, html), parse(STUDIO_RE, html), parse(DVD_RE, html), parse(DATE_RE, html), parse(RUNTIME_RE, html), parse(TRAILER_RE, html), parse(POSTER_RE, html)

    if title is not None:
        info['title']   = title.group(1)
    if studio is not None:
        info['studio']  = studio.group(1)
    if dvd is not None:
        info['dvd']     = dvd.group(1)
    if date is not None:
        info['date']    = date.group(1)
    if runtime is not None:
        info['runtime'] = runtime.group(1)
    if trailer is not None:
        info['trailer'] = trailer.group(1)
    if poster is not None:
        info['poster']  = poster.group(1)

    await pw.delete()

    msg = f"""
Title: {info.get('title', None)}
Studio: {info.get('studio', None)}
DVD ID: {info.get('dvd', None)}
Release Date: {info.get('date', None)}
Runtime: {info.get('runtime', None)}
Trailer: {info.get('trailer', None)}
"""
    poster = info.get('poster', None)
    if poster is not None:
        final_msg = await ctx.reply_photo(poster, caption=msg)
    else:
        final_msg = await ctx.reply(msg)
    
    await asyncio.sleep(60)
    return (await final_msg.delete())

print('JavInfoBot starting...')
bot.run()

