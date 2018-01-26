
Installation and Usage
=============

### 1. Got A Line Bot API devloper account

[Make sure you already registered](https://business.line.me/zh-hant/services/bot), if you need use Line Bot.

### 2. Just Deploy the same on Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

Remember your heroku, ID.

<br><br>

### 3. Go to Line Bot Dashboard, setup basic API

Setup your basic account information. Here is some info you will need to know.

- `Callback URL`: https://{YOUR_HEROKU_SERVER_ID}.herokuapp.com/callback

You will get following info, need fill back to Heroku.

- Channel Secret
- Channel Access Token

### 4. Back to Heroku again to setup environment variables

- Go to dashboard
- Go to "Setting"
- Go to "Config Variables", add following variables:
	- "ChannelSecret"
	- "ChannelAccessToken"

It all done.	


