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
STORE_ELEM = 'sc-iBPRYJ.uDpEv'

APPOINTMENT_CARD_XPATH = '//*[@id="container"]/c-f-s-registration/div/div[1]/div[3]/lightning-card/article/div[2]'
VACCINE_TYPE_XPATH     = APPOINTMENT_CARD_XPATH + '/slot/div/form/div/lightning-combobox[1]/div/lightning-base-combobox/div'
APPOINTMENT_DATE_XPATH = APPOINTMENT_CARD_XPATH + '/slot/div/form/div/lightning-combobox[2]/div/lightning-base-combobox/div'
APPOINTMENT_TIME_XPATH = APPOINTMENT_CARD_XPATH + '/slot/div/form/div/lightning-combobox[3]/div/lightning-base-combobox/div'
CONTINUE_BUTTON_XPATH = '//*[@id="container"]/c-f-s-registration/div/div[1]/div[4]/lightning-button/button'


PERSONAL_INFO_XPATH_PREFIX = '//*[@id="container"]/c-f-s-registration/div/div[1]/div[3]/div/lightning-card/article/div[2]/slot/div/form/div/'
FIRST_NAME_XPATH             = PERSONAL_INFO_XPATH_PREFIX + 'lightning-input[1]/div[1]'
LAST_NAME_XPATH              = PERSONAL_INFO_XPATH_PREFIX + 'lightning-input[2]/div[1]'
EMAIL_XPATH                  = PERSONAL_INFO_XPATH_PREFIX + 'lightning-input[3]/div[1]'
PHONE_NUMBER_XPATH           = PERSONAL_INFO_XPATH_PREFIX + 'div[1]/input'
DATE_OF_BIRTH_XPATH          = PERSONAL_INFO_XPATH_PREFIX + 'div[2]/input'

HAVE_INSURANCE_XPATH         = PERSONAL_INFO_XPATH_PREFIX + 'lightning-combobox[1]/div[1]/lightning-base-combobox/div'
INSURANCE_COMPANY_NAME_XPATH = PERSONAL_INFO_XPATH_PREFIX + 'lightning-input[5]/div[1]'
INSURANCE_ID_NUMBER_XPATH    = PERSONAL_INFO_XPATH_PREFIX + 'lightning-input[6]/div[1]'
INSURANCE_GROUP_NUMBER_XPATH = PERSONAL_INFO_XPATH_PREFIX + 'lightning-input[7]/div[1]'
ELIGIBILITY_XPATH            = PERSONAL_INFO_XPATH_PREFIX + 'lightning-combobox[2]/div/lightning-base-combobox/div'

SCHEDULE_APPOINTMENT_BUTTON_XPATH = '//*[@id="container"]/c-f-s-registration/div/div[1]/div[4]/lightning-button[2]/button'

KM_TO_MILES = 0.621371

recent_failed = {}


dist = GeoDistance('us')

class StoreAddress():
    def __init__(self, address, user_zip_code):
        self.address = address
        self.zip_code = re.search('[78]\d\d\d\d', self.address).group(0)
        self.distance = dist.query_postal_code(self.zip_code, user_zip_code) * KM_TO_MILES
    def __repr__(self):
        return self.address + "\n(" + str(self.distance) + " miles away)"
        
