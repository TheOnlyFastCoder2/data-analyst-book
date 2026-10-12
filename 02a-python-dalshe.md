# Глава 2А. Python: следующий уровень

В главе 2 ты научился писать простые программы. Этого хватает, чтобы пользоваться pandas, но не хватает, чтобы **читать чужой код** и писать свой так, чтобы он не разваливался. В этой главе — то, что отличает человека, «знающего синтаксис», от человека, который понимает язык.

Каждый пример запускай. Меняй в нём что-нибудь и смотри, что получится: так запоминается в разы лучше.

## 2А.1. Имена и объекты: как Python хранит данные

Главная идея, которую стоит понять раз и навсегда: **переменная в Python — это не коробка со значением, а ярлык, привязанный к объекту**.

```python
a = [1, 2, 3]
b = a            # второй ярлык на ТОТ ЖЕ список, а не копия

b.append(4)
print(a)         # [1, 2, 3, 4] — «изменился» и a, потому что список один
print(a is b)    # True — это один и тот же объект
```

Чтобы получить независимую копию, её нужно создать явно:

```python
a = [1, 2, 3]
c = a.copy()     # или list(a), или a[:]
c.append(4)
print(a)         # [1, 2, 3] — оригинал не тронут
print(a is c)    # False
print(a == c[:3])  # True: == сравнивает содержимое, is — сам объект
```

### Изменяемые и неизменяемые типы

| Неизменяемые (immutable) | Изменяемые (mutable) |
|--------------------------|----------------------|
| `int`, `float`, `bool`, `str`, `tuple`, `frozenset`, `None` | `list`, `dict`, `set`, почти все пользовательские объекты, `DataFrame` |

Неизменяемый объект нельзя поменять — можно только создать новый:

```python
s = "москва"
s.upper()          # создаёт НОВУЮ строку, но мы её никуда не сохранили
print(s)           # москва

s = s.upper()      # перепривязали ярлык к новой строке
print(s)           # МОСКВА
```

Это объясняет, почему в pandas нужно писать `df = df.sort_values(...)`: метод возвращает новый объект.

### Ловушка 1: функция меняет переданный список

```python
def add_total(row):
    row.append(sum(row))      # меняет тот самый список, который передали
    return row

data = [10, 20]
result = add_total(data)
print(data)                   # [10, 20, 30] — исходные данные испорчены
```

Правильно — не трогать вход, а вернуть новое значение:

```python
def with_total(row):
    return row + [sum(row)]   # новый список

data = [10, 20]
print(with_total(data), data)   # [10, 20, 30] [10, 20]
```

### Ловушка 2: изменяемое значение по умолчанию

Классическая ошибка, которую спрашивают на собеседованиях:

```python
def add_item(item, basket=[]):       # список создаётся ОДИН раз — при определении функции
    basket.append(item)
    return basket

print(add_item("хлеб"))     # ['хлеб']
print(add_item("молоко"))   # ['хлеб', 'молоко'] — корзина общая на все вызовы!
```

Решение — `None` как значение по умолчанию:

```python
def add_item(item, basket=None):
    if basket is None:
        basket = []
    basket.append(item)
    return basket

print(add_item("хлеб"))     # ['хлеб']
print(add_item("молоко"))   # ['молоко']
```

### Ловушка 3: поверхностная копия

`copy()` копирует только верхний уровень. Вложенные списки остаются общими:

```python
import copy

matrix = [[1, 2], [3, 4]]
shallow = matrix.copy()
deep = copy.deepcopy(matrix)

matrix[0].append(99)
print(shallow[0])   # [1, 2, 99] — вложенный список общий
print(deep[0])      # [1, 2]     — полная независимая копия
```

## 2А.2. Распаковка

Распаковка — присваивание сразу нескольким именам. Делает код короче и понятнее.

```python
point = (55.75, 37.62)
lat, lon = point                      # обычная распаковка

a, b = 1, 2
a, b = b, a                           # обмен значений без временной переменной
print(a, b)                           # 2 1

first, *rest = [10, 20, 30, 40]       # звёздочка забирает «всё остальное»
print(first, rest)                    # 10 [20, 30, 40]

head, *middle, tail = [1, 2, 3, 4, 5]
print(head, middle, tail)             # 1 [2, 3, 4] 5

date_str = "2026-03-15"
year, month, day = date_str.split("-")
print(year, month, day)
```

