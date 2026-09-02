import datetime
from enum import Enum
from time import sleep

from selene import be, browser
from selenium.webdriver.common.keys import Keys

from ai.adapters import EcpAutoclickerException, get_diagnosis_reason_code
from ecp.case_disease import CaseDisease, FromEmhResults
from ecp.utils import send_keys_one_by_one, wait_for_loading
from qinpatients.adapters import get_qinpatients_patients
from qinpatients.result_status import ResultStatus

SET_DATE_ERROR_DLG_TIMEOUT = 1
GET_MAIN_TABLES_ROWS_TIMEOUT = 1


class MainTables(Enum):
    INTACTS = "gp-groupField-2-bd"
    INPATIENTS = "gp-groupField-3-bd"
    OUTPATIENTS = "gp-groupField-4-bd"


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


def get_main_tables_rows(table: MainTables):
    try:
        rows = list(
            browser.element(f"div[id$='{table.value}']")
            .with_(timeout=GET_MAIN_TABLES_ROWS_TIMEOUT)
            .all("tr")
        )
    except Exception:
        rows = []
    return rows


def get_patients_no_outpatient_card_number():
    rows = get_main_tables_rows(MainTables.OUTPATIENTS)
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


def get_patients_data_from_emh(
    patients: list[CaseDisease], doctor_fullname: str
):
    print(f"Всего пациентов для получения данных из ЕЦП: " f"{len(patients)}")
    patients_emh: list[CaseDisease] = []
    for i, patient in enumerate(patients):
        message_start = f"{i + 1:02d}. {patient.ecp_patient_fullname}"
        print(
            f"{message_start:<80}::: получение данных из ЕЦП ...",
            end="\r",
        )
        result = ""
        if patient.is_ecp_inpatient:
            result = "УЖЕ ГОСПИТАЛИЗИРОВАН В ЕЦП С КОДОМ Z00.0"
        else:
            from_emh_result = patient.get_data_from_emh(doctor_fullname)
            if from_emh_result == FromEmhResults.OUTPATIENT:
                patients_emh.append(patient)
            result = from_emh_result.value
        print(
            f"{message_start:<80}::: {result}                  ",
        )
    return patients_emh


def get_patients_intact(doctor_fullname: str):
    print("ПОЛУЧЕНИЕ ДАННЫХ НЕОФОРМЛЕННЫХ ПАЦИЕНТОВ ИЗ БД QInPatients И ЕЦП")
    patients_intact_all: list[CaseDisease] = []
    rows_intacts = get_main_tables_rows(MainTables.INTACTS)
    for element_row in rows_intacts:
        case_disease = CaseDisease(element_row)
        if not case_disease.ecp_diagnosis.startswith("Z00.0."):
            continue
        patients_intact_all.append(case_disease)
    rows_inpatients = get_main_tables_rows(MainTables.INPATIENTS)
    for element_row in rows_inpatients:
        case_disease = CaseDisease(element_row)
        case_disease.is_ecp_inpatient = True
        if not case_disease.ecp_diagnosis.startswith("Z00.0."):
            continue
        patients_intact_all.append(case_disease)
    rows_outpatients = get_main_tables_rows(MainTables.OUTPATIENTS)
    for element_row in rows_outpatients:
        case_disease = CaseDisease(element_row)
        if not case_disease.ecp_diagnosis.startswith("Z00.0."):
            continue
        patients_intact_all.append(case_disease)
    print(f"Всего неоформленных пациентов: {len(patients_intact_all)}")
    patients_qinpatients, patients_noqinpatients = get_qinpatients_patients(
        patients_intact_all, doctor_fullname
    )
    for i, patient in enumerate(patients_qinpatients):
        if not patient.qinpatients_examination:
            raise EcpAutoclickerException(
                f"Ошибка: для пациента {patient.ecp_patient_fullname} "
                "из БД QInPatients возвращено пустое значение "
                "`qinpatients_examination`"
            )
        result_status = "ГОСПИТАЛИЗАЦИЯ"
        if patient.qinpatients_examination.result_status in [
            ResultStatus.OUTPATIENT,
            ResultStatus.SELF_EXIT,
            ResultStatus.SELF_REFUSE,
        ]:
            result_status = "АМБУЛАТОРНОЕ ЛЕЧЕНИЕ"
        message_start = f"{i + 1:02d}. {patient.ecp_patient_fullname}"
        print(
            f"{message_start:<80}::: {result_status}",
        )
    patients_emh = get_patients_data_from_emh(
        patients_noqinpatients, doctor_fullname
    )
    # patients_emh = []
    print()
    return patients_qinpatients + patients_emh


