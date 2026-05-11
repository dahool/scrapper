from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
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
chrome_binary_path = '/usr/bin/google-chrome'

print(f"Initializing Chrome WebDriver at {driver_path}...")

options = ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument("window-size=1920,1080")
options.binary_location = chrome_binary_path

service = Service(executable_path=driver_path)
driver = None

def wait_for_table_rows(driver, wait, min_rows=1):
    """Espera a que la tabla tenga al menos min_rows filas de datos."""
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "table tbody tr")) >= min_rows)

def extract_table_data(driver):
    """Extrae headers y filas de la tabla actual."""
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.find("table")
    if not table:
        print("WARNING: No se encontró tabla en la página.")
        return [], []
    rows = table.find_all("tr")
    headers = [h.text.strip() for h in rows[0].find_all("th")]
    data = []
    for row in rows[1:]:
        cells = row.find_all("td")
        if cells:
            data.append([cell.get_text(strip=True) for cell in cells])
    return headers, data

def set_page_size_to_max(driver, wait):
    """
    Hace click en el selector de tamaño de página y elige la opción máxima (100).
    """
    try:
        # Click en el select trigger (el combobox de tamaño)
        select_trigger = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-slot='select-trigger']"))
        )
        select_trigger.click()
        time.sleep(0.5)

        # Buscar y clickear la opción "100" en el dropdown
        options_elements = driver.find_elements(By.CSS_SELECTOR, "[role='option']")
        for opt in options_elements:
            if opt.text.strip() == "100":
                opt.click()
                print("Tamaño de página cambiado a 100.")
                time.sleep(1)  # Esperar re-render
                return True

        print("WARNING: No se encontró la opción 100 en el selector.")
        return False
    except Exception as e:
        print(f"WARNING: No se pudo cambiar el tamaño de página: {e}")
        return False

def get_page_buttons(driver):
    """
    Retorna los botones de página numéricos (excluye flechas prev/next).
    """
    buttons = driver.find_elements(By.CSS_SELECTOR, "[data-slot='button']")
    page_buttons = []
    for btn in buttons:
        text = btn.text.strip()
        if text.isdigit():
            page_buttons.append((int(text), btn))
    return sorted(page_buttons, key=lambda x: x[0])

try:
    print("Attempting to initialize WebDriver...")
    driver = webdriver.Chrome(service=service, options=options)
    print(f"WebDriver initialized. Chrome: {driver.capabilities['browserVersion']}")

    print(f"Accessing URL: {url}")
    driver.get(url)

    wait = WebDriverWait(driver, 20)

    # Esperar carga inicial
    wait_for_table_rows(driver, wait)
    print("Tabla cargada.")

    # Intentar poner el máximo de filas por página
    set_page_size_to_max(driver, wait)
    wait_for_table_rows(driver, wait)

    all_data = []
    headers = []
    current_page = 1

    while True:
        print(f"Scrapeando página {current_page}...")

        # Esperar a que la tabla esté lista
        wait_for_table_rows(driver, wait)
        time.sleep(0.3)  # pequeño margen para re-renders

        page_headers, page_data = extract_table_data(driver)

        if not headers and page_headers:
            headers = page_headers

        print(f"  Filas encontradas en página {current_page}: {len(page_data)}")
        all_data.extend(page_data)

        # Buscar botón de la siguiente página
        page_buttons = get_page_buttons(driver)
        next_page_num = current_page + 1
        next_btn = next((btn for num, btn in page_buttons if num == next_page_num), None)

        if not next_btn:
            print(f"No hay página {next_page_num}. Scraping completo.")
            break

        # Click en la siguiente página
        try:
            driver.execute_script("arguments[0].click();", next_btn)
            current_page = next_page_num
            time.sleep(0.5)
        except StaleElementReferenceException:
            print("StaleElementReferenceException al navegar. Reintentando...")
            time.sleep(1)
            continue

    # Escribir CSV
    print(f"\nTotal de filas scrapeadas: {len(all_data)}")
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(all_data)

    print(f"Data exportada a {csv_filename}")

except Exception as e:
    print(f"Error durante el scraping: {e}")
    if driver:
        try:
            print("--- Page Source on Error (primeros 2000 chars) ---")
            print(driver.page_source[:2000])
        except Exception as ps_err:
            print(f"No se pudo obtener page source: {ps_err}")
    sys.exit(1)

finally:
    if driver:
        print("Cerrando WebDriver...")
        driver.quit()
        print("WebDriver cerrado.")