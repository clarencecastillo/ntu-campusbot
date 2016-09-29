# ntu-campusbot

A telegram bot to fetch the latest NTU Hub News and to get live screenshots of campus locations. The bot is currently hosted on Heroku and can be accessed via this [link](http://telegram.me/NTU_CampusBot).

## Latest Release
NTU_CampusBot v1.2.0

##### Release Notes
- Crowd density using MSE image comparison
- Subscribers are now returned as list of usernames, first names or group chat names
- Bug fixes

## Required Dependencies
 - [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/)
 - [Telepot](https://github.com/nickoala/telepot)
 - [Tweepy](https://github.com/tweepy/tweepy)
 - [scikit-image](http://scikit-image.org/)
 - [SciPy](https://www.scipy.org/)

## Development
You'll need the Heroku CLI if you want to host this bot. For more information on how to install it, check out their [docs](https://devcenter.heroku.com/articles/heroku-command-line).

#### Local Environment Setup
```bash
# install virtualenv
$ pip install virtualenv

# create a VE
$ virtualenv venv

# enter the VE
$ venv\Scripts\activate # if you're using Windows OR
$ source venv/bin/activate # if you're not using Windows

# install the dependencies
$ pip install -r requirements.txt

# run the bot
$ heroku local
```

Create a `.env` file so you don't have to hardcode these into the codes directly. See the template below on how to create it (note that the number of X's do not reflect the actual character count of these items).
```
ADMINISTRATORS=XXXX,XXXX,XXXX
BOT_TOKEN=XXXXXXXXXXXXXXXXXXXXXXXXXXXX
TWITTER_ACCESS_TOKEN=XXXXXXXXXXXXXXXXXXXXXXXXXXXX
TWITTER_ACCESS_TOKEN_SECRET=XXXXXXXXXXXXXXXXXXXXXXXXXXXX
TWITTER_CONSUMER_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXX
TWITTER_CONSUMER_SECRET=XXXXXXXXXXXXXXXXXXXXXXXXXXXX

```

#### Heroku Deployment
The required dependencies are already inside the `requirements.txt` and `Procfile` has already been setup to activate a worker. You'll need to create your own heroku app and push this project there to get it up and running. 

Don't forget to set the concurrency level for a worker to 1 via Heroku CLI.
```bash
$ heroku ps:scale worker=1
```

## Usage

#### Standard User Commands

| Commands | Description |
| -------- | ----------- |
| **/start** | Returns the welcome message, including disclaimer and other info. |
| **/peek** | Returns a keyboard of available locations. Clicking on an item will return the current screenshot of the area, and if available, along with the current crowd density. |
| **/help** | Returns a list of available commands. |
| **/news** | Returns **5** news items from [NTU News Hub](). |
| **/about** | Returns information about the bot, including version and authors. |
| **/subscribe** | Registers user to receive tweets from [NTUsg](https://twitter.com/NTUsg?ref_src=twsrc%5Egoogle%7Ctwcamp%5Eserp%7Ctwgr%5Eauthor). |
| **/unsubscribe** | Unregisters user to stop receiving tweets. Will return an error message if user is not subscribed. |
| **/shuttle** | Returns a keyboard of available [internal shuttle bus services around NTU](http://www.ntu.edu.sg/has/Transportation/Pages/GettingAroundNTU.aspx). Clicking on an item will return a snapshot of the route, along with a list of stops. |

#### Admin Commands

| Commands | Description |
| -------- | ----------- |
| **/start** | Returns the current status of the bot. Pass the optional parameter *force* to receive the standard **/start** message. |
| **/broadcast** | Broadcasts a text message to all subscribers. Requires the message. |
| **/stats** | Returns statistics about the bot including the total number of times each command has been called and the number of times tweets have been sent out. Command will be omitted from the list if it has never been called before. |
| **/subscribers** | Returns a list of subscribed user ID's or group chat ID's. Will be changed to include the username/group chat name/first name on the next release. |
| **/maintenance** | Toggles maintenance mode on/off. Setting maintenance mode on disables standard users from using the bot. Pass the optional paramter *on* OR *off* to specify the mode. |

## Known Issues

1. `Conflict: terminated by other long poll or webhook error`

   Check that there is no other instance of the bot is running elsewhere.
2. Bot seems unresponsive when fetching **/news**?

   NTU Hub News page responds slowly, so you might need to wait a little longer for your news to arrive.