def get_patients_performed():
    case_disease_list: list[CaseDisease] = []
    rows_inpatients = get_main_tables_rows(MainTables.INPATIENTS)
    for element_row in rows_inpatients:
        case_disease = CaseDisease(element_row)
        if case_disease.ecp_diagnosis.startswith("Z00.0."):
            continue
        case_disease_list.append(case_disease)
    rows_outpatients = get_main_tables_rows(MainTables.OUTPATIENTS)
    for element_row in rows_outpatients:
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
    patients_intact = get_patients_intact(doctor_fullname)
    print("ОФОРМЛЕНИЕ РЕЗУЛЬТАТА ПРИЁМА")
    print(f"Всего пациентов с данными для оформления: {len(patients_intact)}")
    get_diagnosis_reason_code(patients_intact)

    for i, patient in enumerate(patients_intact):
        message_start = (
            f"{i + 1:02d}. {patient.ecp_patient_fullname}, "
            f"код диагноза: {patient.diagnosis_code}, "
            f"код причины: {patient.reason_code}"
        )
        print(
            f"{message_start:<80}::: в процессе оформления результата ...",
            end="\r",
        )
        if not (
            patient.diagnosis_code.startswith("S")
            or patient.diagnosis_code.startswith("T")
        ):
            patient.trauma_type_number = 0
        patient.set_result()
        print(
            f"{message_start:<80}::: РЕЗУЛЬТАТ ОФОРМЛЕН                  ",
        )
    print()


def perform_outpatient_card_number(doctor_fullname: str):
    print("ОФОРМЛЕНИЕ АМБУЛАТОРНОГО НОМЕРА")
    patients_no_ocn_all = get_patients_no_outpatient_card_number()
    patients_no_ocn: list[CaseDisease] = []

    for patient in patients_no_ocn_all:
        if not patient.ecp_operator:
            raise EcpAutoclickerException(
                f"Ошибка: для пациента {patient.ecp_patient_fullname} "
                "отсутствуют данные `ecp_operator`."
            )
        if patient.ecp_operator.upper() in doctor_fullname.upper():
            patients_no_ocn.append(patient)

    for i, patient in enumerate(patients_no_ocn):
        message_start = (
            f"{i + 1:02d}. {patient.ecp_patient_fullname}, "
            f"диагноз: {patient.ecp_diagnosis.split(". ", maxsplit=1)[0]}"
        )
        print(
            f"{message_start:<80}"
            "::: в процессе оформления амбулаторного номера ...",
            end="\r",
        )
        result = (
            "АМБУЛАТОРНЫЙ НОМЕР ОФОРМЛЕН"
            if patient.set_outpatient_card_number(doctor_fullname)
            else "ОТСУТСТВУЕТ ПОЛИС ОМС      "
        )
        print(
            f"{message_start:<80}"
            f"::: {result}                                     ",
        )
    print()


def perform_emh_examination_text(doctor_fullname: str):
    print("ДОБАВЛЕНИЕ ТЕКСТА ОСМОТРА")
    patients_performed_all = get_patients_performed()
    patients_performed, _ = get_qinpatients_patients(
        patients_performed_all, doctor_fullname
    )

    for i, patient in enumerate(patients_performed):
        message_start = (
            f"{i + 1:02d}. {patient.ecp_patient_fullname}, "
            f"диагноз: {patient.ecp_diagnosis.split(". ", maxsplit=1)[0]}"
        )
        print(
            f"{message_start:<80}" "::: в процессе добавления осмотра ...",
            end="\r",
        )
        result = (
            "ОСМОТР ДОБАВЛЕН"
            if patient.set_emh_examination_text(doctor_fullname)
            else "ОСМОТР УЖЕ БЫЛ ДОБАВЛЕН"
        )
        print(
            f"{message_start:<80}" f"::: {result}                        ",
        )
    print()
