'''
This file contains a simple script to setup a twitter stream listener and to
delegate an event callback every time a new tweet is received. Need
to instantiate TwitterStream on the main script to start the actual listener.
'''

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

import tweepy
import json
import asyncio
import commons

LOG_TAG = "twitter"

class TweetListener(StreamListener):

    def __init__(self, on_tweet, *args, **kwargs):

        '''
        Sets up a tweet listener as implemented by Tweepy's StreamListener.

        @param on_tweet: callback method to be executed when a new tweet is sent
        '''

        super(TweetListener, self).__init__(*args, **kwargs)
        self.on_tweet = on_tweet
        self.loop = asyncio.get_event_loop()

    def on_data(self, data):

        '''
        Called when raw data is received from connection (i.e. new tweets are sent, etc).

        @param data: a dictionary containing information about the tweet. See
            https://dev.twitter.com/overview/api/tweets for more information
        '''

        tweet = json.loads(data)
        if not tweet["retweeted"]: # filter out retweets
            self.loop.create_task(self.on_tweet(tweet)) # execute callback
            commons.log(LOG_TAG, "new tweet from " + twitter_account + ": " + tweet['text'])
            return True

    def on_error(self, status):

        '''
        Called when a non-200 status code is returned from the listener.

        @param status: status code of the error received
        '''

        commons.log(LOG_TAG, str(status))

class TwitterStream():

    def __init__(self, tokens, account, on_tweet):

        '''
        Sets up the Twitter API connection and creates a stream listener.

        @param tokens: dictionary containing the app's consumer key + secret,
            and also the associated account's access token + secret
        @param account: username of twitter account to listen to
        @param on_tweet: callback method to be executed when a new tweet is sent
        '''

        # Twitter API authentication
        auth = OAuthHandler(tokens['consumer_key'], tokens['consumer_secret'])
        auth.set_access_token(tokens['access_token'], tokens['access_token_secret'])
        api = tweepy.API(auth)
        user_id = str(api.get_user(account).id)

        global twitter_account
        twitter_account = account + " (" + user_id + ")"

        commons.log(LOG_TAG, "listening for new tweets from " + twitter_account)

        # instantiate tweet listener and start listening
        listener = TweetListener(on_tweet)
        self.stream = Stream(auth = api.auth, listener = listener)
        self.stream.filter(follow = [user_id], async = True)
