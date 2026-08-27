import re

from ai.exceptions import AiException
from ai.gemini import get_mkb_codes
from ecp.case_disease import CaseDisease
from ecp.exceptions import EcpAutoclickerException

MIN_ANAMNESIS_MORBI_LENGTH = 20
MIN_DIAGNOSIS_LENGTH = 8


def get_diagnosis_reason_code(ecp_case_disease_list: list[CaseDisease]):
    anamnesis_diagnosis_list: list[dict] = []
    for case_disease in ecp_case_disease_list:
        if (
            not (case_disease.anamnesis_morbi and case_disease.diagnosis)
            or len(case_disease.anamnesis_morbi) < MIN_ANAMNESIS_MORBI_LENGTH
            or len(case_disease.diagnosis) < MIN_DIAGNOSIS_LENGTH
        ):
            raise EcpAutoclickerException(
                f"Ошибка: у пациента {case_disease.ecp_patient_fullname} "
                "некорректно заполнен анамнез и/или диагноз. "
                "Пожалуйста, исправьте."
            )
        anamnesis_diagnosis_list.append(
            {
                "anamnesis": case_disease.anamnesis_morbi,
                "diagnosis": case_disease.diagnosis,
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
    if not code_list:
        raise AiException("Ошибка: ответ от AI отсутсвует!")
    for i, case_disease in enumerate(ecp_case_disease_list):
        code_pattern = re.compile(r"^[A-Z][0-9][0-9][0-9.]{0,3}$")
        reason_code = code_list[i].get("reason_code")
        diagnosis_code = code_list[i].get("diagnosis_code")
        # print(
        #     f"Number: {i}, Patient: {case_disease.ecp_patient_fullname}, "
        #     f"Reason code: {reason_code}, Diagnosis code: {diagnosis_code}, "
        #     f"Result status: {case_disease.result_status_number}, "
        #     f"Department: {case_disease.inpatient_department_code}"
        # )
        if not (reason_code and diagnosis_code) or not (
            code_pattern.match(reason_code)
            and code_pattern.match(diagnosis_code)
        ):
            raise EcpAutoclickerException(
                "Ошибка: не удалось получить коды МКБ-10 для пациента "
                f"{case_disease.ecp_patient_fullname}. "
                "Возможно серверы AI сейчас не доступны, попробуйте "
                "позже. Также проверьте корректность анамнеза и диагноза "
                "для вышеуказанного пациента."
            )
        case_disease.reason_code = reason_code
        case_disease.diagnosis_code = diagnosis_code
