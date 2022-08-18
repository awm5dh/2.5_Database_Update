import functions
from bs4 import BeautifulSoup
import regex as re
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
import variables
import time
from selenium.webdriver.common.by import By
import os
import zipfile

download_folder = "D:\\Users\\Aidan McManus\\PycharmProjects\\2.5_Database_Update\\ZV Map Files"

def check_map_validity(url, driver):
    url = url.replace("license.jsp?", "licenseMap.jsp?")
    driver.get(variables.license_url + url)
    html_source = driver.page_source
    print(html_source)
    exit()  # STUB


def download_map(url, driver):
    url = url.replace("license.jsp?", "licenseMap.jsp?")
    driver.get(variables.license_url + url)
    selector = Select(driver.find_element(by="id", value="sel-download"))
    selector.select_by_visible_text("KML")
    time.sleep(0.5)
    return driver.find_element(By.XPATH, "//td[contains(text(), 'Call Sign')]/following-sibling::td").text.strip()


def get_maps():

    # Set up browser
    browser = functions.setup_ZV_browser()

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
    lic_links = []
    for link in browser.links():
        if re.match("Page .+", link.attrs[1][1]) and link.url not in page_urls:
            page_urls.append(link.url)
        elif re.search("licKey.+", link.url):
            lic_links.append(link.url)

    # Create remaining page links, then get licenses on every page
    functions.create_remaining_pages(page_urls, num_pages)
    for url in tqdm(page_urls, desc="Fetching License Links From Pages"):
        functions.get_license_links(browser, url, lic_links)

    # Set up driver
    options = Options()
    preferences = {
        "download.default_directory": download_folder}
    options.add_experimental_option("prefs", preferences)
    options.add_argument("--headless")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options)

    # Get license maps
    key_to_callsign = {}
    for link in tqdm(lic_links, desc="Downloading License Maps"):
        # check_map_validity(link, driver)
        key = link[link.find("licKey=")+7:]
        key_to_callsign[key] = download_map(link, driver)

    driver.close()

    # Extract zip files, rename KML files, remove extraneous files
    for file in os.listdir(download_folder):
        if file.endswith(".zip"):
            with zipfile.ZipFile(os.path.join(download_folder, file)) as zip_ref:
                zip_ref.extractall(download_folder)

    for file in os.listdir(download_folder):
        if file.endswith(".kml"):
            key = file.split("-")[2]
            old_name = os.path.join(download_folder, file)
            new_name = os.path.join(download_folder, key_to_callsign[key] + ".kml")
            os.rename(old_name, new_name)
        else:
            os.remove(os.path.join(download_folder, file))


get_maps()
