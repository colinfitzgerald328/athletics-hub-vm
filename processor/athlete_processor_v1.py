import sys

sys.path.append("../")

from top_competitors_specific import get_top_competitors
from personal_bests_specific import get_pbs_for_athlete
from accolades_specific import get_accomplishments
from typing import Dict, List, Any
from langchain.text_splitter import TokenTextSplitter
import requests
from bs4 import BeautifulSoup
import random
import time
import re
import pandas as pd
import openai
from instagram_util import login_user
from Meta.database_connector import get_collection
from Meta.app_secrets import DEEPINFRA_API_KEY

# set up logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

text_splitter = TokenTextSplitter(chunk_size=2800, chunk_overlap=0)

# Point OpenAI client to our endpoint
openai.api_key = DEEPINFRA_API_KEY
openai.api_base = "https://api.deepinfra.com/v1/openai"


# log in to instagram
cl = login_user()


collection = get_collection()


def query_athlete(athlete_name: str) -> Dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Sec-Fetch-Site": "cross-site",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Mode": "cors",
        # 'Accept-Encoding': 'gzip, deflate, br',
        "Origin": "https://worldathletics.org",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
        "Referer": "https://worldathletics.org/",
        # 'Content-Length': '513',
        "Connection": "keep-alive",
        "Host": "huqzljuggnfmdg3kvub37yr5oq.appsync-api.eu-west-1.amazonaws.com",
        "Sec-Fetch-Dest": "empty",
        "x-amz-user-agent": "aws-amplify/3.0.2",
        "x-api-key": "da2-u4xjcnzgxzfqvist6643w75dte",
    }

    json_data = {
        "operationName": "SearchCompetitors",
        "variables": {
            "query": athlete_name,
        },
        "query": "query SearchCompetitors($query: String, $gender: GenderType, $disciplineCode: String, $environment: String, $countryCode: String) {\n  searchCompetitors(query: $query, gender: $gender, disciplineCode: $disciplineCode, environment: $environment, countryCode: $countryCode) {\n    aaAthleteId\n    familyName\n    givenName\n    birthDate\n    disciplines\n    iaafId\n    gender\n    country\n    urlSlug\n    __typename\n  }\n}\n",
    }

    response = requests.post(
        "https://huqzljuggnfmdg3kvub37yr5oq.appsync-api.eu-west-1.amazonaws.com/graphql",
        headers=headers,
        json=json_data,
    )
    results = response.json()["data"]["searchCompetitors"]
    if not results:
        raise Exception("no search results for given query")
    return results["data"]["searchCompetitors"][0]


def get_image_for_athlete(athlete_name_with_country_code: str) -> str:
    results = []
    # Define the base URL
    base_url = "https://www.google.com/search"

    # Define the parameters as a dictionary
    params = {
        "q": athlete_name_with_country_code,
        "sca_esv": "573990738",
        "hl": "en",
        "tbm": "isch",
        "sxsrf": "AM9HkKmPxuxMcAEmXGJ5H8FGXQ1f7nO0tQ:1697511631623",
        "source": "hp",
        "ei": "z_gtZe_lI9vb7_UPk6-5qAg",
        "iflsig": "AO6bgOgAAAAAZS4G3zDCpB0g-qcFKcXTCJGeoi-sFWh6",
    }
    try:
        # Send an HTTP GET request to the URL
        response = requests.get(base_url, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.text, "html.parser")

            # Find all <img> tags
            images = soup.find_all("img")

            # Extract and print the src attribute of each image
            for img in images:
                src = img.get("src")
                if "https" in src:
                    results.append(src)
        else:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    else:
        results[0] if results else None


