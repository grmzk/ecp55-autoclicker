import datetime
from time import sleep

from selene import be, browser
from selenium.webdriver.common.keys import Keys

from case_disease import CaseDisease
from utils import send_keys_one_by_one, wait_for_loading


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


def set_ecp_date(examination_date: datetime.date):
    element = browser.element(
        "input[matomo_event_id='win_swMPWorkPlacePriemWindow_tbr_swdatefield']"
    )
    element.wait.for_(be.present)
    send_keys_one_by_one(
        element, Keys.BACKSPACE * 8 + examination_date.strftime("%d%m%Y")
    )
    element.press_enter()
    wait_for_loading()
    try:
        date_error_dlg = True
        browser.element(".x-window-dlg").with_(timeout=1).wait.for_(be.present)
    # except TimeoutException:
    #     date_error_dlg = False
    #     print("TimeoutException called!")
    # except NoSuchElementException:
    #     date_error_dlg = False
    #     print("NoSuchElementException called!")
    except Exception:
        # print(type(e).__name__)
        date_error_dlg = False
    if date_error_dlg:
        browser.element(".x-window-dlg button").click()
    if element.locate().get_attribute("value") != examination_date.strftime(
        "%d.%m.%Y"
    ):
        send_keys_one_by_one(
            element, Keys.BACKSPACE * 8 + examination_date.strftime("%d%m%Y")
        )
        element.press_enter()
        wait_for_loading()


def set_workplace():
    browser.element("a[id^='header_link_swMPWorkPlace']").click()
    browser.element(
        "div.x-layer.x-menu[style*='visibility: visible'] "
        "a.x-menu-item[matomo_event_id"
        "*='mi_ARM_vracha_priemnogo_otdeleniya_/_BUZOO_']"
    ).click()
    wait_for_loading()


def get_outpatient_list():
    rows = browser.element("div[id$='gp-groupField-4-bd']").all("tr")
    print("Outpatient amount: " + str(len(rows)))
    case_of_disease_list: list[CaseDisease] = []
    for element_row in rows:
        case_of_disease_list.append(CaseDisease(element_row))
    return case_of_disease_list


def get_patient_list():
    rows = browser.element("div[id$='gp-groupField-2-bd']").all("tr")
    patients_amount = len(rows)
    print("Всего неоформленных пациентов: " + str(patients_amount))
    print(
        f"Получение данных из БД QInPatients: 0 из {patients_amount}",
        end="\r",
    )
    case_of_disease_list: list[CaseDisease] = []
    patient_count = 0
    for element_row in rows:
        case_of_disease_list.append(CaseDisease(element_row))
        patient_count += 1
        print(
            "Получение данных из БД QInPatients: "
            f"{patient_count} из {patients_amount}",
            end="\r",
        )
    return case_of_disease_list
