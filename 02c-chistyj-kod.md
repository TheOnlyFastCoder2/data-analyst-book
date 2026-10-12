# Глава 2В. Красивый код и паттерны

Код читают гораздо чаще, чем пишут. Через месяц ты откроешь свой ноутбук и будешь разбираться в нём как в чужом. Коллега получит твой скрипт и должен будет понять, можно ли верить числам. Интервьюер откроет твой GitHub и за две минуты решит, звать ли тебя на собеседование.

Красивый код — это не украшательство. Это код, в котором **легко заметить ошибку**. Для аналитика это вопрос доверия к результату.

## 2В.1. Что такое хороший код

Хороший код:

1. **Работает правильно** — и это можно проверить.
2. **Читается без автора.** Не нужно спрашивать «а что тут происходит?».
3. **Легко меняется.** Правка в одном месте не ломает десять других.
4. **Простой.** Решает задачу самым прямым способом.

В Python есть встроенный свод принципов — выполни `import this`. Главные строки оттуда:

- Явное лучше неявного.
- Простое лучше сложного.
- Читаемость имеет значение.
- Ошибки никогда не должны замалчиваться.

## 2В.2. Оформление: PEP 8

PEP 8 — общепринятое соглашение об оформлении кода на Python. Его придерживаются все, поэтому код разных людей выглядит одинаково и читается легко.

| Правило | Плохо | Хорошо |
|---------|-------|--------|
| Отступ — 4 пробела | табуляция, 2 пробела | 4 пробела |
| Пробелы вокруг операторов | `x=a+b` | `x = a + b` |
| Пробел после запятой | `f(a,b)` | `f(a, b)` |
| Без пробелов у именованных аргументов | `f(a = 1)` | `f(a=1)` |
| Длина строки | 200 символов | до 88–100 |
| Импорты | в середине файла | в начале, каждый с новой строки |
| Две пустые строки | — | между функциями и классами |

Стили имён:

| Что | Стиль | Пример |
|-----|-------|--------|
| Переменные, функции | `snake_case` | `total_revenue`, `load_orders` |
| Классы | `PascalCase` | `DataLoader`, `OrderLine` |
| Константы | `UPPER_SNAKE` | `VAT_RATE`, `MAX_ROWS` |
| Внутренние имена | с подчёркиванием | `_cache`, `_validate` |

Порядок импортов: сначала стандартная библиотека, потом сторонние пакеты, потом свои модули — с пустой строкой между группами.

```python
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.metrics import conversion
```

### Пусть оформляет программа

Запоминать все правила не нужно — есть инструменты, которые форматируют код сами:

```bash
pip install ruff
```

```bash
ruff format .
```

```bash
ruff check .
```

Первая команда приводит оформление к стандарту, вторая находит типичные ошибки: неиспользуемые импорты, необъявленные переменные, подозрительные конструкции. В VS Code можно включить форматирование при каждом сохранении файла.

## 2В.3. Имена

Хорошее имя избавляет от комментария. Это самый дешёвый способ сделать код понятнее.

```python
# Плохо: что это вообще?
d = 86400
l = [1200, 15400, 8900]
def calc(a, b):
    return a / b * 100

# Хорошо: читается как текст
SECONDS_PER_DAY = 86400
order_amounts = [1200, 15400, 8900]
def conversion_percent(orders, visits):
    return orders / visits * 100
```

Правила:

- **Имя отвечает на вопрос «что это?»**, а не «какого оно типа?». `users`, а не `list1` или `data2`.
- **Функции — глаголы:** `load_orders`, `calculate_retention`, `remove_duplicates`.
- **Логические значения — вопросы:** `is_active`, `has_discount`, `should_retry`.
- **Коллекции — во множественном числе:** `for order in orders`.
- **Единицы измерения — в имени:** `timeout_seconds`, `revenue_rub`, `duration_ms`.
- **Никаких сокращений, понятных только тебе:** `cnt_usr_act` → `active_user_count`.
- **Не перекрывай встроенные имена:** `list`, `dict`, `sum`, `max`, `type`, `id`, `input`. Назовёшь переменную `sum` — и функция `sum()` в этом ноутбуке перестанет работать.

Короткие имена допустимы в коротком контексте: `i` в цикле на три строки, `x` в `lambda x: x * 2`, общепринятые `df`, `ax`, `fig`. Но если таблиц несколько — давай им смысловые имена: `orders`, `users`, `orders_with_users`, а не `df`, `df2`, `df_final_new`.

## 2В.4. Функции

### Одна функция — одно дело

Признак плохой функции — слово «и» в описании: «загружает данные **и** чистит их **и** считает метрики **и** рисует график».

```python
# Плохо: всё в куче, нельзя ни проверить, ни использовать по частям
def process(path):
    rows = []
    for line in open(path, encoding="utf-8").read().splitlines()[1:]:
        p = line.split(",")
        if p[1] != "" and float(p[1]) > 0:
            rows.append((p[0], float(p[1])))
    t = {}
    for c, a in rows:
        t[c] = t.get(c, 0) + a
    for c in sorted(t, key=t.get, reverse=True):
        print(c, t[c])
```