def get_socials(name: str) -> List[Dict[str, str]]:
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Sec-Fetch-Site": "same-origin",
        # 'Accept-Encoding': 'gzip, deflate, br',
        "Host": "www.google.com",
        "Sec-Fetch-Mode": "navigate",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
        "Connection": "keep-alive",
        "Referer": "https://www.google.com/",
        # 'Cookie': 'SIDCC=ACA-OxP3pTJT2TdDDHXUhFv3XvKGWo6-v8KkOWg6x3wP6BS_I7yyM0rxk-iwptHdjkGc0_fJIQ; __Secure-1PSIDCC=ACA-OxMlKorvs3oH-MqTW-qg0uCXr_QYZnn8CiV1nA5avv_RG3ieruERoEK3ihXJxyoEHYAZnQ; __Secure-3PSIDCC=ACA-OxMl6cZu9KdmYQxqHqnT0OGKYAaBhJ3zF5Ddm-mnYqdzLGEYatqaNnvIB75XzjwEiHCfKA; 1P_JAR=2023-11-25-19; UULE=a+cm9sZTogMQpwcm9kdWNlcjogMTIKdGltZXN0YW1wOiA3MjI2MzIzNzcyNTUwMDAKbGF0bG5nIHsKICBsYXRpdHVkZV9lNzogMzQyMjUzMzQwCiAgbG9uZ2l0dWRlX2U3OiAtMTE4MjI5MDAxMQp9CnJhZGl1czogMjE3MDAKcHJvdmVuYW5jZTogNgo=; DV=E-zDIf1EC1xbUOIrRFLHLR_4BWN-wNic_rsTMeXkTQAAAGCRZ-SOcitl5AAAAEyZsAiQ3R8qUAAAAJvupkyUQcBsFgAAAA; __Secure-1PSIDTS=sidts-CjIBNiGH7qbi5cgTqMeEYZ-bj6FwCvdg88HLsZXJi1-7Zb62b6mYbXGFDRFKEfl_Q5oWyBAA; __Secure-3PSIDTS=sidts-CjIBNiGH7qbi5cgTqMeEYZ-bj6FwCvdg88HLsZXJi1-7Zb62b6mYbXGFDRFKEfl_Q5oWyBAA; NID=511=sTNyZkuDiTiuZlXEx4-VyTNnFir07uPes9MjRtka8HSVeC7fFkRDeCS_TcYskKKHCwxdl2-KpPtA-htWaW7cYsI-aE_PropKZb7AduHb8g_DQfX9CkcTqIQqr4q8w_5kg7iYmTnP4mPvbnsfUu0U0lLJQw30r2DlypyvDPhiWGMYBS_s3ry3LQPOYNCKGSegFGTsZKS0YWzm87gJnNOhb7FQ169JI5Unasd_9C7CShOjU8oA9GQ2Y_rv84pq69TuBVGEGpZa_FTAKKREYERfWo5bcF8yRZx7YWTm1qoWQInzRKvOM29lOh61jjZsEFznPepoTlzErSopnUCtlndL5aV4SyarxXJ781-Mvi3hKXjkVmhnXTzJ0X0EKnl7XMbjpoSLPFU9xWL22ylEbrBNZs_AULK1df81UF_gu536qTNGvSmMvRdVS7Ei8XYjsnIfMyRNv0ihoqe__xFT0DPV8em-H_OUSXfTgl3fjHM2WLjEHmfF4hoYpTl5rp5-7xWa5tQ_6imBF1RTGjniimvBcQwXn8KmihfM6rx5kN0mpStFV9Bek6xF0oejGSPIw-lNIydi_H6waGDP8VF-ikiXtj5WAG-B_LBQXdJNLqeSdHbI6-EQ5VguG9WWJoT2EozsJ_YubJcp_vDjzwD5wLscm5yTgRDF3jhJF_FSGjpJUAco_NyhqzzZ5HeOk6kQASyGa-xDNTrcSFHpuDBMvCyviJ7yri_IMW6fsMEdC6lVihQ0YMrxrqKtxhxnfeNYs0rdb9955JbJkCUdXI4siY87fyUmRDl0NISwjqW2owT6LbhP9fVBb0y44RV6cAQKdMYpv2K-HA31kXNrYLY3eX7Z_Mjp8HHZsx7sa7LkeD0Y7QJ4qrbJNtiQtPjc-EHJkkJcvS7HopmM9Uoy5CH7erU; AEC=Ackid1SziBr34yx8m6r9gqDsp3OnUQOZRll8vVsWrNBAfQXPvHE61HnBxw; APISID=HNwMPcB7VpBZALwT/AMvGhFHaAsv3NE07i; HSID=A1D_X0Yp5keA7RtbZ; SAPISID=UqpHytrt1wOx4PZE/AglzGSzHzsgovZoGy; SID=dQjp6zQ2LbLsUxknsUizA8CDRUBONuIaeQeORVbQTBFSuAxcFqrWvEIKyXpxjPIn2-4-Cw.; SSID=ASNJgeelUk4UkoasU; __Secure-1PAPISID=UqpHytrt1wOx4PZE/AglzGSzHzsgovZoGy; __Secure-1PSID=dQjp6zQ2LbLsUxknsUizA8CDRUBONuIaeQeORVbQTBFSuAxcRI6TaS4O3LkColjYqRyIqQ.; __Secure-3PAPISID=UqpHytrt1wOx4PZE/AglzGSzHzsgovZoGy; __Secure-3PSID=dQjp6zQ2LbLsUxknsUizA8CDRUBONuIaeQeORVbQTBFSuAxcEBTCMCTLaLHOZ6gXX3Eguw.; OTZ=7295056_88_88_104280_84_446940; OGPC=19037049-1:19030388-1:19030390-1:19039026-1:19038986-1:19031986-1:; SEARCH_SAMESITE=CgQI25kB',
        "Sec-Fetch-Dest": "document",
        "Priority": "u=0, i",
    }

    params = {
        "q": name + " track and field",
        "client": "safari",
        "sca_esv": "732430080e01cdcb",
        "sxsrf": "AM9HkKnx4XkPmL66imEY5yvu0NP1Cscw5A:1700939572237",
        "source": "hp",
        "ei": "NEdiZeKNDJyFwbkP-I2H8AQ",
        "iflsig": "AO6bgOgAAAAAZWJVRKXTKkXK8kxSOXvHTgiaVTjcs7-j",
        "ved": "0ahUKEwji9_DX7d-CAxWcQjABHfjGAU4Q4dUDCAs",
        "uact": "5",
        "gs_lp": "Egdnd3Mtd2l6Igtqb2Uga2xlY2tlcjIKEC4YgAQYigUYJzIEECMYJzIKECMYgAQYigUYJzIFEAAYgAQyBRAAGIAEMgUQABiABDIFEAAYgAQyBRAAGIAEMgUQABiABDIKEAAYgAQYigUYQ0jtSlCiBFjjEHAMeACQAQCYAXmgAXmqAQMwLjG4AQPIAQD4AQGoAgrCAgcQIxjqAhgnwgIKEC4YgAQYigUYQ8ICDhAuGIAEGIoFGLEDGIMBwgIKEC4YgAQYFBiHAsICDRAuGIAEGBQYhwIYsQPCAgUQLhiABMICCxAuGIAEGLEDGIMBwgIIEC4YgAQYsQPCAhEQLhiABBiKBRixAxiDARjUAsICCBAuGLEDGIAEwgIKEC4YFBiHAhiABMICDRAuGIAEGLEDGIMBGAo",
        "sclient": "gws-wiz",
    }
    response = requests.get(
        "https://www.google.com/search", params=params, headers=headers
    )
    soup = BeautifulSoup(response.text, "html.parser")
    social_links = []
    items = soup.find_all("g-link", class_="fl w23JUc")
    for item in items:
        a_tag = item.find_all("a")
        social_link = a_tag[0]["href"]
        if "instagram" in social_link:
            social_links.append({"instagram_url": social_link})
        elif "twitter" in social_link:
            social_links.append({"twitter_url": social_link})
        elif "facebook" in social_link:
            social_links.append({"facebook_url": social_link})
    return social_links


