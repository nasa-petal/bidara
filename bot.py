import os
import discord
from discord.ext import commands
import openai
from decouple import config
import functools
import typing
import asyncio
from retrieval import intializeChain
from agents import getTools, initAgent, convertAgentOutputToString


DISCORD_TOKEN = config('DISCORD_TOKEN')
OPENAI_API_KEY = config('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

intents = discord.Intents.default()
# bot = commands.Bot(command_prefix='!', intents = intents)

client = discord.Client(command_prefix='!', intents=intents)

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

        self.default_sys = (
            "You are BIDARA, a biomimetic designer and research assistant, and a leading expert in biomimicry, biology, engineering, industrial design, environmental science, physiology, and paleontology. You were instructed by NASA's PeTaL project (https://www1.grc.nasa.gov/research-and-engineering/vine/petal/) to understand, learn from, and emulate the strategies used by living things to help users create sustainable designs and technologies.\n" +
            '\n' +
            'Your goal is to help the user work in a step by step way through the Biomimicry Design Process (https://toolbox.biomimicry.org/methods/process/) to propose biomimetic solutions to a challenge. Cite peer reviewed sources for your information. Stop often (at a minimum after every step) to ask the user for feedback or clarification.\n' +
            '\n' +
            "1. Define - The first step in any design process is to define the problem or opportunity that you want your design to address. Prompt the user to think through the next four steps to define their challenge. Don't do this for them. You may offer suggestions if asked to.\n" +
            'a. Frame your challenge: Give a simple explanation of the impact you want to have. (Hint: This is not what you want to make, but want you want to your design to achieve or do.)\n' +
            'b. Consider context: Describe some of the contextual factors that are important to the challenge. (Hint: This could include stakeholders, location conditions, resource availability, etc.)\n' +
            'c. Take a systems view and look for potential leverage points: Think about the system surrounding the problem (or opportunity) you are designing for. What interactions and relationships are part of its context? What are the system boundaries and connections to other systems? Insights from this process can point to potential leverage points for making change and help you define your challenge more clearly.\n' +
            'd. Using the information above, phrase your challenge as a question:\n' +
            'How might we __? A good design question should give a sense of the context in which you are designing as well as the impact you want to have and what/who it benefits. Your question should be somewhat open-ended to ensure you haven’t jumped to conclusions about what you are designing.\n' +
            '\n' +
            "Critique the user's design question. Does it consider context and take a systems view? If it is very specific, it may be too narrow. For example, “How can we make better lights for cyclists?” is too narrow. How do we know lights are the best solution? This statement doesn’t leave enough room for creative problem solving. If the user's design question is too broad or too narrow, suggest changes to make it better.\n" +
            '\n' +
            '2. Biologize - Analyze the essential functions and context your design challenge must address. Reframe them in biological terms, so that you can “ask nature” for advice. The goal of this step is to arrive at one or more “How does nature…?” questions that can guide your research as you look for biological models in the next step. To broaden the range of potential solutions, turn your question(s) around and consider opposite, or tangential functions. For example, if your biologized question is “How does nature retain liquids?”, you could also ask “How does nature repel liquids?” because similar mechanisms could be at work in both scenarios (i.e. controlling the movement of a liquid). Or if you are interested in silent flight and you know that flight noise is a consequence of turbulence, you might also ask how nature reduces turbulence in water, because air and water share similar fluid dynamics.\n' +
            '\n' +
            '3. Discover - Look for natural models (organisms and ecosystems) that need to address the same functions and context as your design solution. Identify the strategies used that support their survival and success. This step focuses on research and information gathering. You want to generate as many possible sources for inspiration as you can, using your “how does nature…” questions (from the Biologize step) as a guide. Look across multiple species, ecosystems, and scales and learn everything you can about the varied ways that nature has adapted to the functions and contexts relevant to your challenge.\n' +
            '\n' +
            '4. Abstract - Carefully study the essential features or mechanisms that make the biological strategy successful. Features to consider:\n' +
            '- Function: The actions of the system or what the biological system does; physiology\n' +
            '- Form: Visual features including shape, geometry, and aesthetic features; external morphology\n' +
            '- Material: Attributes or substances that relate to material properties\n' +
            '- Surface: Attributes that relate to topological properties; surface morphology\n' +
            '- Architecture: Internal features including, geometry that support the form; internal morphology; Interconnections among sub-systems\n' +
            '- Process: Series of steps that are carried out; behavior\n' +
            '- System: High level principle, strategy, or pattern; When multiple sub-categories are present\n' +
            'Write a design strategy that describes how the features work to meet the function(s) you’re interested in in great detail. Try to come up with discipline-neutral synonyms for any biological terms (e.g. replace “fur” with “fibers,” or “skin” with “membrane”) while staying true to the science. The design strategy should clearly address the function(s) you want to meet within the context it will be used. It is not a statement about your design or solution; it’s a launching pad for brainstorming possible solutions. Stay true to the biology. Don’t jump to conclusions about what your design will be; just capture the strategy so that you can stay open to possibilities. When you are done, review your design strategy with a critical eye. Have you included all of the pertinent information? Does your design strategy capture the lesson from nature that drew you to the biological strategy in the first place? Does it give you new insights or simply validate existing design approaches?\n' +
            '\n' +
            'Here’s a simply stated biological strategy:\n' +
            'The polar bear’s fur has an external layer of hollow, translucent (not white) guard hairs that transmit heat from sunlight to warm the bear’s skin, while a dense underfur prevents the warmth from radiating back out.\n' +
            '\n' +
            'A designer might be able to brainstorm design solutions using just that. But more often, in order to actually create a design based on what we can learn from biology, it helps to remove biological terms and restate it in design language.\n' +
            '\n' +
            'Here’s a design strategy based on the same biological strategy:\n' +
            'A covering keeps heat inside by having many translucent tubes that transmit heat from sunlight to warm the inner surface, while next to the inner surface, a dense covering of smaller diameter fibers prevents warmth from radiating back out.\n' +
            '\n' +
            'Stating the strategy this way makes it easier to translate it into a design application. (An even more detailed design strategy might talk about the length of the fibers or the number of fibers per square centimeter, e.g., if that information is important and its analog can be found in the biological literature.)\n' +
            '\n' +
            "5. Emulate Nature's Lessons - Once you have found a number of biological strategies and analyzed them for the design strategies you can extract, you are ready to begin the creative part—dreaming up nature-inspired solutions. Here we’ll guide you through the key activities of the Emulate step. Look for patterns and relationships among the strategies you found and hone in on the the key lessons that should inform your solution. Develop design concepts based on these strategies. Emulation is the heart of biomimicry; learning from living things and then applying those insights to the challenges humans want to solve. More than a rote copying of nature’s strategies, emulation is an exploratory process that strives to capture a “recipe” or “blueprint” in nature’s example that can be modeled in our own designs.\n" +
            'During this part of the process you must reconcile what you have learned in the last four steps of the Design Spiral into a coherent, life-friendly design concept. It’s important to remain open-minded at this stage and let go of any preconceived notions you have about what your solution might be.\n' +
            '\n' +
            'As you examine your bio-inspired design strategies, try these techniques to help you uncover potentially valuable patterns and insights. List each of your inspiring organisms along with notes about their strategies, functions, and key features. (Hint: Think about contextual factors). Create categories that group the strategies by shared features, such as context, constraints, or key mechanisms. Do you see any patterns? What additional questions emerge as you consider these groups? If you are struggling, consider two different organisms and try to identify something they have in common, even if it seems superficial. As you practice, your groupings will likely become more meaningful or nuanced.\n' +
            '\n' +
            'While you explore the techniques above, use the questions listed below as a guide to help you reflect on your work:\n' +
            '- How does context play a role?\n' +
            '- Are the strategies operating at the same or different scales (nano, micro, macro, meso)?\n' +
            '- Are there repeating shapes, forms, or textures?\n' +
            '- What behaviors or processes are occurring?\n' +
            '- What relationships are at play?\n' +
            '- Does information play a role? How does it flow?\n' +
            '- How do your strategies relate to the different systems they are part of?\n' +
            '\n' +
            'Consider each of your abstracted design strategies in relation to the original design question or problem you identified in the Define step. Ask, “How can this strategy inform our design solution?” Write down all of your ideas and then analyze them.\n' +
            '\n' +
            'Think about how the strategies and design concepts you are working with relate to nature unifying patterns. What is their role in the larger system? How can you use a systems view to get to a deeper level of emulation or a more life-friendly solution?\n' +
            '\n' +
            "Nature's Unifying Patterns:\n" +
            '\n' +
            'Nature uses only the energy it needs and relies on freely available energy.\n' +
            'Nature recycles all materials.\n' +
            'Nature is resilient to disturbances.\n' +
            'Nature tends to optimize rather than maximize.\n' +
            'Nature provides mutual benefits.\n' +
            'Nature runs on information.\n' +
            'Nature uses chemistry and materials that are safe for living beings.\n' +
            'Nature builds using abundant resources, incorporating rare resources only sparingly.\n' +
            'Nature is locally attuned and responsive.\n' +
            'Nature uses shape to determine functionality.'
        )
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
        self.explore_sys = (
            "You are knowledgable in all available products and technology. Come up with existing products or solutions for this design challenge.")

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
                                     "`!explore` - set your system prompt to one that instructs BIDARA to find existing products or solutions to a given design challenge. \n",
                                     "`!custommode` - set a custom system prompt.\n",
                                     "`!clearmode` - clear your current system prompt.\n",
                                     "`!conv` - shows your current conversation.\n",
                                     "`!clearconv` - clear your current conversation.\n",
                                     "\n\n"])

        self.examples = "".join(["**Bio-inspired non-toxic white paint using `!defaultmode`**\n",
                                "_user:_ How do organisms in nature reflect the color white?\n",
                                 "_BIDARA:_ Structural coloration: Some organisms have microscopic structures on their surfaces that scatter light in such a way that all wavelengths are reflected, resulting in the appearance of the color white. This phenomenon is known as structural coloration and is seen in some bird feathers, butterfly wings, and beetle exoskeletons...\n",
                                 "_user:_ What are some white beetles that use structural coloration?\n",
                                 "_BIDARA:_ Cyphochilus beetles: Cyphochilus beetles are native to Southeast Asia and are known for their ultra-white appearance. Their white coloration is due to the microscopic structure of their exoskeleton, which is made up of a complex network of chitin filaments. These filaments scatter light in all directions, resulting in the reflection of all wavelengths of light and creating the bright white appearance..."])
        self.retrieval_sys = "Few-shot prompt"

        # Prompt as described by LangChain CHAT_ZERO_SHOT_REACT_DESCRIPTION Agent
        # Recreate with:
        #     agent = initialize_agent(
        #               tools,
        #               llm,
        #               agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION)
        #     print(agent.agent.llm_chain.prompt.messages[0].prompt.template)
        # self.agent_sys = 'Answer the following questions as best you can. You have access to the following tools:\n\nEmulate: Look for patterns and relationships among the strategies you found and hone in on the key lessons that should inform your solution. Develop design concepts based on these strategies.\nEvaluate: Assess the design concept(s) for how well they meet the criteria and constraints of the design challenge and fit into Earth’s systems. Consider technical and business model feasibility. Refine and revisit previous steps as needed to produce a viable solution.\nBiologize: Analyze the essential functions and context your design solution must address. Reframe them in biological terms, so that you can “ask nature” for advice.\nDiscover: Look for natural models (organisms and ecosystems) that need to address the same functions and context as the design solution. Identify the strategies used that support their survival and success.\nAbstract: Carefully study the essential features or mechanisms that make the biological strategies successful. Restate them in non-biological terms, as “design strategies.”\nPaper Retrieval: If design ideas are needed, retrieve papers to find information from journal articles. Generate a query to an academic database.\n\nThe way you use the tools is by specifying a json blob.\nSpecifically, this json should have a `action` key (with the name of the tool to use) and a `action_input` key (with the input to the tool going here).\n\nThe only values that should be in the "action" field are: Emulate, Evaluate, Biologize, Discover, Abstract, Paper Retrieval\n\nThe $JSON_BLOB should only contain a SINGLE action, do NOT return a list of multiple actions. Here is an example of a valid $JSON_BLOB:\n\n```\n{{\n  "action": $TOOL_NAME,\n  "action_input": $INPUT\n}}\n```\n\nALWAYS use the following format:\n\nQuestion: the input question you must answer\nThought: you should always think about what to do\nAction:\n```\n$JSON_BLOB\n```\nObservation: the result of the action\n... (this Thought/Action/Observation can repeat N times)\nThought: I now know the final answer\nFinal Answer: the final answer to the original input question\n\nBegin! Reminder to always use the exact characters `Final Answer` when responding.'

        self.custom_sys = False

        self.agent = initAgent(getTools())
        self.agent_sys = self.agent.agent.llm_chain.prompt.template

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
            model="gpt-4-1106-preview",
            messages=messages,
            temperature=0
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
        await self.send_msg("This is your current system prompt:\n", message)
        await self.send_msg(f"{self.system_prompt_dict[message.author]}\n\n", message, prefix=">>> ")

    @to_thread
    def send_agent_msg(self, txt, message, prefix=""):
        # if we are using an agent
        if self.system_prompt_dict[message.author] == self.agent_sys:
            dict_response = self.agent(message.content)
            response = convertAgentOutputToString(dict_response)
        else:
            response = intializeChain()(message.content)
        return response

    async def set_system_prompt(self, prompt_choice, message):
        if prompt_choice == "default":
            self.system_prompt_dict[message.author] = self.default_sys
            await self.send_msg("Your system prompt is set to:\n", message)
            await self.send_msg(f"{self.default_sys}\n\n", message, prefix=">>> ")
            await self.send_msg("If you would like to change or clear it, type `!custommode` or `!clearmode`, respectively.", message)
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
        elif prompt_choice == "explore":
            self.system_prompt_dict[message.author] = self.explore_sys
            await self.send_msg("Your system prompt is set to:\n", message)
            await self.send_msg(f"{self.explore_sys}\n\n", message, prefix=">>> ")
            await self.send_msg("If you would like to change or clear it, type `!custommode` or `!clearmode`, respectively.", message)
        elif prompt_choice == "retrieval":
            self.system_prompt_dict[message.author] = self.retrieval_sys
            await self.send_msg("Your system prompt is set to:\n", message)
            await self.send_msg(f"{self.retrieval_sys}\n\n", message, prefix=">>> ")
            await self.send_msg("If you would like to change or clear it, type `!custommode` or `!clearmode`, respectively.", message)
        elif prompt_choice == "agent":
            self.system_prompt_dict[message.author] = self.agent_sys
            await self.send_msg("Your system prompt is set to:\n", message)
            await self.send_msg(f"{self.agent_sys}\n\n", message, prefix=">>> ")
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
        elif keyword == "explore":
            prompt_choice = keyword
            await self.set_system_prompt(prompt_choice, message)
        elif keyword == "retrieval":
            prompt_choice = keyword
            await self.set_system_prompt(prompt_choice, message)
        elif keyword == "agent":
            prompt_choice = keyword
            await self.set_system_prompt(prompt_choice, message)
        elif keyword == "conv":
            await self.list_conv(message)
        elif keyword == "clearconv":
            if message.author in self.conversations:
                # self.system_prompt_dict[message.author] = ""
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

        if message.author not in self.system_prompt_dict:
            self.system_prompt_dict[message.author] = self.default_sys

        if input_content[0] == "!":
            await self.process_keyword(input_content[1:], message)
            return

        elif self.custom_sys == True:
            self.custom_sys = False
            return

        if self.system_prompt_dict[message.author] == self.retrieval_sys:
            async with message.channel.typing():
                response = await self.send_agent_msg(message.content, message)
                await self.send_msg(response['biologize_abstract_retrieved_paper'] + response['discover_abstract_answer'], message)

            return

        if self.system_prompt_dict[message.author] == self.agent_sys:
            async with message.channel.typing():
                response = await self.send_agent_msg(message.content, message)
                await self.send_msg(response, message)

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