Распаковка в цикле — самый частый случай:

```python
orders = [("Москва", 1200), ("Казань", 15400), ("Уфа", 700)]

for city, amount in orders:
    print(f"{city}: {amount}")

for number, (city, amount) in enumerate(orders, start=1):
    print(number, city, amount)
```

### zip: идём по нескольким спискам сразу

```python
cities = ["Москва", "Казань", "Уфа"]
revenue = [12200, 15400, 700]

for city, value in zip(cities, revenue):
    print(city, value)

by_city = dict(zip(cities, revenue))          # два списка → словарь
print(by_city)

pairs = [("a", 1), ("b", 2)]
letters, numbers = zip(*pairs)                # обратная операция: «расстегнуть»
print(letters, numbers)                       # ('a', 'b') (1, 2)
```

### Звёздочки при вызове функции

`*` распаковывает список в позиционные аргументы, `**` — словарь в именованные:

```python
def describe(city, amount, currency="руб."):
    return f"{city}: {amount} {currency}"

args = ["Москва", 1200]
kwargs = {"city": "Казань", "amount": 500, "currency": "USD"}

print(describe(*args))       # Москва: 1200 руб.
print(describe(**kwargs))    # Казань: 500 USD

defaults = {"sep": ";", "encoding": "utf-8"}
custom = {**defaults, "sep": ","}            # объединение словарей, правый побеждает
print(custom)
```

Последний приём постоянно встречается в коде: «настройки по умолчанию плюс то, что передал пользователь».

## 2А.3. Функции глубже

### `*args` и `**kwargs`

Так функция принимает произвольное число аргументов:

```python
def total(*args):                 # args — кортеж позиционных аргументов
    return sum(args)

print(total(1, 2, 3))             # 6

def make_report(title, **kwargs): # kwargs — словарь именованных аргументов
    lines = [title]
    for key, value in kwargs.items():
        lines.append(f"  {key}: {value}")
    return "\n".join(lines)

print(make_report("Итоги", выручка=1200, заказы=17))
```

Теперь понятна запись, которую ты увидишь в документации pandas: `df.plot(*args, **kwargs)` — «принимает что угодно и передаёт дальше».

### Только именованные аргументы

Всё, что стоит после `*`, можно передать только по имени. Это защищает от путаницы в порядке:

```python
def conversion(orders, visits, *, as_percent=False, digits=2):
    value = orders / visits
    return round(value * 100, digits) if as_percent else round(value, digits + 2)

print(conversion(30, 1200, as_percent=True))   # 2.5
# conversion(30, 1200, True)  → TypeError: так нельзя, и это хорошо
```

Сравни: `conversion(30, 1200, True, 1)` — что такое `True` и `1`? С именами вопросов нет.

### Функции — это объекты

Функцию можно положить в переменную, в список, в словарь и передать в другую функцию. На этом построены `sorted(key=...)`, `df.apply(...)` и половина паттернов из главы 2В.

```python
def mean(values):
    return sum(values) / len(values)

def spread(values):
    return max(values) - min(values)

metrics = {"среднее": mean, "размах": spread, "максимум": max}

data = [12, 15, 11, 19]
for name, func in metrics.items():
    print(name, func(data))
```

### Замыкания: функция, которая помнит

Функция, созданная внутри другой функции, запоминает переменные внешней:

```python
def make_threshold_checker(threshold):
    def is_big(amount):
        return amount >= threshold      # threshold «запомнен»
    return is_big

is_big_order = make_threshold_checker(10000)
is_vip_order = make_threshold_checker(100000)

print(is_big_order(15000), is_vip_order(15000))   # True False
```

Это основа декораторов (раздел 2А.6).

### Области видимости

Python ищет имя в порядке **LEGB**: Local (внутри функции) → Enclosing (во внешней функции) → Global (в модуле) → Built-in (встроенные).

