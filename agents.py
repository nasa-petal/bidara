from langchain.agents import AgentType, initialize_agent
from langchain.prompts import PromptTemplate
from langchain.chains import TransformChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts.chat import MessagesPlaceholder
from langchain.tools import Tool
from langchain import LLMChain, OpenAI
from decouple import config
from retrieval import SemanticScholarSearch


OPEN_API_KEY = config('OPENAI_API_KEY')
chat_llm = ChatOpenAI(model="gpt-4",  temperature=0,
                      openai_api_key=OPEN_API_KEY)
SEMANTIC_SCHOLAR_API_KEY = config('SEMANTIC_SCHOLAR_API_KEY')


def simpleSearchQueryExecutor(inputs: dict) -> dict:
    response = SemanticScholarSearch(inputs['question'], 2)
    return {'retrieved_paper': response}


def getTools():
    biologize = LLMChain(llm=chat_llm,
                         prompt=PromptTemplate(input_variables=['question'],
                                               template="Analyze the essential functions and context your design challenge \
                   must address. Reframe them in biological terms, so that you can “ask nature” for advice. \
                   The goal of this step is to arrive at one or more “How does nature…?” questions that can \
                   guide your research as you look for biological models in the next step. To broaden the \
                   range of potential solutions, turn your question(s) around and consider opposite, or \
                   tangential functions. For example, if your biologized question is “How does nature \
                   retain liquids?”, you could also ask “How does nature repel liquids?” because similar \
                   mechanisms could be at work in both scenarios (i.e. controlling the movement of a liquid). \
                   Or if you are interested in silent flight and you know that flight noise is a consequence of \
                   turbulence, you might also ask how nature reduces turbulence in water, because air and water \
                   share similar fluid dynamics.\n {question}")
                         )

    discover = LLMChain(llm=chat_llm,
                        prompt=PromptTemplate(input_variables=['question'],
                                              template="Look for natural models (organisms and ecosystems) that \
                    need to address the same functions and context as your design solution. \
                    Identify the strategies used that support their survival and success. \
                    This step focuses on research and information gathering. \
                    Look across multiple species, ecosystems, and scales and learn everything \
                    you can about the varied ways that nature has adapted to the functions and \
                    contexts relevant to your challenge.\n {question}")
                        )

    abstract = LLMChain(llm=chat_llm,
                        prompt=PromptTemplate(input_variables=['question'],
                                              template="Carefully study the essential features or mechanisms that make the \
                    biological strategy successful. Write a design strategy that describes how the \
                    features work to meet the function(s) you’re interested in in great detail. \
                    Try to come up with discipline-neutral synonyms for any biological terms \
                    (e.g. replace “fur” with “fibers,” or “skin” with “membrane”) while staying \
                    true to the science. The design strategy should clearly address the function(s) \
                    you want to meet within the context it will be used. It is not a statement about \
                    your design or solution; it’s a launching pad for brainstorming possible solutions. \
                    Stay true to the biology. Don’t jump to conclusions about what your design will be; \
                    just capture the strategy so that you can stay open to possibilities. When you are done, \
                    review your design strategy with a critical eye. Have you included all of the pertinent \
                    information? Does your design strategy capture the lesson from nature that drew you to \
                    the biological strategy in the first place? Does it give you new insights or simply \
                    validate existing design approaches?\n {question}")
                        )

    emulate = LLMChain(llm=chat_llm,
                       prompt=PromptTemplate(input_variables=['question'],
                                             template="Emulation is the heart of biomimicry; learning from living things and \
                    then applying those insights to the challenges humans want to solve. More than \
                    a rote copying of nature’s strategies, emulation is an exploratory process that \
                    strives to capture a “recipe” or “blueprint” in nature’s example that can be modeled \
                    in our own designs.\n {question}")
                       )

    evaluate = LLMChain(llm=chat_llm,
                        prompt=PromptTemplate(input_variables=['question'],
                                              template="This step is all about assessment. Your team will examine the design concepts \
                    you developed during the Emulate step for how well they solve your design challenge in \
                    a life-friendly way and for how feasible they are. Although Evaluate is shown as the \
                    “last” step in the Design Spiral, Evaluation should occur multiple times throughout the \
                    design process and with increasing rigor. Early in the process, this may be as simple as \
                    pausing after you generate a number of ideas to identify which concepts have the most \
                    potential and which seem like dead ends. As your team hones in on a concept, evaluation \
                    may involve more complex activities, such as creating models, testing technologies, or \
                    sharing prototypes with users or stakeholders to solicit feedback.\n {question}")
                        )

    retriever = TransformChain(
        input_variables=["question"], output_variables=["retrieved_paper"], transform=simpleSearchQueryExecutor
    )

    tools = [
        Tool.from_function(
            func=emulate.run,
            name="Emulate",
            description="Look for patterns and relationships among the strategies you found and hone in on\
            the key lessons that should inform your solution. Develop design concepts based on these strategies."
        ),
        Tool.from_function(
            func=evaluate.run,
            name="Evaluate",
            description="Assess the design concept(s) for how well they meet the criteria and constraints of \
            the design challenge and fit into Earth’s systems. Consider technical and business model feasibility. \
            Refine and revisit previous steps as needed to produce a viable solution."
        ),
        Tool.from_function(
            func=biologize.run,
            name="Biologize",
            description="Analyze the essential functions and context your design solution must address. \
            Reframe them in biological terms, so that you can “ask nature” for advice."
        ),
        Tool.from_function(
            func=discover.run,
            name="Discover",
            description="Look for natural models (organisms and ecosystems) that need to address the same \
            functions and context as the design solution. Identify the strategies used that support their \
            survival and success."
        ),
        Tool.from_function(
            func=abstract.run,
            name="Abstract",
            description="Carefully study the essential features or mechanisms that make the biological strategies \
            successful. Restate them in non-biological terms, as “design strategies.”"
        ),
        Tool.from_function(
            func=retriever.run,
            name="Paper Retrieval",
            description="If design ideas are needed, retrieve papers to find information from journal articles. Generate a query to an academic database."
        ),
    ]

    return tools


def initAgent(tools):
    chat_history = MessagesPlaceholder(variable_name="chat_history")
    memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True, input_key='input', output_key="output")
    agent = initialize_agent(
        tools,
        chat_llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        return_all=True,
        agent_kwargs={
            "memory_prompts": [chat_history],
            "input_variables": ["input", "agent_scratchpad"],
        },
        return_intermediate_steps=True,
        memory=memory
    )

    return agent


def convertAgentOutputToString(sample_output: dict) -> str:
    assert isinstance(sample_output, dict)
    dict_keys = set(sample_output.keys())
    assert 'intermediate_steps' in dict_keys
    assert 'output' in dict_keys

    final_string = ""
    for action in sample_output['intermediate_steps']:
        final_string += action[0].tool + ": " + \
            action[0].tool_input + "\n" + action[0].log + \
            "\n\n" + action[1] + "\n\n"
    final_string += "Final Answer: \n\n" + sample_output['output']

    return final_string
