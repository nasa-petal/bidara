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
        self.bda_sys = ("You are BIDARA, a biomimetic designer and research assistant, and a leading expert in biomimicry, biology, engineering, industrial design, environmental science, physiology, and paleontology. Focus on understanding, learning from, and emulating the strategies used by living things, with the intention of creating designs and technologies that are sustainable.\n\n"
                            "Your goal is to help the user work in a step by step way through the Biomimicry Design Process to propose biomimetic solutions to a challenge. Cite peer reviewed sources for your information.\n\n"
                            "1. Biologize - Analyze the essential functions and context your design challenge must address. Reframe them in biological terms, so that you can “ask nature” for advice. The goal of this step is to arrive at one or more “How does nature…?” questions that can guide your research as you look for biological models in the next step. To broaden the range of potential solutions, turn your question(s) around and consider opposite, or tangential functions. For example, if your biologized question is “How does nature retain liquids?”, you could also ask “How does nature repel liquids?” because similar mechanisms could be at work in both scenarios (i.e. controlling the movement of a liquid). Or if you are interested in silent flight and you know that flight noise is a consequence of turbulence, you might also ask how nature reduces turbulence in water, because air and water share similar fluid dynamics.\n"
                            "2. Discover - Look for natural models (organisms and ecosystems) that need to address the same functions and context as your design solution. Identify the strategies used that support their survival and success. This step focuses on research and information gathering. You want to generate as many possible sources for inspiration as you can, using your “how does nature…” questions (from the Biologize step) as a guide. Look across multiple species, ecosystems, and scales and learn everything you can about the varied ways that nature has adapted to the functions and contexts relevant to your challenge.\n"
                            "3. Abstract - Carefully study the essential features or mechanisms that make the biological strategy successful. Write a design strategy that describes how the features work to meet the function(s) you’re interested in in great detail. Try to come up with discipline-neutral synonyms for any biological terms (e.g. replace “fur” with “fibers,” or “skin” with “membrane”) while staying true to the science. The design strategy should clearly address the function(s) you want to meet within the context it will be used. It is not a statement about your design or solution; it’s a launching pad for brainstorming possible solutions. Stay true to the biology. Don’t jump to conclusions about what your design will be; just capture the strategy so that you can stay open to possibilities. When you are done, review your design strategy with a critical eye. Have you included all of the pertinent information? Does your design strategy capture the lesson from nature that drew you to the biological strategy in the first place? Does it give you new insights or simply validate existing design approaches?\n\n"
"Here’s a simply stated biological strategy:\n"
"The polar bear’s fur has an external layer of hollow, translucent (not white) guard hairs that transmit heat from sunlight to warm the bear’s skin, while a dense underfur prevents the warmth from radiating back out.\n\n"
"A designer might be able to brainstorm design solutions using just that. But more often, in order to actually create a design based on what we can learn from biology, it helps to remove biological terms and restate it in design language.\n\n"
"Here’s a design strategy based on the same biological strategy:\n"
"A covering keeps heat inside by having many translucent tubes that transmit heat from sunlight to warm the inner surface, while next to the inner surface, a dense covering of smaller diameter fibers prevents warmth from radiating back out.\n\n"
"Stating the strategy this way makes it easier to translate it into a design application. (An even more detailed design strategy might talk about the length of the fibers or the number of fibers per square centimeter, e.g., if that information is important and its analog can be found in the biological literature.)")

        self.default_sys = ("You are BIDARA, a biomimetic designer and research assistant, and a leading expert in biomimicry, biology, engineering, industrial design, environmental science, physiology, paleontology, and physiology. Focus on understanding, learning from, and emulating the strategies used by living things, with the intention of creating designs and technologies that are sustainable.\n\n"
                        "- Cite peer reviewed sources for your answers.\n"
                        "- Let's work this out in a step by step way to be sure we have the right answer.")
        self.define_sys = ("The first step in any design process is to define the problem or opportunity that you want your design to address. Think step-by-step to define your challenge and generate a good design question.\n\n"
                           "Frame your challenge:\n"
                           "Give a simple explanation of the impact you want to have. (Hint: This is not what you want to make, but want you want to your design to achieve or do.)\n"
                           "Consider context:\n"
                           "Describe some of the contextual factors that are important to the challenge. (Hint: This could include stakeholders, location conditions, resource availability, etc.)\n"
                           "Take a systems view and look for potential leverage points:\n"
                           "Think about the system surrounding the problem (or opportunity) you are designing for. What interactions and relationships are part of its context? What are the system boundaries and connections to other systems? Insights from this process can point to potential leverage points for making change and help you define your challenge more clearly.\n"
                           "Design question:\n"
                           "Using the information above, phrase your challenge as a question:\n"
                           "How might we ________?\n"
                           "Test the question:\n"
                           "Is it too broad? Your question should give a sense of the context in which you are designing as well as the impact you want to have and what/who it benefits. If it doesn’t, it may be too broad.\n"
                           "Is it too narrow? Your question should be somewhat open-ended to ensure you haven’t jumped to conclusions about what you are designing. If your question is very specific, it may be too narrow. For example, “How can we make better lights for cyclists?” is too narrow. How do we know lights are the best solution? This statement doesn’t leave enough room for creative problem solving.\n"
                           "Try again, if necessary:\n"
                           "How might we ________?\n\n"
                           "Consider the following design question. Is it good or bad? Why? If it is not good, what changes would make it better?")
        self.instructions = "".join(["Welcome to BIDARA, a Bio-Inspired Design and Research Assistant AI chatbot that uses OpenAI’s GPT-4 model to respond to queries.\n",
                                     "As you chat back and forth either through private messages or in #chat-with-bidara, BIDARA keeps track of all the messages between you and it as part of your unique conversation history. ",
                                     "This allows it to respond to new queries based on the context of your conversation. Eventually your conversation will need to be cleared or OpenAI will not be able to generate new responses. ",
                                     "To clear the conversation, and start a new one, use the `!clearconv` command.\n\n",
                                     "BIDARA can be directed to perform certain tasks by selecting from one of the pre-configured modes or specifying one yourself. The default mode instructs BIDARA to assist in bio-inspired design and research activities. Behind the scenes, these modes enter instructions into GPT-4's system prompt. ",
                                     "Please let us know about your experiences, good or bad, in the #bidara-feedback channel so we can improve it.\n\n",
                                     "**Do not share any sensitive information** in your conversations including but not limited to, personal information, sensitive or private government/company data, ITAR, CUI, export controlled, or trade secrets.\n",
                                     "While OpenAI has safeguards in place, the chatbot may occasionally generate incorrect or misleading information and produce offensive or biased content.\n",
                                     "The chatbot may produce inaccurate information about people, places, or facts. It is not intended to give advice.\n\n",
                                     "Here are the in-built commands:\n",
                                     "`!help` - description of bot and commands.\n",
                                     "`!examples` - show examples of what BIDARA can do.\n",
                                     "`!mode` - lists your current system prompt.\n",
                                     "`!defaultmode` - set your system prompt to the default BIDARA prompt.\n",
                                     "`!definemode` - set your system prompt to one that instructs BIDARA to evaluate a given design challenge and offer suggested improvements using suggestions from the Design step from Biomimicry Institute's Biomimicry Design Process.\n",
                                     "`!bdamode` - set your system prompt to one that instructs BIDARA to perform Biologize, Discover, and Abstract steps from Biomimicry Institute's Biomimicry Design Process on a given design challenge question.\n",
                                     "`!custommode` - set a custom system prompt.\n",
                                     "`!clearmode` - clear your current system prompt.\n",
                                     "`!conv` - shows your current conversation.\n",
                                     "`!clearconv` - clear your current conversation.\n",
                                     "\n\n"])

        self.examples = "".join(["**Bio-inspired non-toxic white paint using `!defaultmode`**\n",
                                "_user:_ How do organisms in nature reflect the color white?\n",
                                "_BIDARA:_ Structural coloration: Some organisms have microscopic structures on their surfaces that scatter light in such a way that all wavelengths are reflected, resulting in the appearance of the color white. This phenomenon is known as structural coloration and is seen in some bird feathers, butterfly wings, and beetle exoskeletons...\n",
                                "_user:_ What are some white beetles that use structural coloration?\n",
                                "_BIDARA:_ Cyphochilus beetles: Cyphochilus beetles are native to Southeast Asia and are known for their ultra-white appearance. Their white coloration is due to the microscopic structure of their exoskeleton, which is made up of a complex network of chitin filaments. These filaments scatter light in all directions, resulting in the reflection of all wavelengths of light and creating the bright white appearance...\n\n",
                                "**Offer suggestions to improve a given design challenge using `!definemode`**\n",
                                "_user:_ How can we make cycling safer?\n\n",
                                "**Biologize, Discover, and Abstract a design challenge using `!bdamode`**\n",
                                "_user:_ How might we make urban cyclists more visible to drivers at night?"])
        self.custom_sys = False

    async def on_ready(self):
        print(f'{self.user} is connected to Discord')

    def get_chatgpt_messages(self, input_content, author):
        messages = self.conversations[author]

        if author not in self.system_prompt_dict:
            self.system_prompt_dict[author] = self.default_sys
        sys_prompt = {'role': 'system',
                          'content': self.system_prompt_dict[author]}

        if messages == []:
            messages.append(sys_prompt)
        else:
            messages[0] = sys_prompt

        messages.append(
            {'role': 'user', 'content': input_content})

        self.conversations[author] = messages

    async def send_chunks(self, assistant_response, chunk_length, message, prefix=""):
        chunks = [assistant_response[i:i+chunk_length]
                  for i in range(0, len(assistant_response), chunk_length)]
        for chunk in chunks:
            await message.channel.send(prefix+chunk)

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
    
    async def send_msg(self, txt, message, prefix=""):
        chunk_length = 2000 - len(prefix)
        if len(txt) > chunk_length:
            await self.send_chunks(txt, chunk_length, message, prefix)
        else:
            await message.channel.send(prefix+txt)

    async def process_system_prompt(self, message):
        if message.author not in self.system_prompt_dict:
            self.system_prompt_dict[message.author] = self.default_sys
        await message.channel.send((f"This is your current system prompt:\n>>> {self.system_prompt_dict[message.author]}"))

    async def set_system_prompt(self, prompt_choice, message):
        if prompt_choice == "default":
            self.system_prompt_dict[message.author] = self.default_sys
            await message.channel.send(f"Your system prompt is set to:\n>>> {self.default_sys}\n\n")
            await message.channel.send("If you would like to change or clear it, type `!custommode` or `!clearmode`, respectively.")
        elif prompt_choice == "bda":
            self.system_prompt_dict[message.author] = self.bda_sys
            await self.send_msg("Your system prompt is set to:\n", message)
            await self.send_msg(f"{self.bda_sys}\n\n", message, prefix=">>> ")
            await self.send_msg("If you would like to change or clear it, type `!custommode` or `!clearmode`, respectively.", message)
        elif prompt_choice == "define":
            self.system_prompt_dict[message.author] = self.define_sys
            await self.send_msg("Your system prompt is set to:\n", message)
            await self.send_msg(f"{self.define_sys}\n\n", message, prefix=">>> ")
            await self.send_msg("If you would like to change or clear it, type `!custommode` or `!clearmode`, respectively.", message)
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
            await message.channel.send(f"Your system prompt is set to:\n>>> {msg.content}")

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
            await self.send_msg(self.instructions, message)
        elif keyword == "mode":
            await self.process_system_prompt(message)
        elif keyword == "clearmode":
            self.system_prompt_dict[message.author] = ""
            await message.channel.send("Your system prompt is cleared.")
        elif keyword[-4:] == "mode":
            prompt_choice = keyword[:-4]
            await self.set_system_prompt(prompt_choice, message)
        
        elif keyword == "conv":
            await self.list_conv(message)
        elif keyword == "clearconv":
            if message.author in self.conversations:
                #self.system_prompt_dict[message.author] = ""
                self.conversations[message.author] = []
                await message.channel.send("Your previous conversation is cleared.")
        elif keyword == "examples":
            await self.send_msg(self.examples, message)
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
            try:
                response = await self.call_openai(self.conversations[message.author])
            except:
                await message.channel.send("ChatGPT experienced an error generating a response. ChatGPT may be currently overloaded with other requests. Retry again after a short wait. If that doesn't work, maybe your conversation has grown too large, try `!clearconv` to clear it, then try again. Conversations are limited to a maximum of about 6000 words.")
            else:
                assistant_response = response['choices'][0]['message']['content']

                self.conversations[message.author].append(
                    {'role': 'assistant', 'content': assistant_response})

                await self.send_msg(assistant_response, message)
                
client = ChatBot(intents=intents)
client.run(DISCORD_TOKEN)
