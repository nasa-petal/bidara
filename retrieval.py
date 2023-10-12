from langchain.chains import SequentialChain, TransformChain, LLMChain
from langchain import OpenAI, LLMChain
from langchain.prompts import PromptTemplate
import re
import requests
import json
from langchain.chat_models import ChatOpenAI
from decouple import config
import requests
import openai

'''
Initialize SemanticScholar API Key and OpenAI model 
'''
OPEN_API_KEY = config('OPENAI_API_KEY')
llm = ChatOpenAI(model='gpt-4', temperature=0, openai_api_key=OPEN_API_KEY)
SEMANTIC_SCHOLAR_API_KEY = config('SEMANTIC_SCHOLAR_API_KEY')


'''
Takes two arguments as input: (1) The query to search Semantic Scholar and (2) The number of papers to retrieve.
Some of the retrieved papers do not have abstracts, so we combat this by retrieving 5 times as many papers as requested, but stopping once we've reached the requested amount.

Returns a string that concatenates the title, authors, paper URL, and abstract for each paper
'''


def SemanticScholarSearch(query: str, number_of_papers_to_retrieve: int) -> str:
    URLtoGET = f'https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit={5*number_of_papers_to_retrieve}&fields=abstract,authors,title,url'

    headers = {
        'Content-type': 'application/json',
        'x-api-key': SEMANTIC_SCHOLAR_API_KEY
    }
    GETresult = requests.get(URLtoGET, headers=headers)
    json_GETresult = json.loads(GETresult.text)

    if 'code' in json_GETresult and json_GETresult['code'] == '429':
        raise ValueError(
            "You have been rate-limited by Semantic Scholar. Please wait and try again or apply for a key for higher rate limits. https://www.semanticscholar.org/product/api#api-key-form")
    elif json_GETresult['total'] == 0:
        return ("No papers found. Only generate a search query without any unnecessary words. \n")

    all_papers = ""

    for paper in json_GETresult['data']:
        # if we've retrieved the amount of papers specified
        if number_of_papers_to_retrieve == 0:
            break
        # if no abstract
        if not paper["abstract"]:
            continue
        number_of_papers_to_retrieve -= 1
        all_papers += f"{paper['title']} by {', '.join([x['name'] for x in paper['authors']])}. {paper['url']} \n Abstract: \n {paper['abstract']}"

    all_papers += "\n"

    return all_papers


'''
Extracts search query from Biologize/Action/Search and search it on Semantic Scholar

chainOutput1 = {'biologize_action' : 
            "Biologize 4 Lorem ipsum..
            Action 4 Search['XYZ'] "}

searchQueryExecutor(chainOutput1) -> SemanticScholarSearch("XYZ", 1) -> <Paper1Title> by <Paper1Authors>. <Paper1 URL>. Abstract: <Paper1Abstract> 

'''


def searchQueryExecutor(inputs: dict) -> dict:
    search_query_output = re.findall(
        r"Search\[\+?(-?.+)\s*\]", inputs['biologize_action'])[0]
    response = SemanticScholarSearch(search_query_output, 2)

    return {'biologize_abstract_retrieved_paper': inputs['biologize_action'] + "\n" + response}


'''
Initializes a LangChain SequentialChain instance
'''


