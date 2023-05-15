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
