import re

from ecp.case_disease import CaseDisease
from qinpatients.convert_to_ecp import (
    condition_to_ecp,
    department_to_ecp,
    result_to_ecp,
    trauma_type_to_ecp,
)
from qinpatients.examination import Examination


def get_qinpatients_patients(
    ecp_case_disease_list: list[CaseDisease], doctor_fullname: str
):
    patients_amount = len(ecp_case_disease_list)
    print(
        f"Получение данных из БД QInPatients: 0 из {patients_amount}",
        end="\r",
    )
    case_disease_qinpatients_list: list[CaseDisease] = []
    case_disease_noqinpatients_list: list[CaseDisease] = []
    patient_count = 0
    for case_disease in ecp_case_disease_list:
        examination = Examination.get_examination(
            case_disease.ecp_patient_fullname,
            case_disease.ecp_patient_birthday,
            case_disease.ecp_incoming_date,
            doctor_fullname,
        )
        patient_count += 1
        print(
            "Получение данных из БД QInPatients: "
            f"{patient_count} из {patients_amount}",
            end="\r",
        )
        if not examination:
            case_disease_noqinpatients_list.append(case_disease)
            continue
        case_disease.doctor = examination.doctor
        case_disease.diagnosis = examination.diagnosis
        case_disease.anamnesis_morbi = examination.anamnesis_morbi
        case_disease.trauma_type_number = trauma_type_to_ecp.get(
            examination.trauma_type, 0
        )
        condition_match = re.match(
            r"^Общее состояние [а-я ]+", examination.status_praesens
        )
        if condition_match:
            condition = (
                condition_match.group()
                .split("Общее состояние ")[-1]
                .strip()
                .lower()
            )
            case_disease.condition_number = condition_to_ecp.get(condition, 1)
        case_disease.result_status_number = result_to_ecp.get(
            examination.result_status, 0
        )
        case_disease.inpatient_department_code = department_to_ecp.get(
            examination.department, 0
        )
        case_disease.examination_text = examination.get_examination_text()
        case_disease.qinpatients_examination = examination
        case_disease_qinpatients_list.append(case_disease)
    print(
        "Получение данных из БД QInPatients: "
        f"{patient_count} из {patients_amount}",
    )
    print(
        "Всего пациентов, которые могут быть оформлены данными "
        f"из БД QInPatients: {len(case_disease_qinpatients_list)}"
    )
    return case_disease_qinpatients_list, case_disease_noqinpatients_list
