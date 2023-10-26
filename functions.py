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
'''
This function takes in a query (string) and returns a formatted string of five patents (including title, inventor, pdf, thumbnail) of
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
        model="image-alpha-001",
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
    num_papers = 5 # Can increase num_papers later
    index, documents = create_index(
        research_space_query.lower(), num_papers, True
    )
    sample_questions = generate_sample_questions(documents)
    chat_engine = citation_query_engine(index, 10, False, 512)
    # for key, value in index.ref_doc_info.items():
    #     open_access_pdf = value.get('openAccessPdf')
    #     title = value['metadata']['title']
    #
    #     if open_access_pdf:
    #         print(f'Title: {title}')
    #         print(f'Open Access PDF Link: {open_access_pdf}')
    #         print()
    return "Research space successfully set to: " + "\"" + research_space_query + "\"" + "!\n" + "**Questions to consider:**\n" + sample_questions + "\n**Papers in Index:**\n" + documents_to_df(documents).to_string()

def queryResearchSpace(query):
    # query the citation query engine
    response = chat_engine.query("Elaborate on " + query)
    # display_response(response, show_source=True, source_length=100, show_source_metadata=True)
    return response.response + "\n" + response.get_formatted_sources()