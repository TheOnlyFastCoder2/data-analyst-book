# Глава 2. Основы Python

Python — основной язык аналитиков: простой синтаксис и готовые библиотеки под любую задачу. На карте roadmap.sh есть ещё язык R, но на российском рынке вакансий с Python в разы больше, поэтому учим только его.

Цель главы — не стать программистом, а научиться читать и писать код на том уровне, который нужен для pandas. Выполняй каждый пример в Jupyter.

## 2.1. Переменные и типы данных

Переменная — это имя, привязанное к значению.

```python
price = 1200          # int — целое число
discount = 0.15       # float — дробное число
city = "Москва"       # str — строка
is_new = True         # bool — логическое значение: True или False
nothing = None        # None — «нет значения»

final_price = price * (1 - discount)
print(final_price)        # 1020.0
print(type(final_price))  # <class 'float'>
```

Арифметика:

```python
print(7 + 2)    # 9
print(7 / 2)    # 3.5  — обычное деление, всегда float
print(7 // 2)   # 3    — целая часть
print(7 % 2)    # 1    — остаток
print(7 ** 2)   # 49   — степень
```

Преобразование типов — частая операция при очистке данных:

```python
print(int("42") + 1)      # 43
print(float("3.14") * 2)  # 6.28
print(str(100) + " руб.") # 100 руб.
```

## 2.2. Строки

```python
name = "  Иван Петров  "

print(name.strip())            # 'Иван Петров' — убрать пробелы по краям
print(name.strip().lower())    # 'иван петров'
print(name.strip().split())    # ['Иван', 'Петров'] — разбить по пробелам
print(name.replace("Иван", "Пётр"))
print(len(name.strip()))       # 11 — длина
print("Петров" in name)        # True — проверка вхождения
```

f-строки подставляют значения прямо в текст:

```python
city = "Казань"
revenue = 1534200.5
print(f"Выручка в городе {city}: {revenue:,.0f} руб.")
# Выручка в городе Казань: 1,534,200 руб.
print(f"Доля: {0.1234:.1%}")   # Доля: 12.3%
```

Срезы — способ взять часть строки (и списка). Нумерация идёт с нуля, правая граница не включается:

```python
date = "2026-03-15"
print(date[0:4])   # '2026'
print(date[5:7])   # '03'
print(date[-2:])   # '15' — два последних символа
```

## 2.3. Коллекции

### Список (list) — упорядоченный и изменяемый

```python
sales = [120, 340, 90, 410]

print(sales[0])      # 120 — первый элемент
print(sales[-1])     # 410 — последний
print(sales[1:3])    # [340, 90]

sales.append(250)    # добавить в конец
print(len(sales))    # 5
print(sum(sales))    # 1210
print(max(sales))    # 410
print(sorted(sales, reverse=True))  # [410, 340, 250, 120, 90]
```

### Словарь (dict) — пары «ключ: значение»

```python
order = {"id": 17, "city": "Москва", "amount": 1200}

print(order["city"])               # Москва
order["status"] = "paid"           # добавить ключ
print(order.get("promo", "нет"))   # 'нет' — ключа нет, вернётся значение по умолчанию

for key, value in order.items():
    print(key, "=", value)
```

Словарь — это прообраз строки таблицы, а список словарей — прообраз самой таблицы. Именно в таком виде данные приходят из API (глава 6).

### Кортеж (tuple) и множество (set)

```python
point = (55.75, 37.62)      # кортеж: как список, но изменить нельзя
lat, lon = point            # распаковка

cities = ["Москва", "Казань", "Москва", "Уфа"]
print(set(cities))          # множество: только уникальные значения
print(len(set(cities)))     # 3
```

## 2.4. Условия

Блоки кода в Python выделяются **отступом в 4 пробела**. Это не оформление, а синтаксис.

```python
amount = 7500

if amount >= 10000:
    segment = "крупный"
elif amount >= 3000:
    segment = "средний"
else:
    segment = "мелкий"

print(segment)   # средний
```

Операторы сравнения: `==`, `!=`, `>`, `<`, `>=`, `<=`. Логические: `and`, `or`, `not`.

```python
city = "Москва"
if city == "Москва" and amount > 5000:
    print("Крупный заказ из Москвы")
```

Частая ошибка: `=` — это присваивание, `==` — сравнение.

## 2.5. Циклы