```python
rate = 0.2                    # глобальная

def with_tax(price):
    tax = price * rate        # rate читается из глобальной области
    return price + tax        # tax — локальная, снаружи её нет

print(with_tax(100))          # 120.0
```

Читать глобальные переменные можно, **менять их из функции — плохая практика**: результат функции начинает зависеть от того, что происходило до вызова. Всё, что функции нужно, передавай аргументами.

## 2А.4. Включения (comprehensions)

Короткая запись «построить коллекцию из другой коллекции». Бывают для списков, словарей и множеств.

```python
orders = [
    {"id": 1, "city": "Москва", "amount": 1200},
    {"id": 2, "city": "Казань", "amount": 15400},
    {"id": 3, "city": "Москва", "amount": 8900},
]

amounts = [o["amount"] for o in orders]                          # список
big_ids = [o["id"] for o in orders if o["amount"] > 5000]        # с фильтром
labels = ["крупный" if o["amount"] > 5000 else "обычный" for o in orders]   # с условием

amount_by_id = {o["id"]: o["amount"] for o in orders}            # словарь
cities = {o["city"] for o in orders}                             # множество

print(amounts, big_ids, labels, amount_by_id, cities, sep="\n")
```

Обрати внимание на разницу: `if` **в конце** отбирает элементы, `if ... else` **в начале** выбирает значение.

Вложенное включение читается слева направо, как вложенные циклы:

```python
matrix = [[1, 2, 3], [4, 5, 6]]
flat = [x for row in matrix for x in row]
print(flat)        # [1, 2, 3, 4, 5, 6]
```

Правило меры: если включение не помещается в одну-две строки или в нём больше одного условия — пиши обычный цикл. Краткость не должна вредить понятности.

### Генераторное выражение

То же самое, но в круглых скобках. Оно не строит список в памяти, а выдаёт значения по одному:

```python
total = sum(o["amount"] for o in orders)                 # список не создаётся
has_big = any(o["amount"] > 10000 for o in orders)       # остановится на первом True
all_positive = all(o["amount"] > 0 for o in orders)
print(total, has_big, all_positive)
```

`any` и `all` заменяют целые циклы с флажками — запомни их.

## 2А.5. Итераторы и генераторы

**Итерируемый объект** — всё, по чему можно пройти циклом `for`: список, строка, словарь, файл, DataFrame.

**Генератор** — функция, которая выдаёт значения по одному через `yield` и между вызовами «засыпает», сохраняя состояние. Он не хранит все значения в памяти.

```python
def countdown(n):
    while n > 0:
        yield n          # отдать значение и приостановиться
        n -= 1

for number in countdown(3):
    print(number)        # 3, 2, 1

gen = countdown(2)
print(next(gen))         # 2
print(next(gen))         # 1
```

Зачем это аналитику: обработка файла, который не помещается в память.

```python
with open("big.csv", "w", encoding="utf-8") as f:       # создадим файл для примера
    f.write("city,amount\n")
    for i in range(1000):
        f.write(f"{'Москва' if i % 2 else 'Казань'},{i}\n")


def read_rows(path):
    """Читает CSV построчно, не загружая файл целиком."""
    with open(path, encoding="utf-8") as f:
        header = f.readline().strip().split(",")
        for line in f:
            yield dict(zip(header, line.strip().split(",")))


total = sum(int(row["amount"]) for row in read_rows("big.csv") if row["city"] == "Москва")
print(total)             # 250000
```

Файл читается по одной строке: в памяти в каждый момент ровно одна запись. Так же устроен параметр `chunksize` в `pd.read_csv`.

Генераторы можно соединять в цепочку — получается конвейер обработки:

```python
def only_city(rows, city):
    for row in rows:
        if row["city"] == city:
            yield row

def amounts(rows):
    for row in rows:
        yield int(row["amount"])

pipeline = amounts(only_city(read_rows("big.csv"), "Казань"))
print(max(pipeline))     # 998
```

Важное свойство: **генератор одноразовый**. Пройдя его до конца, второй раз значения не получишь — нужно создать заново.

## 2А.6. Декораторы

Декоратор — функция, которая принимает функцию и возвращает её улучшенную версию. Он добавляет поведение, не трогая код самой функции: замер времени, логирование, повтор при ошибке, кэширование.

