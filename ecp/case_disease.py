import datetime
from enum import Enum

from selene import be, browser, have
from selene.core.entity import Element
from selenium.webdriver.common.keys import Keys

from ecp.exceptions import EcpAutoclickerException
from ecp.utils import send_keys_one_by_one, wait_for_loading
from qinpatients.examination import Examination

SET_RESULT_CODE_LIST_TIMEOUT = 5
OUTPATIENT_CARD_DIALOG_TIMEOUT = 1.5

DEFAULT_REASON_CODE = "X59.9"
DEFAULT_DIAGNOSIS_CODE = "T14.9"
DEFAULT_DIAGNOSIS_BRUISE_CODE = "T14.0"
DEFAULT_DIAGNOSIS_WOUND_CODE = "T14.1"
DEFAULT_DIAGNOSIS_FRACTURE_CODE = "T14.2"
DEFAULT_DIAGNOSIS_DISLOCATED_CODE = "T14.3"
DEFAULT_DIAGNOSIS_AMPUTATION_CODE = "T14.7"


class FromEmhResults(Enum):
    OTHER_DOCTOR = "ДРУГОЙ ВРАЧ"
    INPATIENT = "ГОСПИТАЛИЗАЦИЯ (НЕ МОЖЕТ БЫТЬ ОФОРМЛЕН АВТОМАТИЧЕСКИ)"
    OUTPATIENT = "АМБУЛАТОРНОЕ ЛЕЧЕНИЕ (К ОФОРМЛЕНИЮ)"
    UNKNOWN_RESULT = "РЕЗУЛЬТАТ НЕИЗВЕСТЕН"


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
        self.is_ecp_inpatient = False
        self.doctor = ""
        self.diagnosis = ""
        self.diagnosis_code = ""
        self.reason_code = ""
        self.anamnesis_morbi = ""
        self.trauma_type_number = 6
        self.condition_number = 1
        self.result_status_number = 0
        self.inpatient_department_code = 0
        self.examination_text = ""
        self.qinpatients_examination: Examination | None = None

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
            browser.element("#EPSPEF_DiagRecepCombo").type(
                Keys.BACKSPACE * 6 + diagnosis_code
            )
        browser.element(
            "div.x-combo-list[style*='visibility: visible'] tr:first-child"
        ).click()

    def __set_result_no_criminal_trauma(self):
        browser.element("#EvnPS_IsUnlaw + input").click().type("0")

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
            browser.element("#Diag_eid + input").type(
                Keys.BACKSPACE * 6 + DEFAULT_REASON_CODE
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
        self.__set_result_no_criminal_trauma()
        self.__set_result_trauma_type()
        self.__set_result_reason_code()
        self.__set_result_status()
        self.__set_result_date()
        self.__save_result()

    def __handle_outpatient_card_dialog_window(self):
        try:
            dialog = browser.element(
                "div.x-window-dlg[style*='visibility: visible']"
            )
            dialog.with_(timeout=OUTPATIENT_CARD_DIALOG_TIMEOUT).wait.for_(
                be.present
            )
        except Exception:
            return True
        dialog_message = (
            dialog.element("span.ext-mb-text")
            .locate()
            .get_attribute("innerText")
        )
        if not dialog_message:
            raise EcpAutoclickerException(
                f"Ошибка: для пациента {self.ecp_patient_fullname} "
                "при оформлении амбулаторного номера не удалось получить "
                "сообщение из диалогового окна"
            )
        dialog_messages_yes = [
            "Данное посещение имеет пересечение",
        ]
        for message_yes in dialog_messages_yes:
            if message_yes in dialog_message:
                dialog.all("button").element_by(have.text("Да")).click()
                return True
        dialog_messages_no: list[str] = []
        for message_no in dialog_messages_no:
            if message_no in dialog_message:
                dialog.all("button").element_by(have.text("Нет")).click()
                browser.element(
                    "table[matomo_event_id"
                    "='win_swEvnPLEditWindow_btn_Otmena'] button"
                ).click()
                return False
        raise EcpAutoclickerException(
            f"Ошибка: для пациента {self.ecp_patient_fullname} "
            "при оформлении амбулаторного номера получено неизвестное "
            "сообщение из диалогового окна"
        )

    def __open_outpatient_card(self):
        self.__click()
        browser.element(
            "table[matomo_event_id='win_swMPWorkPlacePriemWindow_tbr"
            "_mpwpprToolbar_btn_Dobavit_sluchay_APL'] button"
        ).click()
        wait_for_loading()
        return self.__handle_outpatient_card_dialog_window()

    def __select_outpatient_card_examination(self, doctor_fullname: str):
        browser.element("#EPLEF_EvnVizitPLGrid .x-grid3-scroller").all(
            "tr div"
        ).element_by(have.text(doctor_fullname.upper())).click().double_click()
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
        self.__handle_outpatient_card_dialog_window()
        wait_for_loading()
        browser.element(
            "table[matomo_event_id='win_swEvnPLEditWindow_btn_Sohranit'] "
            "button"
        ).click()
        wait_for_loading()

    def set_outpatient_card_number(self, doctor_fullname: str):
        if not self.__open_outpatient_card():
            return False
        self.__select_outpatient_card_examination(doctor_fullname)
        self.__set_outpatient_card_visit_code()
        self.__set_outpatient_card_validity_level()
        self.__set_outpatient_card_patient_condition()
        self.__save_outpatient_card_examination()
        return True

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

    def __exists_emh_examination_text(self, doctor_fullname: str) -> bool:
        try:
            browser.all("div.NewStyleDoc > div.WrapDoc").element_by(
                have.text(doctor_fullname.upper())
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
            .element_by(have.exact_text("Первичный осмотр (травматолог)"))
            .click()
        )
        wait_for_loading()
        element.double_click()
        wait_for_loading()
        wait_for_loading()

    def __set_emh_examination_text_to_block(self, field_name: str, text: str):
        iframe = browser.element(
            "div.NewStyleDoc div.WrapDoc div.freedoc_opened "
            f"iframe[id^='{field_name}']"
        )
        iframe.wait.for_(be.present)
        iframe_webelement = iframe.locate()
        browser.driver.switch_to.frame(iframe_webelement)
        element = browser.element("#tinymce > p")
        text_start = text[:-3]
        text_end = text[-3:]
        if len(text) < 7:
            text_start = ""
            text_end = text
        element.click().type(text_start)
        send_keys_one_by_one(element, text_end)
        browser.driver.switch_to.default_content()

    def __set_emh_examination_text(self):
        if not self.qinpatients_examination:
            raise EcpAutoclickerException(
                f"Ошибка: для пациента {self.ecp_patient_fullname} "
                "отсутствуют данные `qinpatients_examination`."
            )
        self.__set_emh_examination_text_to_block(
            "field_complaint", self.qinpatients_examination.complaints
        )
        self.__set_emh_examination_text_to_block(
            "field_anamnesmorbi", self.qinpatients_examination.anamnesis_morbi
        )
        self.__set_emh_examination_text_to_block(
            "field_anamnesvitae", self.qinpatients_examination.anamnesis_vitae
        )
        self.__set_emh_examination_text_to_block(
            "field_objectivestatus",
            self.qinpatients_examination.status_praesens,
        )
        self.__set_emh_examination_text_to_block(
            "field_localstatus", self.qinpatients_examination.status_localis
        )
        self.__set_emh_examination_text_to_block(
            "field_autoname1", self.qinpatients_examination.pre_diagnosis
        )
        self.__set_emh_examination_text_to_block(
            "field_autoname2", self.qinpatients_examination.pre_doctor
        )
        self.__set_emh_examination_text_to_block(
            "field_SurveyPlan",
            self.qinpatients_examination.examination_plan.replace(
                "<br>", "\n"
            ),
        )
        self.__set_emh_examination_text_to_block(
            "field_researchResults",
            self.qinpatients_examination.rg_description,
        )
        self.__set_emh_examination_text_to_block(
            "field_diagnos", self.qinpatients_examination.diagnosis
        )
        self.__set_emh_examination_text_to_block(
            "field_Rationalediag",
            "Диагноз поставлен на основании жалоб, анамнеза, "
            "данных осмотра, результатов лабораторных и инструментальных "
            "исследований, консультаций специалистов.",
        )
        self.__set_emh_examination_text_to_block(
            "field_autoname3", self.qinpatients_examination.doctor
        )
        self.__set_emh_examination_text_to_block(
            "field_autoname4", self.qinpatients_examination.first_doctor
        )
        prescribes = self.qinpatients_examination.prescribes.replace(
            "<br>", "\n"
        )
        manipulations = self.qinpatients_examination.manipulations.replace(
            "<br>", "\n"
        )
        manipulations_all = (
            f"{prescribes + '\n' if prescribes else ''}{manipulations}"
        )
        self.__set_emh_examination_text_to_block(
            "field_AdditionalOper", manipulations_all
        )
        hospitalization = (
            (
                self.qinpatients_examination.hospitalization.replace(
                    "<br>", "\n"
                )
                .replace("<br>", "\n")
                .replace('<span style=" text-decoration: underline;">', "")
                .replace("</span>", "")
            )
            if self.qinpatients_examination.hospitalization
            else "госпитализация не показана"
        )
        self.__set_emh_examination_text_to_block(
            "field_TreatmentPlan", hospitalization
        )
        self.__set_emh_examination_text_to_block(
            "field_AdditionalData", self.qinpatients_examination.special_note
        )
        self.__set_emh_examination_text_to_block(
            "field_recommendations",
            self.qinpatients_examination.recommendations.replace("<br>", "\n"),
        )
        self.__set_emh_examination_text_to_block(
            "field_autoname5", self.qinpatients_examination.doctor
        )

    def __close_emh(self):
        browser.element(
            "table[matomo_event_id='win_swPersonEmkWindow_btn_Zakrit'] button"
        ).click()
        wait_for_loading()

    def set_emh_examination_text(self, doctor_fullname: str):
        self.__open_emh()
        self.__select_emh_case_disease()
        if self.__exists_emh_examination_text(doctor_fullname):
            self.__close_emh()
            return False
        self.__click_emh_add_document()
        self.__select_emh_template()
        self.__set_emh_examination_text()
        self.__close_emh()
        return True

    def __open_emh_examination_text(self, doctor_fullname: str):
        browser.all("div.NewStyleDoc > div.WrapDoc").element_by(
            have.text(doctor_fullname.upper())
        ).element("span[title='Показать документ']").click()

    def __get_emh_examination_block_text(self, field_name: str) -> str:
        iframe = browser.element(
            "div.NewStyleDoc div.WrapDoc div.freedoc_opened "
            f"iframe[id^='{field_name}']"
        )
        iframe.wait.for_(be.present)
        iframe_webelement = iframe.locate()
        browser.driver.switch_to.frame(iframe_webelement)
        element = browser.element("#tinymce > p")
        try:
            block_text = element.locate().get_attribute("innerText")
        except Exception as e:
            raise EcpAutoclickerException(
                f"Ошибка: для пациента {self.ecp_patient_fullname} "
                f"не удалось получить текст блока `{field_name}` "
                "в ЭМК."
            ) from e
        browser.driver.switch_to.default_content()
        return block_text.strip() if block_text else ""

    def get_data_from_emh(self, doctor_fullname: str) -> FromEmhResults:
        self.__open_emh()
        self.__select_emh_case_disease()
        if not self.__exists_emh_examination_text(doctor_fullname):
            self.__close_emh()
            return FromEmhResults.OTHER_DOCTOR
        self.__open_emh_examination_text(doctor_fullname)
        result_field_text = self.__get_emh_examination_block_text(
            "field_autoname10"
        )
        intpatient_triggers = [
            "показана госпитализация",
            "план лечения",
        ]
        outpatient_triggers = [
            "по месту жительства",
            "амбулаторно",
        ]
        for trigger in intpatient_triggers:
            if trigger.lower() in result_field_text.lower():
                return FromEmhResults.INPATIENT
        for trigger in outpatient_triggers:
            if trigger.lower() in result_field_text.lower():
                break
        else:
            return FromEmhResults.UNKNOWN_RESULT
        self.doctor = doctor_fullname
        self.anamnesis_morbi = self.__get_emh_examination_block_text(
            "field_anamnesmorbi"
        )
        self.diagnosis = self.__get_emh_examination_block_text("field_diagnos")
        self.result_status_number = 3  # OUTPATIENT
        self.__close_emh()
        return FromEmhResults.OUTPATIENT
