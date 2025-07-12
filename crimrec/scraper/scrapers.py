import os
import time
import csv
import logging
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
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
        
        # Validate credentials
        if not self.login_email or not self.login_password:
            raise ValueError("ECLERKS_EMAIL and ECLERKS_PASSWORD must be set in environment variables")
        
        self.setup_driver()

    def setup_driver(self):
        """Setup Chrome driver with improved stability options"""
        try:
            options = uc.ChromeOptions()
            
            # Basic options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--start-maximized")
            
            # Anti-detection options
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Stability options
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            
            # Network and timeout options
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-background-networking")
            options.add_argument("--disable-ipc-flooding-protection")
            
            # Memory and performance
            options.add_argument("--memory-pressure-off")
            options.add_argument("--max_old_space_size=4096")
            
            if self.headless:
                options.add_argument("--headless=new")
            
            # Initialize driver with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.driver = uc.Chrome(options=options, version_main=None)
                    self.driver.implicitly_wait(10)
                    self.driver.set_page_load_timeout(60)  # Increased timeout
                    self.driver.set_script_timeout(30)  # Add script timeout
                    logger.info(f"ChromeDriver initialized successfully (attempt {attempt + 1})")
                    break
                except Exception as e:
                    logger.warning(f"ChromeDriver initialization attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(2)
                    
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise

    def login(self):
        """Login to eClerks with improved error handling"""
        try:
            logger.info("Attempting to login...")
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Wait for email field
            email_field = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@placeholder="email address"]'))
            )
            email_field.clear()
            email_field.send_keys(self.login_email)
            
            # Find and fill password field
            password_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@placeholder="password"]'))
            )
            password_field.clear()
            password_field.send_keys(self.login_password)
            
            # Click login button
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@title="Login"]'))
            )
            login_button.click()
            
            # Wait for successful login
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Hello')]"))
            )
            logger.info("Login successful")
            return True
            
        except TimeoutException:
            logger.error("Login timeout - page elements not found")
            return False
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False

    def navigate_to_search_page(self):
        """Navigate to criminal search page with improved error handling"""
        try:
            logger.info("Navigating to search page...")
            self.driver.get(self.base_url)
            time.sleep(5)  # Give page more time to load
            
            # Try multiple strategies to find the criminal search button
            search_button_selectors = [
                (By.ID, "criminal-search-step1"),
                (By.XPATH, "//button[contains(text(), 'Criminal')]"),
                (By.XPATH, "//a[contains(text(), 'Criminal')]"),
                (By.XPATH, "//*[contains(@id, 'criminal') and contains(@id, 'search')]"),
                (By.XPATH, "//button[contains(@class, 'criminal') or contains(@onclick, 'criminal')]"),
            ]
            
            search_button = None
            for selector_type, selector_value in search_button_selectors:
                try:
                    search_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    logger.info(f"Found criminal search button using: {selector_value}")
                    break
                except TimeoutException:
                    continue
            
            if not search_button:
                logger.error("Could not find criminal search button")
                return False
                
            # Click the search button
            search_button.click()
            time.sleep(5)
            
            # Handle EULA if present
            try:
                scrollable_div = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "statewide-portal-eula-body"))
                )
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                time.sleep(2)
                
                accept_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "fetch-criminal-search"))
                )
                accept_button.click()
                time.sleep(5)
                logger.info("Accepted EULA")
            except TimeoutException:
                logger.info("EULA not found, proceeding...")
            
            # Switch to new window if opened
            if len(self.driver.window_handles) > 1:
                logger.info(f"Found {len(self.driver.window_handles)} windows, switching to latest")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                time.sleep(3)
                
            # Wait for the search page to fully load
            try:
                WebDriverWait(self.driver, 20).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                logger.info("Page loading completed")
            except TimeoutException:
                logger.warning("Page may not have fully loaded, but continuing...")
                
            logger.info("Successfully navigated to search page")
            return True
            
        except Exception as e:
            logger.error(f"Navigation to search page failed: {str(e)}")
            return False

    def set_date_range(self, from_date="01/01/2020", to_date="01/07/2025"):
        """Set date range with improved error handling and multiple element detection strategies"""
        try:
            logger.info(f"Setting date range: {from_date} to {to_date}")
            
            # Wait for page to fully load
            time.sleep(3)
            
            # Try multiple strategies to find date fields
            date_field_strategies = [
                # Strategy 1: Current IDs
                {
                    'start_selectors': [
                        (By.ID, "datefield-1029-inputEl"),
                        (By.ID, "datefield-1028-inputEl"),
                        (By.ID, "datefield-1027-inputEl"),
                    ],
                    'end_selectors': [
                        (By.ID, "datefield-1030-inputEl"),
                        (By.ID, "datefield-1031-inputEl"),
                        (By.ID, "datefield-1032-inputEl"),
                    ]
                },
                # Strategy 2: Generic date field patterns
                {
                    'start_selectors': [
                        (By.XPATH, "//input[contains(@id, 'datefield') and contains(@id, 'inputEl')][1]"),
                        (By.XPATH, "//input[@placeholder='Start Date' or @placeholder='From Date']"),
                        (By.XPATH, "//input[contains(@class, 'date') and contains(@name, 'start')]"),
                    ],
                    'end_selectors': [
                        (By.XPATH, "//input[contains(@id, 'datefield') and contains(@id, 'inputEl')][2]"),
                        (By.XPATH, "//input[@placeholder='End Date' or @placeholder='To Date']"),
                        (By.XPATH, "//input[contains(@class, 'date') and contains(@name, 'end')]"),
                    ]
                },
                # Strategy 3: More generic patterns
                {
                    'start_selectors': [
                        (By.XPATH, "//input[@type='text' and contains(@id, 'date')][1]"),
                        (By.XPATH, "//div[contains(@class, 'date')]//input[1]"),
                    ],
                    'end_selectors': [
                        (By.XPATH, "//input[@type='text' and contains(@id, 'date')][2]"),
                        (By.XPATH, "//div[contains(@class, 'date')]//input[2]"),
                    ]
                }
            ]
            
            start_date = None
            end_date = None
            
            # Try each strategy
            for strategy_num, strategy in enumerate(date_field_strategies, 1):
                logger.info(f"Trying date field strategy {strategy_num}...")
                
                # Try to find start date field
                for selector_type, selector_value in strategy['start_selectors']:
                    try:
                        start_date = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((selector_type, selector_value))
                        )
                        logger.info(f"Found start date field using: {selector_value}")
                        break
                    except TimeoutException:
                        continue
                
                # Try to find end date field
                for selector_type, selector_value in strategy['end_selectors']:
                    try:
                        end_date = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((selector_type, selector_value))
                        )
                        logger.info(f"Found end date field using: {selector_value}")
                        break
                    except TimeoutException:
                        continue
                
                # If we found both fields, break out of strategy loop
                if start_date and end_date:
                    logger.info(f"Successfully found both date fields using strategy {strategy_num}")
                    break
                else:
                    # Reset for next strategy
                    start_date = None
                    end_date = None
            
            # If we still haven't found the fields, try to debug the page
            if not start_date or not end_date:
                logger.error("Could not find date fields. Debugging page structure...")
                self._debug_page_structure()
                return False
            
            # Format dates
            from_date_fmt = datetime.strptime(from_date, "%m/%d/%Y").strftime("%m/%d/%Y")
            to_date_fmt = datetime.strptime(to_date, "%m/%d/%Y").strftime("%m/%d/%Y")

            # Clear existing values and set new ones
            logger.info("Clearing and setting date values...")
            
            # Method 1: Direct value setting with JavaScript
            try:
                self.driver.execute_script("arguments[0].value = '';", start_date)
                self.driver.execute_script("arguments[0].value = arguments[1];", start_date, from_date_fmt)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", start_date)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", start_date)
                
                self.driver.execute_script("arguments[0].value = '';", end_date)
                self.driver.execute_script("arguments[0].value = arguments[1];", end_date, to_date_fmt)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", end_date)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", end_date)
                
                logger.info("Set dates using JavaScript method")
                
            except Exception as js_error:
                logger.warning(f"JavaScript method failed: {js_error}")
                
                # Method 2: Selenium send_keys
                try:
                    start_date.clear()
                    start_date.send_keys(from_date_fmt)
                    
                    end_date.clear()
                    end_date.send_keys(to_date_fmt)
                    
                    logger.info("Set dates using Selenium send_keys method")
                    
                except Exception as selenium_error:
                    logger.error(f"Selenium method also failed: {selenium_error}")
                    return False
            
            # Give the page time to process the date changes
            time.sleep(2)
            
            # Verify the dates were set
            try:
                start_value = self.driver.execute_script("return arguments[0].value;", start_date)
                end_value = self.driver.execute_script("return arguments[0].value;", end_date)
                
                logger.info(f"Date verification - Start: {start_value}, End: {end_value}")
                
                if start_value and end_value:
                    logger.info("Date range set successfully")
                    return True
                else:
                    logger.error("Date values appear to be empty after setting")
                    return False
                    
            except Exception as e:
                logger.warning(f"Could not verify date values: {e}")
                # Continue anyway, the dates might still be set
                logger.info("Date range set successfully (verification failed but continuing)")
                return True
             
        except Exception as e:
            logger.error(f"Failed to set date range: {str(e)}")
            return False

    def _debug_page_structure(self):
        """Debug helper to understand page structure when date fields can't be found"""
        try:
            logger.info("=== PAGE STRUCTURE DEBUG ===")
            
            # Get page title
            title = self.driver.title
            logger.info(f"Page title: {title}")
            
            # Get current URL
            url = self.driver.current_url
            logger.info(f"Current URL: {url}")
            
            # Look for any input fields
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            logger.info(f"Found {len(inputs)} input fields on page")
            
            for i, input_field in enumerate(inputs[:10]):  # Limit to first 10
                try:
                    input_type = input_field.get_attribute("type")
                    input_id = input_field.get_attribute("id")
                    input_name = input_field.get_attribute("name")
                    input_class = input_field.get_attribute("class")
                    input_placeholder = input_field.get_attribute("placeholder")
                    
                    logger.info(f"Input {i+1}: type='{input_type}', id='{input_id}', name='{input_name}', class='{input_class}', placeholder='{input_placeholder}'")
                except Exception as e:
                    logger.info(f"Input {i+1}: Could not get attributes - {e}")
            
            # Look for date-related elements
            date_elements = self.driver.find_elements(By.XPATH, "//*[contains(@id, 'date') or contains(@class, 'date') or contains(@name, 'date')]")
            logger.info(f"Found {len(date_elements)} date-related elements")
            
            for i, element in enumerate(date_elements[:5]):  # Limit to first 5
                try:
                    tag_name = element.tag_name
                    element_id = element.get_attribute("id")
                    element_class = element.get_attribute("class")
                    element_name = element.get_attribute("name")
                    
                    logger.info(f"Date element {i+1}: tag='{tag_name}', id='{element_id}', class='{element_class}', name='{element_name}'")
                except Exception as e:
                    logger.info(f"Date element {i+1}: Could not get attributes - {e}")
                    
            logger.info("=== END DEBUG ===")
            
        except Exception as e:
            logger.error(f"Debug page structure failed: {e}")

    def execute_search(self):
        """Execute search with improved error handling"""
        try:
            logger.info("Executing search...")
            
            # Try multiple selectors for the search button
            search_button_selectors = [
                (By.ID, "submitButton"),
                (By.XPATH, "//button[contains(text(), 'Search')]"),
                (By.XPATH, "//input[@type='submit']"),
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//button[contains(@class, 'submit') or contains(@class, 'search')]"),
                (By.XPATH, "//*[contains(@onclick, 'search') or contains(@onclick, 'submit')]"),
            ]
            
            search_button = None
            for selector_type, selector_value in search_button_selectors:
                try:
                    search_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    logger.info(f"Found search button using: {selector_value}")
                    break
                except TimeoutException:
                    continue
            
            if not search_button:
                logger.error("Could not find search button")
                return False
                
            # Click the search button
            search_button.click()
            logger.info("Search button clicked")
            
            # Wait for results with multiple strategies
            results_found = False
            result_selectors = [
                "//div[contains(@id, 'gridview')]/table",
                "//table[contains(@class, 'grid') or contains(@class, 'result')]",
                "//div[contains(@class, 'results')]//table",
                "//table//tbody/tr[td]",  # Any table with data rows
            ]
            
            for selector in result_selectors:
                try:
                    WebDriverWait(self.driver, 45).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    logger.info(f"Found results table using: {selector}")
                    results_found = True
                    break
                except TimeoutException:
                    continue
            
            if not results_found:
                logger.error("No results table found after search")
                # Try to see if there's a "no results" message
                try:
                    no_results = self.driver.find_element(By.XPATH, "//*[contains(text(), 'No results') or contains(text(), 'no records') or contains(text(), 'not found')]")
                    logger.info("Search completed but no results found")
                    return True  # This is actually successful - just no data
                except:
                    pass
                return False
            
            # Scroll to load all content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            logger.info("Search executed successfully")
            return True
            
        except TimeoutException:
            logger.error("Search timeout - results table not found")
            return False
        except Exception as e:
            logger.error(f"Search execution failed: {str(e)}")
            return False

    def scrape_records(self, max_pages=1):
        """Scrape records with improved error handling"""
        try:
            logger.info(f"Starting to scrape records (max {max_pages} pages)")
            current_page = 1
            
            while current_page <= max_pages:
                logger.info(f"Scraping page {current_page}")
                
                # Try multiple strategies to find table rows
                rows = None
                row_selectors = [
                    "//div[contains(@id, 'gridview')]/table/tbody/tr",
                    "//table[contains(@class, 'grid')]/tbody/tr",
                    "//table[contains(@class, 'result')]/tbody/tr",
                    "//div[contains(@class, 'results')]//table/tbody/tr",
                    "//table//tbody/tr[td]",  # Any table with data rows
                    "//table/tr[td]",  # Direct table rows
                ]
                
                for selector in row_selectors:
                    try:
                        rows = WebDriverWait(self.driver, 15).until(
                            EC.presence_of_all_elements_located((By.XPATH, selector))
                        )
                        logger.info(f"Found {len(rows)} rows using selector: {selector}")
                        break
                    except TimeoutException:
                        continue
                
                if not rows:
                    logger.error("Could not find any table rows")
                    self._debug_results_structure()
                    return False
                
                page_records = 0
                for row_index, row in enumerate(rows):
                    try:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        logger.debug(f"Row {row_index + 1}: Found {len(cols)} columns")
                        
                        if len(cols) < 5:  # Minimum required columns (name, case_number, date, charges, parish)
                            logger.debug(f"Row {row_index + 1}: Skipping - insufficient columns")
                            continue
                            
                        # Debug: Print first few column values
                        col_values = []
                        for i, col in enumerate(cols[:10]):  # First 10 columns
                            try:
                                value = col.text.strip()[:50]  # First 50 chars
                                col_values.append(f"col{i}: '{value}'")
                            except:
                                col_values.append(f"col{i}: <error>")
                        logger.debug(f"Row {row_index + 1} values: {', '.join(col_values)}")
                        
                        # Extract record data with flexible mapping
                        record = {
                            'defendant_name': cols[0].text.strip() if len(cols) > 0 else '',
                            'birth_date': self.parse_date(cols[1].text.strip()) if len(cols) > 1 else None,
                            'sex': cols[2].text.strip()[:1] if len(cols) > 2 and cols[2].text.strip() else 'U',
                            'race': cols[3].text.strip()[:1] if len(cols) > 3 and cols[3].text.strip() else 'U',
                            'case_number': cols[4].text.strip() if len(cols) > 4 else '',
                            'date_filed': self.parse_date(cols[5].text.strip()) if len(cols) > 5 else None,
                            'charges': cols[6].get_attribute("innerText").replace('\n', ', ').strip() if len(cols) > 6 else '',
                            'arrest_citation_date': self.parse_date(cols[7].text.strip()) if len(cols) > 7 else None,
                            'parish': cols[8].text.strip() if len(cols) > 8 else '',
                            'alert_available': len(cols) > 9 and bool(cols[9].find_elements(By.CLASS_NAME, 'action-alert'))
                        }
                        
                        # Skip if no case number or defendant name
                        if not record['case_number'] or not record['defendant_name']:
                            logger.debug(f"Row {row_index + 1}: Skipping - missing case number or name")
                            continue
                        
                        # Set default date if missing
                        if not record['date_filed']:
                            record['date_filed'] = datetime.now().date()
                            
                        # Save to database
                        CriminalRecord.objects.update_or_create(
                            case_number=record['case_number'],
                            defaults=record
                        )
                        
                        self.records.append(record)
                        page_records += 1
                        logger.info(f"Saved record: {record['case_number']} - {record['defendant_name']}")
                        
                    except Exception as e:
                        logger.error(f"Error processing row {row_index + 1}: {str(e)}")
                        continue
                
                logger.info(f"Scraped {page_records} records from page {current_page}")
                
                # Try to navigate to next page
                if current_page < max_pages:
                    try:
                        next_btn = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Next')] | //button[contains(., 'Next')]"))
                        )
                        
                        if "disabled" in next_btn.get_attribute("class"):
                            logger.info("Next button is disabled, no more pages")
                            break
                            
                        next_btn.click()
                        time.sleep(3)
                        current_page += 1
                        
                    except TimeoutException:
                        logger.info("No next button found, ending pagination")
                        break
                else:
                    break
                    
            logger.info(f"Scraping completed. Total records: {len(self.records)}")
            return True
            
        except Exception as e:
            logger.error(f"Scraping failed: {str(e)}")
            return False
    
    def _debug_results_structure(self):
        """Debug helper to understand results table structure"""
        try:
            logger.info("=== RESULTS TABLE DEBUG ===")
            
            # Find all tables
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            logger.info(f"Found {len(tables)} tables on page")
            
            for i, table in enumerate(tables):
                try:
                    table_id = table.get_attribute("id")
                    table_class = table.get_attribute("class")
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    
                    logger.info(f"Table {i+1}: id='{table_id}', class='{table_class}', rows={len(rows)}")
                    
                    if len(rows) > 0:
                        # Show first few rows
                        for j, row in enumerate(rows[:3]):
                            cols = row.find_elements(By.TAG_NAME, "td")
                            if len(cols) == 0:
                                cols = row.find_elements(By.TAG_NAME, "th")
                            
                            col_texts = []
                            for col in cols[:5]:  # First 5 columns
                                text = col.text.strip()[:20]  # First 20 chars
                                col_texts.append(f"'{text}'")
                            
                            logger.info(f"  Row {j+1}: {len(cols)} cols - {', '.join(col_texts)}")
                            
                except Exception as e:
                    logger.info(f"Table {i+1}: Error getting info - {e}")
                    
            logger.info("=== END RESULTS DEBUG ===")
            
        except Exception as e:
            logger.error(f"Debug results structure failed: {e}")

    def export_to_csv(self, filename="scraped_records.csv"):
        """Export scraped records to CSV"""
        try:
            if not self.records:
                logger.warning("No records to export")
                return
                
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
        """Parse date string with multiple format support"""
        if not date_str or date_str.strip() == "":
            return None
            
        date_str = date_str.strip()
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None

    def run(self, from_date="01/01/2020", to_date="01/07/2025", max_pages=1):
        """Main scraper execution method"""
        try:
            logger.info("Starting scraper execution...")
            
            if not self.login():
                raise Exception("Login failed")
                
            if not self.navigate_to_search_page():
                raise Exception("Search page navigation failed")
                
            # Try to set date range, but continue even if it fails
            date_range_success = self.set_date_range(from_date, to_date)
            if not date_range_success:
                logger.warning("Date range setting failed, but continuing with search anyway")
                logger.info("The search may return all available records or use default date range")
                
            if not self.execute_search():
                raise Exception("Search execution failed")
                
            if not self.scrape_records(max_pages):
                raise Exception("Scraping failed")
                
            self.export_to_csv()
            
            if date_range_success:
                logger.info("Scraper run completed successfully.")
            else:
                logger.info("Scraper run completed successfully (with date range fallback).")
                
            return True
            
        except Exception as e:
            logger.error(f"Scraper run error: {str(e)}")
            return False
        finally:
            self.quit()

    def quit(self):
        """Safely quit the browser"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")
            finally:
                self.driver = None
