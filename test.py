import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
import time

options = Options()

preferences = {"download.default_directory": "C:\\Users\\Aidan McManus\\PycharmProjects\\2.5_Database_Update\\2.5 Map Files"}

options.add_experimental_option("prefs", preferences)
options.add_argument("--headless")

driver = webdriver.Chrome(service=Service('C:\\Users\\Aidan McManus\\PycharmProjects\\2.5_Database_Update\\chromedriver.exe'), options=options)

driver.get("https://wireless2.fcc.gov/UlsApp/UlsSearch/licenseMap.jsp?licKey=4447455")
selector = Select(driver.find_element(by="id", value="sel-download"))
selector.select_by_visible_text("KML")
time.sleep(0.5)
driver.get("https://wireless2.fcc.gov/UlsApp/UlsSearch/licenseMap.jsp?licKey=4303671")
selector = Select(driver.find_element(by="id", value="sel-download"))
selector.select_by_visible_text("KML")
time.sleep(0.5)
driver.close()