```python
# Хорошо: три маленькие функции, каждую можно проверить отдельно
from pathlib import Path


def read_orders(path):
    """Читает CSV вида «город,сумма» и возвращает список пар."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()[1:]
    return [tuple(line.split(",")) for line in lines]


def clean_orders(raw_orders):
    """Оставляет заказы с положительной суммой, сумму переводит в число."""
    return [(city, float(amount)) for city, amount in raw_orders if amount and float(amount) > 0]


def revenue_by_city(orders):
    """Возвращает словарь «город → выручка»."""
    totals = {}
    for city, amount in orders:
        totals[city] = totals.get(city, 0) + amount
    return totals


Path("sample.csv").write_text("city,amount\nМосква,1200\nКазань,\nМосква,300\nУфа,-5\n", encoding="utf-8")

orders = clean_orders(read_orders("sample.csv"))
print(revenue_by_city(orders))       # {'Москва': 1500.0}
```

Теперь основной код читается как оглавление: прочитать → очистить → посчитать.

### Чистые функции

**Чистая функция** зависит только от своих аргументов и ничего не меняет снаружи: не трогает глобальные переменные, не изменяет переданные объекты, не печатает и не пишет в файлы.

```python
# Нечистая: результат зависит от глобальной переменной и меняет входной список
threshold = 5000

def mark_big(orders):
    for order in orders:
        order["big"] = order["amount"] > threshold
    return orders

# Чистая: всё нужное приходит в аргументах, вход не меняется
def with_big_flag(orders, threshold):
    return [{**order, "big": order["amount"] > threshold} for order in orders]

source = [{"amount": 1200}, {"amount": 9000}]
print(with_big_flag(source, threshold=5000))
print(source)                         # исходные данные не тронуты
```

Чистые функции легко проверять и безопасно использовать повторно. Старайся, чтобы расчётная часть кода состояла из них, а ввод-вывод (чтение файлов, печать, графики) был собран отдельно.

### Ранний возврат вместо вложенности

```python
# Плохо: «лесенка», главное действие спрятано в глубине
def discount(order):
    if order is not None:
        if order["amount"] > 0:
            if order["is_member"]:
                return order["amount"] * 0.1
            else:
                return 0
        else:
            return 0
    else:
        return 0

# Хорошо: сначала отсекаем особые случаи, основная логика — без отступов
def discount(order):
    if order is None:
        return 0
    if order["amount"] <= 0:
        return 0
    if not order["is_member"]:
        return 0
    return order["amount"] * 0.1

print(discount({"amount": 1000, "is_member": True}))     # 100.0
```

Такие проверки в начале функции называют **охранными условиями** (guard clauses).

### Мало аргументов

Если у функции больше 3–4 аргументов, ими неудобно пользоваться и легко перепутать порядок. Решения:

- сделать аргументы только именованными (через `*`, глава 2А);
- объединить связанные аргументы в `dataclass`;
- разделить функцию на несколько.

Отдельно — про логические флаги. `load(path, True, False)` прочитать невозможно. Либо именованный аргумент (`load(path, skip_header=True)`), либо две отдельные функции.

## 2В.5. Магические числа и константы

**Магическое число** — число в коде, смысл которого неизвестен.

```python
# Плохо
def price_with_tax(price):
    return price * 1.2

def is_active(days_since_last_visit):
    return days_since_last_visit <= 30

# Хорошо
VAT_RATE = 0.2
ACTIVE_WINDOW_DAYS = 30

def price_with_tax(price):
    return price * (1 + VAT_RATE)

def is_active(days_since_last_visit):
    return days_since_last_visit <= ACTIVE_WINDOW_DAYS
```

Выгоды: понятно, что означает число; при изменении правится одно место, а не двадцать; видно, где в анализе заложены допущения.

Все параметры анализа собирай в начале ноутбука или в отдельном файле:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    data_path: str = "data/orders.csv"
    big_order_threshold: float = 10_000
    active_window_days: int = 30
    significance_level: float = 0.05


SETTINGS = Settings()
print(SETTINGS.big_order_threshold)
```

## 2В.6. Комментарии и документация

Комментарий должен объяснять **почему**, а не **что**. «Что» видно из кода.

```python
orders = [{"amount": 1200, "status": "paid"}, {"amount": 990000, "status": "test"}]
MAX_REAL_AMOUNT = 500_000

# Плохо: пересказывает код
# фильтруем заказы
filtered = [o for o in orders if o["amount"] < 500000]

# Хорошо: объясняет причину, которую из кода не узнать
# Заказы дороже 500 тыс. — тестовые транзакции отдела QA (см. обсуждение от 12.03)
real_orders = [o for o in orders if o["amount"] < MAX_REAL_AMOUNT]
print(len(real_orders))
```

В аналитике такие комментарии особенно важны: каждое решение об исключении данных должно быть объяснено.

Если хочется написать комментарий «что делает этот кусок» — обычно лучше вынести кусок в функцию с понятным именем.

### Docstring

Строка документации описывает функцию: что делает, что принимает, что возвращает. Она показывается по `help(func)` и по `func?` в Jupyter.

```python
def retention_rate(returned: int, cohort_size: int) -> float:
    """Считает долю вернувшихся пользователей когорты.

    Args:
        returned: сколько пользователей когорты были активны в периоде.
        cohort_size: исходный размер когорты.

    Returns:
        Доля от 0 до 1.

    Raises:
        ValueError: если размер когорты не положителен.
    """
    if cohort_size <= 0:
        raise ValueError("размер когорты должен быть положительным")
    return returned / cohort_size

