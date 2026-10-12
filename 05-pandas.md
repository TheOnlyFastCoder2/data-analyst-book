# Глава 5. pandas

pandas — главный рабочий инструмент аналитика в Python. Это «Excel в коде»: таблицы, фильтры, сводные, соединения — но воспроизводимо и на миллионах строк.

Это самая важная глава книги. Не торопись: каждый пример набери руками и поменяй в нём что-нибудь.

## 5.1. Series и DataFrame

- **DataFrame** — таблица: строки и именованные столбцы.
- **Series** — один столбец таблицы.
- **Index** — подписи строк.

Создадим учебный датасет, с которым будем работать всю главу:

```python
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
n = 500

df = pd.DataFrame({
    "order_id": np.arange(1, n + 1),
    "date": pd.Timestamp("2026-01-01") + pd.to_timedelta(rng.integers(0, 90, n), unit="D"),
    "user_id": rng.integers(1, 121, n),
    "city": rng.choice(["Москва", "Казань", "Уфа", "Самара"], n, p=[0.5, 0.2, 0.15, 0.15]),
    "category": rng.choice(["Книги", "Техника", "Одежда"], n),
    "amount": rng.gamma(shape=2.0, scale=1500, size=n).round(0),
})

df.to_csv("orders.csv", index=False)
```

Мы сохранили файл `orders.csv` — он пригодится в следующих главах.

## 5.2. Первый взгляд на данные

С этих команд начинается работа с любым датасетом:

```python
df = pd.read_csv("orders.csv", parse_dates=["date"])

print(df.head())          # первые 5 строк
print(df.shape)           # (500, 6) — строк и столбцов
df.info()                 # типы столбцов и число непустых значений
print(df.describe())      # статистика по числовым столбцам
print(df["city"].value_counts())                 # частоты значений
print(df["city"].value_counts(normalize=True))   # доли
print(df["user_id"].nunique())                   # число уникальных
print(df.isna().sum())    # пропуски по столбцам
```

Привычка на всю жизнь: загрузил данные — сразу `head()`, `info()`, `describe()`. Половина ошибок в анализе — от того, что данные оказались не такими, как ты думал.

## 5.3. Выбор столбцов и строк

```python
df["amount"]                    # один столбец — Series
df[["city", "amount"]]          # несколько столбцов — DataFrame

df[df["amount"] > 5000]                                     # фильтр
df[(df["city"] == "Москва") & (df["amount"] > 5000)]        # два условия
df[df["city"].isin(["Казань", "Уфа"])]                      # значение из списка
df[df["date"].between("2026-02-01", "2026-02-28")]          # диапазон
df.query("city == 'Москва' and amount > 5000")              # то же строкой
```

Это булевы маски из главы 4: условие даёт столбец из `True` и `False`, по нему отбираются строки. Правила те же: `&`, `|`, `~` и скобки вокруг каждого условия.

`loc` и `iloc` — два способа обращаться к строкам и столбцам одновременно:

```python
df.loc[df["city"] == "Уфа", ["date", "amount"]]   # loc — по условию и именам
df.iloc[0:5, 0:3]                                  # iloc — по номерам позиций
```

Сортировка:

```python
df.sort_values("amount", ascending=False).head(10)
df.sort_values(["city", "amount"], ascending=[True, False])
df.nlargest(5, "amount")
```

## 5.4. Новые столбцы

```python
df["amount_k"] = df["amount"] / 1000
df["month"] = df["date"].dt.to_period("M").astype(str)
df["weekday"] = df["date"].dt.day_name()
df["is_big"] = df["amount"] >= 5000

df["segment"] = np.where(df["amount"] >= 5000, "крупный", "обычный")

df["size_group"] = pd.cut(
    df["amount"],
    bins=[0, 1000, 5000, np.inf],
    labels=["мелкий", "средний", "крупный"],
)
```

Аксессоры — доступ к специальным методам столбца:

- `.dt` — для дат: `.dt.year`, `.dt.month`, `.dt.dayofweek`, `.dt.to_period("M")`;
- `.str` — для строк: `.str.lower()`, `.str.strip()`, `.str.contains("...")`, `.str.replace(...)`.

`apply` применяет произвольную функцию. Он удобен, но медленный — используй, только если нет готового векторного метода:

```python
df["label"] = df["city"].apply(lambda c: f"г. {c}")
```

Изменять значения по условию нужно через `loc`:

```python
df.loc[df["city"] == "Уфа", "region"] = "Башкортостан"
```

Запись вида `df[df["city"] == "Уфа"]["region"] = ...` не сработает и выдаст предупреждение `SettingWithCopyWarning`: изменение уйдёт во временную копию.

## 5.5. Группировка

`groupby` — то же, что `GROUP BY` в SQL и сводная таблица в Excel. Схема называется **split–apply–combine**: разбить на группы, посчитать в каждой, собрать обратно.

```python
df.groupby("city")["amount"].sum()

summary = (
    df.groupby("city")
      .agg(
          orders=("order_id", "count"),
          users=("user_id", "nunique"),
          revenue=("amount", "sum"),
          avg_check=("amount", "mean"),
          median_check=("amount", "median"),
      )
      .sort_values("revenue", ascending=False)
      .reset_index()
)
print(summary)
```

Запись `имя=("столбец", "функция")` — самый читаемый способ агрегации: сразу видно, что и как посчитано. `reset_index()` превращает ключ группировки из индекса обратно в обычный столбец.

Группировка по нескольким полям:

```python
df.groupby(["month", "city"])["amount"].sum().reset_index()
```

Обрати внимание на оформление: длинную цепочку методов берут в круглые скобки и пишут по одному методу на строку. Так код читается сверху вниз, как рецепт.

### transform: аналог оконных функций

`transform` считает агрегат по группе, но возвращает столбец той же длины, что и исходная таблица, — как `OVER (PARTITION BY ...)` в SQL:

```python
df["city_revenue"] = df.groupby("city")["amount"].transform("sum")
df["share_in_city"] = df["amount"] / df["city_revenue"]

df = df.sort_values("date")
df["order_num"] = df.groupby("user_id").cumcount() + 1                # ROW_NUMBER
df["user_cum_amount"] = df.groupby("user_id")["amount"].cumsum()      # накопительный итог
df["prev_order_date"] = df.groupby("user_id")["date"].shift(1)        # LAG
df["rank_in_city"] = df.groupby("city")["amount"].rank(ascending=False, method="dense")
```

## 5.6. Сводные таблицы

```python
pivot = df.pivot_table(
    index="city",
    columns="category",
    values="amount",
    aggfunc="sum",
    fill_value=0,
    margins=True,        # добавить итоги
)
print(pivot)
```

`pd.crosstab(df["city"], df["category"])` — быстрый подсчёт количества по двум признакам.

### Длинный и широкий формат

`pivot_table` делает из длинной таблицы широкую. Обратное преобразование — `melt`:

```python
wide = df.pivot_table(index="month", columns="city", values="amount", aggfunc="sum").reset_index()
long = wide.melt(id_vars="month", var_name="city", value_name="revenue")
print(long.head())
```

Хранить и обрабатывать данные удобнее в длинном формате, показывать человеку — в широком.

## 5.7. Соединение таблиц

`merge` — это `JOIN`.

```python
users = pd.DataFrame({
    "user_id": np.arange(1, 121),
    "source": rng.choice(["реклама", "поиск", "друзья"], 120),
})

merged = df.merge(users, on="user_id", how="left")
print(merged.shape)
```

Параметр `how` принимает `"inner"`, `"left"`, `"right"`, `"outer"` — те же виды соединений, что в SQL. Если ключи называются по-разному, используй `left_on` и `right_on`.

Защита от размножения строк — параметр `validate`:

```python
merged = df.merge(users, on="user_id", how="left", validate="many_to_one")
```