def get_wiki(name: str) -> str:
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Sec-Fetch-Site": "same-origin",
        # 'Accept-Encoding': 'gzip, deflate, br',
        "Host": "www.google.com",
        "Sec-Fetch-Mode": "navigate",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
        "Connection": "keep-alive",
        "Referer": "https://www.google.com/",
        # 'Cookie': 'SIDCC=ACA-OxP3pTJT2TdDDHXUhFv3XvKGWo6-v8KkOWg6x3wP6BS_I7yyM0rxk-iwptHdjkGc0_fJIQ; __Secure-1PSIDCC=ACA-OxMlKorvs3oH-MqTW-qg0uCXr_QYZnn8CiV1nA5avv_RG3ieruERoEK3ihXJxyoEHYAZnQ; __Secure-3PSIDCC=ACA-OxMl6cZu9KdmYQxqHqnT0OGKYAaBhJ3zF5Ddm-mnYqdzLGEYatqaNnvIB75XzjwEiHCfKA; 1P_JAR=2023-11-25-19; UULE=a+cm9sZTogMQpwcm9kdWNlcjogMTIKdGltZXN0YW1wOiA3MjI2MzIzNzcyNTUwMDAKbGF0bG5nIHsKICBsYXRpdHVkZV9lNzogMzQyMjUzMzQwCiAgbG9uZ2l0dWRlX2U3OiAtMTE4MjI5MDAxMQp9CnJhZGl1czogMjE3MDAKcHJvdmVuYW5jZTogNgo=; DV=E-zDIf1EC1xbUOIrRFLHLR_4BWN-wNic_rsTMeXkTQAAAGCRZ-SOcitl5AAAAEyZsAiQ3R8qUAAAAJvupkyUQcBsFgAAAA; __Secure-1PSIDTS=sidts-CjIBNiGH7qbi5cgTqMeEYZ-bj6FwCvdg88HLsZXJi1-7Zb62b6mYbXGFDRFKEfl_Q5oWyBAA; __Secure-3PSIDTS=sidts-CjIBNiGH7qbi5cgTqMeEYZ-bj6FwCvdg88HLsZXJi1-7Zb62b6mYbXGFDRFKEfl_Q5oWyBAA; NID=511=sTNyZkuDiTiuZlXEx4-VyTNnFir07uPes9MjRtka8HSVeC7fFkRDeCS_TcYskKKHCwxdl2-KpPtA-htWaW7cYsI-aE_PropKZb7AduHb8g_DQfX9CkcTqIQqr4q8w_5kg7iYmTnP4mPvbnsfUu0U0lLJQw30r2DlypyvDPhiWGMYBS_s3ry3LQPOYNCKGSegFGTsZKS0YWzm87gJnNOhb7FQ169JI5Unasd_9C7CShOjU8oA9GQ2Y_rv84pq69TuBVGEGpZa_FTAKKREYERfWo5bcF8yRZx7YWTm1qoWQInzRKvOM29lOh61jjZsEFznPepoTlzErSopnUCtlndL5aV4SyarxXJ781-Mvi3hKXjkVmhnXTzJ0X0EKnl7XMbjpoSLPFU9xWL22ylEbrBNZs_AULK1df81UF_gu536qTNGvSmMvRdVS7Ei8XYjsnIfMyRNv0ihoqe__xFT0DPV8em-H_OUSXfTgl3fjHM2WLjEHmfF4hoYpTl5rp5-7xWa5tQ_6imBF1RTGjniimvBcQwXn8KmihfM6rx5kN0mpStFV9Bek6xF0oejGSPIw-lNIydi_H6waGDP8VF-ikiXtj5WAG-B_LBQXdJNLqeSdHbI6-EQ5VguG9WWJoT2EozsJ_YubJcp_vDjzwD5wLscm5yTgRDF3jhJF_FSGjpJUAco_NyhqzzZ5HeOk6kQASyGa-xDNTrcSFHpuDBMvCyviJ7yri_IMW6fsMEdC6lVihQ0YMrxrqKtxhxnfeNYs0rdb9955JbJkCUdXI4siY87fyUmRDl0NISwjqW2owT6LbhP9fVBb0y44RV6cAQKdMYpv2K-HA31kXNrYLY3eX7Z_Mjp8HHZsx7sa7LkeD0Y7QJ4qrbJNtiQtPjc-EHJkkJcvS7HopmM9Uoy5CH7erU; AEC=Ackid1SziBr34yx8m6r9gqDsp3OnUQOZRll8vVsWrNBAfQXPvHE61HnBxw; APISID=HNwMPcB7VpBZALwT/AMvGhFHaAsv3NE07i; HSID=A1D_X0Yp5keA7RtbZ; SAPISID=UqpHytrt1wOx4PZE/AglzGSzHzsgovZoGy; SID=dQjp6zQ2LbLsUxknsUizA8CDRUBONuIaeQeORVbQTBFSuAxcFqrWvEIKyXpxjPIn2-4-Cw.; SSID=ASNJgeelUk4UkoasU; __Secure-1PAPISID=UqpHytrt1wOx4PZE/AglzGSzHzsgovZoGy; __Secure-1PSID=dQjp6zQ2LbLsUxknsUizA8CDRUBONuIaeQeORVbQTBFSuAxcRI6TaS4O3LkColjYqRyIqQ.; __Secure-3PAPISID=UqpHytrt1wOx4PZE/AglzGSzHzsgovZoGy; __Secure-3PSID=dQjp6zQ2LbLsUxknsUizA8CDRUBONuIaeQeORVbQTBFSuAxcEBTCMCTLaLHOZ6gXX3Eguw.; OTZ=7295056_88_88_104280_84_446940; OGPC=19037049-1:19030388-1:19030390-1:19039026-1:19038986-1:19031986-1:; SEARCH_SAMESITE=CgQI25kB',
        "Sec-Fetch-Dest": "document",
        "Priority": "u=0, i",
    }

    params = {
        "q": name + " track and field",
        "client": "safari",
        "sca_esv": "732430080e01cdcb",
        "sxsrf": "AM9HkKnx4XkPmL66imEY5yvu0NP1Cscw5A:1700939572237",
        "source": "hp",
        "ei": "NEdiZeKNDJyFwbkP-I2H8AQ",
        "iflsig": "AO6bgOgAAAAAZWJVRKXTKkXK8kxSOXvHTgiaVTjcs7-j",
        "ved": "0ahUKEwji9_DX7d-CAxWcQjABHfjGAU4Q4dUDCAs",
        "uact": "5",
        "gs_lp": "Egdnd3Mtd2l6Igtqb2Uga2xlY2tlcjIKEC4YgAQYigUYJzIEECMYJzIKECMYgAQYigUYJzIFEAAYgAQyBRAAGIAEMgUQABiABDIFEAAYgAQyBRAAGIAEMgUQABiABDIKEAAYgAQYigUYQ0jtSlCiBFjjEHAMeACQAQCYAXmgAXmqAQMwLjG4AQPIAQD4AQGoAgrCAgcQIxjqAhgnwgIKEC4YgAQYigUYQ8ICDhAuGIAEGIoFGLEDGIMBwgIKEC4YgAQYFBiHAsICDRAuGIAEGBQYhwIYsQPCAgUQLhiABMICCxAuGIAEGLEDGIMBwgIIEC4YgAQYsQPCAhEQLhiABBiKBRixAxiDARjUAsICCBAuGLEDGIAEwgIKEC4YFBiHAhiABMICDRAuGIAEGLEDGIMBGAo",
        "sclient": "gws-wiz",
    }
    response = requests.get(
        "https://www.google.com/search", params=params, headers=headers
    )
    soup = BeautifulSoup(response.text, "html.parser")
    wikipedia_url = None
    items = soup.find_all("a", jsname="UWckNb")
    for item in items:
        href = item["href"]
        if "wikipedia" in href:
            wikipedia_url = href
    return wikipedia_url


