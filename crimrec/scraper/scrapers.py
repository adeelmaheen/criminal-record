import os
import time
import csv
import logging
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.utils.timezone import now
from .models import CriminalRecord

logger = logging.getLogger(__name__)

class EClerksScraper:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.login_email = os.getenv('ECLERKS_EMAIL')
        self.login_password = os.getenv('ECLERKS_PASSWORD')
        self.base_url = "https://eclerksla.com/Home"
        self.records = []
        self.setup_driver()

    def setup_driver(self):
        try:
            options = uc.ChromeOptions()
            options.headless = self.headless
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
            if self.headless:
                options.add_argument("--headless=new")
            self.driver = uc.Chrome(options=options, use_subprocess=True)
            self.driver.implicitly_wait(5)
            logger.info("ChromeDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise

    def login(self):
        try:
            self.driver.get(self.base_url)
            time.sleep(3)
            email = WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@placeholder="email address"]'))
            )
            email.send_keys(self.login_email)
            password = self.driver.find_element(By.XPATH, '//*[@placeholder="password"]')
            password.send_keys(self.login_password)
            login_button = self.driver.find_element(By.XPATH, '//*[@title="Login"]')
            login_button.click()
            WebDriverWait(self.driver, 20).until(
                lambda d: d.find_elements(By.XPATH, "//*[contains(text(), 'Hello')]")
            )
            logger.info("Login successful")
            return True
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False

    def navigate_to_search_page(self):
        try:
            self.driver.get(self.base_url)
            time.sleep(2)
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "criminal-search-step1"))
            )
            search_button.click()
            time.sleep(2)
            scrollable_div = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "statewide-portal-eula-body"))
            )
            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            time.sleep(1)
            accept_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "fetch-criminal-search"))
            )
            accept_button.click()
            time.sleep(3)
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"navigate_to_search_page failed: {str(e)}")
            return False

    def set_date_range(self, from_date="01/01/2020", to_date="01/07/2025"):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "datefield-1029-inputEl"))
            )
            start_date = self.driver.find_element(By.ID, "datefield-1029-inputEl")
            end_date = self.driver.find_element(By.ID, "datefield-1030-inputEl")

            from_date_fmt = datetime.strptime(from_date, "%m/%d/%Y").strftime("%m/%d/%Y")
            to_date_fmt = datetime.strptime(to_date, "%m/%d/%Y").strftime("%m/%d/%Y")

            self.driver.execute_script("arguments[0].value = arguments[1];", start_date, from_date_fmt)
            self.driver.execute_script("arguments[0].value = arguments[1];", end_date, to_date_fmt)

            logger.info("Date range set via JS using new IDs")
            return True
        except Exception as e:
            logger.error(f"Failed to set date range: {str(e)}")
            return False

    def execute_search(self):
        try:
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "submitButton"))
            )
            search_button.click()
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@id, 'gridview')]/table"))
            )
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            logger.info("Search executed.")
            return True
        except Exception as e:
            logger.error(f"Executing search failed: {str(e)}")
            return False

    def scrape_records(self, max_pages=1):
        try:
            current_page = 1
            while current_page <= max_pages:
                rows = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@id, 'gridview')]/table/tbody/tr"))
                )
                for row in rows:
                    try:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        if len(cols) < 10:
                            continue
                        record = {
                            'defendant_name': cols[0].text.strip(),
                            'birth_date': self.parse_date(cols[1].text.strip()),
                            'sex': cols[2].text.strip(),
                            'race': cols[3].text.strip(),
                            'case_number': cols[4].text.strip(),
                            'date_filed': self.parse_date(cols[5].text.strip()),
                            'charges': cols[6].get_attribute("innerText").replace('\n', ', ').strip(),
                            'arrest_citation_date': self.parse_date(cols[7].text.strip()),
                            'parish': cols[8].text.strip(),
                            'alert_available': bool(cols[9].find_elements(By.CLASS_NAME, 'action-alert'))
                        }
                        CriminalRecord.objects.update_or_create(
                            case_number=record['case_number'],
                            defaults=record
                        )
                        self.records.append(record)
                        logger.info(f"Saved record: {record['case_number']}")
                    except Exception as e:
                        logger.error(f"Row parsing error: {str(e)}")
                try:
                    next_btn = self.driver.find_element(By.XPATH, "//a[contains(., 'Next')] | //button[contains(., 'Next')]")
                    if "disabled" not in next_btn.get_attribute("class"):
                        next_btn.click()
                        current_page += 1
                        time.sleep(2)
                    else:
                        break
                except Exception:
                    break
            return True
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")
            return False

    def export_to_csv(self, filename="scraped_records.csv"):
        try:
            keys = ['defendant_name', 'birth_date', 'sex', 'race', 'case_number', 'date_filed', 'charges', 'arrest_citation_date', 'parish', 'alert_available']
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=keys)
                writer.writeheader()
                writer.writerows(self.records)
            logger.info(f"Exported {len(self.records)} records to {filename}")
        except Exception as e:
            logger.error(f"Failed to export CSV: {str(e)}")

    @staticmethod
    def parse_date(date_str):
        for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue
        return None

    def run(self, from_date="01/01/2020", to_date="01/07/2025", max_pages=1):
        try:
            if not self.login():
                raise Exception("Login failed")
            if not self.navigate_to_search_page():
                raise Exception("Search page navigation failed")
            if not self.set_date_range(from_date, to_date):
                raise Exception("Failed to set search criteria")
            if not self.execute_search():
                raise Exception("Search execution failed")
            if not self.scrape_records(max_pages):
                raise Exception("Scraping failed")
            self.export_to_csv()
            logger.info("Scraper run completed successfully.")
            return True
        except Exception as e:
            logger.error(f"Scraper run error: {str(e)}")
            return False
        finally:
            self.quit()

    def quit(self):
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed.")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")