Если в `users` окажутся дубликаты `user_id`, pandas сразу выдаст ошибку, а не молча увеличит таблицу. Используй `validate` всегда.

`concat` склеивает таблицы одинаковой структуры — например, файлы по месяцам:

```python
part1 = df[df["month"] == "2026-01"]
part2 = df[df["month"] == "2026-02"]
both = pd.concat([part1, part2], ignore_index=True)
```

## 5.8. Работа с датами

```python
daily = df.set_index("date")["amount"].resample("D").sum()    # выручка по дням
weekly = df.set_index("date")["amount"].resample("W").sum()   # по неделям

rolling = daily.rolling(7).mean()         # скользящее среднее за 7 дней
growth = weekly.pct_change()              # прирост к предыдущей неделе

first_order = df.groupby("user_id")["date"].min()
days_active = (df["date"].max() - first_order).dt.days
```

`resample` — это `groupby` по периодам времени. Он заполняет и дни без заказов (там будет 0) — обычный `groupby` такие дни просто пропустит, и на графике получится обман.

## 5.9. Повторяем мини-проект из главы 2

В главе 2 мы считали выручку по городам циклом и словарём. Теперь то же самое:

```python
result = (
    df.groupby("city", as_index=False)
      .agg(revenue=("amount", "sum"), avg_check=("amount", "mean"))
      .sort_values("revenue", ascending=False)
)
print(result)
```

Одна цепочка вместо десяти строк — и она так же работает на десяти миллионах заказов.

## 5.9а. Разбор: как решать задачу по шагам

Знать методы недостаточно — нужно уметь превратить вопрос в последовательность действий. Разберём один вопрос так, как это делает аналитик.

**Вопрос от менеджера:** «Какая доля выручки каждого месяца приходится на повторные заказы?»

### Шаг 1. Уточнить, что имеется в виду

- «Повторный заказ» — любой заказ пользователя, кроме его первого.
- «Месяц» — месяц, в котором сделан заказ.
- Нужна доля **выручки**, а не числа заказов.

Половина ошибок в анализе — от того, что аналитик и заказчик по-разному поняли вопрос. Проговори определения до того, как писать код.

### Шаг 2. Понять, как должен выглядеть ответ

Таблица: одна строка на месяц, столбцы — выручка всего, выручка от повторных заказов, доля. Когда видишь форму ответа, план почти очевиден.

### Шаг 3. Составить план словами

1. Для каждого заказа определить, первый он у пользователя или нет.
2. Добавить месяц заказа.
3. Сгруппировать по месяцу и посчитать выручку всего и выручку повторных.
4. Поделить одно на другое.

### Шаг 4. Написать код, проверяя каждый шаг

```python
df = pd.read_csv("orders.csv", parse_dates=["date"])

# 1. Номер заказа у пользователя. Сортировка обязательна: нумеруем по времени
df = df.sort_values(["user_id", "date", "order_id"])
df["order_num"] = df.groupby("user_id").cumcount() + 1
df["is_repeat"] = df["order_num"] > 1

# Проверка: первых заказов должно быть ровно столько, сколько пользователей
assert (~df["is_repeat"]).sum() == df["user_id"].nunique()
print(df[df["user_id"] == df["user_id"].iloc[0]][["user_id", "date", "order_num", "is_repeat"]])
```

Мы не просто добавили столбец, а сразу проверили его двумя способами: общим правилом (`assert`) и глазами — на заказах одного пользователя.

```python
# 2. Месяц и выручка от повторных заказов отдельным столбцом
df["month"] = df["date"].dt.to_period("M").astype(str)
df["repeat_amount"] = df["amount"].where(df["is_repeat"], 0)

# 3–4. Группировка и доля
result = (
    df.groupby("month")
      .agg(revenue=("amount", "sum"), repeat_revenue=("repeat_amount", "sum"), orders=("order_id", "count"))
      .assign(repeat_share=lambda d: d["repeat_revenue"] / d["revenue"])
)
print(result.round(3))
```

