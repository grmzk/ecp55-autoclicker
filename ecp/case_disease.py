import datetime

from selene import be, browser, have
from selene.core.entity import Element
from selenium.webdriver.common.keys import Keys

from ecp.exceptions import EcpAutoclickerException
from ecp.utils import send_keys_one_by_one, wait_for_loading

SET_RESULT_CODE_LIST_TIMEOUT = 5
NO_DOCUMENT_DIALOG_TIMEOUT = 1

DEFAULT_REASON_CODE = "X59.9"
DEFAULT_DIAGNOSIS_CODE = "T14.9"
DEFAULT_DIAGNOSIS_BRUISE_CODE = "T14.0"
DEFAULT_DIAGNOSIS_WOUND_CODE = "T14.1"
DEFAULT_DIAGNOSIS_FRACTURE_CODE = "T14.2"
DEFAULT_DIAGNOSIS_DISLOCATED_CODE = "T14.3"
DEFAULT_DIAGNOSIS_AMPUTATION_CODE = "T14.7"


class CaseDisease:  # pylint: disable=too-many-instance-attributes
    def __init__(self, element_row: Element) -> None:
        self.ecp_incoming_date = datetime.datetime.strptime(
            (
                element_row.element("div[class*='x-grid3-col-12']")
                .locate()
                .get_attribute("innerText")
                or ""
            ).strip(),
            "%d.%m.%Y %H:%M",
        )
        self.ecp_patient_fullname = (
            element_row.element("div[class*='x-grid3-col-13']")
            .locate()
            .get_attribute("innerText")
            or ""
        ).strip()
        self.ecp_patient_birthday = datetime.datetime.strptime(
            (
                element_row.element("div[class*='x-grid3-col-14']")
                .locate()
                .get_attribute("innerText")
                or ""
            ).strip(),
            "%d.%m.%Y",
        )
        self.ecp_department = (
            element_row.element("div[class*='x-grid3-col-23']")
            .locate()
            .get_attribute("innerText")
            or ""
        ).strip()
        self.ecp_diagnosis = (
            element_row.element("div[class*='x-grid3-col-autoexpand']")
            .locate()
            .get_attribute("innerText")
            or ""
        ).strip()
        self.ecp_operator = (
            element_row.element("div[class*='x-grid3-col-66']")
            .locate()
            .get_attribute("innerText")
            or ""
        ).strip()
        self.ecp_social_status = (
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
        self.ecp_outpatient_card_number = (
            int(outpatient_card_number_str)
            if outpatient_card_number_str
            else None
        )
        self.doctor = ""
        self.diagnosis = ""
        self.diagnosis_code = ""
        self.reason_code = ""
        self.anamnesis_morbi = ""
        self.trauma_type_number = 0
        self.condition_number = 1
        self.result_status_number = 0
        self.inpatient_department_code = 0
        self.examination_text = ""

    def __click(self):
        browser.all("div.x-grid-group-body tr").element_by(
            have.text(self.ecp_patient_fullname).and_(
                have.text(self.ecp_incoming_date.strftime("%d.%m.%Y %H:%M"))
            )
        ).click().click()

    def __double_click(self):
        browser.all("div.x-grid-group-body tr").element_by(
            have.text(self.ecp_patient_fullname).and_(
                have.text(self.ecp_incoming_date.strftime("%d.%m.%Y %H:%M"))
            )
        ).click().click().double_click()
        wait_for_loading()

    def __set_result_doctor(self):
        if not self.doctor:
            raise EcpAutoclickerException(
                f"Ошибка: для пациента {self.ecp_patient_fullname} "
                "отсутствуют данные `doctor`."
            )
        browser.element("#EPSPEF_AdmitDepartPanel").click()
        element = browser.element("#EPSPEF_MedStaffFactRecCombo").click()
        send_keys_one_by_one(element, self.doctor)
        browser.element("div.x-combo-selected + div").click()

    def __set_result_diagnosis_code(self):
        if not self.diagnosis_code:
            raise EcpAutoclickerException(
                f"Ошибка: для пациента {self.ecp_patient_fullname} "
                "отсутствуют данные `diagnosis_code`."
            )
        if not self.diagnosis:
            raise EcpAutoclickerException(
                f"Ошибка: для пациента {self.ecp_patient_fullname} "
                "отсутствуют данные `diagnosis`."
            )
        diagnosis_code = self.diagnosis_code
        browser.element("#EPSPEF_DiagRecepCombo").click().type(diagnosis_code)
        try:
            browser.element(
                "div.x-combo-list[style*='visibility: visible']"
            ).with_(timeout=SET_RESULT_CODE_LIST_TIMEOUT).wait.for_(be.present)
        except Exception:
            if (
                "ампутаци" in self.diagnosis.lower()
                or "размозжен" in self.diagnosis.lower()
            ):
                diagnosis_code = DEFAULT_DIAGNOSIS_AMPUTATION_CODE
            elif "перелом" in self.diagnosis.lower():
                diagnosis_code = DEFAULT_DIAGNOSIS_FRACTURE_CODE
            elif (
                "вывих" in self.diagnosis.lower()
                or "растяжение" in self.diagnosis.lower()
            ):
                diagnosis_code = DEFAULT_DIAGNOSIS_DISLOCATED_CODE
            elif "рана" in self.diagnosis.lower():
                diagnosis_code = DEFAULT_DIAGNOSIS_WOUND_CODE
            elif "ушиб" in self.diagnosis.lower():
                diagnosis_code = DEFAULT_DIAGNOSIS_BRUISE_CODE
            else:
                diagnosis_code = DEFAULT_DIAGNOSIS_CODE
            browser.element("#EPSPEF_DiagRecepCombo + input").click().type(
                diagnosis_code
            )
        browser.element(
            "div.x-combo-list[style*='visibility: visible'] tr:first-child"
        ).click()

    def __set_result_trauma_type(self):
        if not self.trauma_type_number:
            return
        # type_number = trauma_type_to_ecp[self.qinpatients.trauma_type]
        browser.element("#PrehospTrauma_id + input").click().type(
            str(self.trauma_type_number)
        )

    def __set_result_reason_code(self):
        if not self.reason_code:
            return
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

    def __set_result_status(self):
        if not self.result_status_number:
            raise EcpAutoclickerException(
                f"Ошибка: для пациента {self.ecp_patient_fullname} "
                "отсутствуют данные `result_status_number`."
            )
        browser.element("#EPSPEF_PriemLeavePanel").click()
        if self.result_status_number == 99:  # hospitalization
            browser.element("#EPSPEF_LpuSectionCombo").click().type(
                str(self.inpatient_department_code)
            ).press_enter()
            browser.element("#DiagSetPhase_pid + input").click().type(
                str(self.condition_number)
            )
            return
        browser.element("#EPSPEF_PrehospWaifRefuseCause_id").click().type(
            str(self.result_status_number)
        )
        browser.element("#DiagSetPhase_aid + input").click().type("1")
        browser.element("#DiagSetPhase_pid + input").click().type("1")
        browser.element("#DeseaseType_id + input").click().type("1")

    def __set_result_date(self):
        result_date = self.ecp_incoming_date + datetime.timedelta(hours=1)
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

    def __save_result(self):
        browser.element(
            "table[matomo_event_id='win_swEvnPSPriemEditWindow_btn_Sohranit'] "
            "button"
        ).click()
        wait_for_loading()

    def set_result(self):
        self.__double_click()
        self.__set_result_doctor()
        self.__set_result_diagnosis_code()
        self.__set_result_trauma_type()
        self.__set_result_reason_code()
        self.__set_result_status()
        self.__set_result_date()
        self.__save_result()

    def __open_outpatient_card(self):
        self.__click()
        browser.element(
            "table[matomo_event_id='win_swMPWorkPlacePriemWindow_tbr"
            "_mpwpprToolbar_btn_Dobavit_sluchay_APL'] button"
        ).click()
        wait_for_loading()
        try:
            dialog = browser.element(
                "div.x-window-dlg[style*='visibility: visible']"
            )
            dialog.with_(timeout=NO_DOCUMENT_DIALOG_TIMEOUT).wait.for_(
                be.present
            )
            dialog.all("button").element_by(have.text("Нет")).click()
            browser.element(
                "table[matomo_event_id='win_swEvnPLEditWindow_btn_Otmena'] "
                "button"
            ).click()
        except Exception:
            return True
        return False

    def __select_outpatient_card_examination(self):
        browser.element("#EPLEF_EvnVizitPLGrid .x-grid3-scroller").all(
            "tr div"
        ).element_by(have.text(self.doctor.upper())).click().double_click()
        wait_for_loading()
        wait_for_loading()

    def __set_outpatient_card_visit_code(self):
        browser.element(
            "#x-form-el-EVPLEF_UslugaComplex "
            ".x-form-twin-triggers img:first-child"
        ).click()
        browser.element("tr.x-combo-selected").click()

    def __set_outpatient_card_validity_level(self):
        browser.element("#DiagValidityType_id + input").click().type("3")

    def __set_outpatient_card_patient_condition(self):
        browser.element("#DiagSetPhase_id + input").click().type("1")

    def __save_outpatient_card_examination(self):
        browser.element(
            "table[matomo_event_id='win_swEvnVizitPLEditWindow_btn_Sohranit'] "
            "button"
        ).click()
        wait_for_loading()
        browser.element(
            "table[matomo_event_id='win_swEvnPLEditWindow_btn_Sohranit'] "
            "button"
        ).click()
        wait_for_loading()

    def set_outpatient_card_number(self):
        if not self.__open_outpatient_card():
            return
        self.__select_outpatient_card_examination()
        self.__set_outpatient_card_visit_code()
        self.__set_outpatient_card_validity_level()
        self.__set_outpatient_card_patient_condition()
        self.__save_outpatient_card_examination()

    def __open_emh(self):
        self.__click()
        browser.element("#mpwpprToolbar").all("button").element_by(
            have.text("Открыть ЭМК")
        ).click()
        wait_for_loading()

    def __select_emh_case_disease(self):
        browser.element("#PersonEmkTree").all(
            "span[unselectable='on']"
        ).element_by(
            have.text(f"{self.ecp_incoming_date.strftime("%d.%m.%Y")} - ")
            .and_(have.text(self.ecp_diagnosis.split(". ", maxsplit=1)[0]))
            .and_(have.text("отделение приемное"))
        ).click()
        wait_for_loading()

    def __exists_emh_examination_text(self):
        try:
            browser.all("div.NewStyleDoc > div.WrapDoc").element_by(
                have.text(self.doctor.upper())
            ).with_(timeout=0.25).should(be.present)
        except Exception:
            return False
        return True

    def __click_emh_add_document(self):
        browser.element(
            "div.caption > h2 > span[id^='EvnXmlProtokolList']"
        ).hover()
        browser.element(
            "a.button[id^='EvnXmlProtokolList'][title='Добавить документ']"
        ).click()
        browser.element("div.x-menu[style*='visibility: visible;']").all(
            "li a"
        ).element_by(have.text("Первичный осмотр при поступлении")).click()
        wait_for_loading()

    def __select_emh_template(self):
        browser.element("input[name='templName']").type(
            "Музыкин"
        ).press_enter()
        wait_for_loading()
        browser.all(
            "#XmlTemplateGrid div.x-grid3-body > div.x-grid3-row"
        ).element_by(have.text("Музыкин")).double_click()
        wait_for_loading()
        element = (
            browser.all("#XmlTemplateGrid div.x-grid3-body > div.x-grid3-row")
            .element_by(have.text("Первичный осмотр"))
            .click()
        )
        wait_for_loading()
        element.double_click()
        wait_for_loading()
        wait_for_loading()

    def __set_emh_examination_text(self):
        iframe = browser.element("div.NewStyleDoc > div.WrapDoc iframe")
        iframe.wait.for_(be.present)
        iframe_webelement = iframe.locate()
        browser.driver.switch_to.frame(iframe_webelement)
        browser.element("#tinymce > p").click().type(
            Keys.BACKSPACE + self.examination_text
        ).press_enter()
        browser.driver.switch_to.default_content()
        self.__select_emh_case_disease()

    def __close_emh(self):
        browser.element(
            "table[matomo_event_id='win_swPersonEmkWindow_btn_Zakrit'] button"
        ).click()
        wait_for_loading()

    def set_emh_examination_text(self):
        self.__open_emh()
        self.__select_emh_case_disease()
        if self.__exists_emh_examination_text():
            self.__close_emh()
            return False
        self.__click_emh_add_document()
        self.__select_emh_template()
        self.__set_emh_examination_text()
        self.__close_emh()
        return True
