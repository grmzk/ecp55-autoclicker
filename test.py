# import re

# code_pattern = re.compile(r"^[A-Z][0-9][0-9][0-9.]{0,3}$")
# print(code_pattern.match("S33.22"))

# status_praesens = (
#     "Общее состояние относительно удовлетворительное. "
#     "Уровень сознания: ясное, адекватна. Кожные покровы обычного цвета. "
#     "Дыхание в легких проводится с обеих сторон во всех отделах. "
#     "ЧДД 16 в мин. ЧСС 76 в мин. АД 120/70 мм.рт.ст. "
#     "Температура тела 36,6C. "
#     "Живот не вздут, при пальпации мягкий, безболезненный. "
#     "Симптом поколачивания отрицательный с обеих сторон."
# )

# condition_match = re.match(r"^Общее состояние [а-я ]+", status_praesens)
# if condition_match:
#     condition = condition_match.group().split("Общее состояние ")[-1]
#     print(condition)

# from time import sleep

# print("Программа запущена. Пожалуйста, подождите...", end="\r")
# sleep(1)
# print("Программа запущена. Пожалуйста, подождите еще...", end="\r")
# sleep(1)
# print("Программа запущена.                             ", end="\n")

# arr = [1]
# if not arr:
#     print("not arr")

# import datetime

# from qinpatients.examination import Examination

# print(
#     Examination.get_examination(
#         "ГОЛОФАЕВ АНТОН СЕРГЕЕВИЧ",
#         datetime.date(1989, 2, 15),
#         datetime.datetime(
#             2026,
#             8,
#             1,
#             17,
#             29,
#         ),
#         "Павельев Петр Владимирович",
#     ).get_examination_text()
# )

# diagnosis = "S62.30. Перелом другой пястной кости закрытый"
# print(diagnosis.split(". ", maxsplit=1)[0])


# test = (
#     "показана госпитализация в отделение травматологии."
#     '<br><span style=" text-decoration: underline;">План лечения:</span><br>'
#     "- Анальгетики: Sol. Ketorolaci 1,0 в/м.<br>"
#     "- Профилактика ТЭЛА: Прадакса 110 мг х 2 р/д, эластичное бинтование "
#     "нижних конечностей.<br>"
#     "Полный список медикаментов в листе назначений."
# )
# test = (
#     test.replace("<br>", "\n")
#     .replace('<span style=" text-decoration: underline;">', "")
#     .replace("</span>", "")
# )

# print(test)
