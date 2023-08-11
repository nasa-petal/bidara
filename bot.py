import discord
import openai
import json
import tracemalloc
tracemalloc.start()
from decouple import config
import functools
import typing   
import discord
from discord.ext import commands
import ast
import asyncio
import tracemalloc

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
#         self.bda_sys = ("You are BIDARA, a biomimetic designer and research assistant, and a leading expert in biomimicry, biology, engineering, industrial design, environmental science, physiology, and paleontology. Focus on understanding, learning from, and emulating the strategies used by living things, with the intention of creating designs and technologies that are sustainable.\n\n"
#                             "Your goal is to help the user work in a step by step way through the Biomimicry Design Process to propose biomimetic solutions to a challenge. Cite peer reviewed sources for your information.\n\n"
#                             "1. Biologize - Analyze the essential functions and context your design challenge must address. Reframe them in biological terms, so that you can “ask nature” for advice. The goal of this step is to arrive at one or more “How does nature…?” questions that can guide your research as you look for biological models in the next step. To broaden the range of potential solutions, turn your question(s) around and consider opposite, or tangential functions. For example, if your biologized question is “How does nature retain liquids?”, you could also ask “How does nature repel liquids?” because similar mechanisms could be at work in both scenarios (i.e. controlling the movement of a liquid). Or if you are interested in silent flight and you know that flight noise is a consequence of turbulence, you might also ask how nature reduces turbulence in water, because air and water share similar fluid dynamics.\n"
#                             "2. Discover - Look for natural models (organisms and ecosystems) that need to address the same functions and context as your design solution. Identify the strategies used that support their survival and success. This step focuses on research and information gathering. You want to generate as many possible sources for inspiration as you can, using your “how does nature…” questions (from the Biologize step) as a guide. Look across multiple species, ecosystems, and scales and learn everything you can about the varied ways that nature has adapted to the functions and contexts relevant to your challenge.\n"
#                             "3. Abstract - Carefully study the essential features or mechanisms that make the biological strategy successful. Write a design strategy that describes how the features work to meet the function(s) you’re interested in in great detail. Try to come up with discipline-neutral synonyms for any biological terms (e.g. replace “fur” with “fibers,” or “skin” with “membrane”) while staying true to the science. The design strategy should clearly address the function(s) you want to meet within the context it will be used. It is not a statement about your design or solution; it’s a launching pad for brainstorming possible solutions. Stay true to the biology. Don’t jump to conclusions about what your design will be; just capture the strategy so that you can stay open to possibilities. When you are done, review your design strategy with a critical eye. Have you included all of the pertinent information? Does your design strategy capture the lesson from nature that drew you to the biological strategy in the first place? Does it give you new insights or simply validate existing design approaches?\n\n"
# "Here’s a simply stated biological strategy:\n"
# "The polar bear’s fur has an external layer of hollow, translucent (not white) guard hairs that transmit heat from sunlight to warm the bear’s skin, while a dense underfur prevents the warmth from radiating back out.\n\n"
# "A designer might be able to brainstorm design solutions using just that. But more often, in order to actually create a design based on what we can learn from biology, it helps to remove biological terms and restate it in design language.\n\n"
# "Here’s a design strategy based on the same biological strategy:\n"
# "A covering keeps heat inside by having many translucent tubes that transmit heat from sunlight to warm the inner surface, while next to the inner surface, a dense covering of smaller diameter fibers prevents warmth from radiating back out.\n\n"
# "Stating the strategy this way makes it easier to translate it into a design application. (An even more detailed design strategy might talk about the length of the fibers or the number of fibers per square centimeter, e.g., if that information is important and its analog can be found in the biological literature.)")

        self.bda_sys_biologize = ("Python list of similar queries formed from the original user query. Come up with as many relevant questions as possible. Avoid redundancies. Use the below strategies to come up with more question similar to the user query: \n"
                            "1. Rephrase/reframe the user question in biological terms, so we can ask nature for advice. Ask 'how does nature?' questions. For example, reframe the following question: 'How does nature make urban cyclists more visible to drivers at night?' into 'How does nature enhance visibility in low light conditions?'. Come up with as many relevant questions as possible and present them in bullet points. \n"
                            "2. Think about analogous life functions and contexts in nature and come up with similar questions that might answer the user question. Come up with as many relevant questions as possible and present them in bullet points. \n"
                            "3. To broaden the range of potential solutions, turn your questions around and consider opposite or tangential functions. Example, for the question 'how does nature retain liquids?', consider 'how does nature repel liquids?' because similar mechanism could work in both situations. (ie, controlling the movement of a liquid). Come up with as many relevant questions as possible and present them in bullet points.\n"
                            "Rank the queries obtained above on the basis of diversity of biological models covered and the relevance of the biological model for solving the query. The top 10 entries combined should contain the most diverse information and least redundant queries.\n"
                            "List of questions: Return a list containing the top 10 questions created above, along with the original user input. In every entry, return just the text of the query, nothing else.")

        self.bda_sys_discover = ("The user message consists of a query. You need to come up with natural biological models (organisms and ecosystems) that we could potentially take inspiration from to solve the problem. Identify the strategies used that support their survival and success, and see if they can be helpful in solving the query. Focus on research and information gathering. Generate as many possible sources for inspiration as you can. Look across multiple species, ecosystems, and scales and consider everything about the varied ways that nature has adapted to the functions and contexts relevant to your challenge. Come up with as many inspiration sources as possible, but avoid redundancies. For every model identified, summarize everything briefly in a sentence and see if the solution is feasible in realtime. Combine all the similar models (or models that solve the problem using the same principle) in a single entry. Rank the models based on their relevance in terms of quality and feasibility of the design solution. Also, try to capture the most diverse information in the top 10 entries \n"
                                  "List of solutions: Return a list containing the top 10 inspiration sources.")

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
            await message.channel.send(f"Your system prompt is set to: BDA mode") #\n>>> {self.default_sys}\n\n")
            await message.channel.send("If you would like to change or clear it, type `!custommode` or `!clearmode`, respectively.")
        elif prompt_choice == "bda":
            self.system_prompt_dict[message.author] = self.bda_sys_biologize
            await self.send_msg("Your system prompt is set to:\n", message)
            await self.send_msg(f"{self.bda_sys_biologize}\n\n", message, prefix=">>> ")
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
    
    # @bot.command(name='shutdown', hidden=True)
    # #@commands.is_owner()
    # async def shutdown(ctx):
    #     await ctx.send("Shutting down...")
    #     await bot.logout()
    #     await bot.close()
    #     os._exit(0)  # Forcefully exit the application

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
                self.conversations[message.author] = []
                await message.channel.send("Your previous conversation is cleared.")
        elif keyword == "examples":
            await self.send_msg(self.examples, message)
        else:
            await message.channel.send("Not a valid commmand.")
    
    ##########################################################################.
    # add code for biologize step
            
    @to_thread
    def call_openai_biologize(self, messages):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0,
            functions = [
            {
                "name": "get_similar_questions",
                "parameters": {
                    "type":"object",
                    "properties":{
                        "queries": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "description": "A similar query",
                            },
                            "description": "Python list of top 10 similar queries formed from the original user query. The original query is also added.",
                        }
                    },
                    "required":["queries"],
                }
            }
        ],
        function_call = "auto",
        )
        reply_content = response["choices"][0].message
        funcs = reply_content.to_dict()["function_call"]["arguments"]
        funcs = json.loads(funcs)
        list_of_queries = funcs["queries"]
        return list_of_queries
    
    async def biologize_on_message(self, discord_message):
        try:
                response_biologize = await self.call_openai_biologize(self.conversations[discord_message.author])
        except:
                await discord_message.channel.send("Error in Biologize step :(")
        else:
                count = 1
                str_to_print = ""
                for q in response_biologize:
                    str_to_print  = str_to_print + "\n" + str(count) + ". " + q
                    count = count + 1
                #assistant_response = str_to_print
                self.conversations[discord_message.author].append(
                    {'role': 'assistant', 'content': str_to_print})
                await self.send_msg(str_to_print, discord_message)
                return response_biologize
    
    #########################################################
    # add code for discover step

    @to_thread
    def call_openai_discover(self, messages):
        print("DISCOVER MESSAGES: ", messages)
        completion = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages = messages,
            functions=[
                {
                    "name": "get_discover_solutions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "models": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "description": "title for a model identified",
                                },
                                "description": "Python list containing the models identified",
                            }
                        },
                        "required": ["models"],
                    }
                }
            ],
            function_call="auto",
        )
        reply_content = completion.choices[0].message
        funcs = reply_content['function_call']['arguments']
        funcs = json.loads(funcs)
        return funcs["models"]
        
    async def discover_on_message(self, discord_message, list_of_queries):
        try:
            messages = []
            openai.api_key = "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"
            for q in list_of_queries:
                message = [
                    {'role': 'user', 'content': q},
                    {'role': 'system', 'content': self.bda_sys_discover}]
                messages.append(message)
            response_discover = []
            for msg in messages:
                temp = await self.call_openai_discover(msg)
                for t in temp:
                    response_discover.append(t)
        except:
            await discord_message.channel.send("Error in Discover step :(")
        else:
            # create a list of responses for passing to next step
            # response_discover = []
            # for lst in res:
            #     for str in lst:
            #         response_discover.append(str)
            #print("RESPONSE DISCOVER: ", response_discover)
            
            # create a string to print intermediate discover results
            string_to_print = response_discover[0]
            for res in response_discover[1:]:
                string_to_print += ", " + res 
            await self.send_msg("DISCOVER STEP SOLUTIONS: " + string_to_print, discord_message)
            
            # return the discover list to be used as input for next step
            return response_discover
        
    ####################################################
    
    # add code for the abstract step

    @to_thread
    def call_openai_abstract(self, messages_abstract):
        print("abstract: ", messages_abstract)
        completion = openai.ChatCompletion.create(
                model = "gpt-4-0613",
                messages = messages_abstract,
        )
        sol = completion["choices"][0]["message"]["content"]
        #print("SOL: ", sol)
        return sol

    async def abstract_on_message(self, discord_message, discover_list, original_input_query):#user_message_biologize, list_of_discover_solutions_2):
        
        system_message_abstract = f"""
        The user inputs a few similar comma-separated biological models. 
        First, carefully study the essential features or mechanisms that make the biological models input by user successful. 
        Then, come up with a design strategy that translates the biological models input by the user into a viable solution for : {original_input_query}. 
        ONLY focus on the biological models input by user, DO NOT ADD ANY yourself.
        The design strategy should describe how the features work to meet the function(s) you're interested in in great detail. 
        Try to come up with discipline-neutral synonyms for any biological terms (e.g. replace “fur” with “fibers,” or “skin” with “membrane”) while staying true to the science. 
        It is not a statement about your design or solution; it’s a launching pad for brainstorming possible solutions. 
        Stay true to the biology. 
        Don’t jump to conclusions about what your design will be; just capture the strategy so that you can stay open to possibilities. 
        When you are done, review your design strategy with a critical eye. Have you included all of the pertinent information? Does your design strategy capture the lesson from nature that drew you to the biological strategy in the first place? Does it give you new insights or simply validate existing design approaches? 
        If possible, give a few examples of how the biological model uses this function in realtime. 
        Dont be repetitive. Dont repeat the user query wording in your paragraph. 
        Then describe the complete design strategy.
        Sum up everything in a minimum of 4-5 sentences.
        Output a single paragraph only.
        Output format: Return a single paragraph as a python string in the format: <Comma-separated biological models input by user><:><relevant characteristics of these biological models><the design strategy of how the given biological models can be used in solving the query defined above>
        """
        
        messages = []
        for discover in discover_list:
            message = [
                {'role': 'user', 'content': str(discover)},
                {'role': 'system', 'content': system_message_abstract}
            ]
            messages.append(message)
        response_abstract = []
        await self.send_msg("ABSTRACT STEP SOLUTIONS: \n", discord_message)
        for msg in messages:
            temp = await self.call_openai_abstract(msg)
            await self.send_msg(temp + "\n", discord_message)
            response_abstract.append(temp)
        str_to_print = ""
        for res in response_abstract:
            str_to_print += res + ", "
        return response_abstract

    ####################################################
