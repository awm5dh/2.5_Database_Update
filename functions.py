from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import mechanize
from bs4 import BeautifulSoup
import regex as re
import requests
from tqdm import tqdm
import variables


def create_remaining_pages(pages, num):
    length = len(pages)
    for i in range(length):
        pages[i] = pages[i].replace("&curPage=1", "&curPage=" + str(i + 1))
    for i in range(num - length - 1):
        code = pages[0].split("results.jsp?licSearchKey=licSearcKey")[1].split("&")[0]
        pages.append(
            "results.jsp?licSearchKey=licSearcKey"
            + code
            + "&curPage="
            + str(i + 1 + length)
            + "&reqPage="
            + str(i + 2 + length)
        )


def get_license_links(browser, page_url, lic_links):
    browser.follow_link(browser.find_link(url=page_url))
    for link in browser.links():
        if re.search("licKey.+", link.url):
            lic_links.append(link.url)


def setup_2_5Ghz_browser():
    browser = mechanize.Browser()
    browser.set_handle_robots(False)
    browser.set_handle_refresh(False)
    browser.addheaders = [
        (
            "User-agent",
            "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 "
            "Fedora/3.0.1-1.fc9 Firefox/3.0.1",
        )
    ]
    browser.open("https://wireless2.fcc.gov/UlsApp/UlsSearch/searchAdvanced.jsp")
    browser.select_form(name="advancedSearch")

    # Input criteria into form
    browser.find_control("fiRowsPerPage").items[3].selected = True
    browser.find_control("fiRadioServiceMatchAllInd").items[1].selected = True
    browser["radioservicecode"] = ["ED", "BR"]
    browser.find_control("statusAll").items[0].selected = False
    browser.find_control("AActive").items[0].selected = True
    browser.find_control("fiExcludeLeaseInd").items[0].selected = True
    # browser["ulsCallSign"] = "WRJS796"
    return browser


def setup_ZV_browser():
    browser = mechanize.Browser()
    browser.set_handle_robots(False)
    browser.set_handle_refresh(False)
    browser.addheaders = [
        (
            "User-agent",
            "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 "
            "Fedora/3.0.1-1.fc9 Firefox/3.0.1",
        )
    ]
    browser.open("https://wireless2.fcc.gov/UlsApp/UlsSearch/searchAdvanced.jsp")
    browser.select_form(name="advancedSearch")

    # Input criteria into form
    browser.find_control("fiRowsPerPage").items[3].selected = True
    browser.find_control("fiRadioServiceMatchAllInd").items[1].selected = True
    browser["radioservicecode"] = ["ZV"]
    browser.find_control("statusAll").items[0].selected = False
    browser.find_control("AActive").items[0].selected = True
    browser.find_control("fiExcludeLeaseInd").items[0].selected = True
    return browser


def setup_cbrs_browser():
    browser = mechanize.Browser()
    browser.set_handle_robots(False)
    browser.set_handle_refresh(False)
    browser.addheaders = [
        (
            "User-agent",
            "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 "
            "Fedora/3.0.1-1.fc9 Firefox/3.0.1",
        )
    ]
    browser.open("https://wireless2.fcc.gov/UlsApp/UlsSearch/searchAdvanced.jsp")
    browser.select_form(name="advancedSearch")

    # Input criteria into form
    browser.find_control("fiRowsPerPage").items[3].selected = True
    browser.find_control("fiRadioServiceMatchAllInd").items[1].selected = True
    browser["radioservicecode"] = ["PL"]
    browser.find_control("statusAll").items[0].selected = False
    browser.find_control("AActive").items[0].selected = True
    browser.find_control("fiExcludeLeaseInd").items[0].selected = True
    return browser


