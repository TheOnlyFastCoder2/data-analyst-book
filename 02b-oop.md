# Глава 2Б. Объектно-ориентированное программирование

ООП часто объясняют на кошках и собаках, и после этого непонятно, зачем оно нужно. Здесь мы пойдём от практики: ты **уже пользуешься** объектами каждый день, а к концу главы научишься создавать свои — там, где это упрощает код.

## 2Б.1. Ты уже работаешь с объектами

```python
text = "москва"
print(text.upper())          # строка — объект, upper — его метод

numbers = [3, 1, 2]
numbers.sort()               # список — объект, sort — его метод
print(numbers)

print(type(text), type(numbers))    # <class 'str'> <class 'list'>
```

<!-- result -->
*Результат:*

```output
МОСКВА
[1, 2, 3]
<class 'str'> <class 'list'>
```
<!-- /result -->



В pandas то же самое: `df` — объект класса `DataFrame`, `df.shape` — его **атрибут** (данные), `df.head()` — его **метод** (действие).

Термины:

- **Класс** — чертёж, описание: какие данные есть у объекта и что он умеет.
- **Объект** (экземпляр) — конкретная вещь, созданная по чертежу.
- **Атрибут** — данные объекта: `df.shape`, `df.columns`.
- **Метод** — функция, принадлежащая объекту: `df.head()`.

Идея ООП: **держать данные и функции для работы с ними в одном месте**.

## 2Б.2. Зачем свой класс: проблема и решение

Допустим, мы описываем заказ словарём и набором функций:

```python
order = {"id": 1, "items": [("Книга", 600, 2), ("Ручка", 50, 4)], "discount": 0.1}

def order_total(order):
    subtotal = sum(price * qty for _, price, qty in order["items"])
    return subtotal * (1 - order["discount"])

print(order_total(order))    # 1260.0
```

<!-- result -->
*Результат:*

```output
1260.0
```
<!-- /result -->



Что здесь неудобно:

- структуру словаря нужно помнить: что лежит в `items`, в каком порядке;
- опечатка в ключе (`"discont"`) обнаружится только при запуске;
- ничто не мешает положить в `discount` значение `5` или `"десять"`;
- функции для заказа разбросаны по коду и никак с ним не связаны.

Класс собирает всё это вместе.

## 2Б.3. Первый класс

```python
class Order:
    def __init__(self, order_id, discount=0.0):
        self.order_id = order_id        # атрибуты объекта
        self.discount = discount
        self.items = []

    def add_item(self, name, price, quantity=1):
        self.items.append((name, price, quantity))

    def subtotal(self):
        return sum(price * qty for _, price, qty in self.items)

    def total(self):
        return self.subtotal() * (1 - self.discount)


order = Order(1, discount=0.1)          # создание объекта: вызывается __init__
order.add_item("Книга", 600, 2)
order.add_item("Ручка", 50, 4)

print(order.total())                    # 1260.0
print(order.order_id, len(order.items))
```

<!-- result -->
*Результат:*

```output
1260.0
1 2
```
<!-- /result -->



Разбор:

- `class Order:` — объявление класса. Имена классов пишут с заглавной буквы, слитно: `Order`, `DataLoader`.
- `__init__` — **конструктор**. Вызывается автоматически при создании объекта и задаёт его начальное состояние.
- `self` — **сам объект**. Через `self.что-то` метод обращается к данным именно того объекта, у которого он вызван.

### Что такое self на самом деле

Запись `order.total()` — это сокращение. Python превращает её в `Order.total(order)`, то есть передаёт объект первым аргументом:

```python
print(order.total() == Order.total(order))    # True
```

<!-- result -->
*Результат:*

```output
True
```
<!-- /result -->



Поэтому первый параметр у каждого метода — `self`, а при вызове его писать не нужно. Забыл `self` в определении — получишь ошибку `takes 0 positional arguments but 1 was given`. Она означает именно это.

У каждого объекта свои данные:

```python
first = Order(1)
second = Order(2)
first.add_item("Книга", 600)

print(len(first.items), len(second.items))    # 1 0
```

<!-- result -->
*Результат:*

```output
1 0
```
<!-- /result -->



## 2Б.4. Атрибуты класса и атрибуты объекта

Атрибут, объявленный прямо в теле класса, общий для всех объектов:

```python
class Order:
    VAT_RATE = 0.2                      # атрибут КЛАССА: один на всех
    created = 0

    def __init__(self, order_id):
        self.order_id = order_id        # атрибут ОБЪЕКТА: у каждого свой
        Order.created += 1

    def vat(self, amount):
        return amount * self.VAT_RATE


a, b = Order(1), Order(2)
print(Order.created)                    # 2
print(a.vat(1000), b.VAT_RATE)          # 200.0 0.2
```

