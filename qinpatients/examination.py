import datetime
from dataclasses import dataclass

from common.postgresql_db import pg_select_data
from qinpatients.result_status import ResultStatus

TIMEZONE = 6 * 60 * 60  # UTC+6
EXAMINATION_DATE_LAG = 2 * 60 * 60  # 2 hour


@dataclass
class Examination:  # pylint: disable=too-many-instance-attributes
    patient_fullname: str
    patient_birthday: datetime.date
    examination_date: datetime.datetime
    trauma_type: str
    complaints: str
    anamnesis_morbi: str
    anamnesis_vitae: str
    anamnesis_gynecological: str
    status_praesens: str
    status_localis: str
    pre_diagnosis: str
    pre_doctor: str
    examination_plan: str
    rg_description: str
    diagnosis: str
    doctor: str
    first_doctor: str
    manipulations: str
    hospitalization: str
    prescribes: str
    recommendations: str
    special_note: str
    department: str
    result_status: ResultStatus

    def get_age(self, at_date=datetime.datetime.now().date()):
        birthday = self.patient_birthday
        age = (
            at_date.year
            - birthday.year
            - ((at_date.month, at_date.day) < (birthday.month, birthday.day))
        )
        ending: str
        if 5 <= age <= 20:
            ending = "лет"
        elif age % 10 == 1:
            ending = "год"
        elif 2 <= age % 10 <= 4:
            ending = "года"
        else:
            ending = "лет"
        return f"{age} {ending}"

    def get_examination_text(self):
        examination_text = (
            f"Осмотр травматолога: {self.doctor}\n"
            f"Дата: {self.examination_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"Ф.И.О.: {self.patient_fullname}, "
            f"{self.examination_date.strftime('%d.%m.%Y')} г. р. "
            f"({self.get_age(self.examination_date.date())})\n"
            f"Вид травмы: {self.trauma_type}\n"
            "Жалобы:\n"
            f"{self.complaints}\n"
            "Анамнез заболевания:\n"
            f"{self.anamnesis_morbi}\n"
            "Анамнез жизни:\n"
            f"{self.anamnesis_vitae}\n"
            "Объективный статус:\n"
            f"{self.status_praesens}\n"
            "Локальный статус:\n"
            f"{self.status_localis}\n"
            "Диагноз предварительный:\n"
            f"{self.pre_diagnosis}\n"
            f"Врач: {self.doctor}\n"
            "План обследования:\n"
            f"{self.examination_plan}\n"
            f"{
                f"Назначено:\n{self.prescribes}\n"
                if self.prescribes else ''
            }"
            "Описание рентгенограмм:\n"
            f"{self.rg_description}\n"
            "Диагноз:\n"
            f"{self.diagnosis}\n"
            "Обоснование диагноза:\n"
            "Диагноз поставлен на основании жалоб, анамнеза, данных осмотра, "
            "результатов лабораторных и инструментальных исследований, "
            "консультаций специалистов.\n"
            f"Врач: {self.doctor}\n"
            "Зав. Отделением (первый дежурный травматолог): "
            f"{self.first_doctor}\n"
            f"{
                f"Манипуляции:\n{self.manipulations}\n"
                if self.manipulations else ''
            }"
            f"{
                f"Госпитализация:\n{self.hospitalization}\n"
                if self.hospitalization else ''
            }"
            f"{
                f"Особые замечания:\n{self.special_note}\n"
                if self.special_note else ''
            }"
            f"{
                f"Рекомендации:\n{self.recommendations}\n"
                if self.recommendations else ''
            }"
            f"Врач: {self.doctor}"
        )
        examination_text = (
            examination_text.replace("<br>", "\n")
            .replace('<span style=" text-decoration: underline;">', "")
            .replace("</span>", "")
        )
        return examination_text

    @staticmethod
    def get_examination(
        patient_fullname: str,
        patient_birthday: datetime.date,
        examination_date: datetime.datetime,
        doctor_fullname: str,
    ) -> Examination | None:
        select_query = (
            "SELECT "
            "       CONCAT_WS(' ', patients.family, patients.name, "
            "                      patients.surname), "
            "       patients.birthday, "
            "       examinations.datetime, "
            "       examinations.traumatype, "
            "       examinations.complaints, "
            "       examinations.anamnesismorbi, "
            "       examinations.anamnesisvitae, "
            "       examinations.anamnesisgynecological, "
            "       examinations.statuspraesens, "
            "       examinations.statuslocalis, "
            "       examinations.prediagnosis, "
            "       CONCAT_WS(' ', pre_doctor.family, pre_doctor.name, "
            "                      pre_doctor.surname), "
            "       examinations.examinationplan, "
            "       examinations.rgdescription, "
            "       examinations.diagnosis, "
            "       CONCAT_WS(' ', doctor.family, doctor.name, "
            "                      doctor.surname), "
            "       CONCAT_WS(' ', first_doctor.family, first_doctor.name, "
            "                      first_doctor.surname), "
            "       examinations.manipulations, "
            "       examinations.hospitalization, "
            "       examinations.prescribes, "
            "       examinations.recommendations, "
            "       examinations.specialnote, "
            "       departments.department, "
            "       casesofdisease.status "
            "FROM patients "
            "   JOIN casesofdisease "
            "       ON patients.idpatient = casesofdisease.patient "
            "   JOIN examinations "
            "       ON casesofdisease.idcaseofdisease "
            "               = examinations.caseofdisease "
            "           AND examinations.examinationtype = 'Первичный осмотр' "
            "   JOIN doctors AS pre_doctor "
            "       ON examinations.prediagnosisdoctor = pre_doctor.iddoctor "
            "   JOIN doctors AS doctor "
            "       ON examinations.diagnosisdoctor = doctor.iddoctor "
            "   JOIN doctors AS first_doctor "
            "       ON examinations.firstdoctor = first_doctor.iddoctor "
            "   JOIN departments "
            "       ON casesofdisease.department = departments.iddepartment "
            "WHERE CONCAT_WS(' ', patients.family, patients.name, "
            "                     patients.surname) ILIKE %s "
            "   AND patients.birthday = %s "
            "   AND CONCAT_WS(' ', doctor.family, doctor.name, "
            "                      doctor.surname) ILIKE %s "
        )
        response = pg_select_data(
            select_query,
            [patient_fullname, patient_birthday, doctor_fullname],
        )
        if not response:
            return None
        examinations: list[Examination] = []
        for examination_data in response:
            examinations.append(
                Examination(
                    *examination_data[:-1],
                    result_status=ResultStatus(examination_data[-1]),
                )
            )
        for examination in examinations:
            date_difference = (
                examination_date.astimezone(
                    datetime.timezone(datetime.timedelta(seconds=TIMEZONE))
                )
                - examination.examination_date
            ).total_seconds()
            if abs(date_difference) < EXAMINATION_DATE_LAG:
                return examination
        return None
