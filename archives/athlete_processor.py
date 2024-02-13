from top_competitors_specific import get_top_competitors
from personal_bests_specific import get_pbs_for_athlete
from accolades_specific import get_accomplishments
import requests
import unicodedata
from bs4 import BeautifulSoup
import random
import time
import re
import urllib
import pandas as pd
from database_connector import get_collection
from app_secrets import DEEPINFRA_API_KEY


def similarity_percentage(str1, str2):
    # Calculate the Levenshtein distance
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    max_length = max(len(str1), len(str2))
    if max_length == 0:
        return 100.0  # Both strings are empty, consider them 100% similar.

    distance = levenshtein_distance(str1, str2)
    similarity = 100.0 * (1 - (distance / max_length))
    return similarity


def convert_special_unicode_to_string(input_str):
    # Normalize the input string to Unicode NFKD (Normalization Form KC)
    normalized_str = unicodedata.normalize("NFKD", input_str)

    # Remove non-spacing marks (e.g., combining accents)
    stripped_str = "".join([c for c in normalized_str if not unicodedata.combining(c)])

    return stripped_str


# In[3]:


def format_disciplines(disciplines):
    results = []
    split_disciplines = disciplines.split(", ")
    for item in split_disciplines:
        item_lower = item.lower()
        split_item = item_lower.split(" ")
        if len(split_item) > 1:
            if split_item[1] == "metres":
                first_item_clean = split_item[0].replace(",", "")
                if (
                    re.search("4x\d+", first_item_clean)
                    or int(first_item_clean) <= 3000
                ):
                    results.append(split_item[0] + "m")
                elif int(first_item_clean) < 9999:
                    results.append(first_item_clean[0] + "k")
                else:
                    results.append(first_item_clean[:2] + "k")
        else:
            results.append(item_lower.strip())
    return results


# In[4]:


def query_athletes(athlete_name):
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
    results = response.json()
    return results["data"]["searchCompetitors"][:1]


def get_image_for_athlete(athlete_name_with_country_code):
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
        return results[0]


# In[3]:


