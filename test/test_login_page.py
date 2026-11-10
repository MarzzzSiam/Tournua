from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time


BASE_URL = "http://127.0.0.1:8000"
EMAIL = "sukantacb20@gmail.com"
PASSWORD = "12345678"
TOURNAMENT_NAME = "Premier Trophy 2025"


driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver, 10)

# LOGIN
driver.get(f"{BASE_URL}/login")

wait.until(EC.visibility_of_element_located((By.NAME, "email"))).send_keys(EMAIL)
driver.find_element(By.NAME, "password").send_keys(PASSWORD)
driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

print("✅ Logged in successfully!")
time.sleep(2)



#  CREATE NEW TOURNAMENT
create_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='verify_modal']")))
create_btn.click()
time.sleep(1)

# PAGE 1
wait.until(EC.visibility_of_element_located((By.ID, "tournament_name"))).send_keys(TOURNAMENT_NAME)
driver.find_element(By.ID, "tournament_descriptions").send_keys("Season’s grand tournament for all teams!")

trophy = driver.find_element(By.CSS_SELECTOR, "input[name='trophy'][value='Trophy1.png']")
driver.execute_script("arguments[0].click();", trophy)
Select(driver.find_element(By.ID, "select_type")).select_by_value("offline")
Select(driver.find_element(By.ID, "player_type")).select_by_value("team")

driver.find_element(By.ID, "next1").click()
time.sleep(1)

# PAGE 2
format_radio = driver.find_element(By.CSS_SELECTOR, "input[name='format'][value='League']")
driver.execute_script("arguments[0].click();", format_radio)
Select(driver.find_element(By.ID, "select_group")).select_by_value("2")
Select(driver.find_element(By.ID, "team_num")).select_by_value("8")
driver.find_element(By.ID, "next2").click()
time.sleep(1)

# PAGE 3
team_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'][name^='team']")
team_names = ["Tigers", "Lions", "Eagles", "Sharks", "Falcons", "Dragons", "Panthers", "Wolves"]
for field, name in zip(team_inputs, team_names):
    field.send_keys(name)
    time.sleep(0.2)

driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
print("🏆 Tournament created successfully!")


time.sleep(5)


cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".tournament-card")))


latest_card = cards[0]  # If newest is shown first; change to [-1] if last
view_button = latest_card.find_element(By.LINK_TEXT, "View")
view_button.click()

time.sleep(2)

wait = WebDriverWait(driver, 20)

match_cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".match")))

latest_match_card = match_cards[0]

set_date_button = latest_match_card.find_element(By.CSS_SELECTOR, ".date-btn")
driver.execute_script("arguments[0].click();", set_date_button)


date_input = wait.until(EC.presence_of_element_located((By.ID, "match_date")))

date_input.clear()
date_input.send_keys("2025-10-16T15:45")

save_btn = wait.until(EC.element_to_be_clickable(
    (By.CSS_SELECTOR, ".date-save-btn")
))

driver.execute_script("arguments[0].click();", save_btn)
driver.refresh()
time.sleep(5)

wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".modal-box")))

print("✅ Test completed successfully!")

time.sleep(3)
driver.quit()