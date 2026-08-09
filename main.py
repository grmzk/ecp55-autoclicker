from datetime import datetime
from os import getenv
from time import sleep

from dotenv import load_dotenv
from selene import be, browser, have
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
    sleep(1)
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


class CaseOfDisease:
    def __init__(self, element_row: Element) -> None:
        self.incoming_date = datetime.strptime(
            (
                element_row.element("div[class*='x-grid3-col-12']")
                .locate()
                .get_attribute("innerText")
                or ""
            ).strip(),
            "%d.%m.%Y %H:%M",
        )
        self.patient = (
            element_row.element("div[class*='x-grid3-col-13']")
            .locate()
            .get_attribute("innerText")
            or ""
        ).strip()
        self.patient_birthday = datetime.strptime(
            (
                element_row.element("div[class*='x-grid3-col-14']")
                .locate()
                .get_attribute("innerText")
                or ""
            ).strip(),
            "%d.%m.%Y",
        )
        self.department = (
            element_row.element("div[class*='x-grid3-col-23']")
            .locate()
            .get_attribute("innerText")
            or ""
        ).strip()
        self.diagnosis = (
            element_row.element("div[class*='x-grid3-col-autoexpand']")
            .locate()
            .get_attribute("innerText")
            or ""
        ).strip()
        self.doctor = (
            element_row.element("div[class*='x-grid3-col-66']")
            .locate()
            .get_attribute("innerText")
            or ""
        ).strip()
        self.social_status = (
            element_row.element("div[class*='x-grid3-col-68']")
            .locate()
            .get_attribute("innerText")
            or ""
        ).strip()
        outpatient_card_number_str = (
            element_row.element("div[class*='x-grid3-col-10']")
            .locate()
            .get_attribute("innerText")
            or None
        )
        self.outpatient_card_number = (
            int(outpatient_card_number_str)
            if outpatient_card_number_str
            else None
        )

    def click(self):
        browser.element("div[id$='gp-groupField-4-bd']").all("tr").element_by(
            have.text(self.patient).and_(
                have.text(self.incoming_date.strftime("%d.%m.%Y %H:%M"))
            )
        ).click().click()

    def add_outpatient_card(self):
        self.click()
        browser.element("button[id='ext-gen742']").click()

    def select_outpatient_card_doctor(self):
        self.add_outpatient_card()
        browser.element(
            "div[class*='x-grid3-col-autoexpand_vizit']"
        ).click().double_click()
        wait_for_loading()
        wait_for_loading()

    def select_outpatient_card_visit_code(self):
        self.select_outpatient_card_doctor()
        browser.element("img[id='ext-gen6682']").click()
        # browser.element("div[id='ext-gen4964']").all("td").element_by(
        #     have.text("B01.050.001")
        # ).click()


def get_outpatient_list():
    rows = browser.element("div[id$='gp-groupField-4-bd']").all("tr")
    print("Outpatient amount: " + str(len(rows)))
    case_of_disease_list: list[CaseOfDisease] = []
    for element_row in rows:
        case_of_disease_list.append(CaseOfDisease(element_row))
    for case_of_disease in case_of_disease_list:
        print(
            case_of_disease.incoming_date,
            " : ",
            case_of_disease.patient,
            " : ",
            case_of_disease.patient_birthday,
            " : ",
            case_of_disease.department,
            " : ",
            case_of_disease.diagnosis,
            " : ",
            case_of_disease.doctor,
            " : ",
            case_of_disease.social_status,
            " : ",
            case_of_disease.outpatient_card_number,
        )
    case_of_disease_list[3].select_outpatient_card_visit_code()
    # case_of_disease_list[0].element_row.click().click()
    # patient = case_of_disease_list[0].patient
    # browser.element("div[id$='gp-groupField-4-bd']").all("tr").element_by(
    #     have.text(patient)
    # ).click().click()


def main():
    browser.config.base_url = "https://ecp55.is-mis.ru"
    browser.config.window_width = 1920
    browser.config.window_height = 900
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