Соберём декоратор по шагам.

```python
import time
import functools

def timer(func):
    @functools.wraps(func)                    # сохраняет имя и описание исходной функции
    def wrapper(*args, **kwargs):             # принимает любые аргументы
        start = time.perf_counter()
        result = func(*args, **kwargs)        # вызывает оригинал
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} выполнилась за {elapsed:.4f} с")
        return result                         # возвращает его результат
    return wrapper


@timer                                        # то же самое, что slow_sum = timer(slow_sum)
def slow_sum(n):
    return sum(i * i for i in range(n))

print(slow_sum(100_000))
```

Строка `@timer` над функцией — просто удобная запись для `slow_sum = timer(slow_sum)`.

Декоратор с параметрами — ещё один уровень вложенности:

```python
def retry(times=3, delay=0.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except ConnectionError as error:
                    print(f"Попытка {attempt} не удалась: {error}")
                    if attempt == times:
                        raise                 # попытки кончились — пробрасываем ошибку
                    time.sleep(delay)
        return wrapper
    return decorator


calls = {"count": 0}

@retry(times=3)
def unstable_api():
    calls["count"] += 1
    if calls["count"] < 3:
        raise ConnectionError("сервер не отвечает")
    return {"status": "ok"}

print(unstable_api())
```

Именно так оборачивают запросы к API и базам данных, которые иногда падают.

Готовый декоратор из стандартной библиотеки, который полезно знать, — кэш результатов:

```python
@functools.lru_cache(maxsize=None)
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)

print(fib(80))       # мгновенно; без кэша считалось бы годами
```

## 2А.7. Менеджеры контекста

Конструкция `with` гарантирует, что ресурс будет освобождён — даже если внутри случилась ошибка. Ты уже видел её с файлами; так же работают соединения с базой.

```python
import sqlite3

with sqlite3.connect(":memory:") as conn:
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.execute("INSERT INTO t VALUES (1), (2), (3)")
    print(conn.execute("SELECT SUM(x) FROM t").fetchone()[0])    # 6
```

Свой менеджер контекста проще всего сделать из генератора: всё до `yield` выполняется на входе, всё после — на выходе.

```python
from contextlib import contextmanager

@contextmanager
def stopwatch(label):
    start = time.perf_counter()
    try:
        yield                                  # здесь выполняется тело блока with
    finally:
        print(f"{label}: {time.perf_counter() - start:.4f} с")


with stopwatch("Подсчёт"):
    total = sum(range(1_000_000))
```

Удобно замерять в ноутбуке, сколько занял каждый шаг анализа.

## 2А.8. Исключения всерьёз

### Полная форма

```python
def parse_amount(text):
    try:
        value = float(text.replace(",", ".").replace(" ", ""))
    except ValueError:
        print(f"Не число: {text!r}")       # выполняется при ошибке
        return None
    else:
        return value                       # выполняется, если ошибки НЕ было
    finally:
        pass                               # выполняется всегда: здесь закрывают ресурсы

print(parse_amount("1 200,50"))    # 1200.5
print(parse_amount("н/д"))         # None
```

### Правила работы с исключениями

1. **Лови конкретные исключения.** `except ValueError`, а не голый `except:` — тот поймает всё подряд, включая опечатки в твоём же коде, и ты никогда не узнаешь об ошибке.
2. **Не глуши ошибки молча.** `except: pass` — худшее, что можно написать: программа «работает», а результат неверный.
3. **Лови там, где знаешь, что делать.** Не знаешь, как обработать, — не лови, пусть ошибка всплывёт выше.
4. **Ошибка лучше неверного числа.** В аналитике упавший скрипт — мелкая неприятность, а тихо посчитанная неправильная выручка — катастрофа.

### Вызываем исключения сами

Проверяй входные данные в начале функции и сообщай о проблеме понятным текстом:

```python
def conversion(orders, visits):
    if visits <= 0:
        raise ValueError(f"visits должно быть больше нуля, получено {visits}")
    if orders > visits:
        raise ValueError(f"заказов ({orders}) больше, чем визитов ({visits})")
    return orders / visits

try:
    conversion(50, 10)
except ValueError as error:
    print("Ошибка:", error)
```

