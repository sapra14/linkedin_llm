# scraper.py

from selenium import webdriver
from bs4 import BeautifulSoup
import time
import json

def get_linkedin_data(url, email, password):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # No browser popup
    driver = webdriver.Chrome(options=options)

    driver.get("https://www.linkedin.com/login")
    time.sleep(2)

    driver.find_element("id", "username").send_keys(email)
    driver.find_element("id", "password").send_keys(password)
    driver.find_element("xpath", "//button[@type='submit']").click()
    time.sleep(3)

    driver.get(url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    name = soup.find("h1").get_text(strip=True)
    title = soup.find("div", class_="text-body-medium").get_text(strip=True)

    return {"name": name, "title": title}

def save_profiles():
    email = "your_email"
    password = "your_password"
    urls = [
        "https://www.linkedin.com/in/example1",
        "https://www.linkedin.com/in/example2"
    ]

    profiles = [get_linkedin_data(url, email, password) for url in urls]
    with open("linkedin_profiles.json", "w") as f:
        json.dump(profiles, f, indent=4)

# Uncomment to run scraping:
# save_profiles()
