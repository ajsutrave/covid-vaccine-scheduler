#!/usr/bin/env python3

import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import StaleElementReferenceException

URL = 'https://vaccine.heb.com/scheduler'
STORE_ELEM = 'sc-iBPRYJ.cKWKVL'
APPOINTMENT_CARD_XPATH = '//*[@id=\'container\']/c-f-s-registration/div/div[1]/div[3]/lightning-card/article/div[2]'


VACCINE_TYPE_XPATH     = '//*[@id="container"]/c-f-s-registration/div/div[1]/div[3]/lightning-card/article/div[2]/slot/div/form/div/lightning-combobox[1]/div/lightning-base-combobox/div'
APPOINTMENT_DATE_XPATH = '//*[@id="container"]/c-f-s-registration/div/div[1]/div[3]/lightning-card/article/div[2]/slot/div/form/div/lightning-combobox[2]/div/lightning-base-combobox/div'
APPOINTMENT_TIME_XPATH = '//*[@id="container"]/c-f-s-registration/div/div[1]/div[3]/lightning-card/article/div[2]/slot/div/form/div/lightning-combobox[3]/div/lightning-base-combobox/div'

CONTINUE_BUTTON_XPATH = '//*[@id="container"]/c-f-s-registration/div/div[1]/div[4]/lightning-button/button'

SCHEDULE_APPOINTMENT_BUTTON_XPATH = '//*[@id="container"]/c-f-s-registration/div/div[1]/div[4]/lightning-button[2]/button'

ERROR_BANNER = '//*[@id=\'container\']/c-f-s-registration/div/div[1]/div[3]/div'



recent_failed = {}
driver = webdriver.Chrome()

def get_store():
    # Wait for page to lead
    driver.get(URL)
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, STORE_ELEM)))

    for store in driver.find_elements_by_class_name(STORE_ELEM):
        try:
            address = store.find_element_by_tag_name('address').text
            if address in recent_failed: continue
        except StaleElementReferenceException as e:
            print( e )
            return None
        available = False
        for store_elem in store.find_elements_by_xpath(".//*"):
            if ("View times" in store_elem.text):
                store_elem.click()
                return address
        
        if not available: return None
            

def reserve_appointment():
    print( "Trying to find a store with vaccines available...", end='')
    while True:
        address = None
        while not address: address = get_store(); time.sleep(1)
        print(".", end='')

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body')))
        body = driver.find_element_by_tag_name('body')
        if "Appointments are no longer available for this location" in body.text:
            recent_failed[address] = datetime.now()
            continue
        print(".", end='')

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, APPOINTMENT_CARD_XPATH)))
        card = driver.find_element_by_xpath(APPOINTMENT_CARD_XPATH)
        if "There are no available time slots" in card.text:
            recent_failed[address] = datetime.now()
            continue
        print(".", end='')

        vaccine_type = driver.find_element_by_xpath(VACCINE_TYPE_XPATH)
        appointment_date = driver.find_element_by_xpath(APPOINTMENT_DATE_XPATH)
        appointment_time = driver.find_element_by_xpath(APPOINTMENT_TIME_XPATH)


        appointment_date.click()
        appointment_date_options = appointment_date.find_elements_by_tag_name("lightning-base-combobox-item")
        appointment_date_options[0].click()

        appointment_time.click()
        appointment_time_options = appointment_time.find_elements_by_tag_name("lightning-base-combobox-item")
        appointment_time_options[0].click()

        driver.find_element_by_xpath(CONTINUE_BUTTON_XPATH).click()
        
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, SCHEDULE_APPOINTMENT_BUTTON_XPATH)))
        except TimeoutException as e:
            print(".", end='')

        return

if __name__ == "__main__":
    reserve_appointment()

    # Now wait if someone closes the window
    while True:
        try:
            _ = driver.window_handles
        except WebDriverException as e:
            break
        time.sleep(1)