`for` перебирает элементы коллекции:

```python
sales = [120, 340, 90, 410]

total = 0
for s in sales:
    total += s        # то же, что total = total + s
print(total)          # 960

for i in range(3):    # range(3) даёт 0, 1, 2
    print(i)

for i, s in enumerate(sales):   # номер и значение одновременно
    print(i, s)
```

`while` повторяет, пока условие истинно:

```python
balance = 1000
months = 0
while balance < 2000:
    balance *= 1.1
    months += 1
print(months)   # 8
```

### Генераторы списков

Короткая запись цикла, который строит новый список. В чужом коде встречается постоянно:

```python
sales = [120, 340, 90, 410]

with_tax = [s * 1.2 for s in sales]
big = [s for s in sales if s > 100]

print(with_tax)   # [144.0, 408.0, 108.0, 492.0]
print(big)        # [120, 340, 410]
```

## 2.6. Функции

Функция — именованный кусок кода, который можно вызывать много раз.

```python
def conversion(orders, visits):
    """Возвращает конверсию в процентах."""
    if visits == 0:
        return 0.0
    return orders / visits * 100

print(conversion(30, 1200))             # 2.5
print(conversion(orders=5, visits=0))   # 0.0
```

Аргументы со значением по умолчанию:

```python
def segment(amount, threshold=10000):
    return "крупный" if amount >= threshold else "обычный"

print(segment(12000))                    # крупный
print(segment(12000, threshold=20000))   # обычный
```

`lambda` — функция в одну строку без имени. В pandas её передают в методы `apply` и `sort_values`:

```python
orders = [{"id": 1, "amount": 500}, {"id": 2, "amount": 90}]
orders_sorted = sorted(orders, key=lambda o: o["amount"])
print(orders_sorted[0]["id"])   # 2
```

Правило: если один и тот же код ты скопировал третий раз — вынеси его в функцию.

## 2.7. Модули и библиотеки

```python
import math
from datetime import date, timedelta
from collections import Counter

print(math.sqrt(16))                        # 4.0

d = date(2026, 3, 15)
print(d + timedelta(days=30))               # 2026-04-14
print(d.weekday())                          # 6 — воскресенье (понедельник = 0)

cities = ["Москва", "Казань", "Москва", "Уфа", "Москва"]
print(Counter(cities).most_common(2))       # [('Москва', 3), ('Казань', 1)]
```

Сторонние библиотеки по традиции импортируют под короткими именами. Запомни их — так пишут все:

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
```

## 2.8. Файлы

```python
with open("notes.txt", "w", encoding="utf-8") as f:
    f.write("Первая строка\nВторая строка\n")

with open("notes.txt", encoding="utf-8") as f:
    for line in f:
        print(line.strip())
```

Конструкция `with` сама закроет файл. Всегда указывай `encoding="utf-8"`. На macOS это кодировка по умолчанию, но на Windows — нет: без явного указания твой код на компьютере коллеги превратит русские буквы в кракозябры.

## 2.9. Ошибки

Сообщение об ошибке (traceback) читают **снизу вверх**: последняя строка говорит, что случилось, строки выше — где.

| Ошибка | Что значит |
|--------|-----------|
| `NameError` | Переменной с таким именем нет (опечатка или ячейка не выполнена) |
| `TypeError` | Операция с неподходящим типом: `"5" + 5` |
| `KeyError` | В словаре или таблице нет такого ключа или столбца |
| `IndexError` | Элемента с таким номером нет |
| `ValueError` | Тип подходит, значение — нет: `int("abc")` |
| `IndentationError` | Сбит отступ |

Перехватить ошибку можно через `try / except`:

```python
raw = ["100", "250", "н/д", "80"]

values = []
for item in raw:
    try:
        values.append(int(item))
    except ValueError:
        print(f"Пропускаю: {item}")

print(values)   # [100, 250, 80]
```

Когда не получается: прочитай последнюю строку ошибки, вбей её в поиск и только потом проси помощи. Умение гуглить ошибки — рабочий навык, а не слабость.

### Как искать ошибку, когда код работает неправильно

Хуже ошибки с красным текстом — код, который выполнился, но посчитал не то. Приёмы поиска:

**1. Смотри на значения.** Не гадай, что лежит в переменной, — выведи её. Запись `f"{имя=}"` печатает и название, и значение:

```python
price = "1200"
quantity = 3