def intializeChain() -> SequentialChain:
    prompt_biologize = PromptTemplate(
        input_variables=['question'],
        template=""" \
            Question: How can we design the nose of an airplane to manage impact? \n\
            Biologize: The essential function we need to address is managing impact. In biological terms, we can ask, "How does nature absorb and distribute impact forces?" Specifically, we can look at the Toco Toucan, which has a large beak that can withstand significant forces without breaking. So, our biologized question becomes, "How does the Toco Toucan's beak manage impact?" \n\
            Action: Search[Toucan’s beak] \n\
            Retrieval: “Structure and mechanical behavior of a toucan beak” by Yasuaki Seki, Matthew S. Schneider, Marc A. Meyers. https://doi.org/10.1016/j.actamat.2005.04.048 \n\

            Abstract: \n\

            The toucan beak, which comprises one third of the length of the bird and yet only about 1/20th of its mass, has outstanding stiffness. The structure of a Toco toucan (Ramphastos toco) beak was found to be a sandwich composite with an exterior of keratin and a fibrous network of closed cells made of calcium-rich proteins. The keratin layer is comprised of superposed hexagonal scales (50 μm diameter and 1 μm thickness) glued together. Its tensile strength is about 50 MPa and Young’s modulus is 1.4 GPa. Micro and nanoindentation hardness measurements corroborate these values. The keratin shell exhibits a strain-rate sensitivity with a transition from slippage of the scales due to release of the organic glue, at a low strain rate (5 × 10−5/s) to fracture of the scales at a higher strain rate (1.5 × 10−3/s). The closed-cell foam is comprised of fibers having a Young’s modulus twice as high as the keratin shells due to their higher calcium content. The compressive response of the foam was modeled by the Gibson–Ashby constitutive equations for open and closed-cell foam. There is a synergistic effect between foam and shell evidenced by experiments and analysis establishing the separate responses of shell, foam, and foam + shell. The stability analysis developed by Karam and Gibson, assuming an idealized circular cross section, was applied to the beak. It shows that the foam stabilizes the deformation of the beak by providing an elastic foundation which increases its Brazier and buckling load under flexure loading. \n\
            Discover: The Toco Toucan's beak is a marvel of natural engineering. Despite its size, it is incredibly lightweight and strong. The beak's structure is composed of a foamy keratin material, reinforced with a network of bony fibers and drum-like membranes. This structure allows the beak to absorb and distribute impact forces effectively, reducing the force that reaches the bird's body. \n\
            Abstract: The essential feature that makes the Toco Toucan's beak successful in managing impact is its unique structure: a lightweight, foamy material reinforced with a network of fibers and membranes. In design terms, we can describe this strategy as follows: "A lightweight, porous material is reinforced with a network of fibers and membranes to absorb and distribute impact forces, reducing the force transmitted to the inner structure." \n\
            Answer: The nose of the airplane could be designed to mimic the structure of the Toco Toucan's beak. This would involve creating a lightweight yet strong material that can absorb impact effectively. The material could be structured in a similar way to the beak, with a network of fibers for added strength and flexibility. This design could potentially improve the safety and efficiency of air travel by better managing impact forces. \n\

            Question: How can we design a submarine to manage compression? \n\
            Biologize: The essential function we need to address is managing compression. In biological terms, we can ask, "How does nature resist and distribute compressive forces?" Specifically, we can look at the sea urchin, which has a shell that can withstand significant pressure without breaking. So, our biologized question becomes, "How does a sea urchin's shell manage compression?" \n\
            Action: Search[Sea Urchin Shell] \n\
            Retrieval: “Microstructure and micromechanics of the heart urchin test from X-ray tomography” by D. Müter, H.O. Sørensen, J. Oddershede, K.N. Dalby, S.L.S. Stipp. \n\
            https://doi.org/10.1016/j.actbio.2015.05.007 \n\

            Abstract: \n\

            The microstructure of many echinoid species has long fascinated scientists because of its high porosity and outstanding mechanical properties. We have used X-ray microtomography to examine the test of Echinocardium cordatum (heart urchin), a burrowing cousin of the more commonly known sea urchins. Three dimensional imaging demonstrates that the bulk of the test is composed of only two distinct, highly porous, fenestrated regions (stereom), in which the thickness of the struts is constant. Different degrees of porosity are achieved by varying the spacing of the struts. Drawing an analogy to vertebrate trabecular bone, where for example, human bone has a connectivity density of ≈1/mm3, we measure up to 150,000 strut connections per mm3. Simulations of mechanical loading using finite element calculations indicate that the test performs at very close to the optimum expected for foams, highlighting the functional link between structure and mechanical properties. \n\
            Discover: The sea urchin's shell, or test, is a marvel of natural engineering. It is composed of numerous calcite plates arranged in a complex, geometric pattern. This structure, known as stereom, allows the shell to distribute pressure evenly across its surface, effectively resisting compression. The shell is also able to repair itself if damaged, further enhancing its durability \n\
            Abstract: The essential feature that makes the sea urchin's shell successful in managing compression is its unique structure: a complex, geometric pattern of calcite plates that distribute pressure evenly. In design terms, we can describe this strategy as follows: "A structure composed of numerous small, interlocking elements arranged in a complex pattern to distribute compressive forces evenly across the surface, enhancing resistance to compression." \n\
            Answer: The hull of the submarine could be designed to mimic the structure of the sea urchin's shell. This would involve creating a complex, geometric pattern of interlocking elements that can distribute pressure evenly, effectively resisting compression. This design could potentially improve the safety and efficiency of submarine travel by better managing compressive forces. \n\

            Question: How can I design a car engine that keeps cool? \n\
            Biologize: The essential function we need to address is cooling. In biological terms, we can ask, "How does nature regulate temperature?" Specifically, we can look at the Apis mellifera, or honeybee, which has a unique way of cooling their hives. So, our biologized question becomes, "How does Apis mellifera manage temperature regulation?" \n\
            Action: Search[Apis mellifera manage temperature regulation] \n\
            Retrieval: “Water homeostasis in bees, with the emphasis on sociality” by Susan W. Nicolson. https://journals.biologists.com/jeb/article/212/3/429/9597/Water-homeostasis-in-bees-with-the-emphasis-on \n\

            Abstract: \n\

            Avenues of water gain and loss in bees are examined here at two levels of organisation: the individual and the colony. Compared with the majority of terrestrial insects, bees have a high water turnover. This is due to their nectar diet and, in larger species, substantial metabolic water production during flight, counteracted by high evaporative and excretory losses. Water fluxes at the colony level can also be very high. When incoming nectar is dilute, honeybees need to remove large volumes of water by evaporation. On the other hand, water is not stored in the nest and must be collected for evaporative cooling and for feeding the brood. Water regulation has many similarities at individual and colony levels. In particular, manipulation of nectar or water on the tongue is extensively used by bees to increase evaporation for either food-concentrating or cooling purposes. \n\
            Discover: Honeybees use a collective cooling technique to regulate the temperature of their hive. When the temperature inside the hive becomes too high, worker bees collect water and distribute it throughout the hive. Other bees then fan their wings to evaporate the water, which cools the hive. This is a form of evaporative cooling, similar to sweating in humans \n\
            Abstract: The essential feature that makes the honeybee's temperature regulation successful is its use of evaporative cooling. In design terms, we can describe this strategy as follows: "A system uses a liquid (like water) distributed throughout its structure, and a method to promote evaporation, to cool the entire system." \n\
            Answer: The car engine could be designed to mimic the honeybee's evaporative cooling technique. This could involve a system where a coolant is distributed throughout the engine. A mechanism (like a fan) could then promote evaporation, cooling the engine. This design could potentially improve the efficiency of car engines by better managing heat. \n\
            
            Question: {question} \
            
            Only generate the Biologize and Action \
            """
    )

    prompt_discoverAbstractAnswer = PromptTemplate(
        input_variables=['biologize_abstract_retrieved_paper'],
        template=""" \
            Question: How can we design the nose of an airplane to manage impact? \n\
            Biologize: The essential function we need to address is managing impact. In biological terms, we can ask, "How does nature absorb and distribute impact forces?" Specifically, we can look at the Toco Toucan, which has a large beak that can withstand significant forces without breaking. So, our biologized question becomes, "How does the Toco Toucan's beak manage impact?" \n\
            Action: Search[Toucan’s beak] \n\
            Retrieval: “Structure and mechanical behavior of a toucan beak” by Yasuaki Seki, Matthew S. Schneider, Marc A. Meyers. https://doi.org/10.1016/j.actamat.2005.04.048 \n\

            Abstract: \n\

            The toucan beak, which comprises one third of the length of the bird and yet only about 1/20th of its mass, has outstanding stiffness. The structure of a Toco toucan (Ramphastos toco) beak was found to be a sandwich composite with an exterior of keratin and a fibrous network of closed cells made of calcium-rich proteins. The keratin layer is comprised of superposed hexagonal scales (50 μm diameter and 1 μm thickness) glued together. Its tensile strength is about 50 MPa and Young’s modulus is 1.4 GPa. Micro and nanoindentation hardness measurements corroborate these values. The keratin shell exhibits a strain-rate sensitivity with a transition from slippage of the scales due to release of the organic glue, at a low strain rate (5 × 10−5/s) to fracture of the scales at a higher strain rate (1.5 × 10−3/s). The closed-cell foam is comprised of fibers having a Young’s modulus twice as high as the keratin shells due to their higher calcium content. The compressive response of the foam was modeled by the Gibson–Ashby constitutive equations for open and closed-cell foam. There is a synergistic effect between foam and shell evidenced by experiments and analysis establishing the separate responses of shell, foam, and foam + shell. The stability analysis developed by Karam and Gibson, assuming an idealized circular cross section, was applied to the beak. It shows that the foam stabilizes the deformation of the beak by providing an elastic foundation which increases its Brazier and buckling load under flexure loading. \n\
            Discover: The Toco Toucan's beak is a marvel of natural engineering. Despite its size, it is incredibly lightweight and strong. The beak's structure is composed of a foamy keratin material, reinforced with a network of bony fibers and drum-like membranes. This structure allows the beak to absorb and distribute impact forces effectively, reducing the force that reaches the bird's body. \n\
            Abstract: The essential feature that makes the Toco Toucan's beak successful in managing impact is its unique structure: a lightweight, foamy material reinforced with a network of fibers and membranes. In design terms, we can describe this strategy as follows: "A lightweight, porous material is reinforced with a network of fibers and membranes to absorb and distribute impact forces, reducing the force transmitted to the inner structure." \n\
            Answer: The nose of the airplane could be designed to mimic the structure of the Toco Toucan's beak. This would involve creating a lightweight yet strong material that can absorb impact effectively. The material could be structured in a similar way to the beak, with a network of fibers for added strength and flexibility. This design could potentially improve the safety and efficiency of air travel by better managing impact forces. \n\

            Question: How can we design a submarine to manage compression? \n\
            Biologize: The essential function we need to address is managing compression. In biological terms, we can ask, "How does nature resist and distribute compressive forces?" Specifically, we can look at the sea urchin, which has a shell that can withstand significant pressure without breaking. So, our biologized question becomes, "How does a sea urchin's shell manage compression?" \n\
            Action: Search[Sea Urchin Shell] \n\
            Retrieval: “Microstructure and micromechanics of the heart urchin test from X-ray tomography” by D. Müter, H.O. Sørensen, J. Oddershede, K.N. Dalby, S.L.S. Stipp. \n\
            https://doi.org/10.1016/j.actbio.2015.05.007 \n\

            Abstract: \n\

            The microstructure of many echinoid species has long fascinated scientists because of its high porosity and outstanding mechanical properties. We have used X-ray microtomography to examine the test of Echinocardium cordatum (heart urchin), a burrowing cousin of the more commonly known sea urchins. Three dimensional imaging demonstrates that the bulk of the test is composed of only two distinct, highly porous, fenestrated regions (stereom), in which the thickness of the struts is constant. Different degrees of porosity are achieved by varying the spacing of the struts. Drawing an analogy to vertebrate trabecular bone, where for example, human bone has a connectivity density of ≈1/mm3, we measure up to 150,000 strut connections per mm3. Simulations of mechanical loading using finite element calculations indicate that the test performs at very close to the optimum expected for foams, highlighting the functional link between structure and mechanical properties. \n\
            Discover: The sea urchin's shell, or test, is a marvel of natural engineering. It is composed of numerous calcite plates arranged in a complex, geometric pattern. This structure, known as stereom, allows the shell to distribute pressure evenly across its surface, effectively resisting compression. The shell is also able to repair itself if damaged, further enhancing its durability \n\
            Abstract: The essential feature that makes the sea urchin's shell successful in managing compression is its unique structure: a complex, geometric pattern of calcite plates that distribute pressure evenly. In design terms, we can describe this strategy as follows: "A structure composed of numerous small, interlocking elements arranged in a complex pattern to distribute compressive forces evenly across the surface, enhancing resistance to compression." \n\
            Answer: The hull of the submarine could be designed to mimic the structure of the sea urchin's shell. This would involve creating a complex, geometric pattern of interlocking elements that can distribute pressure evenly, effectively resisting compression. This design could potentially improve the safety and efficiency of submarine travel by better managing compressive forces. \n\

            Question: How can I design a car engine that keeps cool? \n\
            Biologize: The essential function we need to address is cooling. In biological terms, we can ask, "How does nature regulate temperature?" Specifically, we can look at the Apis mellifera, or honeybee, which has a unique way of cooling their hives. So, our biologized question becomes, "How does Apis mellifera manage temperature regulation?" \n\
            Action: Search[Apis mellifera manage temperature regulation] \n\
            Retrieval: “Water homeostasis in bees, with the emphasis on sociality” by Susan W. Nicolson. https://journals.biologists.com/jeb/article/212/3/429/9597/Water-homeostasis-in-bees-with-the-emphasis-on \n\

            Abstract: \n\

            Avenues of water gain and loss in bees are examined here at two levels of organisation: the individual and the colony. Compared with the majority of terrestrial insects, bees have a high water turnover. This is due to their nectar diet and, in larger species, substantial metabolic water production during flight, counteracted by high evaporative and excretory losses. Water fluxes at the colony level can also be very high. When incoming nectar is dilute, honeybees need to remove large volumes of water by evaporation. On the other hand, water is not stored in the nest and must be collected for evaporative cooling and for feeding the brood. Water regulation has many similarities at individual and colony levels. In particular, manipulation of nectar or water on the tongue is extensively used by bees to increase evaporation for either food-concentrating or cooling purposes. \n\
            Discover: Honeybees use a collective cooling technique to regulate the temperature of their hive. When the temperature inside the hive becomes too high, worker bees collect water and distribute it throughout the hive. Other bees then fan their wings to evaporate the water, which cools the hive. This is a form of evaporative cooling, similar to sweating in humans \n\
            Abstract: The essential feature that makes the honeybee's temperature regulation successful is its use of evaporative cooling. In design terms, we can describe this strategy as follows: "A system uses a liquid (like water) distributed throughout its structure, and a method to promote evaporation, to cool the entire system." \n\
            Answer: The car engine could be designed to mimic the honeybee's evaporative cooling technique. This could involve a system where a coolant is distributed throughout the engine. A mechanism (like a fan) could then promote evaporation, cooling the engine. This design could potentially improve the efficiency of car engines by better managing heat. \n\
            
            Question: {biologize_abstract_retrieved_paper}
        """
    )

    chain_biologizeAction = LLMChain(
        llm=llm, prompt=prompt_biologize, output_key='biologize_action')
    chain_retriever = TransformChain(
        input_variables=["biologize_action"], output_variables=["biologize_abstract_retrieved_paper"], transform=searchQueryExecutor
    )
    chain_discoverAbstractAnswer = LLMChain(
        llm=llm, prompt=prompt_discoverAbstractAnswer, output_key='discover_abstract_answer')

    overall_chain = SequentialChain(chains=[chain_biologizeAction, chain_retriever, chain_discoverAbstractAnswer],
                                    input_variables=['question'],
                                    verbose=True,
                                    return_all=True)

    return overall_chain
