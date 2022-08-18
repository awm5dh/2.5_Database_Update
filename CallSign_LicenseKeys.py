import functions
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import regex as re
from tqdm import tqdm
import pandas as pd
import requests
import variables


def get_callsign(url):
    soup = BeautifulSoup(
        requests.get(variables.license_url + url).content, "html.parser"
    )
    info = [""] * 2
    info[0] = (
        soup.find("td", text=re.compile("Call Sign")).find_next_sibling().text.strip()
    )
    info[1] = url.split("licKey=")[1]
    return info


def get_2_5Ghz_licensekeys():

    # Set up browser
    browser = functions.setup_2_5Ghz_browser()

    # Submit form & Get number of results
    soup = BeautifulSoup(browser.submit().read(), "html.parser")
    num_pages = (
        int(
            soup.find_all("td", class_="cell-pri-dark", valign="middle")[0]
            .find_all("b")[2]
            .text
        )
        // 100
        + 1
    )
    soup.decompose()

    # Get licenses on first page, also urls for linked "next" pages
    page_urls = []
    lic_keys_and_callsigns = []
    for link in browser.links():
        if re.match("Page .+", link.attrs[1][1]) and link.url not in page_urls:
            page_urls.append(link.url)
        elif re.search("licKey.+", link.url):
            lic_keys_and_callsigns.append((link.text, link.url.split("licKey=")[1]))

    # Create remaining page links, then get licenses on every page
    functions.create_remaining_pages(page_urls, num_pages)
    for url in tqdm(page_urls, desc="Fetching License Links From Pages"):
        browser.follow_link(browser.find_link(url=url))
        for link in browser.links():
            if re.search("licKey.+", link.url):
                lic_keys_and_callsigns.append((link.text, link.url.split("licKey=")[1]))

    frame = pd.DataFrame(
        lic_keys_and_callsigns,
        columns=[
            "Call Sign",  # 0
            "License Key",  # 1
        ],
    )
    frame.to_csv("License_Keys.csv", index=False)


get_2_5Ghz_licensekeys()
