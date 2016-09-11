from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

import tweepy
import json
import asyncio

class TweetListener(StreamListener):

    def __init__(self, on_tweet, *args, **kwargs):
        super(TweetListener, self).__init__(*args, **kwargs)
        self.on_tweet = on_tweet
        self.loop = asyncio.get_event_loop()

    def on_data(self, data):
        self.loop.create_task(self.on_tweet(json.loads(data)))
        return True

    def on_error(self, status):
        print(status)

class TwitterStream():

    def __init__(self, tokens, account, on_tweet):

        auth = OAuthHandler(tokens['consumer_key'], tokens['consumer_secret'])
        auth.set_access_token(tokens['access_token'], tokens['access_token_secret'])

        api = tweepy.API(auth)
        user_id = str(api.get_user(account).id)
        print("Watching for new tweets from:", account)

        listener = TweetListener(on_tweet)
        self.stream = Stream(auth = api.auth, listener = listener)
        self.stream.filter(follow = [user_id], async=True)