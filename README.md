# BIDARA : Bio-Inspired Design and Research Assistant

BIDARA is a bot that utilizes GPT-4 to answer questions.
Each question you ask will be redirected to Chat-GPT, and is part of a conversation with Chat-GPT.
To clear the conversation, and start a new one, use the clear_sys command.
There is also a system prompt that Chat-GPT can use, in which you can specify what you want Chat-GPT to act as.
In the case of the default prompt, Chat-GPT mimics a researcher that specializes in all fields of science.
Default prompt:

You are an AI research assistant and an expert in all fields of science.

- Cite peer reviewed sources for your answers.
- Reference relevant grants and NSF numbers.
- Reference relevant patents.
- First think step-by-step - describe your plan written out in great detail.

### Prompt Engineering with GPT-4

The GPT_4_Biologist_ChatBot folder contains experiments to develop suitable system/assistant prompts for the discord bot to act as an AI Scientist Researcher.

### Commands

- !help --> description of bot and commands.
- !example --> example of conversations with BIDARA.
- !system --> lists the current system prompt, if any.
- !set_default_sys --> set the system prompt to the default biomimicry prompt.
- !set_custom_sys --> set a custom system prompt.
- !clear_sys --> clear the current system prompt.
- !curr_conv --> shows your current conversation.
- !clear_conv --> clear the current conversation.

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