<!-- result -->
*Результат:*

```output
2
200.0 0.2
```
<!-- /result -->



Атрибуты класса используют для констант и общих настроек.

Ловушка: изменяемый атрибут класса становится общим для всех объектов — та же история, что со значением по умолчанию `[]` в главе 2А.

```python
class Bad:
    items = []                          # один список на ВСЕ объекты

    def add(self, item):
        self.items.append(item)

x, y = Bad(), Bad()
x.add("книга")
print(y.items)                          # ['книга'] — попало и в y

class Good:
    def __init__(self):
        self.items = []                 # у каждого объекта свой список
```

<!-- result -->
*Результат:*

```output
['книга']
```
<!-- /result -->



Правило: всё изменяемое создавай в `__init__`.

## 2Б.5. Магические методы

Методы с двумя подчёркиваниями по краям (`__init__`, `__repr__`) Python вызывает сам в определённых ситуациях. Через них объект учится вести себя как встроенные типы: печататься, сравниваться, складываться, работать в цикле `for`.

```python
class Money:
    def __init__(self, amount, currency="RUB"):
        self.amount = amount
        self.currency = currency

    def __repr__(self):                         # как объект выглядит при печати и в отладке
        return f"Money({self.amount}, {self.currency!r})"

    def __str__(self):                          # «красивый» вид для print и f-строк
        return f"{self.amount:,.2f} {self.currency}"

    def __eq__(self, other):                    # ==
        return (self.amount, self.currency) == (other.amount, other.currency)

    def __lt__(self, other):                    # <  (этого достаточно для sorted и min)
        self._check(other)
        return self.amount < other.amount

    def __add__(self, other):                   # +
        self._check(other)
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, factor):                  # *
        return Money(self.amount * factor, self.currency)

    def _check(self, other):
        if self.currency != other.currency:
            raise ValueError(f"нельзя смешивать {self.currency} и {other.currency}")


price = Money(1200)
print(price)                        # 1,200.00 RUB        — сработал __str__
print([price])                      # [Money(1200, 'RUB')] — в списке работает __repr__
print(price + Money(300))           # 1,500.00 RUB
print(price * 2 == Money(2400))     # True
print(max(Money(5), Money(9)))      # 9.00 RUB

try:
    price + Money(10, "USD")
except ValueError as error:
    print(error)                    # нельзя смешивать RUB и USD
```

<!-- result -->
*Результат:*

```output
1,200.00 RUB
[Money(1200, 'RUB')]
1,500.00 RUB
True
9.00 RUB
нельзя смешивать RUB и USD
```
<!-- /result -->



Обрати внимание на последний пример: класс не просто хранит данные, а **защищает от бессмысленных операций**. Словарь `{"amount": 1200, "currency": "RUB"}` так не умеет.

Самые полезные магические методы:

| Метод | Когда вызывается |
|-------|------------------|
| `__init__(self, ...)` | Создание объекта |
| `__repr__(self)` | Вывод в консоли и в отладке — **пиши всегда** |
| `__str__(self)` | `print(obj)`, `str(obj)`, f-строки |
| `__eq__(self, other)` | `a == b` |
| `__lt__(self, other)` | `a < b`, сортировка |
| `__add__`, `__sub__`, `__mul__` | `a + b`, `a - b`, `a * b` |
| `__len__(self)` | `len(obj)` |
| `__getitem__(self, key)` | `obj[key]` |
| `__contains__(self, item)` | `item in obj` |
| `__iter__(self)` | `for x in obj` |
| `__enter__`, `__exit__` | `with obj:` |

Сделаем коллекцию, которая ведёт себя как встроенная:

```python
class Basket:
    def __init__(self):
        self._items = {}

    def add(self, name, price):
        self._items[name] = price

    def __len__(self):
        return len(self._items)

    def __contains__(self, name):
        return name in self._items

    def __getitem__(self, name):
        return self._items[name]

    def __iter__(self):
        return iter(self._items.items())

    def __repr__(self):
        return f"Basket({self._items})"


basket = Basket()
basket.add("Книга", 600)
basket.add("Ручка", 50)

print(len(basket), "Книга" in basket, basket["Ручка"])
for name, price in basket:
    print(name, price)
print(sum(price for _, price in basket))
```

<!-- result -->
*Результат:*

```output
2 True 50
Книга 600
Ручка 50
650
```
<!-- /result -->



