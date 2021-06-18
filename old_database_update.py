import pandas as pd
import mechanize
from bs4 import BeautifulSoup
import regex as re
import requests
import variables


def create_remaining_pages(pages, num_pages):
    length = len(pages)
    for i in range(length):
        pages[i] = pages[i].replace("&curPage=1", "&curPage=" + str(i + 1))
    for i in range(num_pages - length - 1):
        code = pages[0].split("results.jsp?licSearchKey=licSearcKey")[1].split("&")[0]
        pages.append(
            "results.jsp?licSearchKey=licSearcKey"
            + code
            + "&curPage="
            + str(i + 1 + length)
            + "&reqPage="
            + str(i + 2 + length)
        )


def get_appl_links(browser, page_url, appl_links):
    browser.follow_link(browser.find_link(url=page_url))
    for link in browser.links():
        if re.search("applID.+", link.url):
            appl_links.append(link.url)


def browser_setup():
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
    browser.open(variables.application_url + "searchAdvanced.jsp")
    browser.select_form(name="search")
    browser.find_control("pageSize").items[3].selected = True
    return browser


def input_ebs_update(browser):
    browser["uls_a_radio_service_code"] = ["ED"]
    browser["uls_a_purpose_code"] = [
        "AA",
        "LN",
    ]
    browser.find_control("ia_date_type").items[1].selected = True
    browser["ia_from_date"] = "3/1/2021"


def create_df_data(appl_links):
    for_df = []
    for url in appl_links:
        soup = BeautifulSoup(
            requests.get(variables.application_url + url).content, "html.parser"
        )

        appl_status = (
            soup.find("td", text="Application Status")
            .find_next_sibling()
            .text.split("- ")[1]
            .strip()
        )
        # exit conditions
        if appl_status in ("Inactive", "Withdrawn"):
            continue

        file_num = soup.find("td", text="File Number").find_next_sibling().text.strip()

        if soup.find("td", text="Original Application Purpose"):
            purpose = (
                soup.find("td", text="Original Application Purpose")
                .find_next_sibling()
                .text.split("- ")[1]
                .strip()
            )
        else:
            purpose = (
                soup.find("td", text="Application Purpose")
                .find_next_sibling()
                .text.split("- ")[1]
                .strip()
            )

        lease_tab = soup.find("a", title="Leases")
        license_tab = soup.find("a", title="Licenses")
        call_signs = []
        lease_ids = []
        expiration_dates = []
        commence_dates = []
        if lease_tab:
            lease_soup = BeautifulSoup(
                requests.get(variables.application_url + lease_tab.get("href")).content,
                "html.parser",
            )
            for a_block in lease_soup.find_all(
                "a", title="Link to License in new window"
            ):
                call_signs.append(a_block.text.strip())
            for a_block in lease_soup.find_all(
                "a", title="Link to new License in new window"
            ):
                lease_ids.append(a_block.text.strip())
                id_soup = BeautifulSoup(
                    requests.get(a_block.get("href")).content,
                    "html.parser",
                )
                expiration_dates.append(
                    id_soup.find("td", text="Expiration")
                    .find_next_sibling()
                    .text.strip()
                )
                commence_dates.append(
                    id_soup.find("td", text="Effective")
                    .find_next_sibling()
                    .text.strip()
                )
        elif license_tab:
            license_soup = BeautifulSoup(
                requests.get(
                    variables.application_url + license_tab.get("href")
                ).content,
                "html.parser",
            )
            for a_block in license_soup.find_all(
                "a", title="Link to License in new window"
            ):
                call_signs.append(a_block.text.strip())
                lic_soup = BeautifulSoup(
                    requests.get(a_block.get("href")).content,
                    "html.parser",
                )
                expiration_dates.append(
                    lic_soup.find("td", text="Expiration")
                    .find_next_sibling()
                    .text.strip()
                )
                commence_dates.append(
                    lic_soup.find("td", text="Effective")
                    .find_next_sibling()
                    .text.strip()
                )

        party = (
            soup.find("td", text="Real Party In Interest")
            .find_next_sibling()
            .text.strip()
        )
        if "t-mobile" in party.lower():
            party = "Sprint"

        if party == "Sprint":
            if purpose == "Assignment of Authorization":
                comment = "Sprint Owned"
            else:
                comment = "Lease " + appl_status
        else:
            if purpose == "Assignment of Authorization":
                comment = "Assignment " + appl_status
            else:
                comment = "Lease " + appl_status

        oa_status = ""
        if purpose == "New Lease":
            oa_status = "2051 Expire"

        for count, call_sign in enumerate(call_signs):
            if lease_ids:
                info = [
                    call_sign,
                    file_num,
                    purpose,
                    appl_status,
                    party,
                    lease_ids[count],
                    commence_dates[count],
                    expiration_dates[count],
                    comment,
                    oa_status,
                ]
                for_df.append(info)
            elif expiration_dates:
                info = [
                    call_sign,
                    file_num,
                    purpose,
                    appl_status,
                    party,
                    "n/a",
                    commence_dates[count],
                    expiration_dates[count],
                    comment,
                    oa_status,
                ]
                for_df.append(info)
            else:
                info = [
                    call_sign,
                    file_num,
                    purpose,
                    appl_status,
                    party,
                    "n/a",
                    appl_status,
                    appl_status,
                    comment,
                    oa_status,
                ]
                for_df.append(info)
    return for_df


def get_result_soup():
    # Set up browser
    browser = browser_setup()

    # Input criteria into form
    input_ebs_update(browser)

    # Submit & Get number of results
    soup = BeautifulSoup(browser.submit().read(), "html.parser")
    num_pages = int(soup.find("b", text="1").find_next_sibling().text) // 100 + 1

    # Get applications on first page, also urls for linked "next" pages
    page_urls = []
    appl_links = []
    for link in browser.links():
        if len(link.attrs) < 2:
            continue
        if re.match("Page .+", link.attrs[1][1]) and link.url not in page_urls:
            page_urls.append(link.url)
        elif re.search("applID.+", link.url):
            appl_links.append(link.url)

    # Create remaining page links, then get applications on every page
    create_remaining_pages(page_urls, num_pages)
    for url in page_urls:
        get_appl_links(browser, url, appl_links)

    # Get info for applications
    for_df = create_df_data(appl_links)

    data_frame = pd.DataFrame(
        for_df,
        columns=[
            "Call Sign",
            "File Number",
            "File Purpose",
            "Application Status",
            "Party in Interest",
            "Lease ID",
            "Commenced",
            "Expires",
            "Comment",
            "OA Status",
        ],
    )
    data_frame.to_csv("update_results.csv", index=False)
