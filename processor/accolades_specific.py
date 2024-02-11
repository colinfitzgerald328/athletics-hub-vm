import requests
from bs4 import BeautifulSoup


def get_accomplishments(url_slug: str) -> str:
    accomplishments = []
    resp_text = requests.get(f"https://worldathletics.org/athletes/{url_slug}").text
    page_soup = BeautifulSoup(resp_text, "html.parser")
    accolades = page_soup.find_all(
        "div", class_="profileStatistics_honourSummaryBlock__1qOBV"
    )
    for accolade in accolades:
        accomplishments.append(accolade.get_text())
    return accomplishments