Именно так устроен `DataFrame`: `len(df)`, `"city" in df`, `df["city"]`, `for column in df` — это всё магические методы.

## 2Б.6. Инкапсуляция и свойства

**Инкапсуляция** — идея о том, что объект сам отвечает за корректность своих данных, а снаружи с ним работают через понятный интерфейс.

В Python нет настоящих закрытых атрибутов, есть соглашение:

- `name` — публичный атрибут, пользуйся свободно;
- `_name` — «внутренний, не трогай снаружи». Технически доступен, но менять его извне — дурной тон.

**Свойство** (`property`) выглядит как атрибут, а работает как метод. Оно даёт два умения: вычисляемые атрибуты и проверку при присваивании.

```python
class Product:
    def __init__(self, name, price, cost):
        self.name = name
        self.price = price            # сработает проверка из setter ниже
        self.cost = cost

    @property
    def price(self):                  # чтение: product.price
        return self._price

    @price.setter
    def price(self, value):           # запись: product.price = 100
        if value <= 0:
            raise ValueError(f"цена должна быть положительной, получено {value}")
        self._price = value

    @property
    def margin(self):                 # вычисляемое свойство, только для чтения
        return (self.price - self.cost) / self.price


book = Product("Книга", price=600, cost=420)
print(book.margin)                    # 0.3 — без скобок, как обычный атрибут

book.price = 700                      # проверка пройдена
print(round(book.margin, 2))          # 0.4 — пересчиталось само

try:
    book.price = -5
except ValueError as error:
    print(error)
```

<!-- result -->
*Результат:*

```output
0.3
0.4
цена должна быть положительной, получено -5
```
<!-- /result -->



Преимущество вычисляемого свойства: маржа никогда не «устареет». Если бы мы хранили её обычным атрибутом, после смены цены в объекте лежало бы старое значение.

## 2Б.7. Наследование

Наследование позволяет создать класс на основе существующего: взять всё, что есть у родителя, и добавить или изменить часть.

```python
class Employee:
    def __init__(self, name, salary):
        self.name = name
        self.salary = salary

    def monthly_cost(self):
        return self.salary

    def __repr__(self):
        return f"{type(self).__name__}({self.name!r})"


class Manager(Employee):                       # Manager наследует Employee
    def __init__(self, name, salary, bonus):
        super().__init__(name, salary)         # вызвать конструктор родителя
        self.bonus = bonus

    def monthly_cost(self):                    # переопределение метода
        return super().monthly_cost() + self.bonus


class Contractor(Employee):
    def __init__(self, name, hourly_rate, hours):
        super().__init__(name, salary=0)
        self.hourly_rate = hourly_rate
        self.hours = hours

    def monthly_cost(self):
        return self.hourly_rate * self.hours


team = [Employee("Анна", 120), Manager("Борис", 200, bonus=50), Contractor("Вера", 1.5, 80)]

for person in team:
    print(person, person.monthly_cost())

print(sum(p.monthly_cost() for p in team))     # 490.0
```

<!-- result -->
*Результат:*

```output
Employee('Анна') 120
Manager('Борис') 250
Contractor('Вера') 120.0
490.0
```
<!-- /result -->



- `super()` — обращение к родительскому классу. Не дублируй код родителя, вызывай его.
- Метод `__repr__` написан один раз в `Employee` и работает для всех наследников.

### Полиморфизм

Посмотри на цикл: мы вызываем `person.monthly_cost()`, не зная и не проверяя, кто перед нами. Каждый объект сам знает, как себя посчитать. Это и есть **полиморфизм**: один интерфейс — разное поведение.

Сравни с кодом без него:

```python
def monthly_cost(person):                       # так делать не надо
    if person["type"] == "employee":
        return person["salary"]
    elif person["type"] == "manager":
        return person["salary"] + person["bonus"]
    elif person["type"] == "contractor":
        return person["rate"] * person["hours"]
```

Чтобы добавить новый тип сотрудника, придётся найти и поправить все такие `if / elif` по всему коду. В объектном варианте достаточно добавить один новый класс, а существующий код не меняется.

### Проверка типов

```python
boss = Manager("Борис", 200, bonus=50)

print(isinstance(boss, Manager))      # True
print(isinstance(boss, Employee))     # True — менеджер тоже сотрудник
print(type(boss) is Employee)         # False — точный тип другой
```

<!-- result -->
*Результат:*

```output
True
True
False
```
<!-- /result -->



Для проверок используй `isinstance`: он учитывает наследование.

## 2Б.8. Абстрактные классы и утиная типизация

