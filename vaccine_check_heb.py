#!/usr/bin/env python3
import re
import time
import sys

from datetime import datetime
from pgeocode import GeoDistance
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

KM_TO_MILES = 0.621371

recent_failed = {}

driver = webdriver.Chrome()
driver.minimize_window()

dist = GeoDistance('us')

class StoreAddress():
    def __init__(self, address, user_zip_code):
        self.address = address
        self.zip_code = re.search('\d\d\d\d\d', self.address).group(0)
        self.distance = dist.query_postal_code(self.zip_code, user_zip_code) * KM_TO_MILES
    def __repr__(self):
        return self.address + "\n(" + str(self.distance) + " miles away)"
        

def get_store(max_distance, zip_code):
    # Wait for page to lead
    driver.get(URL)
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, STORE_ELEM)))

    for store in driver.find_elements_by_class_name(STORE_ELEM):
        try:
            store_address = StoreAddress(address = store.find_element_by_tag_name('address').text,
                                         user_zip_code = zip_code)
            
            if store_address in recent_failed or \
               store_address.distance > max_distance: continue

        except StaleElementReferenceException as e:
            print( e )
            return None
        available = False
        for store_elem in store.find_elements_by_xpath(".//*"):
            if ("View times" in store_elem.text):
                store_elem.click()
                return store_address
        
        if not available: return None
            

def reserve_appointment(max_distance, zip_code):
    print( "Trying to find a store with vaccines available...", end='')
    while True:
        store_address = None
        while not store_address: store_address = get_store(max_distance, zip_code)
        print(".", end='')

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body')))
        body = driver.find_element_by_tag_name('body')
        if "Appointments are no longer available for this location" in body.text:
            recent_failed[store_address] = datetime.now()
            continue
        print(".", end='')

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, APPOINTMENT_CARD_XPATH)))
        card = driver.find_element_by_xpath(APPOINTMENT_CARD_XPATH)
        if "There are no available time slots" in card.text:
            recent_failed[store_address] = datetime.now()
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

        driver.maximize_window()

        try:
            notification = notify.Notify()
            notification.title = "Vaccine Found"
            notification.message = store_address
            notification.send()
        except: 
            print("Vaccine Found")
            print(store_address)
        return

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--zip-code',type=int)
    parser.add_argument('--max-distance',type=int)
    args = parser.parse_args()
    

    reserve_appointment(args.max_distance, args.zip_code)

    # Now wait if someone closes the window
    while True:
        try:
            _ = driver.window_handles
        except WebDriverException as e:
            break
        time.sleep(1)
