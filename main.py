import argparse
import datetime
import sys
from os import getenv

from dotenv import load_dotenv
from selene import browser
from selenium import webdriver

from ecp import main_actions as ecp_main_actions

load_dotenv()

ECP_DATE_FROM = datetime.date(2026, 9, 5)
ECP_DATE_TO = datetime.date(2026, 9, 5)
GLOBAL_BROWSER_TIMEOUT = 45

credentials = {
    "username": getenv("USERNAME", ""),
    "password": getenv("PASSWORD", ""),
}

HEAD_USERNAME = getenv("HEAD_USERNAME", "")

CHROMIUM_CONFIG_DIR = getenv("CHROMIUM_CONFIG_DIR", "")
CHROMIUM_PROFILE = getenv("CHROMIUM_PROFILE", "")
BROWSER_WINDOW_WIDTH = int(getenv("BROWSER_WINDOW_WIDTH", "1920"))
BROWSER_WINDOW_HEIGHT = int(getenv("BROWSER_WINDOW_HEIGHT", "900"))


def create_argparser():
    parser = argparse.ArgumentParser(
        prog="ecp55-autoclicker",
        description="ecp55.is-mis.ru optimizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group_build = parser.add_mutually_exclusive_group()
    # group_build.add_argument(
    #     "--build",
    #     type=str,
    #     metavar="<version>",
    #     help="Building a python interpreter from source code. "
    #     "Example: python-manager --build 3.10.13",
    # )
    group_build.add_argument(
        "--sign",
        action="store_true",
        help="Sign of completed outpatient treatment cases",
    )
    return parser


def main():
    browser.config.base_url = "https://ecp55.is-mis.ru"
    browser.config.window_width = BROWSER_WINDOW_WIDTH
    browser.config.window_height = BROWSER_WINDOW_HEIGHT
    browser.config.timeout = GLOBAL_BROWSER_TIMEOUT
    driver_options = webdriver.ChromeOptions()
    driver_options.add_argument(f"--user-data-dir={CHROMIUM_CONFIG_DIR}")
    driver_options.add_argument(f"--profile-directory={CHROMIUM_PROFILE}")
    driver_options.add_argument("--start-maximized")
    # driver_options.add_argument("--headless")
    browser.config.driver_options = driver_options
    browser.open("/")

    parser = create_argparser()
    args = parser.parse_args(sys.argv[1:])
    if args.sign:
        ecp_main_actions.login_head(HEAD_USERNAME)
        head_fullname = ecp_main_actions.get_doctor_fullname()
        ecp_main_actions.set_workplace()
        for ordinal in range(
            ECP_DATE_FROM.toordinal(), ECP_DATE_TO.toordinal() + 1
        ):
            ecp_date = datetime.date.fromordinal(ordinal)
            ecp_main_actions.set_ecp_date(ecp_date)
            ecp_main_actions.sign_completed_cases(head_fullname)
    else:
        ecp_main_actions.login(
            credentials["username"], credentials["password"]
        )
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