def get_wiki(athlete_name, kw=" track athlete"):
    results = []
    qualifying_results = []

    headers = {
        "authority": "en.wikipedia.org",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        # 'cookie': 'WMF-Last-Access=23-Oct-2023; WMF-Last-Access-Global=23-Oct-2023; GeoIP=US:CA:Berkeley:37.87:-122.29:v4; NetworkProbeLimit=0.001; enwikimwuser-sessionId=b7ec35141ca0ebc0d379',
        "sec-ch-ua": '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    }

    params = {
        "fulltext": "1",
        "search": athlete_name + kw,
        "title": "Special:Search",
        "ns0": "1",
    }

    response = requests.get(
        "https://en.wikipedia.org/w/index.php", params=params, headers=headers
    )
    h_t = response.text
    soup = BeautifulSoup(h_t, "html.parser")
    li_elements = soup.find_all("li", class_="mw-search-result mw-search-result-ns-0")
    track_words_list = [
        "runner",
        "track and field",
        "sprinter",
        "track",
        "athlete",
        "pole vault",
        "shot put",
        "high jump",
        "long jump",
        "hurdles",
        "steeplechase",
        "triple jump",
        "discus",
        "racewalker",
        "javelin",
        "marathon",
    ]
    for li_element in li_elements:
        for word in track_words_list:
            if word in str(li_element).lower():
                a_tag = li_element.find_all("a")[0]
                href = a_tag["href"]
                results.append("https://en.wikipedia.org/" + href)
    for result in results:
        name = result.split("/")[-1].replace(".", "").split("_")
        if len(name) > 1:
            name_joined = name[0] + " " + name[1]
            if similarity_percentage(athlete_name, name_joined) > 50:
                qualifying_results.append(result)
    if qualifying_results:
        return qualifying_results[0]
    return None


def get_nickname(wiki_url):
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


# In[4]:


def is_ig_track_athlete(user_name, list_disciplines):
    delay = random.uniform(1, 5)
    time.sleep(delay)

    headers = {
        "Accept": "*/*",
        "Sec-Fetch-Site": "same-origin",
        "Accept-Language": "en-US,en;q=0.9",
        # 'Accept-Encoding': 'gzip, deflate, br',
        "Sec-Fetch-Mode": "cors",
        "Host": "www.instagram.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
        "Referer": f"https://www.instagram.com/{user_name}/",
        "Connection": "keep-alive",
        "Cookie": 'csrftoken=Q0leiiCpIifbSopf3m4mevzqO92w940z; ds_user_id=39525688001; rur="EAG\\05439525688001\\0541731439959:01f71656e95c28368a5a52ec6aff519a06d0ab0f49015358aba4c521bcc5996de2b986c5"; sessionid=39525688001%3AnpUkkAoPI8FZNb%3A14%3AAYeYyUPY2ufC7gXZAQyXHP4BfE4yQCqwFF6dWT66mJHA; shbid="923\\05439525688001\\0541731438940:01f73e41e2da0074c791653f7ffe69983162e407267faff7ffcab075f569ecbda91f8558"; shbts="1699902940\\05439525688001\\0541731438940:01f74248254c7873258e59fafd5f34133c7286d8add36347b39d027a7c6eb9dc7c3cc5ef"; datr=aWOlYhJ7FTQKfFODIJ98F_ue; ig_did=90782A45-D4D2-4A90-AABB-931301FDF0CB; mid=YhSF7QAEAAETTLhNTUL-MmFE_xKF',
        "Sec-Fetch-Dest": "empty",
        "X-CSRFToken": "Q0leiiCpIifbSopf3m4mevzqO92w940z",
        "X-ASBD-ID": "129477",
        "X-Requested-With": "XMLHttpRequest",
        "X-IG-App-ID": "936619743392459",
        "Priority": "u=3, i",
        "X-IG-WWW-Claim": "hmac.AR20Y_Ah3BGkqc7FwvE0_827iIIcQjsTbTWpLvuu1UO3eQm1",
    }

    params = {
        "count": "60",
    }

    response = requests.get(
        f"https://www.instagram.com/api/v1/feed/user/{user_name}/username/",
        params=params,
        headers=headers,
        proxies=urllib.request.getproxies(),
    )
    results = []
    data = response.json()["items"]
    for item in data:
        if item["caption"]:
            results.append(item["caption"]["text"])
    joined_results = " ".join(results)
    formatted_disciplines = format_disciplines(list_disciplines)
    formatted_disciplines.extend(
        ["runner", "track and field", "sprinter", "WorldAthletics"]
    )
    for item in formatted_disciplines:
        if item in joined_results:
            return True
    return False


# In[5]:


def get_instagram_url_for_athlete(athlete_name, list_disciplines):
    delay = random.uniform(1, 5)
    time.sleep(delay)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
        "Sec-Fetch-Site": "same-origin",
        "Accept-Language": "en-US,en;q=0.9",
        # 'Accept-Encoding': 'gzip, deflate, br',
        "Sec-Fetch-Mode": "cors",
        "Host": "www.instagram.com",
        "Origin": "https://www.instagram.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
        "Referer": "https://www.instagram.com/",
        # 'Content-Length': '1233',
        "Connection": "keep-alive",
        # 'Cookie': 'csrftoken=Q0leiiCpIifbSopf3m4mevzqO92w940z; ds_user_id=39525688001; rur="NAO\\05439525688001\\0541729059081:01f72beb4234971dfc21b5c48a7e79628e8f8a2b2a95710475a9dd6f9cfb07c8c00dd3ca"; sessionid=39525688001%3AnpUkkAoPI8FZNb%3A14%3AAYeQUh5_P_bbishq5oF4zEl1XAV0Uko88owF0ntHnVWI; shbid="923\\05439525688001\\0541729048845:01f773d40ecd06d0933bf1eec78b6d0337763a6663850efdb1b3e49a59fd0180b2dc0993"; shbts="1697512845\\05439525688001\\0541729048845:01f73c08de0447114c8a334ae23a579e9ab1aae60dfb5f5f8dcdb021f312d306d2a15e70"; datr=aWOlYhJ7FTQKfFODIJ98F_ue; ig_did=90782A45-D4D2-4A90-AABB-931301FDF0CB; mid=YhSF7QAEAAETTLhNTUL-MmFE_xKF',
        "Sec-Fetch-Dest": "empty",
        "X-CSRFToken": "Q0leiiCpIifbSopf3m4mevzqO92w940z",
        "X-FB-LSD": "awp8Nl_nMzU-oeQCDQV9Y1",
        "X-ASBD-ID": "129477",
        "X-FB-Friendly-Name": "PolarisSearchBoxRefetchableQuery",
        "X-IG-App-ID": "936619743392459",
    }

    data = {
        "av": "17841439360050711",
        "__d": "www",
        "__user": "0",
        "__a": "1",
        "__req": "1o",
        "__hs": "19647.HYP:instagram_web_pkg.2.1..0.1",
        "dpr": "1",
        "__ccg": "UNKNOWN",
        "__rev": "1009286311",
        "__s": ":60ezyd:0r0u3w",
        "__hsi": "7290806114125542961",
        "__dyn": "7xeUmwlEnwn8K2WnFw9-2i5U4e1ZyUW3qi2K360CEbotw50x609vCwjE1xoswIwuo2awlU-cw5Mx62G3i1ywOwv89k2C1Fwc60AEC7U2czXwae4UaEW2G1NwwwNwKwHw8Xxm16wUwtEvU1aUbpEbUGdG1QwTwFwIw8O321LwTwKG1pg661pwr86C1mwraCgoK",
        "__csr": "gogWzgDd2l_W6h4p_5iYTlIxavV299WlmGRCyeBVmi-tajLVFTy4-aEwxnhqCGcOyQh4WFppoJeiXhBpGJ4umFSh5yGBKhHXLy8nKq7EkzHBxiWnCw04jda0nbwfO7ovwxwt30_w2niw0zXohUAyxV0xOzN83WAw2z83gQaw4fwYh8AK04080Iww28g06iW04fU",
        "__comet_req": "7",
        "fb_dtsg": "NAcMghZfn-WyWbgJGGb4n48sgtSAKFYdQ7y3Scac_HOiWi1jDDagXUQ:17858225011064242:1645512179",
        "jazoest": "26254",
        "lsd": "awp8Nl_nMzU-oeQCDQV9Y1",
        "__spin_r": "1009286311",
        "__spin_b": "trunk",
        "__spin_t": "1697523080",
        "fb_api_caller_class": "RelayModern",
        "fb_api_req_friendly_name": "PolarisSearchBoxRefetchableQuery",
        "variables": f"""{{"data":{{"context":"blended","include_reel":"true","query":"{athlete_name}","rank_token":"1697523083964|8808dcca7b90c271e4c2364e57530928da463d5906745dbd29ca61c1f999cd17","search_surface":"web_top_search"}},"hasQuery":true}}""",
        "server_timestamps": "true",
        "doc_id": "6460896210645763",
    }

    response = requests.post(
        "https://www.instagram.com/api/graphql", headers=headers, data=data
    )
    results = response.json()
    print(results)
    users = results["data"]["xdt_api__v1__fbsearch__topsearch_connection"]["users"]
    if len(users) > 0:
        users = users[:5]
        found_user = None
        for user in users:
            user_name = user["user"]["username"]
            full_name = user["user"]["full_name"]
            first_name_letter_search = re.search("\w\.", full_name)
            if first_name_letter_search:
                full_name = full_name.strip(first_name_letter_search[0]).strip()
            full_name = full_name.lower().split(" ")
            if len(full_name) > 1:
                full_name_formatted = convert_special_unicode_to_string(
                    full_name[0].capitalize() + " " + full_name[1].capitalize()
                )
                if (
                    is_ig_track_athlete(user_name, list_disciplines)
                    and similarity_percentage(full_name_formatted, athlete_name) > 20
                ):
                    found_user = user_name
                    break
            elif len(full_name) == 1:
                full_name_formatted = convert_special_unicode_to_string(
                    full_name[0].capitalize()
                )
                if (
                    is_ig_track_athlete(user_name, list_disciplines)
                    and similarity_percentage(full_name_formatted, athlete_name) > 20
                ):
                    found_user = user_name
                    break
        if found_user:
            return "https://instagram.com/" + found_user
        else:
            return found_user
    else:
        return None


