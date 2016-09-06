from bs4 import BeautifulSoup
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import telepot
import time
import urllib.request
import os

BASE_IMAGE_URL = "https://webcam.ntu.edu.sg/upload/slider/"
NEWS_HUB_URL = "http://news.ntu.edu.sg/Pages/NewsSummary.aspx?Category=news+releases"
TOKEN = os.environ['BOT_TOKEN']
VERSION = "1.0.0"
NEWS_COUNT = 5

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
If you find a bug, or notice that NTU_CampusBot is not working, please send a bug \
report to clarencecastillo@outlook.com.</code>

<b>NOTES</b>
<code>Timestamp shown of the snapshot image may not accurately reflect the camera's \
view at the time of request. You may notice a slight desynchronization due to \
the fixed refresh rate of the cameras.</code>

To check available commands, use /help
'''

ABOUT_MESSAGE = '''
====================
<b>NTU_CampusBot</b>   v<b>%s</b>
====================

Made with %s by:
<b>%s</b>
''' % (VERSION, u'\U00002764', "\n".join(['Clarence', 'Beiyi', 'Yuxin', 'Joel', 'Qixuan']))

PEEK_MESSAGE = "Choose a location to look at:"
NEWS_LOAD_MESSAGE = "Fetching latest news. Please wait."

def on_chat_message(message):

    command = message['text'][1:]
    chat_id = message['chat']['id']

    print("Message received:", command)

    if command == "start":
        bot.sendMessage(chat_id, START_MESSAGE, parse_mode='HTML')
    elif command == "peek":
        buttons = [[InlineKeyboardButton(text = key, callback_data = key)] for key in LOCATIONS.keys()]
        keyboard = InlineKeyboardMarkup(inline_keyboard = buttons)
        bot.sendMessage(chat_id, PEEK_MESSAGE, reply_markup = keyboard)
    elif command == "news":
        bot.sendMessage(chat_id, NEWS_LOAD_MESSAGE)
        news_page = urllib.request.urlopen(NEWS_HUB_URL).read()
        soup = BeautifulSoup(news_page, "html.parser")

        next_news = soup.findAll("div", {"class": "ntu_news_summary_title_first"})[0]
        for i in range(NEWS_COUNT):
            news_title = next_news.a.string.strip().title()
            news_link = next_news.a['href']
            news_date = next_news.next_sibling.string

            news_message = "<b>%s</b>\n<a href='%s'>%s</a>" % (news_date, news_link, news_title)
            bot.sendMessage(chat_id, news_message, parse_mode='HTML')

            next_news = next_news.find_next_sibling("div", {"class": "ntu_news_summary_title"})
    elif command == "help":
        bot.sendMessage(chat_id, HELP_MESSAGE, parse_mode='HTML')
    elif command == "about":
        bot.sendMessage(chat_id, ABOUT_MESSAGE, parse_mode='HTML')

def on_callback_query(message):

    chat_id = message['message']['chat']['id']
    callback_id = message['id']
    location_name = message['data']

    cam_url = BASE_IMAGE_URL + LOCATIONS[location_name] + ".jpg?rand=" + str(time.time())
    timestamp_message = time.strftime("%a, %d %b %y") + " - <b>" + location_name + "</b>"

    bot.answerCallbackQuery(callback_id)
    bot.sendMessage(chat_id, timestamp_message, parse_mode='HTML')
    bot.sendPhoto(chat_id, cam_url)

bot = telepot.Bot(TOKEN)
bot.message_loop({
    'chat': on_chat_message,
    'callback_query': on_callback_query
})

print('NTU_CampusBot is now listening...')

while True:
    time.sleep(10)
