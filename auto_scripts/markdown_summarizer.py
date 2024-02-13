import sys

sys.path.append("../")

import requests
from bs4 import BeautifulSoup
from database_connector import get_collection
from app_secrets import GCLOUD_PROJECT
import time

# set up logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import vertexai
from vertexai.preview.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models

vertexai.init(project=GCLOUD_PROJECT)


def generate(prompt: str) -> str:
    model = GenerativeModel("gemini-pro")
    responses = model.generate_content(
        prompt,
        generation_config={"temperature": 0.9, "top_p": 1},
        safety_settings={
            generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        },
        stream=True,
    )
    retries = 0
    while retries < 3:
        try:
            return "".join([response.text for response in responses])
        except Exception as e:
            print(e)
            logger.info(f"Model failed on api call # {retries}")
            retries += 1
    return None


def get_wiki_profile(url: str) -> str:
    resp = requests.get(url).text
    soup = BeautifulSoup(resp, "html.parser")
    p_tags = soup.find_all("p")
    cleaned_p_tags = [item for item in p_tags if not item.get("class")]
    text = " ".join([item.get_text() for item in cleaned_p_tags])
    return text


def summarize_athlete_wikipedia(wiki_url: str) -> str:
    wiki_text = get_wiki_profile(wiki_url)
    system_prompt = """
        The following is the wikipedia profile of a professional track and field athlete. 

        Section 1: About 
        - This section should give details about who the athlete is 

        Section 2: Athlete Career 
        - This section should give a chronological view into the athlete's story of becoming who they are currently 
        - Section format: paragraph 

        Section 3: Top Accomplishments 
        - This section should give details about the athlete's top accomplishments 
        - Section format: bullet points 

        Section 4: Athlete Archetype 
        - Using the wikipedia profile, take some time to analyze and select which category this athlete fits into best: 
        [
            "Technical Specialists",
            "Versatile Athletes",
            "Late Bloomers",
            "Specialized Specialists",
            "Mental Masters",
            "Genetic Anomalies"
        ]
        - Section format: Concluding paragraph with analysis
        
        Please summarize this text into a raw text document formatted in markdown with the four sections above 
        Make sure to not include any backticks ``` or the word markdown
        
        Example: 
        
        ## About 
        <about_section>
        
        ## Career 
        <athlete_career_section>
        
        ## Accomplishments
        <top_accomplishments_section>
        
        ## Archetype 
        <athlete_archetype_section>
        
        <wikipedia_profile>
    """
    return generate(system_prompt + "\n\n" + wiki_text)


# get 20 documents that don't have a 'markdown_summary' key and do have a wikipedia url
# run summarize_athlete_wikipedia() for each one's wikipedia url
# insert the document as the athlete's markdown summary

collection = get_collection()

documents = collection.find(
    {"$expr": {"$and": ["$wikipedia_url", {"$not": ["$markdown_summary"]}]}}
).limit(10)

for document in documents:
    time.sleep(5)
    wikipedia_url = document["wikipedia_url"]
    markdown_summary = summarize_athlete_wikipedia(wikipedia_url)
    if markdown_summary:
        collection.update_one(
            {"_id": document["_id"]}, {"$set": {"markdown_summary": markdown_summary}}
        )
        logger.info(f"Successfully updated summary for {document['full_name']}")
    else:
        logger.warning(
            f"Failed to generate markdown summary for athlete with Wikipedia URL: {wikipedia_url}"
        )