# In[6]:


def get_hq_image_for_athlete(query):
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


# In[7]:


import random
import time
import requests
import urllib
import openai
import tiktoken
from langchain.text_splitter import TokenTextSplitter
from bs4 import BeautifulSoup

text_splitter = TokenTextSplitter(chunk_size=2800, chunk_overlap=0)

# Point OpenAI client to our endpoint
openai.api_key = "fra0CxJkQ8wVn6N8bWmDLlQFaNWos0JD"
openai.api_base = "https://api.deepinfra.com/v1/openai"


def get_ig_posts_text(user_name):

    headers = {
        "Accept": "*/*",
        "Sec-Fetch-Site": "same-origin",
        "Accept-Language": "en-US,en;q=0.9",
        # 'Accept-Encoding': 'gzip, deflate, br',
        "Sec-Fetch-Mode": "cors",
        "Host": "www.instagram.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
        "Referer": f"https://www.instagram.com/{user_name}/",
        "Connection": "keep-alive",
        "Cookie": 'csrftoken=Q0leiiCpIifbSopf3m4mevzqO92w940z; ds_user_id=39525688001; rur="VLL\\05439525688001\\0541731115289:01f72650b9153324020a0ea13375fe184f61b645dc4d7da781cb1a3cbd05ce0d477c8c75"; sessionid=39525688001%3AnpUkkAoPI8FZNb%3A14%3AAYeGvTT14VT7nLx9fn2GXpsZ9I0W_IdWlgHTxpoYx591; shbid="923\\05439525688001\\0541731115132:01f79daf2c76126a483e6746fbc6985997e34e54b606580ccd1395c3a72d88087a564210"; shbts="1699579132\\05439525688001\\0541731115132:01f7c60ee4a32e47afe2e86d3e535896dc1c88f2a4712b3c0f3c420420343e6c29d63405"; datr=aWOlYhJ7FTQKfFODIJ98F_ue; ig_did=90782A45-D4D2-4A90-AABB-931301FDF0CB; mid=YhSF7QAEAAETTLhNTUL-MmFE_xKF',
        "Sec-Fetch-Dest": "empty",
        "X-CSRFToken": "Q0leiiCpIifbSopf3m4mevzqO92w940z",
        "X-ASBD-ID": "129477",
        "X-Requested-With": "XMLHttpRequest",
        "X-IG-App-ID": "936619743392459",
        "X-IG-WWW-Claim": "hmac.AR20Y_Ah3BGkqc7FwvE0_827iIIcQjsTbTWpLvuu1UO3eQgX",
    }

    params = {"count": 60}

    response = requests.get(
        f"https://www.instagram.com/api/v1/feed/user/{user_name}/username/",
        params=params,
        headers=headers,
        proxies=urllib.request.getproxies(),
    )
    results = []
    data = response.json()["items"]
    for item in data:
        if item["caption"]:
            results.append(item["caption"]["text"])
    joined_results = " ".join(results)
    return joined_results


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
    print(response.text)
    return response.json()["choices"][0]["message"]["content"]


