from os import getenv

from dotenv import load_dotenv
from selene import be, browser
from selene.core.entity import Element
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

load_dotenv()

credentials = {
    "username": getenv("USERNAME", ""),
    "password": getenv("PASSWORD", ""),
}


def send_keys_one_by_one(element: Element, keys: str):
    for key in keys:
        element.send_keys(key)


def wait_for_loading():
    element = browser.element("div[class$='x-mask-loading']")
    print("Waiting for loading...")
    element.wait.for_(be.existing)
    element.wait.for_(be.not_.existing)
    print("Loading completed.")


def login(username: str, password: str):
    browser.element("input[id='promed-login']").type(username)
    browser.element("input[id='promed-password']").type(password)
    browser.element("button[id='auth_submit']").click()
    wait_for_loading()


def get_user_fullname():
    element = browser.element("span[class='x-window-header-text']")
    element.wait.for_(be.existing)
    header_text = element.locate().get_attribute("innerText")
    assert header_text, "Header text is empty"

    return header_text.rsplit("(", maxsplit=1)[-1].split(")")[0].strip()


def set_ecp_date():
    element = browser.element("input[id='ext-comp-1118']")
    element.wait.for_(be.existing)
    send_keys_one_by_one(element, Keys.BACKSPACE * 8 + "02082026")
    element.press_enter()
    wait_for_loading()


def get_outpatient_list():
    element = browser.element("div[id$='gp-groupField-2']")
    element.wait.for_(be.visible)


def main():
    browser.config.base_url = "https://ecp55.is-mis.ru"
    browser.config.window_width = 1920
    browser.config.window_height = 1000
    browser.config.timeout = 60
    driver_options = webdriver.ChromeOptions()
    # driver_options.add_argument("--headless")
    driver_options.add_argument("--start-maximized")
    browser.config.driver_options = driver_options

    browser.open("/")
    login(credentials["username"], credentials["password"])

    print(f"User fullname: {get_user_fullname()}")

    set_ecp_date()
    get_outpatient_list()

    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
