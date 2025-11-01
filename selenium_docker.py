from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException
import time
from dotenv import load_dotenv
import os

def open_whatsapp():
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Remote(
        command_executor='http://localhost:4444/wd/hub',
        options=chrome_options
    )
    
    wait = WebDriverWait(driver, 30)

    try:
        print("Opening WhatsApp Web...")
        driver.get("https://web.whatsapp.com")

        print("Please scan QR code via VNC viewer at http://localhost:7900 (password: secret)")
        print("Waiting for WhatsApp to load (up to 5 minutes)...")
        
        # Wait for chat list to appear (indicates successful login)
        try:
            WebDriverWait(driver, 300).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#side [role="textbox"][contenteditable="true"]'))
            )
            print("WhatsApp Web loaded successfully!")
        except TimeoutException:
            print("Timeout waiting for WhatsApp to load. Please ensure QR code was scanned.")
            raise
        
        # Load environment variables
        load_dotenv()
        group_name = os.getenv("GROUP_NAME")
        
        # Check if GROUP_NAME exists
        if not group_name:
            print("ERROR: GROUP_NAME not found!")
            print("Available environment variables:")
            for key in os.environ.keys():
                if 'GROUP' in key:
                    print(f"  {key} = {os.environ[key]}")
            raise ValueError("GROUP_NAME environment variable is not set. Please set it with -e GROUP_NAME='your group name'")
        
        print(f"env group name: {group_name}")

        # --- Focus the LEFT SIDEBAR search box ---
        search_box = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#side [role="textbox"][contenteditable="true"]')
        ))
        search_box.click()
        search_box.send_keys(Keys.CONTROL, 'a')
        search_box.send_keys(Keys.BACK_SPACE)
        search_box.send_keys(group_name)

        # --- Select the first search result ---
        first_result = None
        try:
            results = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'div[data-testid="cell-frame-container"]')
                )
            )
            if results:
                first_result = results[0]
        except TimeoutException:
            pass

        if not first_result:
            try:
                results = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, '//div[@role="listbox"]//div[@role="option"]')
                    )
                )
                if results:
                    first_result = results[0]
            except TimeoutException:
                pass

        if first_result:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", first_result)
            driver.execute_script("arguments[0].click();", first_result)
        else:
            ActionChains(driver).send_keys(Keys.ARROW_DOWN).send_keys(Keys.ENTER).perform()

        print(f"Opened group: {group_name}")
        time.sleep(10)

        # --- Read last 20 messages ---
        messages = driver.find_elements(By.CSS_SELECTOR, '[data-pre-plain-text]')

        last_20 = messages[-20:] if len(messages) >= 20 else messages

        message_data = []
        for msg in last_20:
            try:
                # Extract metadata 
                meta = msg.get_attribute("data-pre-plain-text")
                if meta:
                    meta = meta.strip("[]")
                    timestamp, sender = meta.split("] ")[0], meta.split("] ")[1].replace(":", "")
                else:
                    timestamp, sender = "?", "?"

                # Extract message text
                text_elems = msg.find_elements(By.CSS_SELECTOR, 'span.selectable-text span')
                text = " ".join([t.text for t in text_elems]) if text_elems else ""

                message_data.append({
                    "sender": sender,
                    "timestamp": timestamp,
                    "text": text
                })
            except Exception as e:
                print("Error reading message:", e)

        print("\n=== Last 20 messages ===")
        for m in message_data:
            print(m)

        print("\nFinished reading messages!")
        print(f"{len(message_data)} messages read")
        return message_data

    finally:
        driver.quit()
        print("Browser closed.")