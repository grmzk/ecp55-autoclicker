import datetime
from os import getenv

from dotenv import load_dotenv
from selene import browser
from selenium import webdriver

from ecp import main_actions as ecp_main_actions

load_dotenv()

ECP_DATE_FROM = datetime.date(2026, 8, 9)
ECP_DATE_TO = datetime.date(2026, 8, 10)
GLOBAL_BROWSER_TIMEOUT = 45

credentials = {
    "username": getenv("USERNAME", ""),
    "password": getenv("PASSWORD", ""),
}


def main():
    browser.config.base_url = "https://ecp55.is-mis.ru"
    browser.config.window_width = 1920
    browser.config.window_height = 900
    browser.config.timeout = GLOBAL_BROWSER_TIMEOUT
    driver_options = webdriver.ChromeOptions()
    driver_options.add_argument(
        "--user-data-dir=/home/miv-sisyphus/.config/chromium"
    )
    driver_options.add_argument("--profile-directory=Profile 1")
    # driver_options.add_argument("--headless")
    driver_options.add_argument("--start-maximized")
    browser.config.driver_options = driver_options
    browser.open("/")

    ecp_main_actions.login(credentials["username"], credentials["password"])
    doctor_fullname = ecp_main_actions.get_doctor_fullname()
    ecp_main_actions.set_workplace()
    for ordinal in range(
        ECP_DATE_FROM.toordinal(), ECP_DATE_TO.toordinal() + 1
    ):
        ecp_date = datetime.date.fromordinal(ordinal)
        ecp_main_actions.set_ecp_date(ecp_date)
        ecp_main_actions.perform_examinations_result(doctor_fullname)
        ecp_main_actions.perform_outpatient_card_number(doctor_fullname)
        ecp_main_actions.perform_emh_examination_text(doctor_fullname)

    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
