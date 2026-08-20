import datetime
import re
from os import getenv

from dotenv import load_dotenv
from selene import browser
from selenium import webdriver

import main_actions
from case_disease import CaseDisease
from exceptions import EcpAutoclickerException
from gemini import get_mkb_codes

load_dotenv()

GLOBAL_BROWSER_TIMEOUT = 60

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
    # driver_options.add_argument("--headless")
    driver_options.add_argument("--start-maximized")
    browser.config.driver_options = driver_options
    browser.open("/")

    main_actions.login(credentials["username"], credentials["password"])
    doctor_fullname = main_actions.get_user_fullname()
    print(f"User fullname: {doctor_fullname}")

    main_actions.set_workplace()
    main_actions.set_ecp_date(datetime.date(2026, 8, 16))

    patients_all = main_actions.get_patient_list()
    patients: list[CaseDisease] = []
    for patient in patients_all:
        if (
            patient.qinpatients
            and patient.qinpatients.doctor.upper() == doctor_fullname.upper()
        ):
            patients.append(patient)
    print(
        "Всего пациентов, которые могут быть оформлены данными "
        f"из БД QInPatients: {len(patients)}"
    )
    anamnesis_diagnosis_list: list[dict] = []
    for patient in patients:
        if (
            not (
                patient.qinpatients
                and patient.qinpatients.anamnesis_morbi
                and patient.qinpatients.diagnosis
            )
            or len(patient.qinpatients.anamnesis_morbi) < 20
            or len(patient.qinpatients.diagnosis) < 8
        ):
            raise EcpAutoclickerException(
                f"Ошибка: у пациента {patient.patient_fullname} в QInPatients "
                "некорректно заполнен анамнез и/или диагноз. "
                "Пожалуйста, исправьте."
            )
        anamnesis_diagnosis_list.append(
            {
                "anamnesis": patient.qinpatients.anamnesis_morbi,
                "diagnosis": patient.qinpatients.diagnosis,
            }
        )

    # input("Press Enter to exit...")
    # return

    code_list = get_mkb_codes(anamnesis_diagnosis_list)
    # code_list = [
    #     {"reason_code": "X59.9", "diagnosis_code": "S93.4"},
    #     {"reason_code": "W19", "diagnosis_code": "S52.1"},
    #     {"reason_code": "X50.9", "diagnosis_code": "S83.4"},
    #     {"reason_code": "W19", "diagnosis_code": "S72.0"},
    #     {"reason_code": "X59.9", "diagnosis_code": "S83.4"},
    #     {"reason_code": "X21", "diagnosis_code": "S93.4"},
    # ]
    for i, patient in enumerate(patients):
        code_pattern = re.compile(r"^[A-Z][0-9][0-9][0-9.]{0,3}$")
        reason_code = code_list[i].get("reason_code")
        diagnosis_code = code_list[i].get("diagnosis_code")
        print(
            f"Number: {i}, Patient: {patient.patient_fullname}, "
            f"Reason code: {reason_code}, Diagnosis code: {diagnosis_code}, "
            f"Result status: {patient.qinpatients.result_status}, "
            f"Department: {patient.qinpatients.department}"
        )
        if not (reason_code and diagnosis_code) or not (
            code_pattern.match(reason_code)
            and code_pattern.match(diagnosis_code)
        ):
            raise EcpAutoclickerException(
                "Ошибка: не удалось получить коды МКБ-10 для пациента "
                f"{patient.patient_fullname}. "
                "Возможно серверы google сейчас не доступны, попробуйте "
                "позже. Также проверьте корректность анамнеза и диагноза "
                "для вышеуказанного пациента в QInPatients."
            )
        patient.reason_code = reason_code
        patient.diagnosis_code = diagnosis_code

    for patient in patients:
        print(
            f"{patient.patient_fullname}, "
            f"код диагноза: {patient.diagnosis_code}, "
            f"код причины: {patient.reason_code}"
            "\t::: в процессе оформления в ECP55 ...",
            end="\r",
        )
        patient.set_result()
        print(
            f"{patient.patient_fullname}, "
            f"код диагноза: {patient.diagnosis_code}, "
            f"код причины: {patient.reason_code}"
            "\t::: ОФОРМЛЕН                         ",
            end="\n",
        )

    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
