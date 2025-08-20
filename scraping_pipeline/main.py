import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from pymongo import MongoClient
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv("config.env")

# Fixed MongoDB connection - use the URI from environment
mongodb_uri = os.getenv("MONGODB_URI")
if not mongodb_uri:
    print("ERROR: MONGODB_URI environment variable not set")
    exit(1)

client = MongoClient(mongodb_uri)
db = client['Scrapper']
main_db = db['posts']
log_db = db['logs']

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

def log_event(message):
    log_db.insert_one({"timestamp": time.ctime(), "event": message})
    print(message)

def login_with_credentials(driver, email, password):
    try:
        driver.get('https://www.linkedin.com/login')
        wait = WebDriverWait(driver, 15)
        
        if email is None or password is None:
            raise ValueError("Email or password is missing.")

        # Wait for and fill email field
        email_field = wait.until(EC.element_to_be_clickable((By.ID, "username")))
        email_field.clear()
        email_field.send_keys(email)
        
        # Wait for and fill password field
        password_field = wait.until(EC.element_to_be_clickable((By.ID, "password")))
        password_field.clear()
        password_field.send_keys(password)
        
        # Click sign in button
        sign_in_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        sign_in_button.click()
        
        # Wait for successful login by checking for the feed or home page
        try:
            wait.until(EC.any_of(
                EC.presence_of_element_located((By.CLASS_NAME, "global-nav")),
                EC.presence_of_element_located((By.CLASS_NAME, "feed-container")),
                EC.url_contains("feed")
            ))
            log_event("✅ Logged in successfully")
            return True
        except:
            log_event("❌ Login may have failed - checking for CAPTCHA or other issues")
            return False
            
    except Exception as e:
        log_event(f"❌ Credential login failed: {e}")
        return False

def get_search_jobs_fetched_latest(driver, job_title, mode):
    try:
        # Build search URL with proper encoding and sorting
        encoded_job_title = job_title.replace(" ", "%20")
        
        # Set sort parameter based on mode
        if mode == "date_posted" or mode == "latest":
            sort_param = "date_posted"
            mode_tag = "latest"
        else:  # relevance or top_match
            sort_param = "relevance" 
            mode_tag = "top_match"
        
        search_url = f'https://www.linkedin.com/search/results/content/?keywords={encoded_job_title}&sortBy=%22{sort_param}%22'
        
        log_event(f"🔗 Navigating to: {search_url}")
        log_event(f"🏷️ Mode: {mode_tag}")
        driver.get(search_url)
        
        wait = WebDriverWait(driver, 15)
        
        # Wait for the page to load completely
        time.sleep(5)
        
        # No need to click sort buttons since we're using URL parameters
        log_event(f"✅ Using URL-based sorting: {sort_param}")
        
        # Scroll to load more content
        log_event("📜 Scrolling to load posts...")
        for i in range(15):
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(1.5)
            
            # Check if we've reached the end
            if i % 5 == 0:
                current_height = driver.execute_script("return document.body.scrollHeight")
                if i > 0 and current_height == previous_height:
                    break
                previous_height = current_height
        
        # Try to expand "see more" buttons
        try:
            see_more_buttons = driver.find_elements(By.XPATH, 
                "//button[contains(@aria-label, 'see more') or contains(text(), 'see more') or contains(text(), '…more')]")
            
            for button in see_more_buttons[:10]:  # Limit to first 10 to avoid timeout
                try:
                    if button.is_displayed():
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(0.5)
                except:
                    continue
            
            log_event(f"✅ Expanded {len(see_more_buttons)} 'see more' buttons")
        except Exception as e:
            log_event(f"⚠️ Error expanding posts: {e}")
        
        time.sleep(3)
        
        # Parse the page content
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        total_text = []
        post_selectors = [
            'div.update-components-text',
            'div[data-id*="update"]',
            'div.feed-shared-update-v2__description-wrapper',
            'span[dir="ltr"]',
            'div.attributed-text-segment-list__content'
        ]
        
        for selector in post_selectors:
            if '.' in selector:
                class_name = selector.split('.')[1]
                posts = soup.find_all('div', class_=class_name)
            else:
                posts = soup.select(selector)
            
            if posts:
                log_event(f"📝 Found {len(posts)} posts with selector: {selector}")
                for post in posts:
                    try:
                        # Extract text content
                        text_content = ""
                        
                        # Get all text from spans and divs
                        text_elements = post.find_all(['span', 'div', 'p'], string=True)
                        for element in text_elements:
                            text = element.get_text(strip=True)
                            if text and len(text) > 10:  # Filter out very short text
                                text_content += text + " "
                        
                        # Clean up the text
                        text_content = text_content.strip()
                        
                        # Only add substantial content
                        if len(text_content) > 50 and text_content not in total_text:
                            total_text.append(text_content)
                            log_event(f"📄 Extracted post: {text_content[:100]}...")
                            
                    except Exception as e:
                        continue
                
                if total_text:
                    break  # Stop if we found posts with this selector
        
        # If no posts found with specific selectors, try a broader approach
        if not total_text:
            log_event("🔍 Trying broader content extraction...")
            all_spans = soup.find_all('span', {'dir': 'ltr'})
            
            for span in all_spans:
                text = span.get_text(strip=True)
                if text and len(text) > 30 and text not in total_text:
                    # Filter out navigation and UI text
                    skip_words = ['Like', 'Comment', 'Share', 'Follow', 'Connect', 'Save', 'Send', 'LinkedIn', 'Home', 'My Network']
                    if not any(skip_word in text for skip_word in skip_words):
                        total_text.append(text)
                        log_event(f"📄 Broad extraction: {text[:100]}...")
        
        # Save to database if we have content
        if total_text:
            main_db.insert_one({
                "job_title": job_title,
                "mode": mode,
                "mode_tag": mode_tag,
                "results": total_text,
                "count": len(total_text),
                "timestamp": time.ctime(),
                "url": search_url
            })
            log_event(f"💾 Saved {len(total_text)} posts to database with tag: {mode_tag}")
        
        return {"job_text": total_text}
        
    except Exception as e:
        log_event(f"⚠️ Error in fetching job posts: {str(e)}")
        # Take a screenshot for debugging
        try:
            driver.save_screenshot(f"/app/debug_screenshot_{int(time.time())}.png")
            log_event("📸 Debug screenshot saved")
        except:
            pass
        return {"job_text": []}