def summarize_instagram(instagram_username):
    if not instagram_username:
        return None
    ig_post_text = get_ig_posts_text(instagram_username)

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


def summarize_information(wiki_url, instagram_url):
    wiki_summary = None
    instagram_summary = None
    if not wiki_url:
        return None
    if wiki_url:
        wiki_summary = summarize_wikipedia(wiki_url)
    if instagram_url:
        instagram_username = instagram_url.split("/")[-1]
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


# In[8]:


def return_athletes_with_codes_and_images(athlete_name):
    athletes = query_athletes(athlete_name)
    instagram_urls = []
    wikipedia_urls = []
    nickname = None
    for athlete in athletes:
        first_name = athlete["givenName"]
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
        suggested_wiki_url = get_wiki(
            athlete["givenName"] + " " + athlete["familyName"].lower().capitalize()
        )
        if not suggested_wiki_url:
            suggested_wiki_url = get_wiki(
                athlete["givenName"] + " " + athlete["familyName"].lower().capitalize(),
                " sprinter",
            )
        if suggested_wiki_url not in wikipedia_urls:
            wikipedia_urls.append(suggested_wiki_url)
            athlete["wikipedia_url"] = suggested_wiki_url
            if athlete["wikipedia_url"]:
                nickname = get_nickname(suggested_wiki_url)
                athlete["nickname"] = nickname
            # get an upgraded image
            athlete["hq_image_url"] = get_hq_image_for_athlete(
                athlete["givenName"]
                + "-"
                + athlete["familyName"].lower().capitalize()
                + "-"
                + "track and field"
            )
        if nickname:
            first_name = nickname
        athlete["instagram_url"] = None
        athlete["summary"] = summarize_information(suggested_wiki_url, None)
        athlete["top_competitors"] = get_top_competitors(athlete)
        athlete["personal_bests"] = get_pbs_for_athlete(athlete)
        athlete["accomplishments"] = get_accomplishments(athlete["urlSlug"])
    return athletes


# In[17]:


import random


def get_csv_athletes():
    names = []
    for i in range(1, 6):
        found_names = pd.read_html(
            f"https://worldathletics.org/world-rankings/overall-ranking/women?regionType=world&page={i}&rankDate=2023-11-21&limitByCountry=0"
        )[0]["Competitor"].tolist()
        names.extend(found_names)

    for i in range(1, 6):
        found_names = pd.read_html(
            f"https://worldathletics.org/world-rankings/overall-ranking/men?regionType=world&page={i}&rankDate=2023-11-21&limitByCountry=0"
        )[0]["Competitor"].tolist()
        names.extend(found_names)
    random.shuffle(names)
    return names


def format_item(item):
    split = item.split(" ")
    lower = [item.lower().capitalize() for item in split]
    joined = " ".join(lower)
    return joined


athletes = get_csv_athletes()
formatted_names = [format_item(item) for item in athletes]
collection = get_collection()


for name in formatted_names:
    time.sleep(20)
    existing_record = collection.find_one({"full_name": name})
    if not existing_record:
        pipeline_results = return_athletes_with_codes_and_images(name)
        result = collection.insert_one(pipeline_results[0])
        print("Record inserted successfully!")
    else:
        print("found record and skipping")
