import datetime
import re

from selene import be, browser, have
from selene.core.entity import Element
from selenium.webdriver.common.keys import Keys

from convert_to_ecp import (
    condition_to_ecp,
    department_to_ecp,
    result_to_ecp,
    trauma_type_to_ecp,
)
from exceptions import EcpAutoclickerException
from qinpatients import Examination
from utils import send_keys_one_by_one, wait_for_loading

SET_RESULT_CODE_LIST_TIMEOUT = 5

DEFAULT_REASON_CODE = "X59.9"
DEFAULT_DIAGNOSIS_CODE = "T14.9"
DEFAULT_DIAGNOSIS_BRUISE_CODE = "T14.0"
DEFAULT_DIAGNOSIS_WOUND_CODE = "T14.1"
DEFAULT_DIAGNOSIS_FRACTURE_CODE = "T14.2"
DEFAULT_DIAGNOSIS_DISLOCATED_CODE = "T14.3"
DEFAULT_DIAGNOSIS_AMPUTATION_CODE = "T14.7"


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
            raise EcpAutoclickerException(
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
        if not self.qinpatients:
            raise EcpAutoclickerException(
                f"Ошибка: для пациента {self.patient_fullname} "
                "отсутствуют данные из БД QInPatients."
            )
        diagnosis_code = self.diagnosis_code
        browser.element("#EPSPEF_DiagRecepCombo").click().type(diagnosis_code)
        try:
            browser.element(
                "div.x-combo-list[style*='visibility: visible']"
            ).with_(timeout=SET_RESULT_CODE_LIST_TIMEOUT).wait.for_(be.present)
        except Exception:
            if (
                "ампутаци" in self.qinpatients.diagnosis.lower()
                or "размозжен" in self.qinpatients.diagnosis.lower()
            ):
                diagnosis_code = DEFAULT_DIAGNOSIS_AMPUTATION_CODE
            elif "перелом" in self.qinpatients.diagnosis.lower():
                diagnosis_code = DEFAULT_DIAGNOSIS_FRACTURE_CODE
            if (
                "вывих" in self.qinpatients.diagnosis.lower()
                or "растяжение" in self.qinpatients.diagnosis.lower()
            ):
                diagnosis_code = DEFAULT_DIAGNOSIS_DISLOCATED_CODE
            elif "рана" in self.qinpatients.diagnosis.lower():
                diagnosis_code = DEFAULT_DIAGNOSIS_WOUND_CODE
            elif "ушиб" in self.qinpatients.diagnosis.lower():
                diagnosis_code = DEFAULT_DIAGNOSIS_BRUISE_CODE
            else:
                diagnosis_code = DEFAULT_DIAGNOSIS_CODE
            browser.element("#EPSPEF_DiagRecepCombo + input").click().type(
                diagnosis_code
            )
        browser.element(
            "div.x-combo-list[style*='visibility: visible'] tr:first-child"
        ).click()

    def set_result_trauma_type(self):
        if not self.qinpatients:
            raise EcpAutoclickerException(
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
        try:
            browser.element(
                "div.x-combo-list[style*='visibility: visible']"
            ).with_(timeout=SET_RESULT_CODE_LIST_TIMEOUT).wait.for_(be.present)
        except Exception:
            browser.element("#Diag_eid + input").click().type(
                DEFAULT_REASON_CODE
            )
        browser.element(
            "div.x-combo-list[style*='visibility: visible'] tr:first-child"
        ).click()

    def set_result_status(self):
        if not self.qinpatients:
            raise EcpAutoclickerException(
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