if __name__ == "__main__":
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    job_title = os.getenv("JOB_TITLE", "hiring")
    mode = os.getenv("MODE", "date_posted")

    log_event(f"🚀 Starting scraper with job_title: '{job_title}', mode: '{mode}'")
    
    if not login_with_credentials(driver, email, password):
        log_event("❌ Exiting due to login failure.")
        driver.quit()
        exit()

    log_event("🔄 Running job search every 5 minutes. Press Ctrl+C to stop.")
    try:
        while True:
            # Search with latest (date_posted) mode first
            log_event(f"🔍 Searching for LATEST posts - job title: {job_title}")
            data_latest = get_search_jobs_fetched_latest(driver, job_title, "latest")
            log_event(f"✅ Fetched {len(data_latest['job_text'])} LATEST posts")
            
            # Wait a bit between searches to avoid rate limiting
            time.sleep(10)
            
            # Search with top match (relevance) mode
            log_event(f"🔍 Searching for TOP MATCH posts - job title: {job_title}")
            data_relevance = get_search_jobs_fetched_latest(driver, job_title, "relevance")
            log_event(f"✅ Fetched {len(data_relevance['job_text'])} TOP MATCH posts")
            
            total_posts = len(data_latest['job_text']) + len(data_relevance['job_text'])
            log_event(f"📊 Total posts fetched this cycle: {total_posts}")
            
            if total_posts == 0:
                log_event("⚠️ No posts found in both searches. This might indicate:")
                log_event("   - LinkedIn has changed their layout")
                log_event("   - The search term returned no results")
                log_event("   - Login session expired")
                log_event("   - CAPTCHA or rate limiting triggered")
            
            log_event("⏳ Waiting 5 minutes before next search cycle...")
            time.sleep(300)  # 5 minutes
    except KeyboardInterrupt:
        log_event("🛑 Script interrupted by user.")
    finally:
        driver.quit()
        log_event("🔚 Driver closed successfully")