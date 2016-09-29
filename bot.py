'''
This file contains the codes of the actual bot, including the message templates
to be sent. Other configurable parameters are written as constants which can
easily be changed without affecting the logic of the bot.
'''

from bs4 import BeautifulSoup
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from io import BytesIO
from scipy import misc
from urllib import request
from skimage import measure

import telepot
import time
import aiohttp
import random
import asyncio
import commons
import functools

VERSION = "1.2.0"
AUTHORS = ['Clarence', 'Beiyi', 'Yuxin', 'Joel', 'Qixuan']
LOG_TAG = "bot"

REPO_URL = "https://github.com/clarencecastillo/ntu-campusbot"
CAM_BASE_IMAGE_URL = "https://webcam.ntu.edu.sg/upload/slider/"
NTU_WEBSITE = "http://www.ntu.edu.sg/"
SHUTTLE_BUS_URL = "has/Transportation/Pages/GettingAroundNTU.aspx"
NEWS_HUB_URL = "http://news.ntu.edu.sg/Pages/NewsSummary.aspx?Category=news+releases"
NEWS_COUNT = 5

HELP_MESSAGE = '''
You can control this bot by sending these commands:

/peek - get current screenshot of a location
/news - get latest news from NTU News Hub
/subscribe - subscribe to NTU's official twitter account feed
/unsubscribe - unsubscribe from NTU's official twitter account feed
/shuttle - get info about NTU internal shuttle bus routes
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

PEEK_MESSAGE = "Which location should I peek for you?"
SHUTTLE_MESSAGE = "Get info about which shuttle bus service?"
NEWS_WAIT_MESSAGE = "Fetching latest news. Please wait."
INVALID_COMMAND_MESSAGE = "Say again? I didn't quite catch that."
ALREADY_SUBSCRIBED_MESSAGE = "You are already subscribed to receive the latest tweets from NTU's official Twitter account! Wanna unsub? /unsubscribe"
NOT_SUBSCRIBED_MESSAGE = "You are not subscribed to receive the latest tweets from NTU's official Twitter account! Wanna sub? /subscribe"
SUCCESSFULLY_SUBSCRIBED = "Successfully subscribed to NTU's official Twitter account! Wanna unsub? /unsubscribe"
SUCCESSFULLY_UNSUBSCRIBED = "Successfully unsubscribed from NTU's official Twitter account! Wanna sub back? /subscribe"
MAINTENANCE_MODE_MESSAGE = "NTU_CampusBot is currently under maintenance! We apologise for any inconvenience caused. Try again later? %s" % (u'\U0001F605')

BUS_SERVICES = {}
LOCATION_PROFILES = {}
LOCATIONS = {
    "Fastfood Level, Admin Cluster": "fastfood",
    "School of Art, Design and Media": "adm",
    "Lee Wee Nam Library": "lwn-inside",
    "Quad": "quad",
    "Walkway between North and South Spines": "WalkwaybetweenNorthAndSouthSpines",
    "Canteen B": "canteenB",
    "Onestop@SAC": "onestop_sac"
}

CALLBACK_COMMAND_LOCATION = "location"
CALLBACK_COMMAND_BUS = "bus"
LOCATIONS_KEYBOARD = None
BUS_SERVICES_KEYBOARD = None

def init():

    '''
    Initializes locations and shuttle bus services keyboards. Also prepares
    profiles to be used for image comparison given the available profiles
    inside /profiles.
    '''

    global LOCATION_PROFILES
    global LOCATIONS_KEYBOARD
    global BUS_SERVICES_KEYBOARD

    # create keyboard for locations available
    LOCATIONS_KEYBOARD = InlineKeyboardMarkup(inline_keyboard = [
        [InlineKeyboardButton(text = key, callback_data = CALLBACK_COMMAND_LOCATION + ":" + key)]
        for key in LOCATIONS.keys()
    ])
    commons.log(LOG_TAG, "locations keyboard ready")

    # fetch bus services from URL
    shuttle_bus_page = request.urlopen(NTU_WEBSITE + SHUTTLE_BUS_URL).read()
    for service in BeautifulSoup(shuttle_bus_page, "html.parser").find_all("span", {"class": "route_label"}):

        service_name = service.string.strip()
        shuttle_bus_info_page = request.urlopen(NTU_WEBSITE + service.find_next_sibling("a")['href']).read()
        shuttle_bus_route = ""
        sub_routes = service.parent.find_all("strong")

        # workaround for inconsistent route layouting for campus rider service
        if len(service.parent.find_all("span")) == 2: del sub_routes[-1]

        # function to get list of bus stops given a header
        parse_bus_stops = lambda element: "\n".join([str(index + 1) + ". " + bus_stop.string for index, bus_stop in enumerate(element.find_next("ul").find_all("li"))])

        if len(sub_routes):
            # combine all sub routes (as combination of the sub route header with its list) with other sub routes
            shuttle_bus_route = "".join(["\n<b>" + sub_route.string + "</b>\n" + parse_bus_stops(sub_route) for sub_route in sub_routes])
        else :
            # just a list of bus stops without any sub route header
            shuttle_bus_route = parse_bus_stops(service)

        BUS_SERVICES[service_name] = {
            # scrape bus service image url
            "image_url": BeautifulSoup(shuttle_bus_info_page, "html.parser").find("div", {"class": "img-caption"}).img['src'],
            # bus route information
            "info": "<b>%s</b>\n\n<b>ROUTE</b>\n%s" % (service_name.upper(), shuttle_bus_route)
        }

    # create keyboard for shuttle bus services available
    BUS_SERVICES_KEYBOARD = InlineKeyboardMarkup(inline_keyboard = [
        [InlineKeyboardButton(text = key, callback_data = CALLBACK_COMMAND_BUS + ":" + key)] for key in BUS_SERVICES.keys()
    ])
    commons.log(LOG_TAG, "bus services keyboard ready")

    # profile all available locations
    for location in LOCATIONS.values():

        img_file_name = "./profiles/" + location + "_%s.jpg"
        try:

            # transforms the images to arrays to be processed by scikit
            LOCATION_PROFILES[location] = {
                "full": misc.imread(img_file_name % ("full")),
                "average": misc.imread(img_file_name % ("average")),
                "empty": misc.imread(img_file_name % ("empty"))
            }
        except Exception as e:
            commons.log(LOG_TAG, "no profile found for " + location)
    commons.log(LOG_TAG, "location profiles ready")

def _new_subscriber(id, name):

    '''
    Performs the write operation for adding a subscriber.

    @param id: stringified unique user id as provided by telegram
    @param name: string to identify the user; can be first name, username or
        group chat name
    '''

    subscribers = commons.get_data("subscribers")
    subscribers[id] = name
    commons.set_data("subscribers", subscribers)
    commons.log(LOG_TAG, "new subscriber: " + name + "[" + id + "]")

def _remove_subscriber(id):

    '''
    Performs the write operation for removing a subscriber.
    TODO: add error handling for when user is not in the list of subscribers

    @param id: stringified unique user id as provided by telegram
    '''

    subscribers = commons.get_data("subscribers")
    commons.log(LOG_TAG, "removing subscriber: " + subscribers[id] + "[" + id + "]")
    del subscribers[id]
    commons.set_data("subscribers", subscribers)

class NTUCampusBot(telepot.aio.helper.ChatHandler):

    def __init__(self, *args, **kwargs):

        '''
        Sets up an implementation of ChatHandler, a delegate to handle a chat.
        '''

        super(NTUCampusBot, self).__init__(*args, **kwargs)

    def _send_news(self, chat, future):

        '''
        Retrieve news from NTU News Hub and send to user.

        @param chat: dictionary containing information about the chat between
            bot and the user/group; see https://core.telegram.org/bots/api#chat
            for more information
        @param future: object containing results of async call to retrieve
            the page source
        '''

        soup = BeautifulSoup(future.result(), "html.parser")
        next_news = soup.find_all("div", {"class": "ntu_news_summary_title_first"})[0]
        for i in range(NEWS_COUNT):
            news_title = next_news.a.string.strip().title()
            news_link = next_news.a['href']
            news_date = next_news.next_sibling.string

            news_message = "<b>%s</b>\n<a href='%s'>%s</a>" % (news_date, news_link, news_title)
            asyncio.ensure_future(self.sender.sendMessage(news_message, parse_mode = 'HTML'))

            next_news = next_news.find_next_sibling("div", {"class": "ntu_news_summary_title"})

        future.remove_done_callback(self._send_news)
        self._log("sent " + str(NEWS_COUNT) + " news items", chat)

    def _log(self, message, chat):

        '''
        Formatted logging to include chat context.

        @param message: the message to be logged
        @param chat: dictionary containing information about the chat between
            bot and the user/group; see https://core.telegram.org/bots/api#chat
            for more information
        '''

        sender = chat['title' if 'title' in chat else ('username' if 'username' in chat else 'first_name')]
        commons.log(LOG_TAG, "[" + sender + ":" + str(chat['id']) + "] " + message)

    async def _load_url(self, url):

        '''
        Async method to load a url as text.

        @param url: string url to load
        '''

        response = await aiohttp.get(url)
        return (await response.text())

    async def _start(self, is_admin, payload = None):

        '''
        Async method to handle /start calls. Sends the current status of the
        bot if user is an admin, otherwise, sends the normal welcome message
        unless the admin passes the payload 'force'

        @param is_admin: boolean to determine if user is admin
        @param payload: optional string that follows the user's command
        '''

        if is_admin and payload != "force":
            await self.sender.sendMessage("Hi Admin!\nCurrent Status: " + commons.get_data("status"))
        else:
            await self.sender.sendMessage(START_MESSAGE, parse_mode = 'HTML', disable_web_page_preview = True)
            await self._subscribe(is_admin)

    async def _peek(self, is_admin, payload = None):

        '''
        Async method to handle /peek calls. Sends the locations keyboard for
        user to select location.

        @param is_admin: boolean to determine if user is admin
        @param payload: optional string that follows the user's command
        '''

        global LOCATIONS_KEYBOARD
        await self.sender.sendMessage(PEEK_MESSAGE, reply_markup = LOCATIONS_KEYBOARD)

    async def _help(self, is_admin, payload = None):

        '''
        Async method to handle /help calls. Sends the help message.

        @param is_admin: boolean to determine if user is admin
        @param payload: optional string that follows the user's command
        '''

        await self.sender.sendMessage(HELP_MESSAGE, parse_mode = 'HTML')

    async def _news(self, is_admin, payload = None):

        '''
        Async method to handle /news calls. Asynchronously retrieves the news
        page source and sends a configured number of most recent articles to
        the user.

        @param is_admin: boolean to determine if user is admin
        @param payload: optional string that follows the user's command
        '''

        await self.sender.sendMessage(NEWS_WAIT_MESSAGE)
        chat = await self.administrator.getChat()

        # async fetch the page source so user won't be blocked while this is in progress
        future = asyncio.ensure_future(self._load_url(NEWS_HUB_URL))
        # set this as callback once the page is ready
        future.add_done_callback(functools.partial(self._send_news, chat))

    async def _about(self, is_admin, payload = None):

        '''
        Async method to handle /about calls. Sends the about message. The
        sequence by which author names are listed and the icon used varies
        randomly every time this command is called.

        @param is_admin: boolean to determine if user is admin
        @param payload: optional string that follows the user's command
        '''

        author_names = "\n".join(random.sample(AUTHORS, len(AUTHORS)))
        random_icon = random.choice([u'\U0001F4A9', u'\U00002764', u'\U0001F340', u'\U00002753', u'\U0000270C', u'\U0001F525'])
        await self.sender.sendMessage(ABOUT_MESSAGE % (VERSION, random_icon, author_names), parse_mode = 'HTML')

    async def _subscribe(self, is_admin, payload = None):

        '''
        Async method to handle /subscribe calls. Adds user to list of
        subscribers. Returns a success message if user successfully registers
        and an error message if user fails to subscribe, that is, when user is
        already subscribed.

        @param is_admin: boolean to determine if user is admin
        @param payload: optional string that follows the user's command
        '''

        chat = await self.administrator.getChat()
        chat_id = str(chat['id'])

        if chat_id not in commons.get_data("subscribers"):
            sender = chat['title' if 'title' in chat else ('username' if 'username' in chat else 'first_name')]
            _new_subscriber(chat_id, sender)
            await self.sender.sendMessage(SUCCESSFULLY_SUBSCRIBED)
        else:
            await self.sender.sendMessage(ALREADY_SUBSCRIBED_MESSAGE)

    async def _unsubscribe(self, is_admin, payload = None):

        '''
        Async method to handle /unsubscribe calls. Removes user from list of
        subscribers. Returns a success message if user successfully unregisters
        and an error message if user fails to unsubscribe, that is, when user is
        not even subscribed.

        @param is_admin: boolean to determine if user is admin
        @param payload: optional string that follows the user's command
        '''

        chat = await self.administrator.getChat()
        chat_id = str(chat['id'])

        if chat_id in commons.get_data("subscribers"):
            _remove_subscriber(chat_id)
            await self.sender.sendMessage(SUCCESSFULLY_UNSUBSCRIBED)
        else:
            await self.sender.sendMessage(NOT_SUBSCRIBED_MESSAGE)

    async def _shuttle(self, is_admin, payload = None):

        '''
        Async method to handle /shuttle calls. Sends the shuttle bus information
        keyboard for user to select bus service.

        @param is_admin: boolean to determine if user is admin
        @param payload: optional string that follows the user's command
        '''

        global BUS_SERVICES_KEYBOARD
        await self.sender.sendMessage(SHUTTLE_MESSAGE, reply_markup = BUS_SERVICES_KEYBOARD)

    async def _broadcast(self, is_admin, payload):

        '''
        Async method to handle /broadcast calls from administrators. Sends a
        broadcasted message to all subscribers.

        @param is_admin: boolean to determine if user is admin
        @param payload: required string that follows the user's command
        '''

        if payload and is_admin:
            for subscriber_id in commons.get_data("subscribers").keys():
                await self.bot.sendMessage(int(subscriber_id), payload)
        else:
            raise ValueError("unauthorised")

    async def _stats(self, is_admin, payload = None):

        '''
        Async method to handle /stats calls from administrators. Sends a
        statistical count of the number of times commands were called and the
        number of times tweets were sent.

        @param is_admin: boolean to determine if user is admin
        @param payload: optional string that follows the user's command
        '''

        if is_admin:
            statistics = commons.get_data("stats")
            message = "NTU_CampusBot Statistics:\n" + ("=" * 25) + "\n\n"
            message += "\n".join([key + ": " + str(statistics[key]) for key in statistics.keys()])
            await self.sender.sendMessage(message)
        else:
            raise ValueError("unauthorised")

    async def _subscribers(self, is_admin, payload = None):

        '''
        Async method to handle /subscribers calls from administrators. Returns
        list of subscribers by their either their first name, username or group
        chat name.

        @param is_admin: boolean to determine if user is admin
        @param payload: optional string that follows the user's command
        '''

        if is_admin:
            subscribers = commons.get_data("subscribers")
            message = "NTU_CampusBot Subscribers:\n" + ("=" * 25) + "\n\n"
            message += "\n".join(subscribers.values())
            await self.sender.sendMessage(message)
        else:
            raise ValueError("unauthorised")

    async def _maintenance(self, is_admin, payload = None):

        '''
        Async method to handle /maintenance calls from administrators. Toggles
        maintenance mode on/off. Toggling it on disables standard users from
        using the bot. Passing 'on'/'off' as payload specifies the mode to be
        switched into.

        @param is_admin: boolean to determine if user is admin
        @param payload: optional string that follows the user's command
        '''

        if is_admin and ((payload.lower() in ["on", "off"]) if payload else True):

            flip_current = "maintenance" if commons.get_data("status") == "running" else "running"
            new_status = "maintenance" if payload == "on" else ("off" if payload == "off" else flip_current)
            commons.set_data("status", new_status)

            message = "Maintenance Mode: " + ("on" if new_status == "maintenance" else "off")
            await self.sender.sendMessage(message)

        else:
            raise ValueError("unauthorised")

    async def on_chat_message(self, message):

        '''
        Async method to delegate command calls to their respective methods.
        Ignores messages that do not start with '/'. Sends non-admins a blocking
        'maintenance mode' message when maintenance mode is on.

        @param message: dictionary containing information about the message
            received from user; see https://core.telegram.org/bots/api#message
            for more information
        '''

        if("text" not in message): return
        command, _, payload = message['text'][1:].partition(" ")
        command = command.split("@")[0]

        chat = await self.administrator.getChat()
        self._log("chat: " + message['text'], chat)
        is_admin = chat['id'] in commons.get_data("admins")

        maintenance_mode = commons.get_data("status") == "maintenance"
        if maintenance_mode and not is_admin:
            await self.sender.sendMessage(MAINTENANCE_MODE_MESSAGE)
        elif message['text'].startswith("/"):

            try:
                command_call = getattr(self, "_" + command)
                await command_call(is_admin, payload)

                # increment command stats count
                stats = commons.get_data("stats")
                stats[command] = (0 if command not in stats else int(stats[command])) + 1
                commons.set_data("stats", stats)

            except Exception as e:
                print(e)
                await self.sender.sendMessage(INVALID_COMMAND_MESSAGE)

    async def on_callback_query(self, message):

        '''
        Async method to be called when user clicks on a keyboard item.

        @param message: dictionary containing information about the message
            received from user; see https://core.telegram.org/bots/api#message
            for more information
        '''

        callback_id = message['id']
        message_payload = message['data'].split(":")
        command = message_payload[0]
        parameter = message_payload[1]

        chat = await self.administrator.getChat()
        self._log("callback - " + message['data'], chat)

        await self.bot.answerCallbackQuery(callback_id, text = 'Fetching data. Please wait.')
        image_url = ""
        response_message = ""

        # if callback was called as a result of user clicking on bus shuttle services keyboard
        if (command == CALLBACK_COMMAND_BUS):
            image_url = NTU_WEBSITE + BUS_SERVICES[parameter]["image_url"]
            response_message = BUS_SERVICES[parameter]["info"]
        else: # if callback was called as a result of user clicking on locations keyboard
            location = LOCATIONS[parameter]
            image_url = CAM_BASE_IMAGE_URL + location + ".jpg?rand=" + str(time.time())
            response_message = time.strftime("%a, %d %b %y") + " - <b>" + parameter + "</b>"

            # if location has a profile (because not all may have a profile)
            if location in LOCATION_PROFILES:

                # read the current screenshot from the URL as a file
                image_file = BytesIO(request.urlopen(image_url).read())
                image = misc.imread(image_file)

                # set default profile to average
                matching_profile = ("average", measure.compare_mse(image, LOCATION_PROFILES[location]["average"]))
                profiles = [key for key in LOCATION_PROFILES[location].keys()]
                if "average" in profiles: profiles.remove("average") # remove this from profiles to be compared with as it is already the default
                for profile in profiles:
                    # calculate the mse between the profile and the current image
                    mse = measure.compare_mse(image, LOCATION_PROFILES[location][profile])
                    # set this as the profile with most resemblance if the mse is lower than the current set
                    if mse < matching_profile[1]: matching_profile = (profile, mse)

                response_message += "\nApproximated crowd density: <b>" + matching_profile[0].upper() + "</b>"

        await self.sender.sendMessage(response_message, parse_mode='HTML')
        asyncio.ensure_future(self.sender.sendPhoto(image_url))

    async def on__idle(self, event):

        '''
        Async method to be called when user turns idle.

        @param event: string information about the event.
        '''

        chat = await self.administrator.getChat()
        self._log("session expired", chat)
        self.close()