### Абстрактный класс: контракт для наследников

Иногда родительский класс существует только для того, чтобы задать общий интерфейс. **Абстрактный класс** нельзя создать напрямую, а его наследники обязаны реализовать отмеченные методы.

```python
from abc import ABC, abstractmethod


class DataSource(ABC):
    """Любой источник данных умеет отдавать список словарей."""

    @abstractmethod
    def load(self) -> list[dict]:
        ...

    def count(self) -> int:              # обычный метод: общий для всех наследников
        return len(self.load())


class ListSource(DataSource):
    def __init__(self, rows):
        self.rows = rows

    def load(self):
        return list(self.rows)


class CsvTextSource(DataSource):
    def __init__(self, text, sep=","):
        self.text = text
        self.sep = sep

    def load(self):
        header, *lines = self.text.strip().splitlines()
        keys = header.split(self.sep)
        return [dict(zip(keys, line.split(self.sep))) for line in lines]


sources = [
    ListSource([{"city": "Москва", "amount": "1200"}]),
    CsvTextSource("city,amount\nКазань,15400\nУфа,700"),
]
for source in sources:
    print(type(source).__name__, source.count(), source.load()[0])

try:
    DataSource()
except TypeError as error:
    print("Нельзя:", error)
```

<!-- result -->
*Результат:*

```output
ListSource 1 {'city': 'Москва', 'amount': '1200'}
CsvTextSource 2 {'city': 'Казань', 'amount': '15400'}
Нельзя: Can't instantiate abstract class DataSource without an implementation for abstract method 'load'
```
<!-- /result -->



Если в наследнике забыть метод `load`, ошибка появится сразу при создании объекта, а не через час работы программы.

### Утиная типизация

В Python часто обходятся без общего родителя. Принцип: «если нечто ходит как утка и крякает как утка — это утка». Функции неважно, какого класса объект; важно, что у него есть нужный метод.

```python
class ApiSource:                         # не наследует DataSource вообще
    def load(self):
        return [{"city": "Самара", "amount": "900"}]


def total_amount(source):
    return sum(float(row["amount"]) for row in source.load())

print(total_amount(ApiSource()))                                       # 900.0
print(total_amount(CsvTextSource("city,amount\nКазань,15400\nУфа,700")))  # 16100.0
```

<!-- result -->
*Результат:*

```output
900.0
16100.0
```
<!-- /result -->



Именно поэтому функция `len()` работает и со списком, и с DataFrame, и с нашим `Basket`: ей нужен только метод `__len__`.

Описать такой «неявный интерфейс» для подсказок редактора можно через `Protocol`:

```python
from typing import Protocol


class Loadable(Protocol):
    def load(self) -> list[dict]: ...


def first_row(source: Loadable) -> dict:
    return source.load()[0]

print(first_row(ApiSource()))
```

<!-- result -->
*Результат:*

```output
{'city': 'Самара', 'amount': '900'}
```
<!-- /result -->



## 2Б.9. Композиция вместо наследования

Наследование выражает отношение **«является»** (менеджер является сотрудником). Композиция — отношение **«содержит»** (отчёт содержит источник данных).

Новички злоупотребляют наследованием. Проверочный вопрос: можно ли честно сказать «A — это разновидность B»? Если нет — нужна композиция.

```python
class Report:
    """Отчёт СОДЕРЖИТ источник и набор метрик, а не наследует их."""

    def __init__(self, source, metrics):
        self.source = source                # любой объект с методом load()
        self.metrics = metrics              # словарь: название → функция

    def build(self):
        amounts = [float(row["amount"]) for row in self.source.load()]
        return {name: func(amounts) for name, func in self.metrics.items()}


metrics = {
    "заказов": len,
    "выручка": sum,
    "средний чек": lambda values: sum(values) / len(values),
}

report = Report(CsvTextSource("city,amount\nКазань,15400\nУфа,700"), metrics)
print(report.build())

report.source = ApiSource()                 # подменили источник — отчёт не изменился
print(report.build())
```

<!-- result -->
*Результат:*

```output
{'заказов': 2, 'выручка': 16100.0, 'средний чек': 8050.0}
{'заказов': 1, 'выручка': 900.0, 'средний чек': 900.0}
```
<!-- /result -->



Отчёту всё равно, откуда данные: из файла, из API или из тестового списка. Части можно менять независимо. Это главный приём построения гибкого кода, и на нём основаны паттерны главы 2В.

Правило, которое стоит запомнить: **предпочитай композицию наследованию**. Глубокие иерархии классов трудно понимать и ещё труднее менять.