#     # add code for the abstract step

#     @to_thread
#     def call_openai_abstract(self, messages_abstract):
#         print("abstract: ", messages_abstract)
#         completion = openai.ChatCompletion.create(
#                 model = "gpt-4-0613",
#                 messages = messages_abstract,
#         )
#         sol = completion["choices"][0]["message"]["content"]
#         print("SOL: ", sol)
#         return sol

#     async def abstract_on_message(self, discord_message, discover_list, original_input_query):#user_message_biologize, list_of_discover_solutions_2):
#         list_of_abstract_solutions = []
        
#         # system_message_abstract = f"""
#         # The user inputs a few similar comma-separated biological models. 
#         # First, carefully study the essential features or mechanisms that make the biological models input by user successful. 
#         # Then, come up with a design strategy that translates the biological models input by the user into a viable solution for : {original_input_query}. 
#         # ONLY focus on the biological models input by user, DO NOT ADD ANY yourself.
#         # The design strategy should describe how the features work to meet the function(s) you're interested in in great detail. 
#         # Try to come up with discipline-neutral synonyms for any biological terms (e.g. replace “fur” with “fibers,” or “skin” with “membrane”) while staying true to the science. 
#         # It is not a statement about your design or solution; it’s a launching pad for brainstorming possible solutions. 
#         # Stay true to the biology. 
#         # Don’t jump to conclusions about what your design will be; just capture the strategy so that you can stay open to possibilities. 
#         # When you are done, review your design strategy with a critical eye. Have you included all of the pertinent information? Does your design strategy capture the lesson from nature that drew you to the biological strategy in the first place? Does it give you new insights or simply validate existing design approaches? 
#         # If possible, give a few examples of how the biological model uses this function in realtime. 
#         # Dont be repetitive. Dont repeat the user query wording in your paragraph. 
#         # Then describe the complete design strategy.
#         # Sum up everything in a minimum of 4-5 sentences.
#         # Output a single paragraph only.
#         # Output format: Return a single paragraph as a python string in the format: <Comma separated biological models input by user><:><relevant characteristics of these biological models><the design strategy of how the given biological models can be used in solving the query defined above>
#         # """
        
