import requests
import PyPDF2
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from tqdm import tqdm
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Function to count keyword occurrences in a webpage using Selenium
def count_keyword_occurrences_webpage(url, keyword):
    options = Options()
    options.headless = True

    # Set Tor proxy settings
    tor_proxy_host = '127.0.0.1'
    tor_proxy_port = 9050

    # Set Firefox binary
    firefox_binary = FirefoxBinary('/Applications/Tor Browser.app/Contents/MacOS/firefox')

    # Set Firefox options
    options.binary = firefox_binary

    # Set Tor proxy profile settings
    profile = webdriver.FirefoxProfile()
    profile.set_preference('network.proxy.type', 1)
    profile.set_preference('network.proxy.socks', tor_proxy_host)
    profile.set_preference('network.proxy.socks_port', tor_proxy_port)
    profile.set_preference('network.proxy.socks_version', 5)
    profile.set_preference('network.proxy.no_proxies_on', '')

    driver = webdriver.Firefox(service=Service(executable_path=GeckoDriverManager().install()), firefox_profile=profile, options=options)

    try:
        driver.get(url)

        # Wait for the page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.XPATH, "//body")))


        alert = driver.switch_to.alert
        # Get the text of the alert
        alert_text = alert.text
        # Accept or dismiss the alert based on its text
        if "Wollen Sie englischsprachige Versionen von Websites anfordern?" in alert_text:
            # If the alert text matches, dismiss the alert using JavaScript
            driver.execute_script("arguments[0].dismiss();", alert)
        else:
            # Otherwise, accept the alert using JavaScript
            driver.execute_script("arguments[0].accept();", alert)
    except:
        # If no alert is present, continue with scraping
        pass

    try:
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        solo_body = soup.body
        if solo_body is None:
            print(f"Error parsing web page: {url}")
            return 0
        else:
            body = solo_body.text.lower()
            keyword_count = body.count(keyword.lower())
            return keyword_count
    finally:
        driver.quit()

# Function to count keyword occurrences in a PDF file
def count_keyword_occurrences_pdf(url, keyword):
    response = requests.get(url)
    with open('temp.pdf', 'wb') as pdf_file:
        pdf_file.write(response.content)
    with open('temp.pdf', 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        keyword_count = 0
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                keyword_count += text.lower().count(keyword.lower())
    return keyword_count

# CSV file paths
input_csv_file_path = 'test.csv'
output_csv_file_path = 'output.csv'

# Keyword to count
keyword = 'like-minded'

# Open input CSV file for reading and output CSV file for writing with specified encoding
with open(input_csv_file_path, 'r', encoding='ISO-8859-1') as input_csv_file, open(output_csv_file_path, 'w', newline='') as output_csv_file:
    csv_reader = csv.DictReader(input_csv_file)
    fieldnames = csv_reader.fieldnames + ['Keyword Count']
    csv_writer = csv.DictWriter(output_csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    total_rows = sum(1 for _ in csv_reader) # Total number of rows in input CSV file
    input_csv_file.seek(0)  # Reset the file pointer to the beginning of the file for progress tracking
    next(csv_reader)  # Skip header row

    # Loop through each row in the input CSV file with progress bar
    for row in tqdm(csv_reader, total=total_rows - 1, desc='Progress', unit='row'):  # Subtracting 1 for header row
        link = row['Link']
        if link.endswith('.pdf'):
            keyword_count = count_keyword_occurrences_pdf(link, keyword)
        else:
            keyword_count = count_keyword_occurrences_webpage(link, keyword)
        row['Keyword Count'] = keyword_count
        csv_writer.writerow(row)