def fetch_2_5Ghz_data(url):
    pops = pd.read_csv("2.5_Population_Reference.csv")

    soup = BeautifulSoup(
        requests.get(variables.license_url + url).content, "html.parser"
    )
    info = [""] * 21

    # Call sign and radio service
    info[0] = (
        soup.find("td", text=re.compile("Call Sign")).find_next_sibling().text.strip()
    )
    info[1] = (
        soup.find("td", text=re.compile("Radio Service"))
        .find_next_sibling()
        .text.strip()
        .split("-")[0]
        .strip()
    )

    info[3] = (
        soup.find("td", text=re.compile("FRN"))
        .find_next_sibling()
        .text.strip()
        .split("(")[0]
        .strip()
    )

    # Licensee Info
    for block in soup.find_all("b", text="Licensee"):
        address = (
            block.find_parent("td")
            .find_parent("tr")
            .find_next_sibling("tr")
            .find("td")
            .text.strip()
        )
        name = address.split("\n")[0]
        info[2] = name
        if (
            "nsac" in name.lower()
            or "wbsy" in name.lower()
            or "sprint" in name.lower()
            or "t-mobile" in name.lower()
            or "clearwire" in name.lower()
            or "american telecasting" in name.lower()
            or "people's choice" in name.lower()
            or "fixed wireless holdings" in name.lower()
            or "tdi acq" in name.lower()
            or "pctv" in name.lower()
        ):
            info[4] = "Yes"
        else:
            info[4] = "No"

        if "ATTN" in address:
            info[18] = address.split("ATTN ")[1].strip()

        contact_info = (
            block.find_parent("td")
            .find_parent("tr")
            .find_next_sibling("tr")
            .find("td")
            .find_next_sibling()
            .text.strip()
        )
        if "E:" in contact_info:
            info[19] = contact_info.split("E:")[1].split("\n")[0].strip()
        if "P:" in contact_info:
            info[20] = contact_info.split("P:")[1].split("\n")[0].strip()

    # Market & Frequency info
    blocks = soup.find_all("td", text=re.compile("MHz"))
    info[5] = ""
    mhz = 0
    for block in blocks:
        letter = block.text.split(" ")[1][0]
        if letter not in info[5]:
            info[5] += letter
        lower = float(block.text.split(" ")[4].split("-")[0])
        upper = float(block.text.split(" ")[4].split("-")[1])
        mhz += upper - lower
    info[5] = "".join((sorted(info[5])))
    info[6] = str(mhz)

    # Population info
    if info[0] in pops["Call Sign"].values:
        info[7] = str(pops[pops["Call Sign"] == info[0]]["POPs"].values[0])
        info[8] = str(round(float(info[7]) * float(info[6])))
    else:
        info[7] = "Unknown"
        info[8] = "Unknown"

    # License Dates
    info[9] = soup.find("td", text="Effective").find_next_sibling().text.strip()
    info[10] = soup.find("td", text="Expiration").find_next_sibling().text.strip()

    # License Characteristics
    if soup.find("b", text=re.compile("This license has pending applications")):
        info[11] = "Yes"
    else:
        info[11] = "No"

    if (
        soup.find("td", text=re.compile("Authorization Type"))
        .find_next_sibling()
        .text.strip()
        == "TPW"
    ):
        if (
            soup.find("td", text="Auth Type").find_next_sibling().text.strip()
            == "Special Temporary"
        ):
            info[12] = "Yes - Special Temporary"
        else:
            info[12] = "Yes"
    else:
        info[12] = "No"

    # Lessee Info
    info[13] = "No active leases"
    info[14] = "N/A"
    info[15] = "N/A"
    info[16] = "N/A"
    info[17] = "N/A"
    lease_tab = soup.find("a", title="Links")
    if lease_tab:
        lease_soup = BeautifulSoup(
            requests.get(variables.license_url + lease_tab.get("href")).content,
            "html.parser",
        )

        status = lease_soup.find("td", text="Active")
        if status:
            info[13] = status.find_previous_siblings()[5].text.strip()
            info[14] = status.find_previous_siblings()[4].text.strip()
            if (
                "nsac" in info[14].lower()
                or "wbsy" in info[14].lower()
                or "sprint" in info[14].lower()
                or "t-mobile" in info[14].lower()
                or "clearwire" in info[14].lower()
                or "american telecasting" in info[14].lower()
                or "people's choice" in info[14].lower()
                or "fixed wireless holdings" in info[14].lower()
                or "tdi acq" in info[14].lower()
                or "pctv" in info[14].lower()
            ):
                info[15] = "Yes"
            else:
                info[15] = "No"
            info[16] = status.find_previous_siblings()[1].text.strip()
            info[17] = status.find_previous_siblings()[0].text.strip()
        lease_soup.decompose()
    soup.decompose()

    return info


