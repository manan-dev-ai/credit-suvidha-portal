from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import requests 
import os # <--- ADDED THIS TO FIX THE PATH ERROR

# --- CONFIGURATION ---
DASHBOARD_URL = "http://127.0.0.1:5000/add_via_bot" 

# --- PATH FIXER (Crucial Step) ---
# This converts "./User_Data_Bot_New" into "C:\Users\Manan\..."
# Chrome needs this full address to work.
current_folder = os.getcwd()
profile_path = os.path.join(current_folder, "User_Data_Bot_Final") 

# --- CHROME SETUP ---
options = Options()
options.add_argument(f"--user-data-dir={profile_path}") 
options.add_argument("--profile-directory=Default")

# Crash Prevention Arguments
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--remote-debugging-pipe")
options.add_argument("--disable-gpu") 
options.add_argument("--start-maximized")

print(f"🚀 Launching WhatsApp Bot...")
print(f"📂 Saving profile to: {profile_path}")

try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://web.whatsapp.com")
    
    print("\n👉 Please scan the QR Code if asked.")
    input("✅ Press ENTER here ONLY after your chats are visible on screen...")
    
except Exception as e:
    print(f"\n❌ CRASH ERROR: {e}")
    print("👉 Solution: Run 'taskkill /IM chrome.exe /F' in terminal.")
    exit()

# --- HELPER FUNCTIONS ---

def get_last_message_text():
    """Reads the text of the very last message in the open chat"""
    try:
        messages = driver.find_elements(By.CSS_SELECTOR, "div.message-in")
        if messages:
            return messages[-1].text
    except: 
        return ""
    return ""

def send_whatsapp_message(message):
    """Types a message into the box and hits Enter"""
    try:
        input_box = driver.find_elements(By.CSS_SELECTOR, "div[contenteditable='true']")
        if input_box:
            box = input_box[-1] 
            box.click()
            time.sleep(0.5)
            box.send_keys(message + Keys.ENTER)
            print(f"📤 Bot Replied: {message}")
            time.sleep(1) 
    except Exception as e:
        print(f"❌ Error sending: {e}")

def notify_dashboard(name, msg):
    """Sends the new lead data to your main.py dashboard"""
    try:
        requests.post(DASHBOARD_URL, data={'name': name, 'msg': msg})
        print("💾 Saved to Dashboard Database")
    except:
        print("⚠️ Dashboard not running? Could not save to Excel.")

# --- MAIN BOT LOOP ---

print("\n✅ BOT IS ACTIVE! Waiting for new green messages...")

while True:
    try:
        # 1. Look for Green Badges
        unread_badges = driver.find_elements(By.XPATH, "//span[@aria-label][contains(@aria-label, 'unread message')]")
        
        if unread_badges:
            unread_badges[0].click()
            time.sleep(1.5) 
            
            # 2. Get Contact Name
            try:
                contact_name = driver.find_element(By.XPATH, "//header//span[@title]").text
            except:
                contact_name = "Unknown Client"
            
            # 3. Read Message
            incoming_msg = get_last_message_text()
            print(f"\n📩 New Message from {contact_name}: {incoming_msg}")
            
            # 4. BOT LOGIC
            msg_lower = incoming_msg.lower()
            
            if "visit" in msg_lower or "office" in msg_lower:
                send_whatsapp_message("ચોક્કસ! અમારી ઓફિસ નો સમય સવારે 10 થી સાંજે 7 છે. (Address: CG Road). અમે તમારી રાહ જોઈશું! 🏢")
                notify_dashboard(contact_name, "Visit Request")
                
            elif "hdfc" in msg_lower or "sbi" in msg_lower or "axis" in msg_lower:
                bank_name = "Unknown"
                if "hdfc" in msg_lower: bank_name = "HDFC"
                if "sbi" in msg_lower: bank_name = "SBI"
                if "axis" in msg_lower: bank_name = "AXIS"
                
                send_whatsapp_message(f"આભાર! {bank_name} કાર્ડ માટે સર્વિસ ઉપલબ્ધ છે. ✅ હવે તમારું નામ અને બિલની રકમ લખો.")
                notify_dashboard(contact_name, f"Card: {bank_name}")
                
            elif "hi" in msg_lower or "hello" in msg_lower:
                send_whatsapp_message("નમસ્તે! CredSuvidha માં સ્વાગત છે. શું તમારે ક્રેડિટ કાર્ડનું બિલ ભરવું છે? (Reply 'Yes')")
                notify_dashboard(contact_name, "New Inquiry")
                
            else:
                print("👉 Unknown message, no auto-reply sent.")
                notify_dashboard(contact_name, "New Inquiry")

            # 5. Reset
            webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(1)
            
        time.sleep(2) 
        
    except KeyboardInterrupt:
        print("🛑 Bot Stopped by User")
        break
    except Exception as e:
        pass