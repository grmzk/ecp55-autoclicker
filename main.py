import datetime
from os import getenv

from dotenv import load_dotenv
from selene import browser
from selenium import webdriver

from ai.adapters import get_diagnosis_reason_code
from ecp import main_actions as ecp_main_actions
from qinpatients.adapters import get_qinpatients_patients

load_dotenv()

ECP_DATE = datetime.date(2026, 8, 18)
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
    print(f"Доктор: {doctor_fullname}")

    ecp_main_actions.set_workplace()
    ecp_main_actions.set_ecp_date(ECP_DATE)

    patients_all = ecp_main_actions.get_patients_list()
    patients = get_qinpatients_patients(patients_all, doctor_fullname)
    get_diagnosis_reason_code(patients)

    # input("Press Enter to exit...")
    # return

    for i, patient in enumerate(patients):
        print(
            f"{i + 1:02d}. {patient.ecp_patient_fullname}, "
            f"код диагноза: {patient.diagnosis_code}, "
            f"код причины: {patient.reason_code}"
            "\t::: в процессе оформления в ECP55 ...",
            end="\r",
        )
        # patient.set_result()
        print(
            f"{i + 1:02d}. {patient.ecp_patient_fullname}, "
            f"код диагноза: {patient.diagnosis_code}, "
            f"код причины: {patient.reason_code}"
            "\t::: ОФОРМЛЕН                         ",
            end="\n",
        )

    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