print(f"{price=} {quantity=}")        # price='1200' quantity=3 — кавычки выдают строку
print(type(price), type(quantity))
print(price * quantity)               # 120012001200 — строка повторилась три раза
print(int(price) * quantity)          # 3600
```

Самая частая причина неверного результата — значение не того типа: число, прочитанное как строка.

**2. Проверяй по частям.** Длинное выражение разбей на шаги и посмотри результат каждого:

```python
orders = [{"city": " Москва", "amount": 1200}, {"city": "москва", "amount": 300}]

# Одной строкой — непонятно, где ошибка
print(sum(o["amount"] for o in orders if o["city"] == "Москва"))     # 0, а ждали 1500

# По шагам — видно сразу
cities = [o["city"] for o in orders]
print(cities)                         # [' Москва', 'москва'] — пробел и регистр!

clean = [o["city"].strip().capitalize() for o in orders]
print(clean)                          # ['Москва', 'Москва']
print(sum(o["amount"] for o in orders if o["city"].strip().capitalize() == "Москва"))   # 1500
```

**3. Уменьши задачу.** Не ищи ошибку на миллионе строк. Возьми три строки, для которых знаешь правильный ответ, и проверь на них.

**4. Читай справку.** `help(функция)` или `функция?` в Jupyter покажут, что функция принимает и возвращает. `dir(объект)` — список всех методов объекта.

```python
help(str.split)
print([name for name in dir(str) if not name.startswith("_")][:8])
```

**5. Объясни код вслух.** Строчка за строчкой расскажи, что делает программа, — хоть коллеге, хоть резиновой утке на столе. Ошибка часто находится на фразе «а здесь оно берёт… стоп».

## 2.10. Мини-проект: анализ заказов без библиотек

Соберём всё вместе. Сделай это упражнение — в главе 5 повторишь его в pandas и увидишь, зачем нужны библиотеки.

```python
orders = [
    {"id": 1, "city": "Москва", "category": "Книги",   "amount": 1200},
    {"id": 2, "city": "Казань", "category": "Техника", "amount": 15400},
    {"id": 3, "city": "Москва", "category": "Техника", "amount": 8900},
    {"id": 4, "city": "Уфа",    "category": "Книги",   "amount": 700},
    {"id": 5, "city": "Москва", "category": "Книги",   "amount": 2100},
]

# Выручка по городам
revenue = {}
for o in orders:
    revenue[o["city"]] = revenue.get(o["city"], 0) + o["amount"]

for city, total in sorted(revenue.items(), key=lambda x: x[1], reverse=True):
    print(f"{city}: {total}")

# Средний чек
avg = sum(o["amount"] for o in orders) / len(orders)
print(f"Средний чек: {avg:.0f}")
```

Результат:

```
Казань: 15400
Москва: 12200
Уфа: 700
Средний чек: 5660
```

## 2.11. Что дальше

Эта глава дала минимум, с которым уже можно работать. Но чтобы уверенно читать чужой код и писать свой, нужны ещё три главы — пройди их до SQL или параллельно с ним:

- [Глава 2А. Python: следующий уровень](02a-python-dalshe.md) — как Python хранит данные, распаковка, генераторы, декораторы, исключения, модули.
- [Глава 2Б. Объектно-ориентированное программирование](02b-oop.md) — классы, наследование, композиция, dataclass.
- [Глава 2В. Красивый код и паттерны](02c-chistyj-kod.md) — оформление, имена, функции, рефакторинг, тесты, паттерны проектирования.

## Практика на GitHub

В списке материалов нет отдельного репозитория по базовому синтаксису, поэтому действуем так:

- [jakevdp/PythonDataScienceHandbook](https://github.com/jakevdp/PythonDataScienceHandbook) — открой папку `notebooks` и пройди первую главу про IPython и Jupyter: автодополнение, справка через `?`, «магические» команды.
- [wesm/pydata-book](https://github.com/wesm/pydata-book) — ноутбуки `ch02` и `ch03` повторяют основы языка и встроенные структуры данных глазами автора pandas.
- В каталоге [awesome-data-analysis](https://github.com/PavelGrigoryevDS/awesome-data-analysis) в разделе Python найди один тренажёр с задачами и решай по 3–5 задач в день.

## Задания

1. Напиши функцию `mean(values)`, которая считает среднее списка без `sum` и `len`.
2. Напиши функцию `median(values)`. Учти чётное и нечётное количество элементов.
3. Дан список строк `["  Москва", "москва ", "КАЗАНЬ", "Казань"]`. Приведи к единому виду и посчитай, сколько раз встречается каждый город.
4. По списку `orders` из раздела 2.10 посчитай: число заказов и средний чек по каждой категории.
5. Напиши функцию, которая принимает дату строкой `"2026-03-15"` и возвращает квартал.
6. Сохрани результат задания 4 в текстовый файл.

## Проверь себя

- Чем список отличается от словаря и когда что использовать?
- Что вернёт `[1, 2, 3, 4][1:3]`?
- Чем `/` отличается от `//`?
- Как читать traceback?
- Что такое генератор списка?