Приём `df["amount"].where(условие, 0)` оставляет значение там, где условие истинно, и ставит 0 в остальных строках. Сумма такого столбца — это «сумма по условию», аналог `SUM(CASE WHEN ... THEN amount ELSE 0 END)` в SQL.

### Шаг 5. Проверить результат на здравый смысл

```python
assert result["revenue"].sum() == df["amount"].sum()          # ничего не потеряли
assert result["repeat_share"].between(0, 1).all()             # доля — от 0 до 1
```

И посмотреть на числа: доля повторных заказов растёт от месяца к месяцу. Логично ли это? Да: в первом месяце наших данных почти все заказы — первые, потому что истории ещё нет.

### Шаг 6. Сформулировать ответ

Плохой ответ — таблица без слов. Хороший:

> Доля выручки от повторных заказов выросла с X % в январе до Y % в марте. Но рост во многом объясняется устройством данных: в январе у пользователей просто не было «прошлых» заказов. Чтобы оценить реальную склонность к повторным покупкам, нужен когортный анализ (глава 10).

Вторая часть ответа важнее первой. Аналитик не только считает число, но и предупреждает, как его **нельзя** интерпретировать.

### Что запомнить

- Сначала определения и форма ответа, потом код.
- План — словами, по шагам.
- После каждого шага — проверка: `assert`, `head()`, пример одного объекта.
- В конце — сверка итогов с исходными данными.
- Ответ — это вывод с оговорками, а не таблица.

## 5.10. Шпаргалка: SQL → pandas

| SQL | pandas |
|-----|--------|
| `SELECT a, b` | `df[["a", "b"]]` |
| `WHERE a > 5` | `df[df["a"] > 5]` |
| `ORDER BY a DESC` | `df.sort_values("a", ascending=False)` |
| `LIMIT 10` | `df.head(10)` |
| `COUNT(DISTINCT a)` | `df["a"].nunique()` |
| `GROUP BY a` | `df.groupby("a").agg(...)` |
| `HAVING` | фильтр после `agg` |
| `JOIN` | `df.merge(other, on=..., how=...)` |
| `UNION ALL` | `pd.concat([df1, df2])` |
| `CASE WHEN` | `np.where(...)` или `pd.cut(...)` |
| `SUM() OVER (PARTITION BY a)` | `df.groupby("a")["x"].transform("sum")` |
| `ROW_NUMBER() OVER (...)` | `df.groupby("a").cumcount() + 1` |
| `LAG(x)` | `df.groupby("a")["x"].shift(1)` |

## 5.11. Частые ошибки

- **`KeyError: 'Amount'`** — нет такого столбца. Проверь регистр и пробелы: `print(df.columns.tolist())`.
- **Числа прочитались как текст** — в `info()` у столбца тип `object`. Причина — запятая вместо точки или мусор в данных. Лечится в главе 6.
- **После `merge` стало больше строк** — в правой таблице дубликаты ключа.
- **Забыл присвоить результат.** Большинство методов возвращают новую таблицу, а не меняют старую: пиши `df = df.sort_values(...)`.
- **Цикл `for` по строкам.** Если пишешь `for i, row in df.iterrows()` — остановись и поищи векторный способ.

## Что дальше

Когда освоишься с материалом этой главы, переходи к углублённой: [Глава 5А. pandas: приёмы и рецепты](05a-pandas-priemy.md).

## Практика на GitHub