print(retention_rate(120, 400))
```

Для простых функций достаточно одной строки. Но определение метрики стоит записывать всегда: «активный пользователь» в разных командах означает разное.

## 2В.7. Питонические приёмы

«Питонический» код использует возможности языка, а не переносит привычки из других языков.

```python
cities = ["Москва", "Казань", "Уфа"]
revenue = [12200, 15400, 700]
order = {"id": 1, "amount": 1200}
```

| Задача | Непитонически | Питонически |
|--------|---------------|-------------|
| Перебор | `for i in range(len(cities)): cities[i]` | `for city in cities:` |
| Перебор с номером | счётчик `i += 1` вручную | `for i, city in enumerate(cities):` |
| Два списка | `revenue[i]` по индексу | `for city, value in zip(cities, revenue):` |
| Проверка на пустоту | `if len(cities) > 0:` | `if cities:` |
| Проверка на None | `if x == None:` | `if x is None:` |
| Логическое значение | `if flag == True:` | `if flag:` |
| Значение по умолчанию | `if "k" in d: v = d["k"] else: v = 0` | `v = d.get("k", 0)` |
| Обмен значений | через временную переменную | `a, b = b, a` |
| Склейка строк | `s += part` в цикле | `", ".join(parts)` |
| Форматирование | `"Город " + name + ": " + str(x)` | `f"Город {name}: {x}"` |
| Файл | `f = open(...)` … `f.close()` | `with open(...) as f:` |
| Диапазон | `x >= 0 and x <= 100` | `0 <= x <= 100` |
| Вхождение | `x == "a" or x == "b"` | `x in {"a", "b"}` |
| Поиск хотя бы одного | цикл с флажком | `any(...)` |

```python
for number, (city, value) in enumerate(zip(cities, revenue), start=1):
    print(f"{number}. {city}: {value:,}")

best_city, best_value = max(zip(cities, revenue), key=lambda pair: pair[1])
print(best_city, ", ".join(cities), order.get("promo", "нет"))
```

## 2В.8. Рефакторинг: пример от начала до конца

**Рефакторинг** — улучшение структуры кода без изменения результата. Посмотрим на типичный «первый скрипт» и приведём его в порядок.

### До

```python
import csv

with open("sales.csv", "w", encoding="utf-8", newline="") as f:
    f.write("date,city,amount,status\n2026-01-05,Москва,1200,paid\n2026-01-06,казань ,15400,paid\n"
            "2026-02-01,Москва,8900,cancelled\n2026-02-03,Уфа,,paid\n2026-02-04,Казань,700,paid\n")

f = open("sales.csv", encoding="utf-8")
r = csv.reader(f)
d = []
for x in r:
    d.append(x)
d = d[1:]
res = {}
for x in d:
    if x[3] == "paid":
        if x[2] != "":
            c = x[1].strip().lower().capitalize()
            m = x[0][0:7]
            if (m, c) in res:
                res[(m, c)] = res[(m, c)] + float(x[2])
            else:
                res[(m, c)] = float(x[2])
for k in res:
    print(k[0], k[1], res[k])
```

Код работает. Но попробуй ответить: что такое `x[3]`? Что будет, если в файле поменяют порядок столбцов? Как проверить, что города нормализуются правильно? Как посчитать то же самое по неделям?

Проблемы:

- имена `f`, `r`, `d`, `x`, `c`, `m`, `res` ничего не говорят;
- обращение к столбцам по номерам;
- файл не закрывается;
- чтение, очистка, расчёт и вывод перемешаны;
- строка `"paid"` и срез `[0:7]` — магические значения;
- ни одну часть нельзя проверить отдельно.

### После

```python
import csv
from collections import defaultdict
from dataclasses import dataclass

PAID_STATUS = "paid"


@dataclass(frozen=True)
class Sale:
    month: str
    city: str
    amount: float


def normalize_city(raw_city: str) -> str:
    """Убирает пробелы и приводит регистр: ' казань ' → 'Казань'."""
    return raw_city.strip().lower().capitalize()