def get_nickname(wiki_url: str) -> str:
    wiki_text = requests.get(wiki_url).text
    soup = BeautifulSoup(wiki_text, "html.parser")
    p_tags = soup.find_all("p")
    clean_tags = []
    for item in p_tags:
        if not item.get("class"):
            clean_tags.append(item)

    profile = str(clean_tags[0])
    try:
        nickname = re.search('"<b>\w+<\/b>"', profile)[0]
        cleaned_nickname = (
            nickname.replace("<b>", "").replace("</b>", "").replace('"', "")
        )
        return cleaned_nickname
    except:
        return None


def get_ig_username(document: Dict[str, Any]) -> str:
    instagram_username = None
    for item in document["social_urls"]:
        if "instagram_url" in item:
            instagram_url = item["instagram_url"]
            matched_username = re.search("instagram.com\/.*", instagram_url)[0]
            instagram_username = matched_username.split("/")[1]
    return instagram_username


def get_ig_caption_text(ig_username: str) -> str:
    try:
        user_id = cl.user_id_from_username(ig_username)
        ig_posts_text = ""
        medias = cl.user_medias(user_id, 40)
        for media in medias:
            ig_posts_text += " " + media.caption_text
    except:
        return None
    return ig_posts_text


def get_hq_image_for_athlete(query: str) -> str:
    results = []

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Sec-Fetch-Site": "none",
        # 'Cookie': '_fbp=fb.1.1698026678111.1952040698; _ga=GA1.2.2132144913.1698026678; _ga_DMJJ3WT1SM=GS1.1.1698026677.1.1.1698026761.47.0.0; _gid=GA1.2.1309145392.1698026678; gtm_ppn=category_browse; sp=rps=closed&mf=&ci=av%2Ct%2Crf&es=best&ei=; unisess=bVdrMHpJSFZQczNrbGgrM1p0bEU5TDBnMDZ3b0haWUp5VjJKcVAvYWh6bkxzaDAvMTVYWnZTUlZBUFE4VWI2TDJLN293VTJoWTV5a0dTUjRNUDh3UHc9PS0tbWdFMUFMUGhoam9JMlZPNlBRT2VwQT09--7c432c7cc48f189014a4c7f33978bff4b4cd4192; IR_4202=1698026748113%7C0%7C1698026748113%7C%7C; _gcl_au=1.1.1311169312.1698026678; ELOQUA=GUID=F9CE87CA12D74638990D74DC0F0619F0; IR_gbd=gettyimages.com; giu=nv=8&lv=2023-10-23T02%3A04%3A35Z; uac=t=EXim5%2F6cRRQ9NKLvRaGslqzbZvOGv9dSFpGj%2F0aPQ7yqRfb028x0QCfQNyPyrmUe9Nu7H9h0130gNyTkl9BVigi%2FTBU%2BMIJJtxdub3W6uoLHVxZ%2F66dNFB8LpdW%2BnzBkD6F3MHOOpfEG8g1KAIbtQxIXMcec6oGiIe4kRk3g4Ww%3D%7C77u%2FR2pjWUxiYVJqSTV5MWpvRlJ5TDUKMTAwCgpOR1lYR0E9PQpQRzBYR0E9PQowCgoKMAoxMDAKNTg3NklBPT0KMTAwCjAKM2E1OGE4NDItODE2OS00OGZlLTkzMDMtMzcwMTYyZmQ5ZDM4Cgo%3D%7C3%7C4%7C1&d; vis=vid=3a58a842-8169-48fe-9303-370162fd9d38; csrf=t=A2I%2BYvHyWi2x0PwNaTpbFaiMv%2BNusXkW4femP3HxO7A%3D; mc=3',
        # 'Accept-Encoding': 'gzip, deflate, br',
        "Sec-Fetch-Mode": "navigate",
        "Host": "www.gettyimages.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Dest": "document",
        "Connection": "keep-alive",
    }

    params = {
        "family": "editorial",
        "assettype": "image",
        "sort": "best",
    }

    response = requests.get(
        f"https://www.gettyimages.com/photos/{query}", params=params, headers=headers
    )
    response_text = response.text
    soup = BeautifulSoup(response_text, "html.parser")
    imgs = soup.find_all("img")
    for img in imgs:
        if "https" in img["src"]:
            results.append(img["src"])
    if results:
        return results[0]
    else:
        print(query)