### Свои классы исключений

Позволяют отличать «наши» ошибки от всех прочих:

```python
class DataQualityError(Exception):
    """Данные не прошли проверку качества."""


def check_orders(orders):
    for order in orders:
        if order["amount"] < 0:
            raise DataQualityError(f"Отрицательная сумма в заказе {order['id']}")
    return True

try:
    check_orders([{"id": 1, "amount": 100}, {"id": 2, "amount": -5}])
except DataQualityError as error:
    print("Проверка не пройдена:", error)
```

### Два стиля: спросить разрешения или попросить прощения

```python
order = {"id": 1, "amount": 1200}

# LBYL (Look Before You Leap) — сначала проверяем
if "promo" in order:
    promo = order["promo"]
else:
    promo = None

# EAFP (Easier to Ask Forgiveness than Permission) — пробуем и ловим
try:
    promo = order["promo"]
except KeyError:
    promo = None

# А для словарей есть готовый способ
promo = order.get("promo")
print(promo)
```

В Python чаще принят второй стиль, но выбирай тот, который в данном месте читается проще.

## 2А.9. Аннотации типов

Аннотации — подсказки о том, какого типа аргументы и результат. Python их **не проверяет** при запуске, но их читают люди, редактор (подсказки и подчёркивание ошибок) и специальные программы-проверяльщики.

```python
def conversion(orders: int, visits: int) -> float:
    return orders / visits

def top_cities(revenue: dict[str, float], n: int = 3) -> list[str]:
    return sorted(revenue, key=revenue.get, reverse=True)[:n]

def find_order(orders: list[dict], order_id: int) -> dict | None:
    for order in orders:
        if order["id"] == order_id:
            return order
    return None

print(top_cities({"Москва": 12200, "Казань": 15400, "Уфа": 700}, n=2))
```

| Запись | Что означает |
|--------|-------------|
| `int`, `float`, `str`, `bool` | Простые типы |
| `list[int]` | Список целых чисел |
| `dict[str, float]` | Словарь: ключи-строки, значения-числа |
| `tuple[str, int]` | Кортеж из строки и числа |
| `str \| None` | Строка или `None` |
| `-> None` | Функция ничего не возвращает |
| `pd.DataFrame` | Таблица pandas |

Пиши аннотации хотя бы у функций, которые используешь больше одного раза: через месяц ты сам не вспомнишь, что принимает `prepare(data, cfg)`.

## 2А.10. Стандартная библиотека: что нужно знать

Прежде чем писать своё, проверь, нет ли готового. У Python очень богатая стандартная библиотека.

### pathlib — пути к файлам

Забудь про склейку путей строками. `Path` работает одинаково на Windows, macOS и Linux.

```python
from pathlib import Path

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)                      # создать папку, если её нет

for month in ["2026-01", "2026-02"]:
    (data_dir / f"orders_{month}.csv").write_text("id,amount\n1,100\n", encoding="utf-8")

path = data_dir / "orders_2026-01.csv"             # оператор / склеивает путь
print(path.name, path.stem, path.suffix)           # orders_2026-01.csv orders_2026-01 .csv
print(path.exists(), path.parent)

for file in sorted(data_dir.glob("orders_*.csv")): # найти файлы по шаблону
    print(file.name, len(file.read_text(encoding="utf-8").splitlines()))
```

Перебор файлов через `glob` — стандартный способ собрать выгрузки за много месяцев в одну таблицу.

### collections — удобные коллекции

```python
from collections import Counter, defaultdict, namedtuple

cities = ["Москва", "Казань", "Москва", "Уфа", "Москва"]

counts = Counter(cities)                           # подсчёт частот
print(counts.most_common(2))                       # [('Москва', 3), ('Казань', 1)]

orders = [("Москва", 1200), ("Казань", 15400), ("Москва", 8900)]
by_city = defaultdict(list)                        # словарь, который сам создаёт значение
for city, amount in orders:
    by_city[city].append(amount)                   # не нужно проверять, есть ли ключ
print(dict(by_city))

Order = namedtuple("Order", ["city", "amount"])    # кортеж с именованными полями
order = Order("Москва", 1200)
print(order.city, order.amount, order[0])
```