def fetch_cbrs_data(url):

    info = [""] * 10
    soup = BeautifulSoup(
        requests.get(variables.license_url + url).content, "html.parser"
    )

    info[1] = (
        soup.find("td", text=re.compile("Call Sign")).find_next_sibling().text.strip()
    )
    info[3] = (
        soup.find("td", text=re.compile("FRN"))
        .find_next_sibling()
        .text.strip()
        .split("(")[0]
        .strip()
    )

    market_info = soup.find_all("td", text=re.compile("Market"))[1].find_next_sibling().text.split("-")
    info[4] = market_info[0].strip()
    info[0] = info[4].replace("D", "")
    info[5] = market_info[1].strip()

    tribal = soup.find("b", text=re.compile("Tribal")).find_parent().text
    if "This license did not have tribal land bidding credits" in tribal:
        info[6] = "No"
    else:
        info[6] = "Yes"

    for block in soup.find_all("b", text="Licensee"):
        address = (
            block.find_parent("td")
            .find_parent("tr")
            .find_next_sibling("tr")
            .find("td")
            .text.strip()
        )
        name = address.split("\n")[0]
        info[2] = name

        if "ATTN" in address:
            info[7] = address.split("ATTN ")[1].strip()

        contact_info = (
            block.find_parent("td")
            .find_parent("tr")
            .find_next_sibling("tr")
            .find("td")
            .find_next_sibling()
            .text.strip()
        )
        if "E:" in contact_info:
            info[8] = contact_info.split("E:")[1].split("\n")[0].strip()
        if "P:" in contact_info:
            info[9] = contact_info.split("P:")[1].split("\n")[0].strip()

    return info


def get_2_5Ghz_result():

    # Set up browser
    browser = setup_2_5Ghz_browser()

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
    create_remaining_pages(page_urls, num_pages)
    for url in tqdm(page_urls, desc="Fetching License Links From Pages"):
        get_license_links(browser, url, lic_links)

    # Get info for licenses
    data = []
    threads = []
    with tqdm(total=len(lic_links), desc="Downloading Info From Licenses") as pbar:
        with ThreadPoolExecutor(max_workers=8) as executor:
            for link in lic_links:
                threads.append(executor.submit(fetch_2_5Ghz_data, link))
            for task in as_completed(threads):
                data.append(task.result())
                pbar.update(1)

    frame = pd.DataFrame(
        data,
        columns=[
            "Call Sign",  # 0
            "Radio Service Code",  # 1
            "License Holder",  # 2
            "FRN",  # 3
            "Sprint Equivalent",  # 4
            "Block",  # 5
            "MHz",  # 6
            "POPs",  # 7
            "MHz-POPs",  # 8
            "License Effective",  # 9
            "License Expires",  # 10
            "Pending Applications",  # 11
            "Tribal License",  # 12
            "Lease ID",  # 13
            "Lessee Name",  # 14
            "Lessee Sprint Equivalent",  # 15
            "Lease Commenced",  # 16
            "Lease Expires",  # 17
            "License Contact",  # 18
            "License Email",  # 19
            "License Phone",  # 20
        ],
    )
    frame.to_csv("API_results.csv", index=False)


def get_cbrs_result():

    # Set up browser
    browser = setup_cbrs_browser()

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
    create_remaining_pages(page_urls, num_pages)
    for url in tqdm(page_urls, desc="Fetching License Links From Pages"):
        get_license_links(browser, url, lic_links)

    # Get info for licenses
    data = []
    threads = []
    with tqdm(total=len(lic_links), desc="Downloading Info From Licenses") as pbar:
        with ThreadPoolExecutor(max_workers=8) as executor:
            for link in lic_links:
                threads.append(executor.submit(fetch_cbrs_data, link))
            for task in as_completed(threads):
                data.append(task.result())
                pbar.update(1)

    frame = pd.DataFrame(
        data,
        columns=[
            "FIPS",  # 0
            "Call Sign",  # 1
            "Licensee Name",  # 2
            "FRN",  # 3
            "Market Code",  # 4
            "Market Name",  # 5
            "Tribal Bidder?",  # 6
            "Contact Name",  # 7
            "Contact Email",  # 8
            "Contact Phone",  # 9
        ],
    )
    frame.to_csv("API_results.csv", index=False)