def get_wiki_profile(url: str) -> str:
    resp = requests.get(url).text
    soup = BeautifulSoup(resp, "html.parser")
    p_tags = soup.find_all("p")
    cleaned_p_tags = [item for item in p_tags if not item.get("class")]
    text = " ".join([item.get_text() for item in cleaned_p_tags])
    return text


def summarize_wikipedia(wikipedia_url: str) -> str:
    if not wikipedia_url:
        return None
    wiki_profile_text = get_wiki_profile(wikipedia_url)

    if not wiki_profile_text:
        return None

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


def summarize_instagram(instagram_username: str) -> str:
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
    print(response.text)
    return response.json()["choices"][0]["message"]["content"]


def summarize_information(wiki_url: str, instagram_username: str) -> str:
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
        # in this case, there is no information, so we return nothing
        return None

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


def return_athlete_with_codes_and_images(athlete_name: str) -> Dict[str, str]:
    athlete = query_athlete(athlete_name)
    athlete["full_name"] = (
        athlete["givenName"] + " " + athlete["familyName"].lower().capitalize()
    )
    athlete["image_url"] = get_image_for_athlete(
        athlete["givenName"]
        + " "
        + athlete["familyName"]
        + " "
        + athlete["country"]
        + " track and field"
    )
    wiki_url = get_wiki(
        athlete["givenName"] + " " + athlete["familyName"].lower().capitalize()
    )
    athlete["wikipedia_url"] = wiki_url
    if athlete["wikipedia_url"]:
        # nickname = get_nickname(wiki_url)
        # athlete["nickname"] = nickname
        # get an upgraded image
        athlete["hq_image_url"] = get_hq_image_for_athlete(
            athlete["givenName"]
            + "-"
            + athlete["familyName"].lower().capitalize()
            + "-"
            + "track and field"
        )
    athlete["social_urls"] = get_socials(athlete["full_name"])
    instagram_username = get_ig_username(athlete)
    athlete["summary"] = summarize_information(wiki_url, instagram_username)
    athlete["top_competitors"] = get_top_competitors(athlete)
    athlete["personal_bests"] = get_pbs_for_athlete(athlete)
    athlete["accomplishments"] = get_accomplishments(athlete["urlSlug"])
    return athlete


