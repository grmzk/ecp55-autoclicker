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


# print(
#     Examination.get_examination(
#         "ОВАСАПЯН АЛЬБЕРТ ВАНИКОВИЧ",
#         datetime.date(1988, 6, 14),
#         datetime.datetime(
#             2024,
#             6,
#             3,
#             14,
#             31,
#         ),
#     )
# )