def read_paid_sales(path: str) -> list[Sale]:
    """Читает оплаченные продажи с указанной суммой."""
    sales = []
    with open(path, encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["status"] != PAID_STATUS or not row["amount"]:
                continue
            sales.append(Sale(
                month=row["date"][:7],             # 'ГГГГ-ММ' из даты 'ГГГГ-ММ-ДД'
                city=normalize_city(row["city"]),
                amount=float(row["amount"]),
            ))
    return sales


def revenue_by_month_and_city(sales: list[Sale]) -> dict[tuple[str, str], float]:
    totals = defaultdict(float)
    for sale in sales:
        totals[(sale.month, sale.city)] += sale.amount
    return dict(totals)


def print_report(totals: dict[tuple[str, str], float]) -> None:
    for (month, city), revenue in sorted(totals.items()):
        print(f"{month}  {city:<10} {revenue:>10,.0f}")


sales = read_paid_sales("sales.csv")
print_report(revenue_by_month_and_city(sales))
```

Что изменилось:

- `csv.DictReader` — обращение по именам столбцов, порядок больше не важен;
- `with` закрывает файл;
- `Sale` описывает, с чем мы работаем;
- каждая функция делает одно дело и проверяется отдельно;
- `defaultdict` убрал ветвление «есть ключ — нет ключа»;
- охранное условие с `continue` убрало вложенность.

Кода стало больше — и это нормально. Цель не в краткости, а в том, чтобы ошибке было негде спрятаться.

### Запахи кода

Признаки того, что код пора улучшать:

| Запах | Что делать |
|-------|------------|
| Скопированный кусок встречается третий раз | Вынести в функцию |
| Функция не помещается на экран | Разделить |
| Больше трёх уровней вложенности | Ранний возврат, вынос в функции |
| Имена `data2`, `tmp`, `final_new` | Переименовать по смыслу |
| Числа и строки без объяснения | Константы |
| Длинная цепочка `if / elif` по типу | Словарь функций или полиморфизм |
| Закомментированный код | Удалить: история есть в Git |
| Функция меняет свои аргументы | Возвращать новое значение |

Принцип **DRY** (Don't Repeat Yourself): у каждого знания в программе должно быть одно место. Формула конверсии, записанная в пяти ячейках, рано или поздно в одной из них окажется другой.

Обратная крайность тоже вредна: не строй сложных обобщений «на будущее». Принцип **YAGNI** (You Aren't Gonna Need It) — не пиши того, что пока не понадобилось.

## 2В.9. Тесты

Тест — код, который проверяет другой код. В аналитике это страховка от самого страшного: тихо изменившегося числа.

Простейший тест — `assert`. Он ничего не делает, если условие истинно, и останавливает программу, если ложно:

```python
assert normalize_city("  казань ") == "Казань"
assert normalize_city("МОСКВА") == "Москва"
assert revenue_by_month_and_city([Sale("2026-01", "Уфа", 100), Sale("2026-01", "Уфа", 50)]) == {
    ("2026-01", "Уфа"): 150
}
print("Все проверки пройдены")
```

### pytest

Для проектов используют `pytest`. Тесты кладут в папку `tests`, в файлы с именами `test_*.py`; каждая проверка — функция с именем `test_...`.

```bash
pip install pytest
```

Файл `tests/test_metrics.py`:

```python
import pytest

from src.metrics import conversion


def test_conversion_basic():
    assert conversion(orders=30, visits=1200) == 0.025


def test_conversion_no_orders():
    assert conversion(orders=0, visits=100) == 0


def test_conversion_zero_visits_raises():
    with pytest.raises(ValueError):
        conversion(orders=1, visits=0)


@pytest.mark.parametrize("raw, expected", [
    ("  казань ", "Казань"),
    ("МОСКВА", "Москва"),
    ("уфа", "Уфа"),
])
def test_normalize_city(raw, expected):
    assert normalize_city(raw) == expected
```

Запуск всех тестов:

```bash
pytest
```

Что стоит проверять:

- **обычный случай** — типичные входные данные;
- **граничные случаи** — пустой список, ноль, одно значение, пропуски;
- **ошибочные входы** — что функция падает с понятной ошибкой, а не возвращает чушь;
- **найденные баги** — нашёл ошибку, сначала напиши тест, который её ловит, потом чини.

Структура хорошего теста — три шага: подготовить данные, выполнить действие, проверить результат.

Тесты писать проще, если функции чистые (раздел 2В.4): дал вход — проверил выход.

### Проверки внутри анализа

В ноутбуках полноценные тесты редки, но `assert` после ключевых шагов — обязательная привычка:

```python
orders_with_users = orders.merge(users, on="user_id", how="left")
assert len(orders_with_users) == len(orders), "merge размножил строки"
assert orders_with_users["amount"].ge(0).all(), "есть отрицательные суммы"
```

## 2В.10. Паттерны проектирования

**Паттерн** — проверенное решение часто встречающейся задачи. Это не готовый код, а идея, у которой есть имя. Имена нужны, чтобы понимать друг друга: фраза «сделай тут стратегию» заменяет пять минут объяснений.

Ниже — паттерны, которые реально встречаются в аналитическом коде. В Python многие из них получаются короче, чем в учебниках, потому что функции можно передавать как значения.

### Стратегия (Strategy)

**Задача:** есть несколько взаимозаменяемых способов сделать одно и то же, и нужный выбирается во время работы.

```python
def fill_with_zero(values):
    return [0 if v is None else v for v in values]

def fill_with_mean(values):
    known = [v for v in values if v is not None]
    mean = sum(known) / len(known)
    return [mean if v is None else v for v in values]

def fill_with_previous(values):
    result, last = [], None
    for v in values:
        last = v if v is not None else last
        result.append(last)
    return result


def prepare(values, fill_strategy):
    """Алгоритм подготовки один, а способ заполнения пропусков — сменный."""
    filled = fill_strategy(values)
    return [round(v, 1) for v in filled]


data = [10, None, 30, None]
print(prepare(data, fill_with_zero))        # [10, 0, 30, 0]
print(prepare(data, fill_with_mean))        # [10, 20.0, 30, 20.0]
print(prepare(data, fill_with_previous))    # [10, 10, 30, 30]
```

Ты уже пользуешься стратегиями: параметр `key` в `sorted` и название функции в `df.agg("mean")` — это они и есть.

### Реестр и фабрика (Registry, Factory)

**Задача:** выбрать нужную функцию или класс по названию — например, из настроек или аргумента командной строки — без длинной цепочки `if / elif`.

```python
FILL_STRATEGIES = {
    "zero": fill_with_zero,
    "mean": fill_with_mean,
    "previous": fill_with_previous,
}

def get_fill_strategy(name):
    try:
        return FILL_STRATEGIES[name]
    except KeyError:
        raise ValueError(f"неизвестная стратегия {name!r}, доступны: {sorted(FILL_STRATEGIES)}") from None


config = {"fill": "mean"}                          # например, прочитано из config.json
print(prepare(data, get_fill_strategy(config["fill"])))
```

Добавить новый вариант — значит добавить одну строку в словарь.

Реестр можно наполнять декоратором — тогда новая функция «регистрирует себя сама»:

```python
METRICS = {}

def metric(name):
    def register(func):
        METRICS[name] = func
        return func
    return register


@metric("выручка")
def revenue(amounts):
    return sum(amounts)

@metric("средний чек")
def average_check(amounts):
    return sum(amounts) / len(amounts)

@metric("медиана")
def median_check(amounts):
    ordered = sorted(amounts)
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2


amounts = [1200, 15400, 8900, 700]
for name, func in METRICS.items():
    print(f"{name}: {func(amounts):,.0f}")
```

**Фабрика** — та же идея для создания объектов: функция, которая по параметрам решает, объект какого класса вернуть.

```python
import json


class CsvReader:
    def read(self, text):
        header, *lines = text.strip().splitlines()
        return [dict(zip(header.split(","), line.split(","))) for line in lines]

class JsonReader:
    def read(self, text):
        return json.loads(text)

READERS = {".csv": CsvReader, ".json": JsonReader}

def make_reader(filename):
    suffix = Path(filename).suffix
    if suffix not in READERS:
        raise ValueError(f"формат {suffix!r} не поддерживается")
    return READERS[suffix]()


print(make_reader("orders.csv").read("id,amount\n1,100"))
print(make_reader("orders.json").read('[{"id": 1, "amount": 100}]'))
```

Точно так же устроено семейство `pd.read_csv`, `pd.read_json`, `pd.read_excel`.

### Конвейер (Pipeline)

**Задача:** данные проходят последовательность шагов, и каждый шаг — отдельная функция. Главный паттерн обработки данных.

```python
def strip_names(rows):
    return [{**row, "city": row["city"].strip().capitalize()} for row in rows]

def drop_missing_amount(rows):
    return [row for row in rows if row["amount"] is not None]

def drop_negative(rows):
    return [row for row in rows if row["amount"] >= 0]

def add_size(rows):
    return [{**row, "size": "крупный" if row["amount"] >= 5000 else "обычный"} for row in rows]


def run_pipeline(data, steps, verbose=False):
    for step in steps:
        before = len(data)
        data = step(data)
        if verbose:
            print(f"{step.__name__:<22} {before} → {len(data)} строк")
    return data


raw = [
    {"city": " москва", "amount": 1200},
    {"city": "казань ", "amount": None},
    {"city": "Уфа", "amount": -500},
    {"city": "Самара", "amount": 9000},
]

clean = run_pipeline(raw, [strip_names, drop_missing_amount, drop_negative, add_size], verbose=True)
print(clean)
```

Достоинства:

- порядок шагов виден в одном месте и читается как список;
- каждый шаг проверяется отдельно;
- шаг легко добавить, убрать или переставить;
- журнал «было → стало» получается бесплатно — а это ровно тот отчёт об очистке, который нужен в главе 6.

В pandas этот паттерн реализован методом `.pipe()` (раздел 2В.11), в scikit-learn — классом `Pipeline`.

### Декоратор (Decorator)

**Задача:** добавить функции поведение, не меняя её кода. В Python это встроено в язык — глава 2А. Типичные применения: замер времени, журнал вызовов, повтор при сбое, кэш, проверка аргументов.

```python
import functools

def validate_not_empty(func):
    @functools.wraps(func)
    def wrapper(values, *args, **kwargs):
        if not values:
            raise ValueError(f"{func.__name__}: получен пустой список")
        return func(values, *args, **kwargs)
    return wrapper


@validate_not_empty
def safe_mean(values):
    return sum(values) / len(values)

print(safe_mean([1, 2, 3]))
try:
    safe_mean([])
except ValueError as error:
    print(error)
```

### Адаптер (Adapter)

**Задача:** есть данные или объект с «неудобным» интерфейсом, а остальной код ждёт другого. Адаптер — тонкая прослойка, которая переводит одно в другое.

У аналитика это происходит постоянно: в каждом источнике столбцы называются по-своему.

```python
def from_shop_export(row):
    """Выгрузка из магазина: русские названия, сумма строкой с запятой."""
    return {"order_id": int(row["Номер"]), "amount": float(row["Сумма"].replace(",", ".")), "source": "shop"}

def from_app_api(row):
    """Ответ API приложения: другие имена, сумма в копейках."""
    return {"order_id": row["id"], "amount": row["total_kopecks"] / 100, "source": "app"}


shop_rows = [{"Номер": "101", "Сумма": "1200,50"}]
app_rows = [{"id": 202, "total_kopecks": 990000}]

orders = [from_shop_export(r) for r in shop_rows] + [from_app_api(r) for r in app_rows]
print(orders)
```

Правило: **приводи данные к единому виду на входе**, сразу после загрузки. Весь остальной код работает только с единым форматом и не знает, откуда что пришло.

### Шаблонный метод (Template Method)

**Задача:** общий порядок действий одинаков, а отдельные шаги отличаются. Родительский класс задаёт «скелет», наследники заполняют шаги.

```python
from abc import ABC, abstractmethod


class BaseReport(ABC):
    def run(self):                       # скелет: порядок шагов фиксирован
        data = self.load()
        data = self.clean(data)
        result = self.calculate(data)
        return self.render(result)

    @abstractmethod
    def load(self): ...

    def clean(self, data):               # шаг по умолчанию — можно переопределить
        return [x for x in data if x is not None]

    @abstractmethod
    def calculate(self, data): ...

    def render(self, result):
        return f"{type(self).__name__}: {result}"


class RevenueReport(BaseReport):
    def load(self):
        return [1200, None, 8900, 700]

    def calculate(self, data):
        return sum(data)


class AverageCheckReport(RevenueReport):
    def calculate(self, data):
        return round(sum(data) / len(data), 1)


for report in (RevenueReport(), AverageCheckReport()):
    print(report.run())
```

### Репозиторий (Repository)

**Задача:** отделить «откуда берутся данные» от «что с ними делают». Весь код доступа к данным живёт в одном классе, а остальная программа вызывает понятные методы и не знает ни про SQL, ни про файлы.

```python
import sqlite3


class OrderRepository:
    def __init__(self, connection):
        self._conn = connection

    def add(self, city, amount):
        self._conn.execute("INSERT INTO orders (city, amount) VALUES (?, ?)", (city, amount))

    def revenue_by_city(self):
        query = "SELECT city, SUM(amount) FROM orders GROUP BY city ORDER BY 2 DESC"
        return dict(self._conn.execute(query).fetchall())

    def big_orders(self, threshold):
        query = "SELECT city, amount FROM orders WHERE amount >= ?"
        return self._conn.execute(query, (threshold,)).fetchall()


connection = sqlite3.connect(":memory:")
connection.execute("CREATE TABLE orders (city TEXT, amount REAL)")

repo = OrderRepository(connection)
for city, amount in [("Москва", 1200), ("Казань", 15400), ("Москва", 8900)]:
    repo.add(city, amount)

print(repo.revenue_by_city())
print(repo.big_orders(5000))
```

Обрати внимание на знаки `?` в запросах. Значения передаются отдельно от текста запроса — **никогда не вставляй их в SQL через f-строку**: это открывает дорогу SQL-инъекциям и ломается на первой же кавычке в данных.

Выгода репозитория: запросы собраны в одном месте, а для тестов можно подставить объект с такими же методами, который возвращает заранее заготовленные данные.

### Одиночка (Singleton)

**Задача:** объект должен существовать в единственном экземпляре — настройки, соединение с базой.

В Python для этого не нужен особый класс: **модуль уже одиночка**. Он загружается один раз, и все, кто его импортирует, получают один и тот же объект. Создай файл `settings.py` с константами — и импортируй его откуда угодно. Именно так мы поступили с `SETTINGS` в разделе 2В.5.

### Как относиться к паттернам

- Паттерн — это средство от конкретной проблемы. Нет проблемы — не нужен паттерн.
- Не начинай с паттерна. Напиши просто; когда код начнёт сопротивляться изменениям, посмотри, какой паттерн это лечит.
- Самые полезные для аналитика: **конвейер**, **стратегия**, **реестр**, **адаптер**. Остальные достаточно узнавать в чужом коде.

## 2В.11. Паттерны кода в pandas

Забегаем вперёд, к главе 5 — вернись сюда после неё. Примеры ниже требуют pandas, поэтому приведены без запуска.

### Цепочка методов вместо промежуточных переменных

```python
# Плохо: пять таблиц с невнятными именами, легко перепутать
df2 = df[df["status"] == "paid"]
df3 = df2.copy()
df3["month"] = df3["date"].dt.to_period("M")
df4 = df3.groupby("month")["amount"].sum()
df5 = df4.reset_index()

# Хорошо: одна цепочка, читается сверху вниз
monthly_revenue = (
    df
    .query("status == 'paid'")
    .assign(month=lambda d: d["date"].dt.to_period("M"))
    .groupby("month", as_index=False)["amount"]
    .sum()
)
```

- `.query()` — фильтр внутри цепочки;
- `.assign()` — новый столбец внутри цепочки; `lambda d:` получает таблицу в текущем состоянии;
- скобки вокруг выражения позволяют писать каждый метод с новой строки.

### Функции-шаги и .pipe()

Тот самый конвейер, только для таблиц. Каждая функция принимает DataFrame и возвращает DataFrame:

```python
def normalize_city(df):
    return df.assign(city=df["city"].str.strip().str.capitalize())

def drop_test_orders(df, max_amount):
    return df[df["amount"] < max_amount]

def add_month(df):
    return df.assign(month=df["date"].dt.to_period("M"))


clean = (
    raw
    .pipe(normalize_city)
    .pipe(drop_test_orders, max_amount=500_000)
    .pipe(add_month)
)
```

### Не меняй входную таблицу

```python
# Плохо: функция портит таблицу, которую ей передали
def add_revenue(df):
    df["revenue"] = df["price"] * df["quantity"]
    return df

# Хорошо: возвращает новую таблицу
def add_revenue(df):
    return df.assign(revenue=df["price"] * df["quantity"])
```

Это та же ловушка с изменяемыми объектами из главы 2А: DataFrame передаётся в функцию не копией, а ярлыком на тот же объект.

### Ноутбук должен выполняться сверху вниз

- сначала импорты и настройки, потом загрузка, очистка, анализ, выводы;
- никаких ячеек, которые работают, только если до них запустить что-то ниже;
- одна ячейка — один логический шаг;
- сырую таблицу не перезаписывай: `raw` → `clean` → `orders_by_month`, чтобы любую ячейку можно было перезапустить.

## 2В.12. От ноутбука к проекту

Путь, по которому растёт код аналитика:

1. **Ноутбук-черновик.** Исследуешь, пробуешь, всё в ячейках. Это нормально.
2. **Функции в ноутбуке.** Повторяющиеся куски вынесены в функции в начале ноутбука.
3. **Модули.** Функции переехали в `src/`, ноутбук их импортирует и занимается только анализом и графиками.
4. **Тесты.** На функции из `src/` написаны тесты.
5. **Скрипт.** То, что нужно выполнять регулярно, запускается одной командой без ноутбука.

Не каждому анализу нужно проходить весь путь. Разовое исследование может остаться на шаге 1–2. Но всё, что считается повторно — еженедельный отчёт, общие метрики, — должно дойти хотя бы до шага 3.

Чтобы изменения в модулях подхватывались ноутбуком без перезапуска ядра, выполни в первой ячейке:

```
%load_ext autoreload
%autoreload 2
```

## 2В.13. Чек-лист перед тем, как показать код

- [ ] Запускается с нуля: Restart Kernel and Run All без ошибок.
- [ ] Имена объясняют смысл; нет `df2`, `tmp`, `x1`.
- [ ] Нет скопированных кусков — они вынесены в функции.
- [ ] Числа-параметры вынесены в константы в начале.
- [ ] Каждое исключение данных объяснено комментарием.
- [ ] После соединений и очистки стоят проверки `assert`.
- [ ] Нет закомментированного и неиспользуемого кода.
- [ ] Код отформатирован (`ruff format`).
- [ ] Нет паролей, ключей и абсолютных путей вида `C:\Users\...`.
- [ ] Есть выводы словами, а не только код и графики.

## Задания

1. **Имена.** Перепиши, дав понятные имена и убрав магические числа:
   `def f(l): return [x for x in l if x[1] > 18 and x[2] == 1]` — известно, что `x` это кортеж «имя, возраст, признак активности».
2. **Ранний возврат.** Перепиши функцию без вложенных `if`: она принимает словарь пользователя и возвращает `"vip"`, если пользователь активен, не заблокирован и потратил больше 100 000; `"regular"`, если активен и не заблокирован; иначе `"inactive"`.
3. **Чистая функция.** Функция `normalize(rows)` в цикле меняет словари на месте: приводит `city` к нижнему регистру. Перепиши её так, чтобы вход не менялся, и докажи это проверкой.
4. **Рефакторинг.** Приведи в порядок код ниже. В нём `t` — тип операции, `a` — сумма, `0.8` — доля, остающаяся после комиссии 20 %.

```python
def calc(d):
    r = []
    for i in range(len(d)):
        if d[i]["t"] == "buy":
            r.append(d[i]["a"] * 0.8)
        elif d[i]["t"] == "refund":
            r.append(d[i]["a"] * -1)
    s = 0
    for i in range(len(r)):
        s = s + r[i]
    return s
```

5. **Тесты.** Напиши не менее пяти проверок `assert` для функции `median(values)`: обычные случаи, один элемент, чётное количество, неотсортированный вход, пустой список (должна быть ошибка).
6. **Стратегия и реестр.** Напиши функцию `aggregate(values, how)`, где `how` — одно из `"sum"`, `"mean"`, `"max"`, `"range"`. Реализуй через словарь функций. Неизвестное название должно давать понятную ошибку.
7. **Конвейер.** Дан список строк с «грязными» суммами: `["1 200", "3,5", "", "abc", "-40", "990"]`. Построй конвейер из отдельных шагов: убрать пустые → убрать пробелы и заменить запятую на точку → превратить в числа, отбросив нечисловые → убрать отрицательные. Выведи, сколько значений осталось после каждого шага.
8. **Адаптер.** Есть два источника: `[{"user": "u1", "sum": "100"}]` и `[("u2", 250.0, "2026-03-01")]`. Напиши два адаптера, приводящих оба к виду `{"user_id": ..., "amount": float}`, и посчитай общую сумму.

## Проверь себя

- Почему читаемость кода важна именно для аналитика?
- Какие стили имён приняты для переменных, классов и констант?
- Что такое чистая функция и чем она удобна?
- Что такое магическое число и чем оно опасно?
- О чём должен рассказывать комментарий?
- Что означают принципы DRY и YAGNI?
- Какие случаи стоит покрывать тестами?
- Какую задачу решают паттерны «стратегия», «конвейер» и «адаптер»?
- Почему значения нельзя вставлять в SQL-запрос через f-строку?

## Решения

### Задание 1. Имена

```python
ADULT_AGE = 18

def active_adults(users):
    """Возвращает активных пользователей старше 18 лет."""
    return [
        (name, age, is_active)
        for name, age, is_active in users
        if age > ADULT_AGE and is_active
    ]

users = [("Анна", 25, 1), ("Борис", 17, 1), ("Вера", 40, 0)]
print(active_adults(users))      # [('Анна', 25, 1)]
```

Распаковка кортежа в цикле заменила `x[1]` и `x[2]` на имена. Сравнение `== 1` убрано: признак активности и так читается как условие.

### Задание 2. Ранний возврат

```python
VIP_SPENDING_THRESHOLD = 100_000

def user_segment(user):
    if not user["is_active"] or user["is_blocked"]:
        return "inactive"
    if user["total_spent"] > VIP_SPENDING_THRESHOLD:
        return "vip"
    return "regular"

print(user_segment({"is_active": True, "is_blocked": False, "total_spent": 150_000}))   # vip
print(user_segment({"is_active": True, "is_blocked": False, "total_spent": 500}))       # regular
print(user_segment({"is_active": True, "is_blocked": True, "total_spent": 150_000}))    # inactive
```

Сначала отсекается общий для двух веток отрицательный случай, после него условия «активен и не заблокирован» повторять уже не нужно.

### Задание 3. Чистая функция

```python
def normalize(rows):
    return [{**row, "city": row["city"].lower()} for row in rows]

source = [{"city": "МОСКВА", "amount": 1}, {"city": "Казань", "amount": 2}]
result = normalize(source)

assert source[0]["city"] == "МОСКВА"          # вход не изменился
assert result[0]["city"] == "москва"
assert result[0] is not source[0]             # это разные объекты
print(result)
```

`{**row, "city": ...}` создаёт новый словарь: копирует все ключи и заменяет один.

### Задание 4. Рефакторинг

```python
COMMISSION_RATE = 0.2


def operation_income(operation):
    """Доход от одной операции: покупка за вычетом комиссии, возврат — со знаком минус."""
    kind, amount = operation["t"], operation["a"]
    if kind == "buy":
        return amount * (1 - COMMISSION_RATE)
    if kind == "refund":
        return -amount
    return 0


def net_income(operations):
    return sum(operation_income(operation) for operation in operations)


operations = [{"t": "buy", "a": 1000}, {"t": "refund", "a": 200}, {"t": "view", "a": 0}]
print(net_income(operations))        # 600.0
```

Что сделано: имена по смыслу, комиссия вынесена в константу и записана как комиссия (20 %), а не как непонятное `0.8`; перебор по индексам заменён прямым перебором; два цикла — на `sum` с генератором; правило для одной операции вынесено в отдельную функцию, которую легко проверить.

Если бы ключи `t` и `a` были под нашим контролем, их тоже стоило бы переименовать в `type` и `amount` — на входе, адаптером.

### Задание 5. Тесты

```python
def median(values):
    if not values:
        raise ValueError("медиана пустого списка не определена")
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


assert median([1, 2, 3]) == 2                 # нечётное количество
assert median([1, 2, 3, 4]) == 2.5            # чётное количество
assert median([7]) == 7                       # один элемент
assert median([3, 1, 2]) == 2                 # неотсортированный вход
assert median([5, 5, 5, 5]) == 5              # одинаковые значения
assert median([1, 2, 3, 1000]) == 2.5         # выброс не влияет

data = [3, 1, 2]
median(data)
assert data == [3, 1, 2]                      # функция не меняет вход

try:
    median([])
except ValueError:
    pass
else:
    raise AssertionError("ожидалась ошибка на пустом списке")

print("Все тесты пройдены")
```

Проверка «функция не меняет вход» поймала бы реализацию через `values.sort()` — частую ошибку.

### Задание 6. Стратегия и реестр

```python
AGGREGATIONS = {
    "sum": sum,
    "mean": lambda values: sum(values) / len(values),
    "max": max,
    "range": lambda values: max(values) - min(values),
}

def aggregate(values, how):
    if how not in AGGREGATIONS:
        raise ValueError(f"неизвестная агрегация {how!r}; доступны: {', '.join(sorted(AGGREGATIONS))}")
    return AGGREGATIONS[how](values)

data = [12, 15, 11, 19]
for how in AGGREGATIONS:
    print(how, aggregate(data, how))

try:
    aggregate(data, "avg")
except ValueError as error:
    print(error)
```

Сообщение об ошибке перечисляет допустимые варианты — пользователю функции не придётся лезть в исходный код.

### Задание 7. Конвейер

```python
def drop_empty(values):
    return [v for v in values if v.strip()]

def normalize_format(values):
    return [v.replace(" ", "").replace(",", ".") for v in values]

def to_numbers(values):
    numbers = []
    for value in values:
        try:
            numbers.append(float(value))
        except ValueError:
            continue                      # нечисловое значение отбрасываем
    return numbers

def drop_negative_numbers(values):
    return [v for v in values if v >= 0]


def run_steps(data, steps):
    for step in steps:
        data = step(data)
        print(f"{step.__name__:<24} осталось: {len(data)}")
    return data


raw = ["1 200", "3,5", "", "abc", "-40", "990"]
print(run_steps(raw, [drop_empty, normalize_format, to_numbers, drop_negative_numbers]))
# [1200.0, 3.5, 990.0]
```

Здесь `except ValueError: continue` — допустимое «проглатывание» ошибки: мы делаем это осознанно, а потеря значений видна в журнале шагов.

### Задание 8. Адаптер

```python
def from_dict_source(row):
    return {"user_id": row["user"], "amount": float(row["sum"])}

def from_tuple_source(row):
    user_id, amount, _date = row
    return {"user_id": user_id, "amount": float(amount)}


source_a = [{"user": "u1", "sum": "100"}]
source_b = [("u2", 250.0, "2026-03-01")]

payments = [from_dict_source(r) for r in source_a] + [from_tuple_source(r) for r in source_b]
print(payments)
print(sum(p["amount"] for p in payments))      # 350.0
```

После адаптеров код подсчёта не знает и не должен знать, что источников было два.