Сравни `defaultdict` с тем, как мы считали выручку по городам в главе 2 через `revenue.get(city, 0)`.

### itertools и functools

```python
from itertools import groupby, combinations, accumulate, islice, chain

print(list(accumulate([100, 200, 300])))               # [100, 300, 600] — накопительная сумма
print(list(combinations(["A", "B", "C"], 2)))          # все пары — пригодится для попарных тестов
print(list(islice(countdown(100), 3)))                 # первые 3 элемента генератора
print(list(chain([1, 2], [3], [4, 5])))                # склеить несколько коллекций

rows = sorted(orders)                                  # groupby требует сортировки по ключу!
for city, group in groupby(rows, key=lambda row: row[0]):
    print(city, sum(amount for _, amount in group))
```

### datetime — даты и время

```python
from datetime import datetime, date, timedelta

moment = datetime.strptime("15.03.2026 14:30", "%d.%m.%Y %H:%M")   # строка → дата
print(moment.strftime("%Y-%m-%d"), moment.strftime("%A"))          # дата → строка

start = date(2026, 1, 1)
print((date(2026, 3, 15) - start).days)                # 73 — разница в днях
print(start + timedelta(weeks=2))                      # 2026-01-15
print(date(2026, 3, 15).isocalendar().week)            # номер недели в году
```

| Код | Значение | Код | Значение |
|-----|----------|-----|----------|
| `%Y` | Год, 4 цифры | `%H` | Часы (24) |
| `%m` | Месяц | `%M` | Минуты |
| `%d` | День | `%S` | Секунды |

### json и csv

```python
import json
import csv

config = {"source": "orders.csv", "threshold": 10000, "cities": ["Москва", "Казань"]}

Path("config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
loaded = json.loads(Path("config.json").read_text(encoding="utf-8"))
print(loaded["cities"])

with open("big.csv", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)                         # каждая строка — словарь
    first = next(reader)
print(first)
```

`ensure_ascii=False` нужен, чтобы русские буквы записались буквами, а не кодами вида `М`.

### logging — вместо print

`print` годится для ноутбука. В скрипте, который работает сам по расписанию, нужен журнал: с временем, уровнем важности и возможностью писать в файл.

```python
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True)
log = logging.getLogger("report")

log.info("Загружено строк: %s", 500)
log.warning("Найдено дубликатов: %s", 10)
log.error("Файл не найден")
```

Уровни по возрастанию важности: `DEBUG` → `INFO` → `WARNING` → `ERROR` → `CRITICAL`.

## 2А.11. Модули и пакеты

**Модуль** — любой файл `.py`. **Пакет** — папка с модулями. Вынося функции в модули, ты перестаёшь копировать их из ноутбука в ноутбук.

Создадим модуль `metrics.py`:

```python
Path("metrics.py").write_text('''
"""Функции расчёта метрик."""


def conversion(orders: int, visits: int) -> float:
    """Доля визитов, закончившихся заказом."""
    if visits <= 0:
        raise ValueError("visits должно быть больше нуля")
    return orders / visits


def average_check(revenue: float, orders: int) -> float:
    return revenue / orders if orders else 0.0


if __name__ == "__main__":
    # Этот блок выполняется, только если файл запущен напрямую: python metrics.py
    # При импорте он НЕ выполняется.
    print(conversion(30, 1200))
''', encoding="utf-8")
```

И используем его:

```python
import sys
sys.path.insert(0, ".")            # нужно только в этом примере

import metrics
from metrics import average_check

print(metrics.conversion(30, 1200))
print(average_check(56600, 10))
```

Конструкция `if __name__ == "__main__":` встречается почти в каждом скрипте. Она отделяет «код для запуска» от «кода для импорта»: файл можно и запустить как программу, и подключить как библиотеку.

Способы импорта:

