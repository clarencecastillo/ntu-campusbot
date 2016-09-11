from telepot.aio.delegate import per_chat_id, create_open, pave_event_space, include_callback_query_chat_id
from twitter import TwitterStream
from bot import NTUCampusBot

import os
import telepot
import asyncio
import commons

TELEGRAM_TOKEN = os.environ['BOT_TOKEN']

TWITTER_FEED_ACCOUNT = "NTUsg"
TWITTER_TOKENS = {
    "consumer_key": os.environ['TWITTER_CONSUMER_KEY'],
    "consumer_secret": os.environ['TWITTER_CONSUMER_SECRET'],
    "access_token": os.environ['TWITTER_ACCESS_TOKEN'],
    "access_token_secret": os.environ['TWITTER_ACCESS_TOKEN_SECRET']
}

async def on_tweet(data):
    tweet_message = "<b>" + data['user']['screen_name'] + "</b>: " + data['text']
    print("New tweet from", TWITTER_FEED_ACCOUNT, "-", data['text'])
    for subscriber_id in commons.subscribers:
        await bot.sendMessage(subscriber_id, tweet_message, parse_mode = 'HTML')

if __name__ == '__main__':

    commons.init()

    global bot
    bot = telepot.aio.DelegatorBot(TELEGRAM_TOKEN, [
        include_callback_query_chat_id(pave_event_space()) (
            per_chat_id(), create_open, NTUCampusBot, timeout = 10
        )
    ])

    stream = TwitterStream(TWITTER_TOKENS, TWITTER_FEED_ACCOUNT, on_tweet)

    bot_loop = asyncio.get_event_loop()
    bot_loop.create_task(bot.message_loop())
    print('NTU_CampusBot is now listening...')
    bot_loop.run_forever()