1. [guipsamora/pandas_exercises](https://github.com/guipsamora/pandas_exercises) — основной тренажёр. Папки пронумерованы по темам; проходи по порядку: знакомство с данными, фильтрация и сортировка, группировка, apply, соединения, статистика. В каждой папке есть ноутбук с заданиями и отдельный с решениями — решения открывай только после своей попытки.
2. [jakevdp/PythonDataScienceHandbook](https://github.com/jakevdp/PythonDataScienceHandbook) — глава 3 (ноутбуки с префиксом `03`): индексация, пропуски, группировка, сводные таблицы, даты.
3. [wesm/pydata-book](https://github.com/wesm/pydata-book) — ноутбуки `ch05`, `ch08`, `ch10`: основы, соединения и изменение формы, группировка. Это материалы к книге создателя pandas.
4. [jvns/pandas-cookbook](https://github.com/jvns/pandas-cookbook) — девять коротких глав на реальных данных. Хорош тем, что показывает ход мысли: «вот вопрос — вот как я иду к ответу».

## Задания

На файле `orders.csv`:

1. Какой город приносит больше всего выручки? А какой — самый высокий средний чек?
2. Найди 10 пользователей с максимальной суммой покупок.
3. Построй сводную таблицу: месяцы в строках, категории в столбцах, в значениях — число заказов.
4. Какая доля заказов дороже 5000 в каждой категории?
5. Для каждого пользователя найди дату первого заказа и число заказов. Сколько пользователей сделали только один заказ?
6. Посчитай выручку по неделям и её прирост к предыдущей неделе.
7. Добавь столбец с порядковым номером заказа у пользователя. Отличается ли средний чек первого заказа от повторных?
8. В какой день недели заказывают чаще всего?
9. Загрузи базу Chinook через `pd.read_sql` (раздел 3.9) и реши задания 1, 4 и 6 из главы 3 средствами pandas. Сравни с ответами SQL.

## Проверь себя

- Чем `loc` отличается от `iloc`?
- Чем `agg` отличается от `transform`?
- Что делает `reset_index()`?
- Как убедиться, что `merge` не размножил строки?
- Почему для временных рядов лучше `resample`, чем `groupby`?
- Чем длинный формат отличается от широкого?

## Решения

Во всех решениях данные загружаются так:

```python
import numpy as np
import pandas as pd

df = pd.read_csv("orders.csv", parse_dates=["date"])
```

Числа в твоих ответах совпадут с числами у других читателей, потому что генератор в разделе 5.1 создан с фиксированным зерном.

### Задание 1. Выручка и средний чек по городам

```python
by_city = (
    df.groupby("city")
      .agg(revenue=("amount", "sum"), avg_check=("amount", "mean"), orders=("order_id", "count"))
      .sort_values("revenue", ascending=False)
)
print(by_city)

print("Больше всего выручки:", by_city["revenue"].idxmax())
print("Самый высокий средний чек:", by_city["avg_check"].idxmax())
```

`idxmax` возвращает подпись строки с максимумом — здесь это название города. Обрати внимание, что ответы на два вопроса могут не совпасть: город с самой большой выручкой лидирует за счёт **количества** заказов, а не их размера. Поэтому столбец `orders` в таблице не лишний.

### Задание 2. Десять лучших пользователей

```python
top_users = (
    df.groupby("user_id")["amount"]
      .sum()
      .nlargest(10)
      .reset_index(name="total")
)
print(top_users)
```

`nlargest(10)` заменяет связку `sort_values(ascending=False).head(10)`.

### Задание 3. Сводная: месяцы × категории

```python
df["month"] = df["date"].dt.to_period("M").astype(str)

pivot = df.pivot_table(
    index="month",
    columns="category",
    values="order_id",
    aggfunc="count",
    fill_value=0,
    margins=True,
    margins_name="Итого",
)
print(pivot)
```

Для подсчёта количества в `values` можно указать любой столбец без пропусков. Короткая запись того же: `pd.crosstab(df["month"], df["category"], margins=True)`.

### Задание 4. Доля крупных заказов по категориям

```python
share = (df["amount"] > 5000).groupby(df["category"]).mean()
print(share.round(3))
```

Сравнение даёт столбец из `True` и `False`, а среднее от него — это доля `True`. Группировать можно по столбцу, которого нет в самом объекте: достаточно передать его в `groupby`.

Более длинный, но и более наглядный вариант:

```python
df["is_big"] = df["amount"] > 5000
print(df.groupby("category").agg(orders=("order_id", "count"), big_share=("is_big", "mean")))
```

### Задание 5. Первый заказ и число заказов

```python
users = df.groupby("user_id").agg(
    first_order=("date", "min"),
    orders=("order_id", "count"),
)
print(users.head())

one_order = (users["orders"] == 1).sum()
print(f"Только один заказ: {one_order} из {len(users)} ({one_order / len(users):.1%})")
```

### Задание 6. Выручка по неделям и прирост

```python
weekly = (
    df.set_index("date")["amount"]
      .resample("W")
      .sum()
      .to_frame("revenue")
)
weekly["growth"] = weekly["revenue"].pct_change()
print(weekly.round(3))
```

У первой недели прирост `NaN` — сравнивать не с чем. Первая и последняя недели обычно неполные (данные начинаются и заканчиваются не в понедельник), поэтому их прирост обманчив. Перед выводами их стоит отбросить: `weekly.iloc[1:-1]`.

### Задание 7. Первый заказ против повторных

```python
df = df.sort_values(["user_id", "date"])
df["order_num"] = df.groupby("user_id").cumcount() + 1
df["order_type"] = np.where(df["order_num"] == 1, "первый", "повторный")

print(df.groupby("order_type")["amount"].agg(["count", "mean", "median"]).round(0))
```

Сортировка перед `cumcount` обязательна: нумерация идёт в том порядке, в каком строки лежат в таблице.

В наших данных суммы заказов сгенерированы случайно и от номера заказа не зависят, поэтому различие между группами будет небольшим и случайным. Как отличить случайную разницу от настоящей — тема главы 9.

### Задание 8. День недели

```python
order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

by_weekday = df["date"].dt.day_name().value_counts().reindex(order)
print(by_weekday)
print("Чаще всего:", by_weekday.idxmax())
```

`value_counts` сортирует по убыванию частоты. `reindex(order)` расставляет дни в календарном порядке — для таблицы и графика это удобнее.

### Задание 9. Chinook средствами pandas

Загружаем таблицы целиком и повторяем логику запросов:

```python
import sqlite3

conn = sqlite3.connect("Chinook_Sqlite.sqlite")
customers = pd.read_sql("SELECT * FROM Customer", conn)
invoices = pd.read_sql("SELECT * FROM Invoice", conn, parse_dates=["InvoiceDate"])
lines = pd.read_sql("SELECT * FROM InvoiceLine", conn)
tracks = pd.read_sql("SELECT * FROM Track", conn)
genres = pd.read_sql("SELECT * FROM Genre", conn)
conn.close()

# Задание 1 главы 3: клиенты по странам
print(customers["Country"].value_counts().head())

# Задание 4: выручка по годам
print(invoices.groupby(invoices["InvoiceDate"].dt.year)["Total"].sum().round(2))

# Задание 6: самый популярный жанр в каждой стране
sales = (
    lines
    .merge(invoices[["InvoiceId", "BillingCountry"]], on="InvoiceId", validate="many_to_one")
    .merge(tracks[["TrackId", "GenreId"]], on="TrackId", validate="many_to_one")
    .merge(genres.rename(columns={"Name": "Genre"}), on="GenreId", validate="many_to_one")
)
genre_sales = sales.groupby(["BillingCountry", "Genre"], as_index=False)["Quantity"].sum()

top_genre = (
    genre_sales
    .sort_values(["BillingCountry", "Quantity"], ascending=[True, False])
    .drop_duplicates("BillingCountry")           # первая строка каждой страны = лидер
)
print(top_genre.head(10))
```

Приём «отсортировать и взять первую строку группы через `drop_duplicates`» — pandas-аналог `ROW_NUMBER() ... WHERE rn = 1`.

Сравни результаты с ответами SQL: они должны совпасть. Если при равенстве продаж лидер отличается — это не ошибка, а разный порядок среди равных.

В реальной работе загружать таблицы целиком нельзя — они слишком большие. Там соединения и группировки делают в SQL, а в pandas забирают уже готовый небольшой результат.
