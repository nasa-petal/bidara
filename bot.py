import os
import discord
import openai
from decouple import config
import re
import functools
import typing
import asyncio


DISCORD_TOKEN = config('DISCORD_TOKEN')
OPEN_API_KEY = config('OPENAI_API_KEY')
openai.api_key = OPEN_API_KEY

intents = discord.Intents.default()
# intents.messages = True

# turn off messages from guilds, so you only get messages from DM channels
# intents.guild_messages = False
intents.message_content = True


class ChatBot(discord.Client):

    def __init__(self, intents):
        super().__init__(intents=intents)
        self.system_prompt_dict = {}
        self.conversations = {}
        self.default_sys = ("You are BIDARA, Bio-Inspired Design and Research Assistant, and an expert in all fields of science.\n"
                            " - Cite peer reviewed sources for your answers.\n"
                            " - Reference relevant grants and NSF numbers.\n"
                            " - Reference relevant patents.\n"
                            " - First think step-by-step - describe your plan written out in great detail.")

        # TODO
        # !examples
        self.instructions = "".join(["Welcome to BIDARA, which stands for Bio-Inspired Design and Research Assistant.\n",
                                     "BIDARA is a bot that utilizes GPT-4 to answer questions. Each question you ask will be redirected to Chat-GPT, and is part of a conversation with Chat-GPT.\n",
                                     "To clear the conversation, and start a new one, use the clear_sys command.\n",
                                     "There is also a system prompt that Chat-GPT can use, in which you can specify what you want Chat-GPT to act as. For example, a biology researcher.\n\n"
                                     "**Do not share any sensitive information** in your conversations including but not limited to, personal information, ITAR, CUI, export controlled, or trade secrets.\n"
                                     "While OpenAI has safeguards in place, the chatbot may occasionally generate incorrect or misleading information and produce offensive or biased content.\n"
                                     "The chatbot may produce inaccurate information about people, places, or facts. It is not intended to give advice. Conversations may be reviewed by OpenAI's AI trainers to improve their systems.\n\n"
                                     "Here are the in-built commands:\n",
                                     "`!help` - description of bot and commands.\n",
                                     "`!examples` - examples of conversations with BIDARA.\n"
                                     "`!system` - lists the current system prompt, if any.\n",
                                     "`!set_default_sys` - set the system prompt to the default biomimicry prompt.\n"
                                     "`!set_custom_sys` - set a custom system prompt.\n"
                                     "`!clear_sys` - clear the current system prompt.\n",
                                     "`!curr_conv` - shows your current conversation.\n"
                                     "`!clear_conv` - clear the current conversation.\n",
                                     "\n\n"])

        self.example = "".join(["system: "+self.default_sys + "\n\n",
                                "user: Tell me what is biomimicry in one sentence.\n\n",
                                "assistant: Biomimicry is an interdisciplinary approach to innovation that seeks sustainable solutions to human challenges by emulating nature's time-tested patterns and strategies, often leading to more efficient and sustainable designs (Benyus, J. M. (1997). Biomimicry: Innovation Inspired by Nature. William Morrow & Co.).\n\n",
                                "user: Tell me the names of animals that could inspire the design of a biomimetic car.\n\n",
                                "assistant:\n",
                                "1. Cheetah - known for its speed and agility, could inspire a car with a streamlined design and efficient acceleration.\n",
                                "2. Shark - its hydrodynamic shape and skin texture could inspire a car with reduced drag and improved aerodynamics\n",
                                "3. Box fish - its unique exoskeleton and body shape could inspire a car with a strong, lightweight frame and efficient fuel consumption.\n",
                                "4. Falcon - known for its speed and precision in flight, could inspire a car with excellent handling and maneuverability.\n",
                                "5. Gecko - its adhesive feet could inspire a car with advanced traction and grip on various surfaces.\n",
                                "6. Tortoise - its protective shell could inspire a car with enhanced safety features and a durable exterior.\n",
                                "7. Electric eel - its ability to generate electricity could inspire a car with innovative energy generation and storage systems.\n",
                                "8. Kangaroo - its powerful legs and efficient movement could inspire a car with advanced suspension and energy recovery systems.\n",
                                "9. Hummingbird - its hovering and rapid directional changes could inspire a car with advanced maneuverability and stability control systems.\n"
                                "10. Spider - its lightweight and strong silk could inspire a car with advanced materials for weight reduction and structural strength.\n"])
        self.custom_sys = False

    async def on_ready(self):
        print(f'{self.user} is connected to Discord')

    def get_chatgpt_messages(self, input_content, author):
        messages = self.conversations[author]

        if author in self.system_prompt_dict:
            sys_prompt = {'role': 'system',
                          'content': self.system_prompt_dict[author]}
        else:
            sys_prompt = {'role': 'system', 'content': ""}

        if messages == []:
            messages.append(sys_prompt)
        else:
            messages[0] = sys_prompt

        messages.append(
            {'role': 'user', 'content': input_content})

        self.conversations[author] = messages

    async def send_chunks(self, assistant_response, chunk_length, message):
        chunks = [assistant_response[i:i+chunk_length]
                  for i in range(0, len(assistant_response), chunk_length)]
        for chunk in chunks:
            await message.channel.send(chunk)

    def to_thread(func: typing.Callable) -> typing.Coroutine:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            loop = asyncio.get_event_loop()
            wrapped = functools.partial(func, *args, **kwargs)
            return await loop.run_in_executor(None, wrapped)
        return wrapper

    @to_thread
    def call_openai(self, messages):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0,
        )
        return response

    async def process_system_prompt(self, message):
        if message.author not in self.system_prompt_dict:
            self.system_prompt_dict[message.author] = ""

            await message.channel.send("It seems you haven't set a system prompt yet for ChatGPT.\nWould you like to set a custom one or use the default?\nThe default prompt is:\n")

            await message.channel.send(">>> " + self.default_sys)
            await message.channel.send("Please type `!set_custom_sys` or `!set_default_sys` to choose.")
        else:
            await message.channel.send((f"This is the current system prompt:\n>>> {self.system_prompt_dict[message.author]}"))

    async def set_system_prompt(self, prompt_choice, message):
        if prompt_choice == "default":
            self.system_prompt_dict[message.author] = self.default_sys
            await message.channel.send(f"The system prompt is set to:\n>>> {self.default_sys}\n\n")
            await message.channel.send("If you would like to change or clear it, type `!set_custom_sys` or `!clear_sys`, respectively.")
        elif prompt_choice == "custom":
            self.custom_sys = True

            def check(m):
                return m.content != "" and m.channel == message.channel

            await message.channel.send("Please type the system prompt you would like to use.")

            try:
                msg = await self.wait_for('message', timeout=200.0, check=check)
            except asyncio.TimeoutError:
                await message.channel.send("No system prompt was set.")
                return

            self.system_prompt_dict[message.author] = msg.content
            await message.channel.send(f"The system prompt is set to:\n>>> {msg.content}")

    async def list_conv(self, message):
        curr_conversation = self.conversations[message.author]
        if curr_conversation == []:
            await message.channel.send("No conversation currently.")

        for i in curr_conversation:
            content = i["content"]
            role = i["role"]
            if role == "system" and content == "":
                content = "No system prompt set"
            await message.channel.send(role + ": " + content)

    async def process_keyword(self, keyword, message):
        if keyword == "help":
            await message.channel.send(self.instructions)
        elif keyword == "system":
            await self.process_system_prompt(message)
        elif keyword[-3:] == "sys" and keyword[:3] == "set":
            prompt_choice = keyword.split("_")[1]
            await self.set_system_prompt(prompt_choice, message)
        elif keyword == "clear_sys":
            if message.author in self.system_prompt_dict:
                self.system_prompt_dict[message.author] = ""
                await message.channel.send("The system prompt for Chat-GPT is cleared.")
        elif keyword == "curr_conv":
            await self.list_conv(message)
        elif keyword == "clear_conv":
            if message.author in self.conversations:
                self.system_prompt_dict[message.author] = ""
                self.conversations[message.author] = []
                await message.channel.send("Your previous conversation is cleared.")
        elif keyword == "example":
            await message.channel.send(self.example)
        else:
            await message.channel.send("Not a valid commmand.")

    async def on_message(self, message):
        # Check if a message is a DM
        # if isinstance(message.channel, discord.channel.DMChannel):

        if message.author == self.user:
            return

        input_content = message.content

        if message.author not in self.conversations:
            self.conversations[message.author] = []

        if input_content[0] == "!":
            await self.process_keyword(input_content[1:], message)
            return
        elif self.custom_sys == True:
            self.custom_sys = False
            return

        self.get_chatgpt_messages(input_content, message.author)

        async with message.channel.typing():
            response = await self.call_openai(self.conversations[message.author])
            assistant_response = response['choices'][0]['message']['content']

            self.conversations[message.author].append(
                {'role': 'assistant', 'content': assistant_response})

            chunk_length = 2000
            if len(assistant_response) > chunk_length:

                await message.channel.send("Sorry for the wait, OpenAI response is large.\n Response greater than 2000 characters, sending response in chunks.\n")
                await self.send_chunks(assistant_response, chunk_length, message)
            else:
                await message.channel.send(assistant_response)


client = ChatBot(intents=intents)
client.run(DISCORD_TOKEN)