class HEBVaccineChecker():
    def __init__(self, browser, browser_driver_path):
        if browser == "Chrome":
            self.driver = webdriver.Chrome(browser_driver_path)
        elif browser == "Firefox":
            self.driver = webdriver.Firefox(browser_driver_path)
        self.driver.minimize_window()

    def get_store(self, max_distance, zip_code):
        # Wait for page to load
        self.driver.get(URL)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, STORE_ELEM)))
        except TimeoutException: return None

        for store in self.driver.find_elements_by_class_name(STORE_ELEM):
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


    def reserve_appointment(max_distance, zip_code, personal_info):
        print( "Trying to find a store with vaccines available...", end='')
        while True:
            store_address = None
            while not store_address: store_address = get_store(max_distance, zip_code)
            print(".", end='')

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'body')))
            except TimeoutException: continue


            body = self.driver.find_element_by_tag_name('body')
            if "Appointments are no longer available for this location" in body.text:
                recent_failed[store_address] = datetime.now()
                continue
            print(".", end='')

            for fail_store_address in list(recent_failed.keys()):
                fail_time = recent_failed[fail_store_address]
                if (fail_time - datetime.now()).total_seconds() > 600:
                    del recent_failed[fail_store_address]

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, APPOINTMENT_CARD_XPATH)))
            except TimeoutException: continue

            card = self.driver.find_element_by_xpath(APPOINTMENT_CARD_XPATH)
            if "There are no available time slots" in card.text:
                recent_failed[store_address] = datetime.now()
                continue
            print(".", end='')

            vaccine_type = self.driver.find_element_by_xpath(VACCINE_TYPE_XPATH)
            appointment_date = self.driver.find_element_by_xpath(APPOINTMENT_DATE_XPATH)
            appointment_time = self.driver.find_element_by_xpath(APPOINTMENT_TIME_XPATH)


            appointment_date.click()
            appointment_date_options = appointment_date.find_elements_by_tag_name("lightning-base-combobox-item")
            appointment_date_options[0].click()

            appointment_time.click()
            appointment_time_options = appointment_time.find_elements_by_tag_name("lightning-base-combobox-item")
            appointment_time_options[0].click()

            self.driver.find_element_by_xpath(CONTINUE_BUTTON_XPATH).click()

            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, SCHEDULE_APPOINTMENT_BUTTON_XPATH)))
            except TimeoutException: continue

            self.driver.maximize_window()

            print("Vaccine Found")
            print(store_address)

            first_name = self.driver.find_element_by_xpath(FIRST_NAME_XPATH)
            first_name.click()
            first_name.send_keys(personal_info.first_name)

            last_name = self.driver.find_element_by_xpath(LAST_NAME_XPATH)
            last_name.click()
            last_name.send_keys(personal_info.last_name)

            email = self.driver.find_element_by_xpath(EMAIL_XPATH)
            email.click()
            email.send_keys(personal_info.email)

            phone_number = self.driver.find_element_by_xpath(PHONE_NUMBER_XPATH)
            phone_number.click()
            phone_number.send_keys(personal_info.phone_number)

            phone_number = self.driver.find_element_by_xpath(PHONE_NUMBER_XPATH)
            phone_number.click()
            phone_number.send_keys(personal_info.phone_number)

            date_of_birth = self.driver.find_element_by_xpath(DATE_OF_BIRTH_XPATH)
            date_of_birth.click()
            date_of_birth.send_keys(personal_info.date_of_birth)

            have_insurance = self.driver.find_element_by_xpath(HAVE_INSURANCE_XPATH)
            have_insurance.click()
            have_insurance = self.driver.find_element_by_xpath(HAVE_INSURANCE_XPATH)
            have_insurance_options = have_insurance.find_elements_by_tag_name("lightning-base-combobox-item")

            if personal_info.have_insurance:
                have_insurance_options[0].click()
                if personal_info.insurance_company_name:
                    insurance_company_name = self.driver.find_element_by_xpath(INSURANCE_COMPANY_NAME_XPATH)
                    insurance_company_name.click()
                    insurance_company_name.send_keys(personal_info.insurance_company_name)

                if personal_info.insurance_id_number:
                    insurance_id_number = self.driver.find_element_by_xpath(INSURANCE_ID_NUMBER_XPATH)
                    insurance_id_number.click()
                    insurance_id_number.send_keys(personal_info.insurance_id_number)

                if personal_info.insurance_group_number:
                    insurance_group_number = self.driver.find_element_by_xpath(INSURANCE_GROUP_NUMBER_XPATH)
                    insurance_group_number.click()
                    insurance_group_number.send_keys(personal_info.insurance_group_number)
            else:
                have_insurance_options[1].click()

            eligibility = self.driver.find_element_by_xpath(ELIGIBILITY_XPATH)
            eligibility.click()
            eligibility_options = eligibility.find_elements_by_tag_name("lightning-base-combobox-item")
            eligibility_options[1].click()

            if args.auto_accept:
                self.driver.find_element_by_xpath(SCHEDULE_APPOINTMENT_BUTTON_XPATH).click()

            return

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('--browser-driver-path',type=str)
    parser.add_argument('--browser',type=str)

    parser.add_argument('--zip-code',type=int)
    parser.add_argument('--max-distance',type=int)

    parser.add_argument('--first-name',type=str)
    parser.add_argument('--last-name',type=str)
    parser.add_argument('--email',type=str)
    parser.add_argument('--phone-number',type=int)
    parser.add_argument('--date-of-birth',type=str,
                        help='MMDDYYYY with no punctuation')

    parser.add_argument('--have-insurance',action='store_true',
                        help='set this flag if you have health insurance')
    parser.add_argument('--insurance-company-name',type=str)
    parser.add_argument('--insurance-id-number',type=str)
    parser.add_argument('--insurance-group-number',type=int)

    parser.add_argument('--auto-accept',action='store_true',
                        help="""set this flag to automatically accept the appointment when one is found. 
                        Note that you can cancel via email if you cannot make the appointment""")

    args = parser.parse_args(args.brower, args.browser_driver_path)
    from pprint import pprint; pprint(vars(args))

    if args.auto_accept and (args.first_name is None or \
                             args.last_name is None or \
                             args.email is None or \
                             args.phone_number is None or \
                             args.date_of_birth is None ) :
        print("""If --auto-accept is used, first name, last name, DOB, email,
        and phone number need to be filled out """)
        exit(1)

    args = parser.parse_args()

    HEBVaccineChecker(args.browser, args.browser_driver_path).\
        reserve_appointment(args.max_distance, args.zip_code, personal_info = args)

    # Now wait if someone closes the window
    while True:
        try:
            _ = driver.window_handles
        except WebDriverException as e:
            break
        time.sleep(1)
        