## 2Б.10. dataclass: классы для данных

Большинство классов у аналитика — это просто «записи» с полями. Писать для них `__init__`, `__repr__` и `__eq__` вручную скучно. Декоратор `@dataclass` генерирует их сам.

```python
from dataclasses import dataclass, field
from datetime import date


@dataclass
class OrderLine:
    name: str
    price: float
    quantity: int = 1

    @property
    def total(self) -> float:
        return self.price * self.quantity


@dataclass
class CustomerOrder:
    order_id: int
    customer: str
    created: date
    lines: list[OrderLine] = field(default_factory=list)    # изменяемое значение по умолчанию
    discount: float = 0.0

    def __post_init__(self):                 # выполняется сразу после __init__: место для проверок
        if not 0 <= self.discount < 1:
            raise ValueError(f"скидка должна быть от 0 до 1, получено {self.discount}")

    @property
    def total(self) -> float:
        return sum(line.total for line in self.lines) * (1 - self.discount)


order = CustomerOrder(1, "Анна", date(2026, 3, 15), discount=0.1)
order.lines.append(OrderLine("Книга", 600, 2))
order.lines.append(OrderLine("Ручка", 50, 4))

print(order)                                  # готовый __repr__ со всеми полями
print(order.total)                            # 1260.0
print(OrderLine("Ручка", 50) == OrderLine("Ручка", 50))    # True — готовый __eq__
```

<!-- result -->
*Результат:*

```output
CustomerOrder(order_id=1, customer='Анна', created=datetime.date(2026, 3, 15), lines=[OrderLine(name='Книга', price=6…
1260.0
True
```
<!-- /result -->



Что нужно знать:

- поля описываются с аннотациями типов;
- поля со значением по умолчанию идут после полей без него;
- для списков и словарей используется `field(default_factory=list)` — защита от той самой ловушки с общим списком;
- `__post_init__` — место для проверки данных.

### Неизменяемые объекты

`frozen=True` запрещает менять поля после создания. Такие объекты безопасно передавать куда угодно, и их можно использовать как ключи словаря.

```python
@dataclass(frozen=True, order=True)
class Period:
    year: int
    month: int

    def label(self) -> str:
        return f"{self.year}-{self.month:02d}"


revenue = {Period(2026, 1): 1_200_000, Period(2026, 2): 1_350_000}
print(revenue[Period(2026, 2)])
print(sorted([Period(2026, 3), Period(2025, 12)]))     # order=True даёт сравнение

try:
    Period(2026, 1).month = 5
except Exception as error:
    print(type(error).__name__)                        # FrozenInstanceError
```

<!-- result -->
*Результат:*

```output
1350000
[Period(year=2025, month=12), Period(year=2026, month=3)]
FrozenInstanceError
```
<!-- /result -->



### Enum: фиксированный набор значений

Вместо строк `"paid"`, `"Paid"`, `"оплачен"`, в которых легко опечататься:

```python
from enum import Enum


class Status(Enum):
    NEW = "new"
    PAID = "paid"
    CANCELLED = "cancelled"


status = Status("paid")                 # из строки, например из базы
print(status, status.value, status is Status.PAID)
print([s.value for s in Status])

try:
    Status("Paid")                      # опечатка ловится сразу
except ValueError as error:
    print(error)
```

<!-- result -->
*Результат:*

```output
Status.PAID paid True
['new', 'paid', 'cancelled']
'Paid' is not a valid Status
```
<!-- /result -->



## 2Б.11. Методы класса и статические методы

```python
@dataclass
class Point:
    lat: float
    lon: float

    @classmethod
    def from_string(cls, text):               # альтернативный конструктор
        lat, lon = (float(part) for part in text.split(","))
        return cls(lat, lon)

    @staticmethod
    def is_valid(lat, lon):                   # функция «по теме», объект не нужен
        return -90 <= lat <= 90 and -180 <= lon <= 180


moscow = Point.from_string("55.75, 37.62")
print(moscow, Point.is_valid(95, 10))
```

<!-- result -->
*Результат:*

```output
Point(lat=55.75, lon=37.62) False
```
<!-- /result -->



| Вид метода | Первый аргумент | Зачем |
|------------|-----------------|-------|
| Обычный | `self` — объект | Работает с данными объекта |
| `@classmethod` | `cls` — класс | Альтернативные конструкторы: `from_string`, `from_dict`, `from_csv` |
| `@staticmethod` | нет | Вспомогательная функция, логически относящаяся к классу |

Ты уже встречал методы класса: `pd.DataFrame.from_dict(...)`, `datetime.strptime(...)`, `date.today()`.

