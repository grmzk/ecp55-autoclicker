import datetime
from os import getenv

from dotenv import load_dotenv
from selene import browser
from selenium import webdriver

from ai.adapters import get_diagnosis_reason_code
from ecp import main_actions as ecp_main_actions
from qinpatients.adapters import get_qinpatients_patients

load_dotenv()

ECP_DATE = datetime.date(2026, 8, 23)
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

    ecp_main_actions.login(credentials["username"], credentials["password"])
    doctor_fullname = ecp_main_actions.get_user_fullname()
    print(f"Врач: {doctor_fullname}")

    ecp_main_actions.set_workplace()
    ecp_main_actions.set_ecp_date(ECP_DATE)

    # patients_intact = ecp_main_actions.get_patients_intact()
    # patients_qinpatients = get_qinpatients_patients(
    #     patients_intact, doctor_fullname
    # )
    # get_diagnosis_reason_code(patients_qinpatients)

    # # input("Press Enter to exit...")
    # # return

    # for i, patient in enumerate(patients_qinpatients):
    #     print(
    #         f"{i + 1:02d}. {patient.ecp_patient_fullname}, "
    #         f"код диагноза: {patient.diagnosis_code}, "
    #         f"код причины: {patient.reason_code}"
    #         "\t::: в процессе оформления результата ...",
    #         end="\r",
    #     )
    #     patient.set_result()
    #     print(
    #         f"{i + 1:02d}. {patient.ecp_patient_fullname}, "
    #         f"код диагноза: {patient.diagnosis_code}, "
    #         f"код причины: {patient.reason_code}"
    #         "\t::: РЕЗУЛЬТАТ ОФОРМЛЕН                  ",
    #     )

    patients_no_ocn = ecp_main_actions.get_patients_no_outpatient_card_number()

    for i, patient in enumerate(patients_no_ocn[0:2]):
        # print(
        #     f"{i + 1:02d}. {patient.ecp_patient_fullname}, "
        #     f"диагноз: {patient.ecp_diagnosis}"
        #     "\t::: в процессе оформления амбулаторного номера ...",
        #     end="\r",
        # )
        patient.set_outpatient_card_number()
        # print(
        #     f"{i + 1:02d}. {patient.ecp_patient_fullname}, "
        #     f"диагноз: {patient.ecp_diagnosis}"
        #     "\t::: АМБУЛАТОРНЫЙ НОМЕР ОФОРМЛЕН                   ",
        # )

    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
