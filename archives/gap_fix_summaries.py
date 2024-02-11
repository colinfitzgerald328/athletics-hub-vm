import re
import requests
import openai
from langchain.text_splitter import TokenTextSplitter
from bs4 import BeautifulSoup
from instagrapi import Client
from tqdm import tqdm
from database_connector import get_collection
from vm_secrets import DEEPINFRA_API_KEY


text_splitter = TokenTextSplitter(chunk_size=2800, chunk_overlap=0)

# Point OpenAI client to our endpoint
openai.api_key = DEEPINFRA_API_KEY
openai.api_base = "https://api.deepinfra.com/v1/openai"


settings = {
    "uuids": {
        "phone_id": "b3dd111b-ebb1-4721-bac8-99380213fed9",
        "uuid": "01da8278-98b6-427e-90ee-d9070c8479c7",
        "client_session_id": "fd6ebba3-888a-458e-8e77-a3d86322296f",
        "advertising_id": "988dc00c-7666-4c68-a8a7-4f14e0e32d6b",
        "android_device_id": "android-b82e8140929d53be",
        "request_id": "cc6cb415-1bff-4f8c-8618-cd9010cb6b7c",
        "tray_session_id": "8e6c5be2-14c9-4977-973a-c469755f5ed1",
    },
    "mid": "ZWRGJAABAAHJdzOGmS-r9osHP9SG",
    "ig_u_rur": None,
    "ig_www_claim": None,
    "authorization_data": {
        "ds_user_id": "63235896997",
        "sessionid": "63235896997%3AVZfFMqCr6m9Xdn%3A1%3AAYdSWIv2_6VnN9LH8FQ89M8gLUjMEg7_8zRLysIFZQ",
    },
    "cookies": {},
    "last_login": 1701070380.727972,
    "device_settings": {
        "app_version": "269.0.0.18.75",
        "android_version": 26,
        "android_release": "8.0.0",
        "dpi": "480dpi",
        "resolution": "1080x1920",
        "manufacturer": "OnePlus",
        "device": "devitron",
        "model": "6T Dev",
        "cpu": "qcom",
        "version_code": "314665256",
    },
    "user_agent": "Instagram 269.0.0.18.75 Android (26/8.0.0; 480dpi; 1080x1920; OnePlus; 6T Dev; devitron; qcom; en_US; 314665256)",
    "country": "US",
    "country_code": 1,
    "locale": "en_US",
    "timezone_offset": -14400,
}

cl = Client(settings)
cl.login("jhow_dusherly", "iriquois23!")


def get_ig_username(document):
    instagram_username = None
    for item in document["social_urls"]:
        if "instagram_url" in item:
            instagram_url = item["instagram_url"]
            matched_username = re.search("instagram.com\/.*", instagram_url)[0]
            instagram_username = matched_username.split("/")[1]
    return instagram_username


def get_ig_caption_text(ig_username):
    try:
        user_id = cl.user_id_from_username(ig_username)
        ig_posts_text = ""
        medias = cl.user_medias(user_id, 40)
        for media in medias:
            ig_posts_text += " " + media.caption_text
        return ig_posts_text
    except:
        return None


def get_wiki_profile(url):
    resp = requests.get(url).text
    soup = BeautifulSoup(resp, "html.parser")
    p_tags = soup.find_all("p")
    cleaned_p_tags = [item for item in p_tags if not item.get("class")]
    text = " ".join([item.get_text() for item in cleaned_p_tags])
    return text


def summarize_wikipedia(wikipedia_url):
    if not wikipedia_url:
        return None
    wiki_profile_text = get_wiki_profile(wikipedia_url)

    chunk = text_splitter.split_text(wiki_profile_text)[0]

    prompt = """
    the following is a wikipedia profile of a professional track and field athlete. 
    read through the article and come up with a list of the most important things you would want to tell someone about this athlete. 
    You should order the summary by the most recent achievements. 
    The first sentence should introduce the athlete's name and background on how they have ascended to the professional ranks. 
    Return your final response in the form of a well-written summary that you would want your teacher to read. 
    """

    # Construct the message
    message = {"role": "user", "content": prompt + "\n\n Wikipedia Profile: " + chunk}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
    }

    json_data = {
        "model": "meta-llama/Llama-2-70b-chat-hf",
        "messages": [message],
    }

    response = requests.post(
        "https://api.deepinfra.com/v1/openai/chat/completions",
        headers=headers,
        json=json_data,
    )
    return response.json()["choices"][0]["message"]["content"]


def summarize_instagram(instagram_username):
    if not instagram_username:
        return None
    ig_post_text = get_ig_caption_text(instagram_username)

    if not ig_post_text:
        return None

    chunk = text_splitter.split_text(ig_post_text)[0]

    prompt = """
    the following are a series of instagram captions for a professional track and field athlete.
    pull out the most important events and accomplishments from this information.
    your response should be in the form of a summary that could be submitted in high school. 
    The first sentence should state the athlete's name and introduce them.
    """

    # Construct the message
    message = {
        "role": "user",
        "content": prompt + "\n\n Instagram Post Captions: " + chunk,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
    }

    json_data = {
        "model": "meta-llama/Llama-2-70b-chat-hf",
        "messages": [message],
    }

    response = requests.post(
        "https://api.deepinfra.com/v1/openai/chat/completions",
        headers=headers,
        json=json_data,
    )
    return response.json()["choices"][0]["message"]["content"]


def summarize_information(wiki_url, instagram_username):
    wiki_summary = None
    instagram_summary = None
    if not wiki_url:
        return None
    if wiki_url:
        wiki_summary = summarize_wikipedia(wiki_url)
    if instagram_username:
        instagram_summary = summarize_instagram(instagram_username)

    if wiki_summary is not None and instagram_summary is not None:
        information = wiki_summary + "\n\n" + instagram_summary
    elif wiki_summary is not None:
        information = wiki_summary
    elif instagram_summary is not None:
        information = instagram_summary
    else:
        information = "No information available."

    prompt = """
    Combine the following two pieces of text into a summary explaining who the athlete is to someone in the running community.  
    """

    # Construct the message
    message = {"role": "user", "content": prompt + "\n\n Information: " + information}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
    }

    json_data = {
        "model": "meta-llama/Llama-2-70b-chat-hf",
        "messages": [message],
    }

    response = requests.post(
        "https://api.deepinfra.com/v1/openai/chat/completions",
        headers=headers,
        json=json_data,
    )
    return response.json()["choices"][0]["message"]["content"]


collection = get_collection()


documents = collection.find(
    {"$and": [{"wikipedia_url": {"$ne": None}}, {"summary": {"$eq": None}}]}
).limit(10)
for document in tqdm(documents):
    ig_username = get_ig_username(document)
    wikipedia_url = document["wikipedia_url"]
    summary = summarize_information(wikipedia_url, ig_username)
    print("got summary, now updating document")
    document["summary"] = summary
    collection.update_one({"_id": document["_id"]}, {"$set": {"summary": summary}})
