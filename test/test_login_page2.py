from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import random



# CONFIGURATION

BASE_URL = "http://127.0.0.1:8000"
EMAIL = "sukantacb20@gmail.com"
PASSWORD = "12345678"
TOURNAMENT_NAME = "Testing Premier League"

driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver, 15)



# HELPER FUNCTIONS

def human_type(element, text):
    """Type text slowly like a human"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.12))


def smooth_scroll_to(element):
    """Smooth scroll element into view"""
    driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", element)
    time.sleep(random.uniform(0.8, 1.2))


def scroll_and_click(element):
    """Smooth scroll and perform click via JS"""
    smooth_scroll_to(element)
    driver.execute_script("arguments[0].click();", element)
    time.sleep(random.uniform(0.6, 1.0))


def confirmation_done():
    """Click OK on confirmation modal"""
    confirmation = wait.until(EC.element_to_be_clickable((By.ID, "confirmation_ok")))
    scroll_and_click(confirmation)


def smooth_scroll_page():
    """Smoothly scroll through entire page"""
    driver.execute_script("""
        let pos = 0;
        const step = 300;
        const delay = 200;
        const scrollHeight = document.body.scrollHeight;
        function scrollDown() {
            if (pos < scrollHeight) {
                window.scrollBy(0, step);
                pos += step;
                setTimeout(scrollDown, delay);
            }
        }
        scrollDown();
    """)
    time.sleep(3)



#  STEP 1: LOGIN

driver.get(f"{BASE_URL}/login")
print("\n🚀 Opening login page...")

email_input = wait.until(EC.visibility_of_element_located((By.NAME, "email")))
password_input = wait.until(EC.visibility_of_element_located((By.NAME, "password")))

human_type(email_input, EMAIL)
human_type(password_input, PASSWORD)

login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
scroll_and_click(login_btn)
print("✅ Logged in successfully!")
time.sleep(2)

smooth_scroll_page()

# STEP 2: CREATE TOURNAMENT

create_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='verify_modal']")))
scroll_and_click(create_btn)

# --- Page 1 ---
tournament_name_input = wait.until(EC.visibility_of_element_located((By.ID, "tournament_name")))
desc_input = driver.find_element(By.ID, "tournament_descriptions")

human_type(tournament_name_input, TOURNAMENT_NAME)
human_type(desc_input, "This tournament is created for Selenium testing")

trophy_radio = driver.find_element(By.CSS_SELECTOR, "input[type='radio'][value='Trophy3.png']")
scroll_and_click(trophy_radio)

scroll_and_click(driver.find_element(By.ID, "next1"))

try:
    wait.until(EC.alert_is_present()).accept()
    print("✅ JS alert handled successfully")
except:
    print("⚠️ No alert appeared — continuing...")

# --- Page 2 ---
Select(driver.find_element(By.ID, "select_type")).select_by_value("online")
Select(driver.find_element(By.ID, "player_type")).select_by_value("single")

scroll_and_click(driver.find_element(By.ID, "next1"))

# --- Page 3 ---
scroll_and_click(wait.until(EC.element_to_be_clickable((By.ID, "League"))))
Select(driver.find_element(By.ID, "team_num")).select_by_value("6")

scroll_and_click(driver.find_element(By.ID, "next2"))

confirmation_done()
print("🏆 Tournament created successfully!")

# --- Open created tournament ---
cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".tournament-card")))
latest_card = cards[0]
smooth_scroll_to(latest_card)
view_button = latest_card.find_element(By.LINK_TEXT, "View")
scroll_and_click(view_button)

# STEP 3: ADD TEAMS

add_teams_btn = wait.until(EC.element_to_be_clickable((By.ID, "add_teams")))
scroll_and_click(add_teams_btn)


team_inputs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#team_fields_container input[type='text']")))
team_names = ["Tigers", "Lions", "Eagles", "Lions", "Sharks", "Wolves"]

for input_box, name in zip(team_inputs, team_names):
    input_box.clear()
    human_type(input_box, name)

scroll_and_click(wait.until(EC.element_to_be_clickable((By.ID, "team_submit"))))


try:
    alert = wait.until(EC.alert_is_present())
    print(f"⚠️ Alert Text: {alert.text}")
    alert.accept()
    print("✅ Duplicate alert handled.")
except:
    print("❌ No alert found.")

# Fix duplicate
team_inputs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#team_fields_container input[type='text']")))
team_inputs[3].clear()
human_type(team_inputs[3], "Panthers")

scroll_and_click(driver.find_element(By.ID, "team_submit"))
print("✅ Teams added successfully!")
time.sleep(2)


#  STEP 4: SET MATCH DATE & SCORE

match_card = wait.until(EC.presence_of_element_located((By.ID, "match-1")))
smooth_scroll_to(match_card)

scroll_and_click(wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#match-1 .date-btn"))))
date_field = wait.until(EC.presence_of_element_located((By.ID, "match_date")))
driver.execute_script("arguments[0].value = '2025-10-25T15:30';", date_field)

scroll_and_click(wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".date-save-btn"))))
print("✅ Match date set successfully!")

update_score_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#match-1 .update_score")))
scroll_and_click(update_score_btn)

team1_input = wait.until(EC.presence_of_element_located((By.ID, "team1_score")))
team2_input = wait.until(EC.presence_of_element_located((By.ID, "team2_score")))
team1_input.clear()
team2_input.clear()
human_type(team1_input, "2")
human_type(team2_input, "1")

scroll_and_click(wait.until(EC.element_to_be_clickable((By.ID, "submit_score_btn"))))
print("✅ Match score updated (2–1)!")


# STEP 5: LEADERBOARD & FIXTURE VIEW

smooth_scroll_page()

leaderboard_btn = wait.until(EC.element_to_be_clickable((By.ID, "tournament-leaderboard")))
scroll_and_click(leaderboard_btn)
print("🏆 Viewing Leaderboard...")
time.sleep(2)

fixture_btn = wait.until(EC.element_to_be_clickable((By.ID, "fixture")))
scroll_and_click(fixture_btn)
print("📅 Viewing Fixture page...")

search_input = wait.until(EC.visibility_of_element_located((By.NAME, "q")))
search_input.clear()
human_type(search_input, "Eagles")

search_btn = wait.until(EC.element_to_be_clickable((By.ID, "team_search")))
scroll_and_click(search_btn)
print("🔍 Team searched successfully!")

smooth_scroll_page()


#STEP 6: DELETE & ADD TOURNAMENT

scroll_and_click(wait.until(EC.element_to_be_clickable((By.ID, "delete_tournament"))))
scroll_and_click(wait.until(EC.element_to_be_clickable((By.ID, "delete_confirmation"))))
confirmation_done()

# Add again via code
scroll_and_click(wait.until(EC.element_to_be_clickable((By.ID, "add_tournament_btn"))))
tournament_input = wait.until(EC.presence_of_element_located((By.ID, "tournament_code")))
human_type(tournament_input, "THN14M")
scroll_and_click(wait.until(EC.element_to_be_clickable((By.ID, "add_new_tournament"))))
confirmation_done()

latest_card = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "tournament-card")))[0]
smooth_scroll_to(latest_card)
view_button = latest_card.find_element(By.LINK_TEXT, "View")
scroll_and_click(view_button)


# Remove joined tournament
scroll_and_click(wait.until(EC.element_to_be_clickable((By.ID, "remove_tournament"))))
scroll_and_click(wait.until(EC.element_to_be_clickable((By.ID, "remove_confirmation"))))
confirmation_done()


#STEP 7: FOLLOW PUBLIC TOURNAMENT

scroll_and_click(wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='add_tournament2']"))))
code_input = wait.until(EC.presence_of_element_located((By.ID, "tournament_code2")))
human_type(code_input, "THN14M")
scroll_and_click(wait.until(EC.element_to_be_clickable((By.ID, "go_button"))))

leaderboard_link = wait.until(EC.element_to_be_clickable((By.ID, "tournament-leaderboard")))
scroll_and_click(leaderboard_link)
home_link = wait.until(EC.element_to_be_clickable((By.ID, "leaderboard_home")))
scroll_and_click(home_link)
time.sleep(1)

logout_button = wait.until(EC.element_to_be_clickable((By.ID, "logout")))
logout_button.click()


time.sleep(2)

driver.quit()
print("All automation steps completed smoothly!")
