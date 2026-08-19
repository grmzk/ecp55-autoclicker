from qinpatients import ResultStatus

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