## 2Б.12. Сквозной пример: конвейер проверки качества данных

Соберём всё вместе. Задача из жизни: перед анализом таблицу нужно прогнать через набор проверок и получить отчёт.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    details: str = ""

    def __str__(self):
        mark = "OK  " if self.passed else "FAIL"
        return f"[{mark}] {self.name}" + (f" — {self.details}" if self.details else "")


class Check(ABC):
    """Одна проверка. Наследники реализуют run()."""

    name = "проверка"

    @abstractmethod
    def run(self, rows: list[dict]) -> CheckResult:
        ...


class NotEmpty(Check):
    name = "таблица не пустая"

    def run(self, rows):
        return CheckResult(self.name, passed=len(rows) > 0, details=f"строк: {len(rows)}")


class NoMissing(Check):
    def __init__(self, column):
        self.column = column
        self.name = f"нет пропусков в «{column}»"

    def run(self, rows):
        missing = sum(1 for row in rows if row.get(self.column) in (None, ""))
        return CheckResult(self.name, missing == 0, f"пропусков: {missing}")


class Unique(Check):
    def __init__(self, column):
        self.column = column
        self.name = f"значения «{column}» уникальны"

    def run(self, rows):
        values = [row[self.column] for row in rows]
        duplicates = len(values) - len(set(values))
        return CheckResult(self.name, duplicates == 0, f"дубликатов: {duplicates}")


class InRange(Check):
    def __init__(self, column, low, high):
        self.column, self.low, self.high = column, low, high
        self.name = f"«{column}» в диапазоне [{low}, {high}]"

    def run(self, rows):
        bad = [row[self.column] for row in rows
               if row[self.column] is not None and not self.low <= row[self.column] <= self.high]
        return CheckResult(self.name, not bad, f"вне диапазона: {bad}" if bad else "")


class QualityReport:
    """Содержит набор проверок (композиция) и запускает их все."""

    def __init__(self, checks: list[Check]):
        self.checks = checks

    def run(self, rows) -> list[CheckResult]:
        return [check.run(rows) for check in self.checks]

    def is_ok(self, rows) -> bool:
        return all(result.passed for result in self.run(rows))


orders = [
    {"id": 1, "city": "Москва", "amount": 1200},
    {"id": 2, "city": "", "amount": 15400},
    {"id": 2, "city": "Уфа", "amount": -500},
    {"id": 4, "city": "Казань", "amount": None},
]

report = QualityReport([
    NotEmpty(),
    NoMissing("city"),
    NoMissing("amount"),
    Unique("id"),
    InRange("amount", 0, 1_000_000),
])

for result in report.run(orders):
    print(result)
