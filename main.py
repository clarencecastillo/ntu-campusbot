from telepot.aio.delegate import per_chat_id, create_open, pave_event_space, include_callback_query_chat_id
from twitter import TwitterStream
from bot import NTUCampusBot

import os
import telepot
import asyncio
import commons
import bot

LOG_TAG = "main"

TELEGRAM_TOKEN = os.environ['BOT_TOKEN']
TWITTER_FEED_ACCOUNT = "NTUsg"
TWITTER_TOKENS = {
    "consumer_key": os.environ['TWITTER_CONSUMER_KEY'],
    "consumer_secret": os.environ['TWITTER_CONSUMER_SECRET'],
    "access_token": os.environ['TWITTER_ACCESS_TOKEN'],
    "access_token_secret": os.environ['TWITTER_ACCESS_TOKEN_SECRET']
}

async def on_tweet(data):

    # increment tweet stat count
    stats = commons.get_data("stats")
    stats["tweets"] = (0 if "tweets" not in stats else int(stats["tweets"])) + 1
    commons.set_data("stats", stats)

    # send tweet to all subscribers
    tweet_message = "<b>" + data['user']['screen_name'] + "</b>: " + data['text']
    subscribers = commons.get_data("subscribers")
    commons.log(LOG_TAG, "sending tweet to " + str(len(subscribers)) + " subscribers")
    for subscriber_id in subscribers.keys():
        await bot_delegator.sendMessage(int(subscriber_id), tweet_message, parse_mode = 'HTML')

if __name__ == '__main__':

    administrators = [admin_id for admin_id in os.environ['ADMINISTRATORS'].split(",")]
    commons.set_data("admins", [int(admin_id) for admin_id in administrators])
    commons.log(LOG_TAG, "initialized administrators: " + ", ".join(administrators))

    bot.init()
    commons.log(LOG_TAG, "initialized bot")

    global bot_delegator
    bot_delegator = telepot.aio.DelegatorBot(TELEGRAM_TOKEN, [
        include_callback_query_chat_id(pave_event_space()) (
            per_chat_id(), create_open, NTUCampusBot, timeout = 10
        )
    ])

    stream = TwitterStream(TWITTER_TOKENS, TWITTER_FEED_ACCOUNT, on_tweet)
    commons.log(LOG_TAG, "initialized twitter listener")

    bot_loop = asyncio.get_event_loop()
    bot_loop.create_task(bot_delegator.message_loop())
    commons.log(LOG_TAG, "NTU_CampusBot ready!")
    commons.set_data("status", "running")
    bot_loop.run_forever()
