import datetime
from time import sleep

from selene import be, browser
from selenium.webdriver.common.keys import Keys

from ai.adapters import get_diagnosis_reason_code
from ecp.case_disease import CaseDisease
from ecp.utils import send_keys_one_by_one, wait_for_loading
from qinpatients.adapters import get_qinpatients_patients

SET_DATE_ERROR_DLG_TIMEOUT = 1


def login(username: str, password: str):
    browser.element("input[id='promed-login']").type(username)
    browser.element("input[id='promed-password']").type(password)
    sleep(1)
    browser.element("button[id='auth_submit']").click()
    wait_for_loading()


def get_doctor_fullname():
    element = browser.element("span[class='x-window-header-text']")
    element.wait.for_(be.existing)
    header_text = element.locate().get_attribute("innerText")
    assert header_text, "Header text is empty"
    user_fullname = (
        header_text.rsplit("(", maxsplit=1)[-1].split(")")[0].strip()
    )
    print(f"Врач: {user_fullname}")
    print()
    return user_fullname


def set_ecp_date(examination_date: datetime.date):
    print("==================================================================")
    print(f"ДАТА: {examination_date.strftime("%d.%m.%Y")}")
    print()
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
        browser.element(".x-window-dlg").with_(
            timeout=SET_DATE_ERROR_DLG_TIMEOUT
        ).wait.for_(be.present)
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


def get_patients_no_outpatient_card_number():
    rows = browser.element("div[id$='gp-groupField-4-bd']").all("tr")
    case_disease_list: list[CaseDisease] = []
    for element_row in rows:
        case_disease = CaseDisease(element_row)
        if (
            case_disease.ecp_outpatient_card_number
            or case_disease.ecp_diagnosis.startswith("Z00.0.")
        ):
            continue
        case_disease_list.append(case_disease)
    print(
        "Всего амбулаторных пациентов без амбулаторного номера: "
        f"{len(case_disease_list)}"
    )
    return case_disease_list


def get_patients_intact():
    rows = list(browser.element("div[id$='gp-groupField-2-bd']").all("tr"))
    rows.extend(browser.element("div[id$='gp-groupField-3-bd']").all("tr"))
    rows.extend(browser.element("div[id$='gp-groupField-4-bd']").all("tr"))
    case_disease_list: list[CaseDisease] = []
    for element_row in rows:
        case_disease = CaseDisease(element_row)
        if not case_disease.ecp_diagnosis.startswith("Z00.0."):
            continue
        case_disease_list.append(case_disease)
    print(f"Всего неоформленных пациентов: {len(case_disease_list)}")
    return case_disease_list


def get_patients_performed():
    case_disease_list: list[CaseDisease] = []
    rows = list(browser.element("div[id$='gp-groupField-3-bd']").all("tr"))
    for element_row in rows:
        case_disease = CaseDisease(element_row)
        if case_disease.ecp_diagnosis.startswith("Z00.0."):
            continue
        case_disease_list.append(case_disease)
    rows = browser.element("div[id$='gp-groupField-4-bd']").all("tr")
    for element_row in rows:
        case_disease = CaseDisease(element_row)
        if (
            not case_disease.ecp_outpatient_card_number
            or case_disease.ecp_diagnosis.startswith("Z00.0.")
        ):
            continue
        case_disease_list.append(case_disease)
    print(f"Всего оформленных пациентов: {len(case_disease_list)}")
    return case_disease_list


def perform_examinations_result(doctor_fullname: str):
    print("ОФОРМЛЕНИЕ РЕЗУЛЬТАТА ПРИЁМА")
    patients_intact_all = get_patients_intact()
    patients_intact = get_qinpatients_patients(
        patients_intact_all, doctor_fullname
    )
    get_diagnosis_reason_code(patients_intact)

    for i, patient in enumerate(patients_intact):
        print(
            f"{i + 1:02d}. {patient.ecp_patient_fullname}, "
            f"код диагноза: {patient.diagnosis_code}, "
            f"код причины: {patient.reason_code}"
            "\t::: в процессе оформления результата ...",
            end="\r",
        )
        patient.set_result()
        print(
            f"{i + 1:02d}. {patient.ecp_patient_fullname}, "
            f"код диагноза: {patient.diagnosis_code}, "
            f"код причины: {patient.reason_code}"
            "\t::: РЕЗУЛЬТАТ ОФОРМЛЕН                  ",
        )
    print()


def perform_outpatient_card_number(doctor_fullname: str):
    print("ОФОРМЛЕНИЕ АМБУЛАТОРНОГО НОМЕРА")
    patients_no_ocn_all = get_patients_no_outpatient_card_number()
    patients_no_ocn = get_qinpatients_patients(
        patients_no_ocn_all, doctor_fullname
    )

    for i, patient in enumerate(patients_no_ocn):
        print(
            f"{i + 1:02d}. {patient.ecp_patient_fullname}, "
            f"диагноз: {patient.ecp_diagnosis.split(". ", maxsplit=1)[0]}"
            "\t::: в процессе оформления амбулаторного номера ...",
            end="\r",
        )
        result = (
            "АМБУЛАТОРНЫЙ НОМЕР ОФОРМЛЕН"
            if patient.set_outpatient_card_number()
            else "ОТСУТСТВУЕТ ПОЛИС ОМС      "
        )
        print(
            f"{i + 1:02d}. {patient.ecp_patient_fullname}, "
            f"диагноз: {patient.ecp_diagnosis.split(". ", maxsplit=1)[0]}"
            f"\t::: {result}                   ",
        )
    print()


def perform_emh_examination_text(doctor_fullname: str):
    print("ДОБАВЛЕНИЕ ТЕКСТА ОСМОТРА")
    patients_performed_all = get_patients_performed()
    patients_performed = get_qinpatients_patients(
        patients_performed_all, doctor_fullname
    )

    for i, patient in enumerate(patients_performed):
        print(
            f"{i + 1:02d}. {patient.ecp_patient_fullname}, "
            f"диагноз: {patient.ecp_diagnosis.split(". ", maxsplit=1)[0]}"
            "\t::: в процессе добавления осмотра ...",
            end="\r",
        )
        result = (
            "ОСМОТР ДОБАВЛЕН"
            if patient.set_emh_examination_text()
            else "ОСМОТР УЖЕ БЫЛ ДОБАВЛЕН"
        )
        print(
            f"{i + 1:02d}. {patient.ecp_patient_fullname}, "
            f"диагноз: {patient.ecp_diagnosis.split(". ", maxsplit=1)[0]}"
            f"\t::: {result}                  ",
        )
    print()