#         system_message_abstract = f"""
#         The user inputs a biological model. Come up with a design strategy that translates the biological model input by the user into a viable solution for answering the query: {original_input_query}. 
#         Output a single paragraph. In the paragraph, first define and describe the characteristics of the biological model that we are translating into design strategies in 2-3 sentences. If possible, give a few examples of how the biological 
#         model uses this function in realtime. Dont be repetitive. Dont repeat the user query wording in your paragraph again and again. Then describe the complete design strategy.
#         Sum up everything in a minimum of 4-5 sentences.
#         Solution: Return a paragraph as a python string in the format: <biological model name input by the user><:><the design strategy of how a biological model can be used in solving the query defined above>
#         """
        
#        # #The design strategy should clearly address the function(s) you want to meet within the context it 
#        # #will be used. \n\n"
# # "Here’s a simply stated biological strategy:\n"
# # "The polar bear’s fur has an external layer of hollow, translucent (not white) guard hairs that transmit heat from sunlight to warm the bear’s skin, while a dense underfur prevents the warmth from radiating back out.\n\n"
# # "A designer might be able to brainstorm design solutions using just that. But more often, in order to actually create a design based on what we can learn from biology, it helps to remove biological terms and restate it in design language.\n\n"
# # "Here’s a design strategy based on the same biological strategy:\n"
# # "A covering keeps heat inside by having many translucent tubes that transmit heat from sunlight to warm the inner surface, while next to the inner surface, a dense covering of smaller diameter fibers prevents warmth from radiating back out.\n\n"
# # "Stating the strategy this way makes it easier to translate it into a design application. (An even more detailed design strategy might talk about the length of the fibers or the number of fibers per square centimeter, e.g., if that information is important and its analog can be found in the biological literature.)")
        