def get_csv_athletes() -> List[str]:
    names = []
    for i in range(1, 60):
        found_names = pd.read_html(
            f"https://worldathletics.org/world-rankings/overall-ranking/women?regionType=world&page={i}&rankDate=2023-11-21&limitByCountry=0"
        )[0]["Competitor"].tolist()
        names.extend(found_names)

    for i in range(1, 60):
        found_names = pd.read_html(
            f"https://worldathletics.org/world-rankings/overall-ranking/men?regionType=world&page={i}&rankDate=2023-11-21&limitByCountry=0"
        )[0]["Competitor"].tolist()
        names.extend(found_names)
    random.shuffle(names)
    return names


def format_item(item: str) -> str:
    split = item.split(" ")
    lower = [item.lower().capitalize() for item in split]
    joined = " ".join(lower)
    return joined


athletes = get_csv_athletes()
formatted_names = [format_item(item) for item in athletes]


for name in formatted_names:
    time.sleep(random.uniform(6, 15))
    existing_record = collection.find_one({"full_name": name})
    if not existing_record:
        pipeline_results = return_athlete_with_codes_and_images(name)
        result = collection.insert_one(pipeline_results[0])
        logger.info("Record inserted successfully! \n\n =====")
    else:
        logger.info("found record and skipping \n\n =====")
