# BIDARA : Bio-Inspired Design and Research Assistant

BIDARA is a bot that utilizes GPT-4 to answer questions.
Each question you ask will be redirected to Chat-GPT, and is part of a conversation with Chat-GPT.

### Prompt Engineering with GPT-4

The GPT_4_Biologist_ChatBot folder contains experiments to develop suitable system/assistant prompts for the discord bot to act as an AI Scientist Researcher.

### Commands

- !help --> description of bot and commands.

### Run Locally

1. Clone the repository
2. Put your OpenAI and Discord API keys in the .env file
3. Install the requirements
4. Run python3 bot.py

### Create a Discord Bot (to get API key)

1. Go to Discord portal online
2. Create a New Application
3. Go to Bot tab
4. Toggle SERVER MEMBERS INTENT and MESSAGE CONTENT INTENT, make sure REQUIRES OAUTH2 CODE GRANT is off
5. Reset Token to copy the API key
6. Then go to OAuth2 --> URL Generator
7. Toggle Bot and choose permissions
8. Paste the generated url in the browser
9. Add the bot to your desired server

### Run on AWS

1. Clone the repository
2. Input the API keys
3. Go to AWS console
4. Deploy an EC2 instance, and stop it
5. Create an image from that EC2 instance
6. Go to Cloud Formation
7. Create Stack
8. Add the yaml file
9. Input a key pair and the image id
10. Deploy and check discord

### Update Bot on AWS

1. Login to AWS console
2. switch to us-east-2
3. type EC2 in the search bar and enter. Click on Instances(running) option. Select the instance ID for BIDARA.
4. Choose 'Connect'.
5. Connect to BIDARA EC2 instance using session manager
6. Run these commands in the terminal to stop the discord bot, pull changes from github, and restart the bot.
```
sudo su
screen -r discord
CTRL-C
git pull
python3.8 bot.py
```
