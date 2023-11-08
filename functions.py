import openai
from decouple import config
from retrieval import SemanticScholarSearch
from serpapi import GoogleSearch
from utils import (
    create_index,
    citation_query_engine,
    generate_sample_questions,
    documents_to_df,
)
# Now using Llama 2 for research paper shenanigans
chat_engine = None
research_space_dict = {} # Dictionary to keep track of users and their research spaces
# cur_step = None

function_descriptions = [ # Self-explanatory functions for OpenAI function calling.
            {
                "name": "paperSearch",
                "description": "Retrieve papers with information from journal articles.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Query for an academic database.",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "setResearchSpace",
                "description": "Only call this function when the user says 'Set research space to...' Creates a query engine the user can ask specific research questions with regard to papers in a research space.\
                               Run this before queryResearchSpace(). Return the sources in the research space with corresponding links and list of broad suggested questions to the user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "research_space_query": {
                            "type": "string",
                            "description": "Description of an overarching research space (i.e. 'bias in large language models,' 'biomimicry for aerospace,' etc.).",
                        },
                    },
                    "required": ["research_space_query"],
                },
            },
            {
                "name": "queryResearchSpace",
                "description": "With regards to a specific research space (created by running setResearchSpace()) first), ask a specific question. Returns the answer according to the sources in the space.\
                               If the answer to the question is not directly provided, tell the user that the research space does not contain that information. Remember to cite your sources!",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Query for the citation query engine.",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "generateImage",
                "description": "Generate an image URL given a prompt. When linking the image, do not include the '!' before the markdown [Description](Link).", # The additional instruction does not work
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Description of image to generate.", # Try to highlight the biomimetic features of the animal in the prompt.
                        },
                    },
                    "required": ["prompt"],
                },
            },
        {
            "name": "patentSearch",
            "description": "Retrieves the top patent results and their links/thumbnails from Google Patents with a given query. Return this answer to the user verbatim.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query for the patent search engine",
                    },
                },
                "required": ["query"],
            },
        },
    #     {
    #         "name": "setStep",
    #         "description": "Set step state variable to one of define, biologize, discover, abstract, or emulate. Call this function while executing the associated step only if you are BIDARA.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "step": {
    #                     "type": "string",
    #                     "description": "One of define, biologize, discover, abstract, or emulate (all lowercase).",
    #                 },
    #             },
    #             "required": ["query"],
    #         }
    # }
        ]

# def setStep(step):
#     cur_step = step

'''
This function takes in a query (string) and returns a formatted string of patents (including title, inventor, pdf, thumbnail) of
the top results from Google Patents for that query.
'''
def patentSearch(query):
    params = {
        "engine": "google_patents",
        "q": query,
        "api_key": config('SERP_API_KEY')
    }

    search = GoogleSearch(params)
    res = search.get_dict()
    ans = ""
    for i in range(5):
        ans += "**" + res["organic_results"][i]["title"] + "**\n"
        ans += res["organic_results"][i]["inventor"] + "\n"
        ans += res["organic_results"][i]["pdf"] + "\n"
        ans += res["organic_results"][i]["thumbnail"] + "\n\n"
    return ans

'''
This function is a wrapper that uses the Semantic Scholar API to find and return a list of two papers related to the query.
May remove because redundant.
'''
def paperSearch(query):
    return SemanticScholarSearch(query, 2)

'''
This function takes in a prompt (string) and returns the URL (string) to an image generated by Dall-E 2.
'''
def generateImage(prompt):
    # Generate an image
    response = openai.Image.create(
        prompt=prompt,
        size="512x512",
        response_format="url"
    )

    # Print the URL of the generated image
    # with open('res.txt', 'w') as f:
    #     f.write(response["data"][0]["url"])
    return response["data"][0]["url"]

'''
This function takes in a description of a research space (string, "bias in large language models," "penguins," etc.) and creates a query engine
the user can ask more specific research questions to. Returns a string informing that research space is set and list of sample questions to ask on success
'''
def setResearchSpace(research_space_query):
    global chat_engine
    num_papers = 5 # Can change this value (number of papers in research space)
    index, documents = create_index(
        research_space_query.lower(), num_papers, True
    )
    sample_questions = generate_sample_questions(documents)

    for key in research_space_dict:
        if research_space_dict[key] == ["citation_" + research_space_query.lower().replace(" ", "_") + "_5_full_text_True"]:
            for doc in documents:
                research_space_dict[key].append(doc.metadata["paperId"])
    chat_engine = citation_query_engine(index, 10, False, 512)
    # print(documents_to_df(documents).to_string())
    # for key, value in index.ref_doc_info.items():
    #     open_access_pdf = value.get('openAccessPdf')
    #     title = value['metadata']['title']
    #     # authors = value['metadata']['authors']
    #     if open_access_pdf:
    #         print(f'Title: {title}')
    #         print(f'Open Access PDF Link: {open_access_pdf}')
    #         # print(f'Authors: {authors}')
    return "Research space successfully set to: " + "\"" + research_space_query + "\"" + "!\n" + "**Questions to consider:**\n" + sample_questions + "\n**Papers in Index:**\n" + documents_to_df(documents).to_string()

def queryResearchSpace(query):
    # query the citation query engine
    response = chat_engine.query("Elaborate on " + query)
    # display_response(response, show_source=True, source_length=100, show_source_metadata=True)
    return response.response + "\n" + response.get_formatted_sources()