## Решения

### Задание 1. Среднее без sum и len

```python
def mean(values):
    total = 0
    count = 0
    for value in values:
        total += value
        count += 1
    if count == 0:
        raise ValueError("среднее пустого списка не определено")
    return total / count

print(mean([12, 15, 11, 19]))     # 14.25
```

Сумму и количество накапливаем в одном проходе. Проверка на пустой список нужна, иначе получится деление на ноль с непонятным сообщением.

### Задание 2. Медиана

```python
def median(values):
    ordered = sorted(values)              # sorted возвращает новый список, исходный не меняется
    n = len(ordered)
    middle = n // 2
    if n % 2 == 1:                        # нечётное количество — берём средний элемент
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2    # чётное — среднее двух центральных

print(median([5, 1, 3]))          # 3
print(median([5, 1, 3, 100]))     # 4.0
```

Частая ошибка — забыть отсортировать. Вторая — использовать `values.sort()`: он меняет список, который передали в функцию.

### Задание 3. Города

```python
raw = ["  Москва", "москва ", "КАЗАНЬ", "Казань"]

counts = {}
for city in raw:
    clean = city.strip().lower().capitalize()
    counts[clean] = counts.get(clean, 0) + 1

print(counts)                     # {'Москва': 2, 'Казань': 2}
```

Цепочка `strip → lower → capitalize` приводит любое написание к одному виду. Порядок важен: сначала убираем пробелы, иначе `capitalize` попытается сделать заглавным пробел.

### Задание 4. Заказы и средний чек по категориям

```python
orders = [
    {"id": 1, "city": "Москва", "category": "Книги",   "amount": 1200},
    {"id": 2, "city": "Казань", "category": "Техника", "amount": 15400},
    {"id": 3, "city": "Москва", "category": "Техника", "amount": 8900},
    {"id": 4, "city": "Уфа",    "category": "Книги",   "amount": 700},
    {"id": 5, "city": "Москва", "category": "Книги",   "amount": 2100},
]

stats = {}
for order in orders:
    category = order["category"]
    if category not in stats:
        stats[category] = {"count": 0, "total": 0}
    stats[category]["count"] += 1
    stats[category]["total"] += order["amount"]

for category, s in stats.items():
    print(f"{category}: заказов {s['count']}, средний чек {s['total'] / s['count']:.0f}")
```

Результат: «Книги: заказов 3, средний чек 1333» и «Техника: заказов 2, средний чек 12150». Средний чек считаем в конце, из накопленных суммы и количества: усреднять «на ходу» нельзя.

### Задание 5. Квартал по дате

```python
def quarter(date_text):
    month = int(date_text[5:7])           # символы с индексами 5 и 6 — месяц
    return (month - 1) // 3 + 1

for d in ["2026-01-10", "2026-03-15", "2026-04-01", "2026-12-31"]:
    print(d, quarter(d))                  # 1, 1, 2, 4
```

Формула `(month - 1) // 3 + 1`: вычитаем единицу, чтобы месяцы 1–3 попали в одну тройку (0, 1, 2 → 0), делим нацело и возвращаем нумерацию с единицы.

### Задание 6. Сохранение в файл

```python
with open("category_report.txt", "w", encoding="utf-8") as f:
    f.write("Категория;Заказов;Средний чек\n")
    for category, s in stats.items():
        f.write(f"{category};{s['count']};{s['total'] / s['count']:.0f}\n")

with open("category_report.txt", encoding="utf-8") as f:
    print(f.read())
```

Сразу после записи читаем файл обратно и смотрим глазами — привычка проверять результат, а не верить, что «наверное, записалось».