#         # system_message_abstract = f"""Come up with a design strategy that translates the biological model input by the user into a viable solution for answering the query: {original_input_query}. Sum up the strategy in 2-3 sentences. Try to be as brief and informative as possible. 
#         #                               Solution: Return a paragraph as a python string in the format: <biological model name input by the user><:><the design strategy of how a biological model can be used in solving the query defined above>"""         
        
#         messages = []
#         print("DISCOVER LIST: ", discover_list)
#         print('TYPE: ', type(discover_list))
#         for discover in discover_list:
#             #print("original_discover: ", discover)
#             discover = discover.split(",")[0]
#             #print("entry: ", discover)
#             message = [
#                 {'role': 'user', 'content': discover},
#                 {'role': 'system', 'content': system_message_abstract}
#             ]
#             messages.append(message)
#         response_abstract = []
#         await self.send_msg("ABSTRACT STEP SOLUTIONS: \n", discord_message)
#         counter = 1
#         for msg in messages:
#             temp = await self.call_openai_abstract(msg)
#             #await self.send_msg(counter, discord_message)
#             await self.send_msg(temp + "\n", discord_message)
#             #print("")
#             #counter = counter + 1
#             response_abstract.append(temp)
#         str_to_print = ""
#         for res in response_abstract:
#             str_to_print += res + ", "
#         #await self.send_msg("ABSTRACT STEP SOLUTIONS: " + str_to_print, discord_message)
#         return response_abstract
    
    #########################################################
    # add code for redundancy eliminated response - after abstract step
    
    @to_thread
    def call_openai_red_elim(self, messages):
        completion = openai.ChatCompletion.create(
            model = "gpt-4-0613",
            messages = messages,
            functions=[
                {
                    "name": "get_redundancy_eliminated_solutions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "models": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    #"description": "comma-separated models list",
                                },
                                #"description": "Python list",
                            }
                        },
                        "required": ["models"],
                    }
                }
            ],
            function_call="auto",
        )
        return completion["choices"][0]["message"]["content"]
    
    
    #     f"""The user inputs a list of design solutions. Carefully study all the individual entries of the list and identify the designs that use the same (or very similar) biological model or strategy to give solutions to the problem: {original_input_query}.
    #     Combine these similar entries into a single entry by 
    #     Sum up everything in a minimum of 4-5 sentences. It is not a statement about your design or solution; it’s a launching pad for brainstorming possible solutions. Stay true to the biology. Don’t jump to conclusions about what your design will be; just capture the strategy so that you can stay open to possibilities. 
    #     When you are done, review your design strategy with a critical eye. Have you included all of the pertinent information? Does your design strategy capture the lesson from nature that drew you to the biological strategy in the first place? Does it give you new insights or simply validate existing design approaches?
    #     Solution: Return a paragraph as a python string in the format: <biological model name input by the user><:><relevant characteristics of biological model><the design strategy of how a biological model can be used in solving the query defined above>"""
    
    async def red_elim_on_message(self, discord_message, abstract_list, original_input_query):
        system_message_redundancy_elimination =f"""Take in a list input by the user. The list consists of paragraphs describing design strategies. Eliminate the redundant design strategies by combining contents of paragraphs that are inspired by similar biological models for answering the query: {original_input_query}. Sum up each strategy in 2-3 sentences. Try to be as brief and informative as possible. Return the new list with redundancy eliminated entries. 
                                               Solution: Return a list where each entry is a paragraph, ie, a python string, in the format: <biological model name><:><the design strategy of how a biological model can be used in solving the query defined above>"""
        await self.send_msg("REDUNDANCY ELIMINATION STEP SOLUTIONS: \n", discord_message)
        messages =  [{'role':'user', 'content': str(abstract_list)},
                                            {'role': 'system','content': system_message_redundancy_elimination}]
        response_red_elim = await self.call_openai_red_elim(messages)
        await self.send_msg(response_red_elim + "\n", discord_message)
        return response_red_elim
    
    ###########################################################
    # add redundancy elimination after discover step
    @to_thread
    def call_openai_red_elim_2(self, messages):
        completion = openai.ChatCompletion.create(
            model = "gpt-4-0613",
            messages = messages,
            # functions=[
            #     {
            #         "name": "get_sorted_solutions",
            #         "parameters": {
            #             "type": "object",
            #             "properties": {
            #                 "models": {
            #                     "type": "array",
            #                     "items": {
            #                         "type": "string",
            #                         "description": "list of similar biological models separated by a comma",
            #                     },
            #                     "description": "Python list of size 10",
            #                 }
            #             },
            #             "required": ["models"],
            #         }
            #     }
            # ],
            # function_call="auto",
        )
        print("red elim completion: ", completion)
        return completion["choices"][0]["message"]["content"]
    
    async def red_elim_2(self, discord_message, discover_list, original_input_query):
        
        lowercase_list = [item.lower() for item in discover_list]
        unique_list_1 = list(set(lowercase_list))
        
        # system_msg_red_elim_after_discover = f"""
        # Take in a list input by the user. This list consists of different biological models. 
        # Your task is to first get rid of redundancies. For example, if 2 or more entries denote the same thing but are just worded differently, eliminate one of them from the list. For example, the models "fireflies" and "fire fly" should be converted to just "fireflies". 
        # After this, combine similar models into a single entry. For example: To answer the question "How can we make urban cyclists more visible to drivers at night?", the biological models "fireflies", "bioluminiscent organisms" and firefly eyes" should be combined into a single entry as "fireflies, bioluminiscent organisms, and firefly eyes". But, if the 2 entries are exactly similar, one of them should be eliminated. 
        # To determine whether 2 biological models are similar, come up with design solutions using these biological models one by one to give solutions to the query: {original_input_query}. Carefully study the essential features or mechanisms that make the biological strategy successful. The design strategy should describe how the features work to meet the function(s) you're interested in in great detail.
        # If any 2 entries use the same features or mechanisms to give the design solution, they are considered similar and should be combined using "and".
        # Examples: "glow-in-the-dark organisms" and "bioluminescent organisms" should be combined; "fireflies" and "glow worms" should be combined; "bioluminiscent fungi" and "bioluminiscent mushrooms" should be combined.
        # Try to combine as many entries as possible, so that the resulting number of entries becomes less than 20. 
        
        # Eliminate the redundancies, combine similar entries, and return a new python list consisting of the new entries of biological models. 
        # Dont give steps to perform above tasks, but actually perform them.
        # Solution: <Python list of 20 entries. Every entry can contain either single biological model or a list of similar biological models, each separated with a comma.>
        # """
        system_msg_red_elim_after_discover = f"""
        Take in a list input by the user. This list consists of different biological models. You need to group similar biological models into a single entry.
        Sort all the biological models into groups of 20. make these groups based on similarity of these models.
        You need to output a list of 20 strings, each containing similar biological models separated by a comma. 
        To identify the similar models, use the following strategy: Come up with design solutions using these biological models one by one to give solutions to the query: {original_input_query}. 
        Carefully study the essential features or mechanisms that make the biological strategy successful. The design strategy should describe how the features work to meet the function(s) you're interested in.
        If any 2 models use the same features or mechanisms to give the design solution, they are considered similar and should be combined using a comma.
        Solution: <Python list of 20 entries. Every entry can contain either single biological model or a list of similar biological models, each separated with a comma.>
        """
        
        await self.send_msg("DISCOVER SOLUTIONS AFTER REDUNDANCY ELIMINATION: \n", discord_message)
        messages = [{'role': 'user', 'content': str(unique_list_1)},
                    {'role': 'system', 'content': system_msg_red_elim_after_discover}]
        response = await self.call_openai_red_elim_2(messages)
        print("intermediate res: ", response)
        print("type: ", type(response))
        await self.send_msg(str(response) + "\n", discord_message)
        return response        
    
    #########################################################
    # async def final_red_elim(self, discord_message, response_discover, original_input_query):
    #     lowercase_list = [item.lower() for item in response_discover]
    #     unique_discover = list(set(lowercase_list))
        
    #     system_msg_red_elim_after_discover = f"""
        
    #     """
        
    
    
    ########################################################

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
        
        # for bda mode
        async with message.channel.typing():
            
            original_input_query = self.conversations[message.author]
            response_biologize = await self.biologize_on_message(message)
            response_discover = await self.discover_on_message(message, response_biologize)
            #print("DIS: ", response_discover)
            #print("Type", type(response_discover))
            #response_unique_discover_2 = await self.final_red_elim(message, response_discover, original_input_query)
            #temp = response_discover.split("'")
            #print(type(response_discover))
            
            ##########
            response_unique_discover_2 = await self.red_elim_2(message, response_discover, original_input_query)
            #print(type(response_unique_discover_2))
            str_to_lst = ast.literal_eval(response_unique_discover_2)
            print("STR TO LIST:  ", str_to_lst)   
            print("TYPE:  ", type(str_to_lst))         
            response_abstract = await self.abstract_on_message(message, str_to_lst, original_input_query)

            # response_red_elim = await self.red_elim_on_message(message, response_abstract, original_input_query)
            # print(response_red_elim)
            ##########
# if __name__ == "__main__":
#     client = ChatBot(intents=intents)
#     client.run(DISCORD_TOKEN)

client = ChatBot(intents = intents)
client.run(DISCORD_TOKEN)