print("Данные годятся для анализа:", report.is_ok(orders))
```

<!-- result -->
*Результат:*

```output
[OK  ] таблица не пустая — строк: 4
[FAIL] нет пропусков в «city» — пропусков: 1
[FAIL] нет пропусков в «amount» — пропусков: 1
[FAIL] значения «id» уникальны — дубликатов: 1
[FAIL] «amount» в диапазоне [0, 1000000] — вне диапазона: [-500]
Данные годятся для анализа: False
```
<!-- /result -->



Что здесь использовано:

- **абстрактный класс** `Check` задаёт контракт: у любой проверки есть `run`;
- **наследование и полиморфизм**: `QualityReport` вызывает `check.run(rows)`, не зная, какая это проверка;
- **композиция**: отчёт содержит список проверок;
- **dataclass** для результата и `__str__` для красивого вывода.

Главное достоинство: чтобы добавить новую проверку, нужно написать один маленький класс. Ни `QualityReport`, ни остальные проверки менять не придётся.

## 2Б.13. Когда ООП не нужно

Объекты — инструмент, а не цель. Аналитический код в основном состоит из преобразований данных, и для них обычные функции подходят лучше.

Класс **не нужен**, если:

- у него один метод кроме `__init__` — это просто функция;
- он не хранит состояния между вызовами;
- это ноутбук с разовым исследованием.

Класс **полезен**, когда:

- есть данные и набор операций, которые имеют смысл только вместе (`Money`, `Order`);
- нужно гарантировать корректность данных (проверки в конструкторе и свойствах);
- есть несколько взаимозаменяемых вариантов одного поведения (источники данных, проверки, способы расчёта);
- объект держит ресурс или состояние: соединение с базой, кэш, настройки.

Разумный порядок: начинай с функций. Когда заметишь, что несколько функций всё время принимают один и тот же набор аргументов, — это кандидат в класс.

## Задания

1. **Класс `Rectangle`.** Атрибуты `width` и `height`, методы `area()` и `perimeter()`, понятный `__repr__`. Запрети отрицательные размеры.
2. **Класс `Temperature`.** Хранит градусы Цельсия. Свойство `fahrenheit` (чтение и запись), проверка, что температура не ниже −273,15. Объекты должны сравниваться через `<` и `==`.
3. **Класс `Stats`.** Принимает список чисел. Поддерживает `len(stats)`, `stats[i]`, цикл `for`, оператор `in`; свойства `mean` и `median`.
4. **Наследование.** Базовый класс `Shape` с абстрактным методом `area()`. Наследники `Circle` и `Square`. Напиши функцию, которая считает суммарную площадь списка фигур.
5. **dataclass.** Опиши `Transaction` с полями `id`, `user_id`, `amount`, `created` (дата). Сделай его неизменяемым, добавь проверку `amount != 0` и метод класса `from_dict`.
6. **Композиция.** Класс `Funnel` принимает список названий шагов и словарь «шаг → число пользователей». Метод `conversions()` возвращает конверсию каждого шага от предыдущего, `bottleneck()` — шаг с самой низкой конверсией.
7. **Расширение примера.** Добавь в конвейер из раздела 2Б.12 проверку `AllowedValues(column, allowed)`, которая убеждается, что в столбце только разрешённые значения.

## Проверь себя

- Чем класс отличается от объекта?
- Что такое `self`? Почему его нет при вызове метода?
- Чем атрибут класса отличается от атрибута объекта?
- Зачем нужен `__repr__`?
- Что даёт `@property`?
- Что такое полиморфизм? Приведи пример из pandas или встроенных функций.
- Чем композиция отличается от наследования и что предпочитать?
- Что генерирует `@dataclass`? Зачем нужен `field(default_factory=list)`?
- Когда вместо класса лучше написать функцию?

## Решения

### Задание 1. Rectangle

```python
class Rectangle:
    def __init__(self, width, height):
        if width <= 0 or height <= 0:
            raise ValueError("размеры должны быть положительными")
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

    def perimeter(self):
        return 2 * (self.width + self.height)

    def __repr__(self):
        return f"Rectangle({self.width}, {self.height})"


r = Rectangle(3, 4)
print(r, r.area(), r.perimeter())     # Rectangle(3, 4) 12 14
```

<!-- result -->
*Результат:*

```output
Rectangle(3, 4) 12 14
```
<!-- /result -->



Проверка стоит в конструкторе: объект с неверными размерами просто не может появиться. Недостаток — после создания можно написать `r.width = -1`. Чтобы закрыть и эту дыру, нужны свойства, как в следующем решении.

### Задание 2. Temperature

```python
import functools

ABSOLUTE_ZERO = -273.15


@functools.total_ordering                 # по __eq__ и __lt__ достраивает <=, >, >=
class Temperature:
    def __init__(self, celsius):
        self.celsius = celsius            # идёт через setter, проверка сработает

    @property
    def celsius(self):
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        if value < ABSOLUTE_ZERO:
            raise ValueError(f"ниже абсолютного нуля: {value}")
        self._celsius = value

    @property
    def fahrenheit(self):
        return self._celsius * 9 / 5 + 32

    @fahrenheit.setter
    def fahrenheit(self, value):
        self.celsius = (value - 32) * 5 / 9     # снова через проверку

    def __eq__(self, other):
        return self.celsius == other.celsius

    def __lt__(self, other):
        return self.celsius < other.celsius

    def __repr__(self):
        return f"Temperature({self.celsius:.1f}°C)"


t = Temperature(25)
print(t.fahrenheit)                       # 77.0
t.fahrenheit = 212
print(t, t > Temperature(30), max(Temperature(5), Temperature(-3)))
```

<!-- result -->
*Результат:*

```output
77.0
Temperature(100.0°C) True Temperature(5.0°C)
```
<!-- /result -->



Хранится одно значение (`_celsius`), а Фаренгейт вычисляется из него. Хранить оба числа было бы ошибкой: они могли бы разойтись.

### Задание 3. Stats

```python
class Stats:
    def __init__(self, values):
        if not values:
            raise ValueError("нужен непустой список")
        self._values = list(values)            # копия: внешний список нас не изменит

    def __len__(self):
        return len(self._values)

    def __getitem__(self, index):
        return self._values[index]

    def __iter__(self):
        return iter(self._values)

    def __contains__(self, value):
        return value in self._values

    @property
    def mean(self):
        return sum(self._values) / len(self._values)

    @property
    def median(self):
        ordered = sorted(self._values)
        middle = len(ordered) // 2
        if len(ordered) % 2:
            return ordered[middle]
        return (ordered[middle - 1] + ordered[middle]) / 2

    def __repr__(self):
        return f"Stats(n={len(self)}, mean={self.mean:.2f})"


