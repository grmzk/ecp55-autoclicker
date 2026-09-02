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

# text = "f"
# print(text[:-2])  # Output: "fu"
# print(text[-2:])  # Output: "fuc"

# list1 = [1, 2, 3]
# list2 = [4, 5, 6]
# print(list1 + list2)  # Output: [1, 2, 3, 4, 5, 6]

# i1, i2, i3 = 1234567, 45, 856
# # Выводим числа в колонки шириной по 10 символов
# print(f'{f"({i1})":<5}{f"({i2})":<5}{f"({i3})":<5}')

# from datetime import date

# start_date = date(2023, 1, 1)
# end_date = date(2023, 1, 7)  # Включаем end_date

# # Важно: end_date нужно сдвинуть на день вперёд, иначе цикл его не захватит
# for ordinal in range(start_date.toordinal(), end_date.toordinal() + 1):
#     current_date = date.fromordinal(ordinal)
#     print(current_date)
