from bs4 import BeautifulSoup
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

import telepot
import time
import aiohttp
import random
import asyncio
import commons

VERSION = "1.0.0"
AUTHORS = ['Clarence', 'Beiyi', 'Yuxin', 'Joel', 'Qixuan']

REPO_URL = "https://github.com/clarencecastillo/ntu-campusbot"
CAM_BASE_IMAGE_URL = "https://webcam.ntu.edu.sg/upload/slider/"
NEWS_HUB_URL = "http://news.ntu.edu.sg/Pages/NewsSummary.aspx?Category=news+releases"
NEWS_COUNT = 5
NEWS_TIMEOUT = 60

LOCATIONS = {
    "Fastfood Level, Admin Cluster": "fastfood",
    "School of Art, Design and Media": "adm",
    "Lee Wee Nam Library": "lwn-inside",
    "Quad": "quad",
    "Walkway between North and South Spines": "WalkwaybetweenNorthAndSouthSpines",
    "Canteen B": "canteenB",
    "Onestop@SAC": "onestop_sac"
}

HELP_MESSAGE = '''
You can control this bot by sending these commands:

/peek - get current screenshot of a location
/news - get latest news from NTU News Hub
/about - get info about this bot
'''

START_MESSAGE = '''
Thank you for using <b>NTU_CampusBot</b>!

I can help you fetch the latest news from NTU News Hub and also check for crowded \
areas around the campus so you can effectively plan your stay.

<b>DISCLAIMER</b>
<code>This bot is for informational purposes only. Use of NTU surveillance is \
governed by the university and may be subject to change without prior notice. \
If you find a bug, or notice that NTU_CampusBot is not working, please file a \
New Issue on Github.</code> [<a href='%s'>link</a>]

<b>NOTES</b>
<code>Timestamp shown of the snapshot image may not accurately reflect the camera's \
view at the time of request. You may notice a slight desynchronization due to \
the fixed refresh rate of the cameras.</code>

To check available commands, use /help
''' % (REPO_URL)

ABOUT_MESSAGE = '''
====================
<b>NTU_CampusBot</b>   v<b>%s</b>
====================

Made with %s by:
<b>%s</b>
'''

PEEK_MESSAGE = "Choose a location to look at:"
NEWS_WAIT_MESSAGE = "Fetching latest news. Please wait."
INVALID_COMMAND_MESSAGE = "Say again? I didn't quite catch that."
ALREADY_SUBSCRIBED_MESSAGE = "You are already subscribed to receive the latest tweets from NTU's official Twitter account! Wanna unsub? /unsubscribe"
NOT_SUBSCRIBED_MESSAGE = "You are not subscribed to receive the latest tweets from NTU's official Twitter account! Wanna sub? /subscribe"
SUCCESSFULLY_SUBSCRIBED = "Successfully subscribed to NTU's official Twitter account! Wanna unsub? /unsubscribe"
SUCCESSFULLY_UNSUBSCRIBED = "Successfully unsubscribed from NTU's official Twitter account! Wanna sub back? /subscribe"

class NTUCampusBot(telepot.aio.helper.ChatHandler):

    def __init__(self, *args, **kwargs):

        super(NTUCampusBot, self).__init__(*args, **kwargs)
        self._locations_keyboard = InlineKeyboardMarkup(inline_keyboard = [
            [InlineKeyboardButton(text = key, callback_data = key)] for key in LOCATIONS.keys()
        ])

    def _send_news(self, future):

        soup = BeautifulSoup(future.result(), "html.parser")
        next_news = soup.findAll("div", {"class": "ntu_news_summary_title_first"})[0]
        for i in range(NEWS_COUNT):
            news_title = next_news.a.string.strip().title()
            news_link = next_news.a['href']
            news_date = next_news.next_sibling.string

            news_message = "<b>%s</b>\n<a href='%s'>%s</a>" % (news_date, news_link, news_title)
            asyncio.ensure_future(self.sender.sendMessage(news_message, parse_mode = 'HTML'))

            next_news = next_news.find_next_sibling("div", {"class": "ntu_news_summary_title"})

        future.remove_done_callback(self._send_news)

    async def _load_url(self, url, timeout):
        response = await aiohttp.get(url)
        return (await response.text())

    async def _start(self):
        await self.sender.sendMessage(START_MESSAGE, parse_mode = 'HTML', disable_web_page_preview = True)
        await self._subscribe()

    async def _peek(self):
        await self.sender.sendMessage(PEEK_MESSAGE, reply_markup = self._locations_keyboard)

    async def _help(self):
        await self.sender.sendMessage(HELP_MESSAGE, parse_mode = 'HTML')

    async def _fetch_news(self):
        await self.sender.sendMessage(NEWS_WAIT_MESSAGE)

        future = asyncio.ensure_future(self._load_url(NEWS_HUB_URL, NEWS_TIMEOUT))
        future.add_done_callback(self._send_news)

    async def _about(self):

        author_names = "\n".join(random.sample(AUTHORS, len(AUTHORS)))
        heart_icon = u'\U00002764'
        await self.sender.sendMessage(ABOUT_MESSAGE % (VERSION, heart_icon, author_names), parse_mode = 'HTML')

    async def _subscribe(self):

        chat = await self.administrator.getChat()
        chat_id = chat['id']

        if chat_id not in commons.subscribers:
            commons.new_subscriber(chat_id, chat['title' if 'title' in chat else 'username'])
            await self.sender.sendMessage(SUCCESSFULLY_SUBSCRIBED)
        else:
            await self.sender.sendMessage(ALREADY_SUBSCRIBED_MESSAGE)

    async def _unsubscribe(self):

        chat = await self.administrator.getChat()
        chat_id = chat['id']

        if chat_id in commons.subscribers:
            commons.remove_subscriber(chat_id, chat['title' if 'title' in chat else 'username'])
            await self.sender.sendMessage(SUCCESSFULLY_UNSUBSCRIBED)
        else:
            await self.sender.sendMessage(NOT_SUBSCRIBED_MESSAGE)

    async def on_chat_message(self, message):

        command = message['text'][1:]
        chat = message['chat']
        sender = chat['title' if 'title' in chat else 'username']
        print("Message received from:", sender, "-", message['text'])

        if command.startswith("start"):
            await self._start()
        elif command.startswith("peek"):
            await self._peek()
        elif command.startswith("news"):
            await self._fetch_news()
        elif command.startswith("help"):
            await self._help()
        elif command.startswith("about"):
            await self._about()
        elif command.startswith("subscribe"):
            await self._subscribe()
        elif command.startswith("unsubscribe"):
            await self._unsubscribe()
        elif message['text'].startswith("/"):
            await self.sender.sendMessage(INVALID_COMMAND_MESSAGE)

    async def on_callback_query(self, message):

        callback_id = message['id']
        location_name = message['data']

        await self.bot.answerCallbackQuery(callback_id, text = 'Fetching image. Please wait.')
        cam_url = CAM_BASE_IMAGE_URL + LOCATIONS[location_name] + ".jpg?rand=" + str(time.time())
        timestamp_message = time.strftime("%a, %d %b %y") + " - <b>" + location_name + "</b>"
        await self.sender.sendMessage(timestamp_message, parse_mode='HTML')
        asyncio.ensure_future(self.sender.sendPhoto(cam_url))

    async def on__idle(self, event):
        chat = await self.administrator.getChat()
        print("Closing chat:", chat['title' if 'title' in chat else 'username'])
        self.close()