s = Stats([12, 15, 11, 19, 95])
print(s, len(s), s[0], 19 in s, s.median)
print([x for x in s if x > 12])
```

<!-- result -->
*Результат:*

```output
Stats(n=5, mean=30.40) 5 12 True 15
[15, 19, 95]
```
<!-- /result -->



### Задание 4. Наследование

```python
import math
from abc import ABC, abstractmethod


class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        ...


class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return math.pi * self.radius ** 2


class Square(Shape):
    def __init__(self, side):
        self.side = side

    def area(self):
        return self.side ** 2


def total_area(shapes):
    return sum(shape.area() for shape in shapes)

print(round(total_area([Circle(1), Square(2)]), 2))     # 7.14
```

<!-- result -->
*Результат:*

```output
7.14
```
<!-- /result -->



Функция `total_area` не знает о существовании кругов и квадратов. Добавишь `Triangle` — она продолжит работать без изменений.

### Задание 5. dataclass

```python
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Transaction:
    id: int
    user_id: int
    amount: float
    created: date

    def __post_init__(self):
        if self.amount == 0:
            raise ValueError("сумма транзакции не может быть нулевой")

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=int(data["id"]),
            user_id=int(data["user_id"]),
            amount=float(data["amount"]),
            created=date.fromisoformat(data["created"]),
        )

    @property
    def is_refund(self):
        return self.amount < 0


t = Transaction.from_dict({"id": "7", "user_id": "42", "amount": "-350.5", "created": "2026-03-15"})
print(t, t.is_refund)
```

<!-- result -->
*Результат:*

```output
Transaction(id=7, user_id=42, amount=-350.5, created=datetime.date(2026, 3, 15)) True
```
<!-- /result -->



`from_dict` — место, где «сырые» строки превращаются в правильные типы. Дальше по коду гуляет объект, в корректности которого можно не сомневаться.

### Задание 6. Композиция

```python
class Funnel:
    def __init__(self, steps, users):
        missing = [step for step in steps if step not in users]
        if missing:
            raise ValueError(f"нет данных для шагов: {missing}")
        self.steps = list(steps)
        self.users = dict(users)

    def conversions(self):
        pairs = zip(self.steps, self.steps[1:])
        return {f"{a} → {b}": self.users[b] / self.users[a] for a, b in pairs}

    def bottleneck(self):
        conversions = self.conversions()
        return min(conversions, key=conversions.get)

    def total_conversion(self):
        return self.users[self.steps[-1]] / self.users[self.steps[0]]


funnel = Funnel(
    ["визит", "товар", "корзина", "оплата"],
    {"визит": 10000, "товар": 4200, "корзина": 1300, "оплата": 520},
)
for step, value in funnel.conversions().items():
    print(f"{step}: {value:.1%}")
print("Узкое место:", funnel.bottleneck())
print(f"Общая конверсия: {funnel.total_conversion():.1%}")
```

<!-- result -->
*Результат:*

```output
визит → товар: 42.0%
товар → корзина: 31.0%
корзина → оплата: 40.0%
Узкое место: товар → корзина
Общая конверсия: 5.2%
```
<!-- /result -->



Приём `zip(steps, steps[1:])` даёт пары соседних элементов — запомни его, он нужен постоянно.

### Задание 7. Расширение примера

```python
class AllowedValues(Check):
    def __init__(self, column, allowed):
        self.column = column
        self.allowed = set(allowed)
        self.name = f"«{column}» содержит только разрешённые значения"

    def run(self, rows):
        unexpected = sorted({row[self.column] for row in rows} - self.allowed)
        return CheckResult(self.name, not unexpected,
                           f"неожиданные значения: {unexpected}" if unexpected else "")


report = QualityReport([NotEmpty(), AllowedValues("city", ["Москва", "Казань", "Уфа"])])
for result in report.run(orders):
    print(result)
```

<!-- result -->
*Результат:*

```output
[OK  ] таблица не пустая — строк: 4
[FAIL] «city» содержит только разрешённые значения — неожиданные значения: ['']
```
<!-- /result -->



Мы не изменили ни одной строки существующего кода — только добавили класс. Это называют принципом открытости-закрытости: код открыт для расширения и закрыт для изменения.
