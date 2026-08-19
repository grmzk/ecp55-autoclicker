import datetime
import re
from os import getenv
from time import sleep

from dotenv import load_dotenv
from selene import be, browser, have
from selene.core.entity import Element
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from gemini import get_mkb_codes
from qinpatients import Examination, ResultStatus

load_dotenv()

credentials = {
    "username": getenv("USERNAME", ""),
    "password": getenv("PASSWORD", ""),
}


trauma_type_to_ecp = {
    "производственная": 5,
    "производственная, ДТП": 3,
    "производственная, кататравма": 5,
    "производственная, насильственная": 5,
    "бытовая": 6,
    "бытовая, ДТП": 9,
    "бытовая, кататравма": 6,
    "бытовая, насильственная": 6,
}

result_to_ecp = {
    ResultStatus.UNCOMPLETED: 0,
    ResultStatus.DISCHARGED: 99,
    ResultStatus.TRANSFER_INTERNAL: 99,
    ResultStatus.TRANSFER_EXTERNAL: 99,
    ResultStatus.OUTPATIENT: 3,
    ResultStatus.SELF_EXIT: 8,
    ResultStatus.SELF_REFUSE: 2,
    ResultStatus.HOSPITALIZATION: 99,
    ResultStatus.HOSPITALIZATION_SELF_EXIT: 99,
    ResultStatus.HOSPITALIZATION_SELF_REFUSE: 99,
    ResultStatus.DEATH: 99,
    ResultStatus.DISCHARGED_UNKNOWN_RESULT: 99,
}

department_to_ecp = {
    "Отделение травматологии": 45010010,
    "Отделение нейрохирургии": 45010036,
    "Хирургическое отделение": 45010006,
    "Отделение гнойной хирургии": 45010008,
    "Урологическое отделение": 45010009,
    "Гинекологическое отделение": 45010011,
    "Терапевтическое отделение №1": 45010001,
    "Терапевтическое отделение №2": 0,
    "Кардиологическое отделение": 45010037,
    "Неврологическое отделение": 45010032,
    "Отделение острых отравлений": 45010004,
    "Ожоговое отделение": 45010013,
    "Кардиологическое отделение №2": 45010099,
}

condition_to_ecp = {
    "удовлетворительное": 1,
    "средней тяжести": 2,
    "тяжелое": 3,
    "крайне тяжелое": 4,
    "клиническая смерть": 5,
    "терминальное": 6,
}


def send_keys_one_by_one(element: Element, keys: str):
    for key in keys:
        element.send_keys(key)


def wait_for_loading():
    # print("Waiting for loading...", end="\r")
    try:
        element = browser.element("div[class$='x-mask-loading']")
        element.wait.for_(be.existing)
        element.wait.for_(be.not_.existing)
    # except TimeoutException:
    #     pass
    except Exception:
        pass
    # print("Loading completed.    ")


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