| Запись | Когда использовать |
|--------|-------------------|
| `import metrics` | Основной способ: видно, откуда функция — `metrics.conversion` |
| `from metrics import conversion` | Когда функция используется часто |
| `import pandas as pd` | Общепринятые сокращения |
| `from metrics import *` | Никогда: непонятно, какие имена появились и откуда |

Типичная структура аналитического проекта с модулями:

```
project/
├── notebooks/
│   └── analysis.ipynb       — исследование и графики
├── src/
│   ├── __init__.py          — пустой файл: делает папку пакетом
│   ├── load.py              — загрузка данных
│   ├── clean.py             — очистка
│   └── metrics.py           — расчёт метрик
├── tests/
│   └── test_metrics.py      — тесты
└── requirements.txt
```

Ноутбук — для исследования и рассказа. Всё, что используется повторно, переезжает в `src`. Подробнее — в главе 2В.

## Задания

1. **Копии.** Дан список `prices = [[100, 200], [300, 400]]`. Напиши функцию `with_discount(prices, percent)`, которая возвращает новый вложенный список со скидкой и **не меняет** исходный. Проверь это.
2. **Распаковка.** Дан список строк вида `"2026-03-15;Москва;1200"`. Одним включением преврати его в список словарей с ключами `date`, `city`, `amount` (сумма — числом).
3. **`*args` и `**kwargs`.** Напиши функцию `describe(*values, **options)`, которая возвращает словарь с минимумом, максимумом и средним. Если передан `digits=N`, округляй среднее до `N` знаков.
4. **Генератор.** Напиши генератор `batches(items, size)`, который выдаёт элементы пачками по `size` штук: `batches([1,2,3,4,5], 2)` → `[1,2]`, `[3,4]`, `[5]`.
5. **Декоратор.** Напиши декоратор `log_calls`, который печатает имя функции, её аргументы и результат.
6. **Менеджер контекста.** Напиши `working_directory(path)`, который на время блока `with` переходит в указанную папку, а потом возвращается обратно — даже при ошибке.
7. **Исключения.** Напиши функцию `safe_divide(a, b, default=None)`. При делении на ноль она возвращает `default`, а если аргументы не числа — вызывает `TypeError` с понятным сообщением.
8. **Стандартная библиотека.** Дан список событий `[("u1", "view"), ("u2", "view"), ("u1", "buy"), ...]`. С помощью `defaultdict` и `Counter` получи: список событий по каждому пользователю и самое частое событие.
9. **Модуль.** Вынеси функции из заданий 3 и 7 в файл `tools.py`, добавь блок `if __name__ == "__main__":` с примерами и импортируй модуль из другого файла.

## Проверь себя

- Чем `a == b` отличается от `a is b`?
- Почему нельзя писать `def f(x, items=[])`?
- Что делают `*` и `**` при определении функции и при её вызове?
- Чем генератор отличается от списка? Когда он нужен?
- Что делает декоратор? Зачем внутри него `functools.wraps`?
- Почему голый `except:` — плохая идея?
- Зачем нужен блок `if __name__ == "__main__":`?
- Проверяет ли Python аннотации типов при запуске?

## Решения

Сначала реши сам. Решение открывай, только если потратил на задачу минимум 15 минут — или чтобы сравнить со своим.

### Задание 1. Копии

```python
def with_discount(prices, percent):
    factor = 1 - percent / 100
    return [[price * factor for price in row] for row in prices]

prices = [[100, 200], [300, 400]]
discounted = with_discount(prices, 10)

print(discounted)     # [[90.0, 180.0], [270.0, 360.0]]
print(prices)         # [[100, 200], [300, 400]] — не изменился
```

Вложенное включение строит новые списки на обоих уровнях, поэтому оригинал в безопасности. Вариант с `prices.copy()` и изменением на месте испортил бы исходные данные: поверхностная копия делит вложенные списки с оригиналом.

### Задание 2. Распаковка

```python
lines = ["2026-03-15;Москва;1200", "2026-03-16;Казань;15400"]

orders = [
    {"date": date_, "city": city, "amount": int(amount)}
    for date_, city, amount in (line.split(";") for line in lines)
]
print(orders)
```

Внутреннее генераторное выражение разбивает строки, внешнее включение распаковывает каждую тройку в три имени. Имя `date_` с подчёркиванием — чтобы не перекрыть модуль `date`.

