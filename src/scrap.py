from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions # Import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException # Import TimeoutException
from bs4 import BeautifulSoup
import csv
import time
import os
import sys

# config
url = os.environ['SCRAP_URL']
csv_filename = os.environ['OUTPUT']
# Path to the ChromeDriver executable within the Docker container
driver_path = '/usr/local/bin/chromedriver'
# Path to the Google Chrome binary within the Docker container
chrome_binary_path = '/usr/bin/google-chrome' # Standard location after .deb install

print(f"Initializing Chrome WebDriver at {driver_path}...")
print(f"Using Chrome binary at {chrome_binary_path}")

# Configure Chrome options for headless operation in Docker
options = ChromeOptions() # Use imported Options
options.add_argument('--headless')  # Run Chrome in headless mode (no GUI)
options.add_argument('--no-sandbox') # Required for running as root in Docker
options.add_argument('--disable-dev-shm-usage') # Overcome limited resource problems
options.add_argument('--disable-gpu') # Often needed in headless/docker environments
options.add_argument("window-size=1920,1080") # Set a reasonable window size

# *** Add this line to explicitly set the Chrome binary location ***
options.binary_location = chrome_binary_path

service = Service(executable_path=driver_path)
driver = None # Initialize driver to None

try:
    # Initialize the Chrome driver with the specified options and service
    print("Attempting to initialize WebDriver...")
    driver = webdriver.Chrome(service=service, options=options)
    print(f"Successfully initialized WebDriver. Chrome version: {driver.capabilities['browserVersion']}")

    print(f"Attempting to access URL: {url}")
    driver.get(url)
    print("Page requested. Waiting for dynamic content...")

    # === IMPORTANT: Wait Strategy ===
    # Using a fixed sleep is simple but unreliable. It's better to wait for a
    # specific element that indicates the content you need has loaded.
    # Inspect the page (using browser dev tools) to find a unique ID, class,
    # or XPath for an element that appears *after* the JavaScript loads the data.

    # Example using WebDriverWait (Recommended):
    wait_time = 20 # Max seconds to wait
    # Replace 'some-data-container' with an actual ID/selector from the target page
    # target_element_selector = (By.ID, 'some-data-container')
    target_element_selector = (By.TAG_NAME, 'body') # Example: Wait for body tag (very basic)

    try:
        print(f"Waiting up to {wait_time} seconds for element: {target_element_selector}...")
        wait = WebDriverWait(driver, wait_time)
        wait.until(EC.presence_of_element_located(target_element_selector))
        print("Target element found or timeout reached for basic check.")
    except TimeoutException:
        print("Timed out waiting for the basic page element. Scraping might fail or be incomplete.")

    # Optional: Add a small extra sleep if needed after element wait
    # time.sleep(2)

    # Get the page source after JavaScript rendering
    print("Retrieving page source...")
    page_source = driver.page_source
    print(f"Page source retrieved. Length: {len(page_source)} characters.")

    # --- Add your data extraction logic here ---
    # Now you can parse 'page_source' with BeautifulSoup or use driver.find_element(s)
    print(f"Page Title: {driver.title}")

    # Example: Find an element by its tag name (replace 'h1' as needed)
    # try:
    #     header_element = driver.find_element(By.TAG_NAME, 'h1')
    #     print(f"Found H1 element: {header_element.text}")
    # except Exception as find_err:
    #     print(f"Could not find H1 element: {find_err}")


    # Parse the HTML
    soup = BeautifulSoup(page_source, "html.parser")

    # Find the table and rows
    table = soup.find("table")
    rows = table.find_all("tr")

    # Extract headers
    headers = [header.text.strip() for header in rows[0].find_all("th")]

    # Extract data
    data = []
    for row in rows[1:]:
        cells = row.find_all("td")
        row_data = [cell.get_text(strip=True) for cell in cells]
        data.append(row_data)

    # Write to CSV
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)  # Write headers
        writer.writerows(data)    # Write rows

    print(f"Data has been successfully exported to {csv_filename}")
    # --- End of data extraction logic ---

except Exception as e:
    print(f"An error occurred during scraping: {e}")
    # Optionally print page source on error for debugging
    if driver:
       try:
           print("--- Page Source on Error ---")
           print(driver.page_source[:2000]) # Print first 2000 chars
           print("----------------------------")
       except Exception as ps_err:
           print(f"Could not get page source on error: {ps_err}")
    sys.exit(1)

finally:
    # Ensure the browser is closed even if errors occur
    if driver:
        print("Closing the WebDriver...")
        driver.quit()
        print("WebDriver closed.")