class CaseDisease:
    def __init__(self, element_row: Element) -> None:
        self.incoming_date = datetime.datetime.strptime(
            (
                element_row.element("div[class*='x-grid3-col-12']")
                .locate()
                .get_attribute("innerText")
                or ""
            ).strip(),
            "%d.%m.%Y %H:%M",
        )
        self.patient_fullname = (
            element_row.element("div[class*='x-grid3-col-13']")
            .locate()
            .get_attribute("innerText")
            or ""
        ).strip()
        self.patient_birthday = datetime.datetime.strptime(
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
        self.qinpatients = Examination.get_examination(
            self.patient_fullname, self.patient_birthday, self.incoming_date
        )
        self.diagnosis_code = ""
        self.reason_code = ""

    def click(self):
        browser.element("div[id$='gp-groupField-4-bd']").all("tr").element_by(
            have.text(self.patient_fullname).and_(
                have.text(self.incoming_date.strftime("%d.%m.%Y %H:%M"))
            )
        ).click().click()

    def double_click(self):
        browser.element("div[id$='gp-groupField-2-bd']").all("tr").element_by(
            have.text(self.patient_fullname).and_(
                have.text(self.incoming_date.strftime("%d.%m.%Y %H:%M"))
            )
        ).click().click().double_click()
        wait_for_loading()

    def add_outpatient_card(self):
        self.click()
        browser.element("button[id='ext-gen742']").click()
        browser.all("span[class='x-window-dlg']").element_by(
            have.text("Продолжить сохранение?")
        )

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

    def set_result_doctor(self):
        if not self.qinpatients:
            raise Ecp55AutoclickerException(
                f"Ошибка: для пациента {self.patient_fullname} "
                "отсутствуют данные из БД QInPatients."
            )
        result_doctor = self.qinpatients.doctor
        browser.element("#EPSPEF_AdmitDepartPanel").click()
        browser.element("#EPSPEF_MedStaffFactRecCombo").click().type(
            result_doctor
        )
        browser.element("div.x-combo-selected + div").click()

    def set_result_diagnosis_code(self):
        diagnosis_code = self.diagnosis_code
        browser.element("#EPSPEF_DiagRecepCombo").click().type(diagnosis_code)
        browser.element(
            "div.x-combo-list[style*='visibility: visible'] tr:first-child"
        ).click()

    def set_result_trauma_type(self):
        if not self.qinpatients:
            raise Ecp55AutoclickerException(
                f"Ошибка: для пациента {self.patient_fullname} "
                "отсутствуют данные из БД QInPatients."
            )
        type_number = trauma_type_to_ecp[self.qinpatients.trauma_type]
        browser.element("#PrehospTrauma_id + input").click().type(
            str(type_number)
        )

    def set_result_reason_code(self):
        reason_code = self.reason_code
        browser.element("#Diag_eid + input").click().type(reason_code)
        browser.element(
            "div.x-combo-list[style*='visibility: visible'] tr:first-child"
        ).click()

    def set_result_status(self):
        if not self.qinpatients:
            raise Ecp55AutoclickerException(
                f"Ошибка: для пациента {self.patient_fullname} "
                "отсутствуют данные из БД QInPatients."
            )
        result_status = result_to_ecp.get(self.qinpatients.result_status)
        department_code = department_to_ecp.get(self.qinpatients.department)
        browser.element("#EPSPEF_PriemLeavePanel").click()
        if result_status == 99:  # hospitalization
            browser.element("#EPSPEF_LpuSectionCombo").click().type(
                str(department_code)
            ).press_enter()
            condition_code = 1
            condition_match = re.match(
                r"^Общее состояние [а-я ]+", self.qinpatients.status_praesens
            )
            if condition_match:
                condition = (
                    condition_match.group()
                    .split("Общее состояние ")[-1]
                    .strip()
                    .lower()
                )
                condition_code = condition_to_ecp.get(condition, 1)
            browser.element("#DiagSetPhase_pid + input").click().type(
                str(condition_code)
            )
            return
        browser.element("#EPSPEF_PrehospWaifRefuseCause_id").click().type(
            str(result_status)
        )
        browser.element("#DiagSetPhase_aid + input").click().type("1")
        browser.element("#DiagSetPhase_pid + input").click().type("1")
        browser.element("#DeseaseType_id + input").click().type("1")

    def set_result_date(self):
        result_date = self.incoming_date + datetime.timedelta(hours=1)
        date_element = browser.element("input[name='EvnPS_OutcomeDate']")
        send_keys_one_by_one(
            date_element, Keys.BACKSPACE * 8 + result_date.strftime("%d%m%Y")
        )
        if date_element.locate().get_attribute(
            "value"
        ) != result_date.strftime("%d.%m.%Y"):
            send_keys_one_by_one(
                date_element,
                Keys.BACKSPACE * 8 + result_date.strftime("%d%m%Y"),
            )
        time_element = browser.element("input[name='EvnPS_OutcomeTime']")
        send_keys_one_by_one(
            time_element, Keys.BACKSPACE * 4 + result_date.strftime("%H%M")
        )
        if time_element.locate().get_attribute(
            "value"
        ) != result_date.strftime("%H:%M"):
            send_keys_one_by_one(
                date_element,
                Keys.BACKSPACE * 4 + result_date.strftime("%H%M"),
            )

    def save_result(self):
        browser.element(
            "table[matomo_event_id='win_swEvnPSPriemEditWindow_btn_Sohranit'] "
            "button"
        ).click()
        wait_for_loading()

    def set_result(self):
        self.double_click()
        self.set_result_doctor()
        self.set_result_diagnosis_code()
        self.set_result_trauma_type()
        self.set_result_reason_code()
        self.set_result_status()
        self.set_result_date()
        self.save_result()


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


class Ecp55AutoclickerException(Exception):
    pass


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

    doctor_fullname = get_user_fullname()
    print(f"User fullname: {doctor_fullname}")

    set_workplace()
    set_ecp_date(datetime.date(2026, 8, 16))

    patients_all = get_patient_list()
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
            raise Ecp55AutoclickerException(
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
            raise Ecp55AutoclickerException(
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