### Задание 3. `*args` и `**kwargs`

```python
def describe(*values, **options):
    if not values:
        raise ValueError("нужно передать хотя бы одно значение")
    mean = sum(values) / len(values)
    if "digits" in options:
        mean = round(mean, options["digits"])
    return {"min": min(values), "max": max(values), "mean": mean}

print(describe(12, 15, 11, 19))
print(describe(1, 2, 2, digits=2))
```

В реальном коде лучше объявить параметр явно: `def describe(*values, digits=None)`. Тогда опечатка в имени (`digit=2`) вызовет ошибку, а не будет молча проигнорирована. `**kwargs` оправдан, когда аргументы передаются дальше в другую функцию.

### Задание 4. Генератор

```python
def batches(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]

print(list(batches([1, 2, 3, 4, 5], 2)))     # [[1, 2], [3, 4], [5]]
```

`range` с шагом `size` даёт начала пачек, срез сам корректно обрежется на последней. Так отправляют данные в API или базу порциями.

### Задание 5. Декоратор

```python
import functools

def log_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        parts = [repr(a) for a in args] + [f"{k}={v!r}" for k, v in kwargs.items()]
        result = func(*args, **kwargs)
        print(f"{func.__name__}({', '.join(parts)}) -> {result!r}")
        return result
    return wrapper

@log_calls
def conversion(orders, visits):
    return orders / visits

conversion(30, visits=1200)      # conversion(30, visits=1200) -> 0.025
```

`repr` и `!r` показывают значение «как в коде»: строки будут в кавычках, и `"5"` не спутается с `5`.

### Задание 6. Менеджер контекста

```python
import os
from contextlib import contextmanager
from pathlib import Path

@contextmanager
def working_directory(path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)        # выполнится даже при ошибке внутри блока

Path("tmp_dir").mkdir(exist_ok=True)
print(Path.cwd().name)
with working_directory("tmp_dir"):
    print(Path.cwd().name)        # tmp_dir
print(Path.cwd().name)            # снова исходная папка
```

Ключевое — `try / finally`: без него ошибка внутри блока оставила бы программу в чужой папке.

### Задание 7. Исключения

```python
def safe_divide(a, b, default=None):
    for value in (a, b):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"ожидалось число, получено {value!r} ({type(value).__name__})")
    try:
        return a / b
    except ZeroDivisionError:
        return default

print(safe_divide(10, 4))               # 2.5
print(safe_divide(10, 0))               # None
print(safe_divide(10, 0, default=0.0))  # 0.0

try:
    safe_divide("10", 2)
except TypeError as error:
    print(error)
```

`bool` проверяется отдельно, потому что в Python `True` — это тоже `int`, и `safe_divide(True, 2)` без этой проверки спокойно вернул бы `0.5`.

### Задание 8. Стандартная библиотека

```python
from collections import Counter, defaultdict

events = [("u1", "view"), ("u2", "view"), ("u1", "buy"), ("u3", "view"), ("u2", "cart")]

by_user = defaultdict(list)
for user, event in events:
    by_user[user].append(event)
print(dict(by_user))

most_common_event, count = Counter(event for _, event in events).most_common(1)[0]
print(most_common_event, count)       # view 3
```

Подчёркивание `_` — общепринятое имя для значения, которое нам не нужно.

### Задание 9. Модуль

Файл `tools.py`:

```python
def describe(*values, digits=None):
    mean = sum(values) / len(values)
    if digits is not None:
        mean = round(mean, digits)
    return {"min": min(values), "max": max(values), "mean": mean}


def safe_divide(a, b, default=None):
    try:
        return a / b
    except ZeroDivisionError:
        return default


if __name__ == "__main__":
    print(describe(1, 2, 2, digits=2))
    print(safe_divide(1, 0, default=0))
```

Файл `main.py` в той же папке:

```python
import tools

print(tools.describe(10, 20, 30))
```

Запуск `python tools.py` выполнит примеры из блока `__main__`. Запуск `python main.py` — только то, что написано в `main.py`: при импорте блок `__main__` пропускается.
