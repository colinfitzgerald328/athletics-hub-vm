import sys

sys.path.append("../")

from openai import OpenAI
from app_secrets import OPENAI_API_KEY, LETSRUN_COLLECTION_NAME

client = OpenAI(api_key=OPENAI_API_KEY)
import requests
from datetime import datetime
import pytz
from typing import List, Dict
from bs4 import BeautifulSoup
from tqdm import tqdm
import json
from database_connector import get_collection

# set up logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_current_date_in_pacific():
    # Set the time zone to Pacific
    pacific_tz = pytz.timezone("US/Pacific")

    # Get the current time in the Pacific time zone
    current_time_pacific = datetime.now(pacific_tz)

    # Format and return the current date
    return current_time_pacific.strftime("%Y-%m-%d")


def get_top_threads() -> List[str]:
    """
    Returns the links to the top threads currently on Letsrun
    """
    thread_links = []
    resp = requests.get("https://www.letsrun.com/").text
    soup = BeautifulSoup(resp, "html.parser")
    elements = soup.find_all("a", class_="on-the-boards-link")
    for element in elements:
        thread_links.append(element["href"])
    return thread_links


def get_thread_text(thread_link: str) -> str:
    """
    Returns the text content of a Letsrun thread
    """
    resp = requests.get(thread_link).text
    soup = BeautifulSoup(resp)
    elements = soup.find_all("div", class_="post-body")
    return "".join([element.get_text() for element in elements])


def get_thread_title(thread_link: str) -> str:
    """
    Gets the title of a thread given a link
    """
    resp = requests.get(thread_link).text
    soup = BeautifulSoup(resp)
    thread_title = soup.find_all("h1")[0].get_text()
    return thread_title


def generic_ai_service(prompt: str, json_mode: bool = False) -> str:
    """
    Generates a response from OpenAI given a prompt
    """
    params = {
        "model": "gpt-4-0125-preview",
        "messages": [{"role": "system", "content": prompt}],
    }

    if json_mode:
        params["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**params)
    return response.choices[0].message.content


def summarize_thread_text(thread_title: str, thread_text: str) -> Dict[str, str]:
    """
    Summarizes the thread text based on the thread title and the thread text
    """
    prompt = f"""
        LetsRun is a forum where running fans chat about news in the professional running world.
        You are an agent designed to summarize threads, which are forums where people chat about events
        and races.
        Please tell the reader what the thread is about.
        Here is the thread title: {thread_title}
        Here is the thread text: {thread_text}
        
        JSON output example:
        {{"thread_summary": <thread_summary>}}
    """
    return json.loads(generic_ai_service(prompt, json_mode=True))


def get_todays_summaries() -> List[Dict[str, str]]:
    """
    Final function that runs the AI service to get all of the thread summaries
    """
    thread_summaries = []
    thread_links = get_top_threads()
    for thread_link in tqdm(thread_links):
        thread_title = get_thread_title(thread_link)
        thread_text = get_thread_text(thread_link)
        result = summarize_thread_text(thread_title, thread_text)
        print(result)
        thread_summaries.append(
            {"thread_link": thread_link, "thread_summary": result["thread_summary"]}
        )
    return thread_summaries


def summarize_today_narrative(snippets: List[Dict[str, str]]) -> str:
    """
    Summarizes the thread summaries into one narrative
    """
    # cast the list of summaries into a string for the prompt
    str_snippets = str(snippets)
    prompt = f"""
        The following are snippets of text detailing the top threads in the world of track 
        and field today from a forum called Letsrun.com 
        Summarize these snippets into a .md (markdown) document.
        {str_snippets}
        
        Expected response for each thread 
        
        ## [Title for thread](<thread_link>)
        > Block quote explaining the thread - do not mention the word thread but rather summarize the content
    """
    return generic_ai_service(prompt)


def log_today_summary():
    collection = get_collection(LETSRUN_COLLECTION_NAME)
    today_summaries = get_todays_summaries()
    md_doc = summarize_today_narrative(today_summaries)
    # now insert the document
    # Create a dictionary with the document and the current date as keys
    insert_doc = {"document": md_doc, "date": get_current_date_in_pacific()}

    # Insert the document into the collection
    collection.insert_one(insert_doc)
    logger.info("SUCCESSFULLY INSERTED SUMMARY")


log_today_summary()
