# Глава 5А. pandas: приёмы и рецепты

Глава 5 научила основам. Здесь — то, чем пользуются каждый день после первого месяца работы: рецепты для типовых задач, приёмы для больших таблиц и ловушки, из-за которых получаются неверные числа.

Данные для главы — таблица заказов из раздела 5.1 и небольшой справочник пользователей:

```python
import numpy as np
import pandas as pd

df = pd.read_csv("orders.csv", parse_dates=["date"])

rng = np.random.default_rng(7)
users = pd.DataFrame({
    "user_id": np.arange(1, 121),
    "source": rng.choice(["реклама", "поиск", "друзья"], 120, p=[0.5, 0.3, 0.2]),
    "signup": pd.Timestamp("2025-12-01") + pd.to_timedelta(rng.integers(0, 60, 120), unit="D"),
})
```

## 5А.1. Типы данных и память

Правильные типы — это не аккуратность ради аккуратности: от них зависят скорость, память и корректность расчётов.

```python
df.info(memory_usage="deep")
print(df.memory_usage(deep=True))        # байт на каждый столбец
```

<!-- result -->
*Результат:*

```output
<class 'pandas.DataFrame'>
RangeIndex: 500 entries, 0 to 499
Data columns (total 6 columns):
 #   Column    Non-Null Count  Dtype         
---  ------    --------------  -----         
 0   order_id  500 non-null    int64         
 1   date      500 non-null    datetime64[us]
 2   user_id   500 non-null    int64         
 3   city      500 non-null    str           
 4   category  500 non-null    str           
 5   amount    500 non-null    float64       
dtypes: datetime64[us](1), float64(1), int64(2), str(2)
memory usage: 34.8 KB
Index        132
order_id    4000
date        4000
user_id     4000
city        9556
category    9986
amount      4000
dtype: int64
```
<!-- /result -->



Текстовые столбцы — самые тяжёлые. В `info()` у них тип `str` (в pandas 3) или `object` (в более старых версиях). Если уникальных значений мало, преврати столбец в **категорию**: значения хранятся один раз, а в таблице лежат короткие числовые коды.

```python
before = df.memory_usage(deep=True).sum()

df["city"] = df["city"].astype("category")
df["category"] = df["category"].astype("category")
df["user_id"] = pd.to_numeric(df["user_id"], downcast="integer")
df["amount"] = pd.to_numeric(df["amount"], downcast="float")

after = df.memory_usage(deep=True).sum()
print(f"было {before / 1024:.0f} КБ, стало {after / 1024:.0f} КБ")
```

<!-- result -->
*Результат:*

```output
было 35 КБ, стало 11 КБ
```
<!-- /result -->



Что даёт тип `category`:

- память сокращается в разы, группировки ускоряются;
- можно задать **порядок** значений — он будет использоваться при сортировке и на графиках:

```python
sizes = pd.Categorical(
    ["средний", "мелкий", "крупный", "мелкий"],
    categories=["мелкий", "средний", "крупный"],
    ordered=True,
)
print(pd.Series(sizes).sort_values().tolist())     # по смыслу, а не по алфавиту
print(pd.Series(sizes).max())
```

<!-- result -->
*Результат:*

```output
['мелкий', 'мелкий', 'средний', 'крупный']
крупный
```
<!-- /result -->



Обратная сторона: при группировке по категории pandas может показать и те значения, которых в данных нет. Пиши `groupby(..., observed=True)`, чтобы видеть только встретившиеся.

### Типы сразу при чтении

Быстрее всего задать типы прямо в `read_csv` — таблица не будет создаваться дважды:

```python
df = pd.read_csv(
    "orders.csv",
    parse_dates=["date"],
    dtype={"city": "category", "category": "category", "user_id": "int32"},
    usecols=["order_id", "date", "user_id", "city", "category", "amount"],
)
```

### Parquet вместо CSV

CSV — текстовый формат: он большой, медленный и не хранит типы (даты приходится разбирать при каждом чтении). Для промежуточных результатов используй **Parquet**:

```python
df.to_parquet("orders.parquet")              # нужна библиотека: pip install pyarrow
df = pd.read_parquet("orders.parquet")
print(df.dtypes)                             # типы, включая даты и категории, сохранились
```

<!-- result -->
*Результат:*

```output
order_id             int64
date        datetime64[us]
user_id              int32
city              category
category          category
amount             float64
dtype: object
```
<!-- /result -->



| | CSV | Parquet |
|---|---|---|
| Размер | Большой | В 5–10 раз меньше |
| Скорость чтения | Медленно | Быстро |
| Типы столбцов | Теряются | Сохраняются |
| Чтение части столбцов | Читает всё | `columns=[...]` читает только нужные |
| Открыть глазами | Можно | Нельзя |

Правило: сырые данные оставляй как получил, обмен с людьми — CSV или Excel, всё промежуточное — Parquet.

## 5А.2. Условная логика без циклов

Пять способов создать столбец по условию — от простого к сложному.

```python
# 1. Два варианта — np.where
df["segment"] = np.where(df["amount"] >= 5000, "крупный", "обычный")

# 2. Несколько условий — np.select: условия проверяются по порядку, берётся первое истинное
conditions = [
    df["amount"] >= 10000,
    df["amount"] >= 5000,
    df["amount"] >= 1000,
]
df["tier"] = np.select(conditions, ["vip", "крупный", "средний"], default="мелкий")

# 3. Числовые интервалы — pd.cut (границы задаёшь сам)
df["bucket"] = pd.cut(df["amount"], bins=[0, 1000, 5000, 10000, np.inf],
                      labels=["до 1 тыс.", "1–5 тыс.", "5–10 тыс.", "от 10 тыс."], right=False)

# 4. Равные по числу строк группы — pd.qcut
df["quartile"] = pd.qcut(df["amount"], q=4, labels=["Q1", "Q2", "Q3", "Q4"])

# 5. Замена значений по словарю — map
region = {"Москва": "Центр", "Казань": "Поволжье", "Самара": "Поволжье", "Уфа": "Урал"}
df["region"] = df["city"].astype(str).map(region)

print(df[["amount", "segment", "tier", "bucket", "quartile", "region"]].head())
```

<!-- result -->
*Результат:*

```output
   amount  segment     tier     bucket quartile    region
0    78.0  обычный   мелкий  до 1 тыс.       Q1      Урал
1   377.0  обычный   мелкий  до 1 тыс.       Q1  Поволжье
2   826.0  обычный   мелкий  до 1 тыс.       Q1  Поволжье
3  2415.0  обычный  средний   1–5 тыс.       Q2  Поволжье
4  3383.0  обычный  средний   1–5 тыс.       Q3  Поволжье
```
<!-- /result -->



Тонкости:

- `map` возвращает `NaN` для значений, которых нет в словаре. Это удобно: `df["region"].isna().sum()` сразу покажет, что в справочнике чего-то не хватает.
- `right=False` в `pd.cut` означает, что левая граница входит в интервал, правая — нет: `[0, 1000)`. Всегда проверяй, куда попадают значения ровно на границе.
- `np.select` — аналог `CASE WHEN` из SQL, с той же логикой «первое подошедшее условие».

Ещё два полезных метода:

```python
df["amount_capped"] = df["amount"].clip(upper=df["amount"].quantile(0.99))   # обрезать хвост
df["big_amount"] = df["amount"].where(df["amount"] >= 5000)                  # остальное → NaN
df["repeat_amount"] = df["amount"].mask(df["amount"] < 1000, 0)              # заменить по условию
```

`where` **оставляет** значения, где условие истинно; `mask` — наоборот, **заменяет** их.

## 5А.3. Группировка: всё, что нужно знать

### Четыре вида операций над группами

| Операция | Что возвращает | Пример |
|----------|----------------|--------|
| `agg` | Одну строку на группу | Выручка по городам |
| `transform` | Столбец исходной длины | Доля заказа в выручке города |
| `filter` | Исходные строки, но только из подходящих групп | Заказы пользователей с 5+ заказами |
| `apply` | Что угодно | Нестандартная логика; медленно |

```python
# agg: несколько функций и собственная функция
stats = df.groupby("city", observed=True).agg(
    orders=("order_id", "count"),
    buyers=("user_id", "nunique"),
    revenue=("amount", "sum"),
    median_check=("amount", "median"),
    p90=("amount", lambda s: s.quantile(0.9)),
    big_share=("amount", lambda s: (s >= 5000).mean()),
)
print(stats.round(2))

# transform: значение группы возвращается на каждую строку
df["city_revenue"] = df.groupby("city", observed=True)["amount"].transform("sum")
df["share_in_city"] = df["amount"] / df["city_revenue"]
df["vs_city_median"] = df["amount"] / df.groupby("city", observed=True)["amount"].transform("median")

# filter: оставить строки только активных пользователей
active = df.groupby("user_id").filter(lambda g: len(g) >= 5)
print(len(df), len(active), active["user_id"].nunique())
```

<!-- result -->
*Результат:*

```output
        orders  buyers   revenue  median_check     p90  big_share
city                                                             
Казань      87      63  252482.0        2456.0  5289.4       0.13
Москва     254     104  775234.0        2691.5  5913.0       0.15
Самара      85      60  273076.0        2480.0  6501.2       0.22
Уфа         74      56  190422.0        2102.0  4509.1       0.05
500 301 48
```
<!-- /result -->



### Доля от итога

Одна из самых частых задач. Три варианта:

```python
revenue = df.groupby("city", observed=True)["amount"].sum()

print((revenue / revenue.sum()).round(3))                      # доля в общем итоге

by_month_city = (
    df.assign(month=df["date"].dt.to_period("M"))
      .groupby(["month", "city"], observed=True)["amount"].sum()
)
share_in_month = by_month_city / by_month_city.groupby(level="month").transform("sum")
print(share_in_month.round(3).head(8))                          # доля города внутри месяца

print(pd.crosstab(df["city"], df["category"], values=df["amount"],
                  aggfunc="sum", normalize="index").round(3))   # доли по строкам
```

<!-- result -->
*Результат:*

```output
city
Казань    0.169
Москва    0.520
Самара    0.183
Уфа       0.128
Name: amount, dtype: float64
month    city  
2026-01  Казань    0.166
         Москва    0.494
         Самара    0.191
         Уфа       0.150
2026-02  Казань    0.180
         Москва    0.480
         Самара    0.246
         Уфа       0.094
Name: amount, dtype: float64
category  Книги  Одежда  Техника
city                            
Казань    0.295   0.389    0.316
Москва    0.385   0.271    0.344
Самара    0.293   0.388    0.319
Уфа       0.339   0.330    0.331
```
<!-- /result -->



Параметр `normalize` у `crosstab` и `value_counts` избавляет от ручного деления: `"index"` — доли по строкам, `"columns"` — по столбцам, `"all"` — от общего итога.

### Топ-N в каждой группе

```python
top2 = (
    df.sort_values("amount", ascending=False)
      .groupby("city", observed=True)
      .head(2)
      [["city", "order_id", "amount"]]
      .sort_values(["city", "amount"], ascending=[True, False])
)
print(top2)
```

<!-- result -->
*Результат:*

```output
       city  order_id   amount
218  Казань       219  10556.0
496  Казань       497   9571.0
237  Москва       238  10494.0
267  Москва       268   9964.0
411  Самара       412  13120.0
455  Самара       456  12243.0
273     Уфа       274  12842.0
66      Уфа        67  10171.0
```
<!-- /result -->



`groupby().head(n)` возвращает первые `n` строк каждой группы в текущем порядке сортировки. Это аналог `ROW_NUMBER() ... WHERE rn <= n`.

### Первое, последнее и «строка с максимумом»

```python
ordered = df.sort_values(["user_id", "date", "order_id"])

first_last = ordered.groupby("user_id").agg(
    first_date=("date", "first"),
    last_date=("date", "last"),
    first_amount=("amount", "first"),
    last_amount=("amount", "last"),
    orders=("order_id", "count"),
)
print(first_last.head())

# Целая строка с максимальной суммой у каждого пользователя
best_order = df.loc[df.groupby("user_id")["amount"].idxmax()]
print(best_order[["user_id", "order_id", "date", "amount"]].head())
```

<!-- result -->
*Результат:*

```output
        first_date  last_date  first_amount  last_amount  orders
user_id                                                         
1       2026-01-14 2026-03-31        4511.0       1661.0       6
2       2026-01-19 2026-03-22        2257.0        907.0       4
3       2026-01-29 2026-02-26        4058.0       2843.0       2
4       2026-01-15 2026-02-19        1962.0       3053.0       2
5       2026-02-06 2026-03-25        3347.0       1963.0       4
     user_id  order_id       date  amount
345        1       346 2026-01-24  5062.0
300        2       301 2026-02-02  4045.0
320        3       321 2026-01-29  4058.0
329        4       330 2026-02-19  3053.0
343        5       344 2026-02-16  5058.0
```
<!-- /result -->



`idxmax` возвращает индекс строки с максимумом, а `loc` достаёт по этим индексам строки целиком.

### Номера, накопления и сдвиги внутри группы

```python
ordered = df.sort_values(["user_id", "date", "order_id"]).copy()
g = ordered.groupby("user_id")

ordered["order_num"] = g.cumcount() + 1                    # номер заказа
ordered["cum_amount"] = g["amount"].cumsum()               # накопительная сумма
ordered["prev_date"] = g["date"].shift(1)                  # дата предыдущего заказа
ordered["days_since_prev"] = (ordered["date"] - ordered["prev_date"]).dt.days
ordered["amount_change"] = g["amount"].diff()              # разница с предыдущим
ordered["rank_in_user"] = g["amount"].rank(method="dense", ascending=False)
ordered["is_last"] = g.cumcount(ascending=False) == 0      # последний заказ пользователя

print(ordered[["user_id", "date", "amount", "order_num", "cum_amount", "days_since_prev"]].head(8))
print("Медианный интервал между заказами:", ordered["days_since_prev"].median())
```

<!-- result -->
*Результат:*

```output
     user_id       date  amount  order_num  cum_amount  days_since_prev
272        1 2026-01-14  4511.0          1      4511.0              NaN
345        1 2026-01-24  5062.0          2      9573.0             10.0
74         1 2026-03-03  4727.0          3     14300.0             38.0
206        1 2026-03-10  4900.0          4     19200.0              7.0
344        1 2026-03-23   600.0          5     19800.0             13.0
400        1 2026-03-31  1661.0          6     21461.0              8.0
338        2 2026-01-19  2257.0          1      2257.0              NaN
300        2 2026-02-02  4045.0          2      6302.0             14.0
Медианный интервал между заказами: 12.0
```
<!-- /result -->



Перед любыми операциями «по порядку» таблицу нужно **отсортировать**: `cumcount`, `shift`, `diff`, `first` и `last` работают в том порядке, в каком лежат строки.

### Ловушки группировки

- **Пропуски в ключе пропадают.** По умолчанию строки с `NaN` в столбце группировки молча исключаются. Чтобы увидеть их отдельной группой, пиши `groupby(..., dropna=False)`.
- **`count` против `size`.** `size()` считает строки, `count()` — непустые значения. Числа различаются, если в столбце есть пропуски.
- **Среднее средних.** Средний чек по городам и среднее из этих средних — разные числа: города с малым числом заказов получают тот же вес, что и крупные. Усредняй исходные строки или считай взвешенное среднее.

```python
by_city = df.groupby("city", observed=True)["amount"].agg(["mean", "size"])
print(round(by_city["mean"].mean(), 1))                                   # среднее средних — неверно
print(round(df["amount"].mean(), 1))                                      # настоящее среднее
print(round(np.average(by_city["mean"], weights=by_city["size"]), 1))     # взвешенное — совпадает
```

<!-- result -->
*Результат:*

```output
2935.0
2982.4
2982.4
```
<!-- /result -->



## 5А.4. Индексы и MultiIndex

Индекс — подписи строк. Обычно это просто номера, но после группировки по нескольким столбцам появляется **многоуровневый** индекс, и с ним нужно уметь обращаться.

```python
multi = (
    df.assign(month=df["date"].dt.to_period("M").astype(str))
      .groupby(["month", "city"], observed=True)["amount"]
      .sum()
)
print(multi.head(6))

print(multi.loc["2026-01"])                       # срез по первому уровню
print(multi.loc[("2026-01", "Москва")])           # одно значение
print(multi.xs("Москва", level="city"))           # срез по второму уровню

wide = multi.unstack("city")                      # уровень индекса → столбцы
print(wide)
print(wide.stack().head(4))                       # обратно в длинный вид
```

<!-- result -->
*Результат:*

```output
month    city  
2026-01  Казань     80609.0
         Москва    240206.0
         Самара     92835.0
         Уфа        72740.0
2026-02  Казань     82804.0
         Москва    221191.0
Name: amount, dtype: float64
city
Казань     80609.0
Москва    240206.0
Самара     92835.0
Уфа        72740.0
Name: amount, dtype: float64
240206.0
month
2026-01    240206.0
2026-02    221191.0
2026-03    313837.0
Name: amount, dtype: float64
city      Казань    Москва    Самара      Уфа
month                                        
2026-01  80609.0  240206.0   92835.0  72740.0
2026-02  82804.0  221191.0  113668.0  43504.0
2026-03  89069.0  313837.0   66573.0  74178.0
month    city  
2026-01  Казань     80609.0
         Москва    240206.0
         Самара     92835.0
         Уфа        72740.0
… (ещё 1 строк)
```
<!-- /result -->



`unstack` и `stack` — пара взаимно обратных операций: первая разворачивает уровень индекса в столбцы (получается сводная таблица), вторая сворачивает обратно.

Практический совет: если MultiIndex мешает, избавляйся от него сразу — `reset_index()` или `groupby(..., as_index=False)`. С плоской таблицей работать проще.

После `agg` с несколькими функциями многоуровневыми становятся **названия столбцов**. Их удобно «сплющить»:

```python
flat = df.pivot_table(index="city", columns="category", values="amount",
                      aggfunc=["sum", "count"], observed=True)
flat.columns = [f"{func}_{category}" for func, category in flat.columns]
print(flat.head())
```

<!-- result -->
*Результат:*

```output
        sum_Книги  sum_Одежда  sum_Техника  count_Книги  count_Одежда  count_Техника
city                                                                                
Казань    74484.0     98108.0      79890.0           23            35             29
Москва   298748.0    209818.0     266668.0          100            71             83
Самара    80118.0    105896.0      87062.0           25            26             34
Уфа       64635.0     62757.0      63030.0           26            27             21
```
<!-- /result -->



Именованная агрегация из главы 5 (`имя=("столбец", "функция")`) хороша как раз тем, что не создаёт многоуровневых названий.

## 5А.5. Соединения: приёмы и ловушки

### Проверка соединения: indicator

Параметр `indicator=True` добавляет столбец `_merge`, который говорит, откуда строка: из обеих таблиц, только из левой или только из правой.

```python
users_part = users[users["user_id"] <= 100]           # сделаем справочник неполным

checked = df.merge(users_part, on="user_id", how="outer", indicator=True)
print(checked["_merge"].value_counts())
```

<!-- result -->
*Результат:*

```output
_merge
both          414
left_only      86
right_only      3
Name: count, dtype: int64
```
<!-- /result -->



Это лучшая диагностика перед любым анализом: сразу видно, сколько заказов осталось без пользователя и сколько пользователей без заказов.

### Антисоединение

Строки левой таблицы, которым не нашлось пары, — аналог `LEFT JOIN ... WHERE right.id IS NULL`:

```python
orphans = (
    df.merge(users_part[["user_id"]], on="user_id", how="left", indicator=True)
      .query("_merge == 'left_only'")
      .drop(columns="_merge")
)
print(len(orphans), "заказов без пользователя в справочнике")

# То же проще, если нужен только фильтр
orphans_simple = df[~df["user_id"].isin(users_part["user_id"])]
assert len(orphans) == len(orphans_simple)
```

<!-- result -->
*Результат:*

```output
86 заказов без пользователя в справочнике
```
<!-- /result -->



`isin` и `~isin` — самый быстрый способ отфильтровать таблицу по списку значений из другой таблицы.

### validate

```python
merged = df.merge(users, on="user_id", how="left", validate="many_to_one")
assert len(merged) == len(df)
```

Четыре значения `validate`: `"one_to_one"`, `"one_to_many"`, `"many_to_one"`, `"many_to_many"`. Указывай всегда: если в справочнике окажутся дубликаты ключа, получишь ошибку сразу, а не завышенную выручку через неделю.

### Соединение по ближайшему значению: merge_asof

Задача: к каждому заказу подтянуть курс валюты, **действовавший на момент заказа**, хотя курс обновлялся не каждый день. Обычный `merge` требует точного совпадения, `merge_asof` берёт ближайшее предыдущее значение.

```python
rates = pd.DataFrame({
    "date": pd.to_datetime(["2026-01-01", "2026-01-20", "2026-02-10", "2026-03-05"]),
    "usd_rate": [90.0, 92.5, 89.0, 91.2],
})

with_rate = pd.merge_asof(
    df.sort_values("date"),
    rates.sort_values("date"),
    on="date",
    direction="backward",          # последнее значение не позже даты заказа
)
with_rate["amount_usd"] = with_rate["amount"] / with_rate["usd_rate"]
with_rate["amount_usd"] = with_rate["amount_usd"].round(2)
print(with_rate[["date", "amount", "usd_rate", "amount_usd"]].iloc[::100])
```

<!-- result -->
*Результат:*

```output
          date  amount  usd_rate  amount_usd
0   2026-01-01  3712.0      90.0       41.24
100 2026-01-18  3516.0      90.0       39.07
200 2026-02-07  2804.0      92.5       30.31
300 2026-02-23  2321.0      89.0       26.08
400 2026-03-12  2271.0      91.2       24.90
```
<!-- /result -->



Обе таблицы должны быть отсортированы по ключу. Тем же приёмом находят последнюю цену, действовавший тариф, ближайшее предшествующее событие. Параметр `by="user_id"` ищет ближайшее значение отдельно для каждого пользователя.

### Все комбинации: cross join

```python
cities = pd.DataFrame({"city": ["Москва", "Казань", "Уфа", "Самара"]})
months = pd.DataFrame({"month": ["2026-01", "2026-02", "2026-03"]})

grid = cities.merge(months, how="cross")
print(len(grid))                                  # 12 — каждая пара «город, месяц»
```

<!-- result -->
*Результат:*

```output
12
```
<!-- /result -->



Зачем это нужно: в отчёте должны быть **все** комбинации, включая те, где продаж не было. Строим полную сетку, присоединяем к ней факты через `left` и заполняем пропуски нулями.

```python
facts = (
    df.assign(month=df["date"].dt.to_period("M").astype(str), city=df["city"].astype(str))
      .groupby(["city", "month"], as_index=False)["amount"].sum()
)
report = grid.merge(facts, on=["city", "month"], how="left").fillna({"amount": 0})
print(report.head())
```

<!-- result -->
*Результат:*

```output
     city    month    amount
0  Москва  2026-01  240206.0
1  Москва  2026-02  221191.0
2  Москва  2026-03  313837.0
3  Казань  2026-01   80609.0
4  Казань  2026-02   82804.0
```
<!-- /result -->



### Склейка с пометкой источника

```python
jan = df[df["date"].dt.month == 1]
feb = df[df["date"].dt.month == 2]

combined = pd.concat([jan, feb], keys=["январь", "февраль"], names=["source"]).reset_index(level="source")
print(combined["source"].value_counts())
```

<!-- result -->
*Результат:*

```output
source
январь     174
февраль    149
Name: count, dtype: int64
```
<!-- /result -->



Типичный рабочий сценарий — собрать много файлов в одну таблицу:

```python
from pathlib import Path

frames = [
    pd.read_csv(path).assign(source_file=path.name)
    for path in sorted(Path(".").glob("orders_2026-*.csv"))
]
all_orders = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
```

Столбец с именем файла позволяет потом найти, откуда пришла подозрительная строка.

## 5А.6. Изменение формы таблицы

```python
monthly = (
    df.assign(month=df["date"].dt.to_period("M").astype(str), city=df["city"].astype(str))
      .groupby(["month", "city"], as_index=False)["amount"].sum()
)

wide = monthly.pivot(index="month", columns="city", values="amount")       # длинная → широкая
print(wide.round(0))

long = wide.reset_index().melt(id_vars="month", var_name="city", value_name="amount")  # обратно
print(long.head())
```

<!-- result -->
*Результат:*

```output
city      Казань    Москва    Самара      Уфа
month                                        
2026-01  80609.0  240206.0   92835.0  72740.0
2026-02  82804.0  221191.0  113668.0  43504.0
2026-03  89069.0  313837.0   66573.0  74178.0
     month    city    amount
0  2026-01  Казань   80609.0
1  2026-02  Казань   82804.0
2  2026-03  Казань   89069.0
3  2026-01  Москва  240206.0
4  2026-02  Москва  221191.0
```
<!-- /result -->



| Метод | Что делает | Особенность |
|-------|-----------|-------------|
| `pivot` | Длинная → широкая | Без агрегации: упадёт, если пара «индекс, столбец» повторяется |
| `pivot_table` | Длинная → широкая | С агрегацией: дубликаты сворачивает функцией |
| `melt` | Широкая → длинная | Обратная операция |
| `stack` / `unstack` | То же через индекс | Удобны после `groupby` |
| `explode` | Список в ячейке → отдельные строки | Для вложенных данных |

### explode

Когда в ячейке лежит список — теги, товары в заказе, ответы с множественным выбором:

```python
survey = pd.DataFrame({
    "user_id": [1, 2, 3],
    "interests": ["книги, техника", "одежда", "техника, одежда, книги"],
})

exploded = (
    survey.assign(interests=survey["interests"].str.split(", "))
          .explode("interests")
)
print(exploded)
print(exploded["interests"].value_counts())
```

<!-- result -->
*Результат:*

```output
   user_id interests
0        1     книги
0        1   техника
1        2    одежда
2        3   техника
2        3    одежда
2        3     книги
interests
книги      2
техника    2
одежда     2
Name: count, dtype: int64
```
<!-- /result -->



Вложенный JSON из API разворачивают функцией `pd.json_normalize(data, record_path=..., meta=[...])`.

## 5А.7. Даты и время

### Что можно достать из даты

```python
d = df["date"]

parts = pd.DataFrame({
    "date": d,
    "year": d.dt.year,
    "month": d.dt.month,
    "day": d.dt.day,
    "weekday": d.dt.dayofweek,                # 0 — понедельник
    "weekday_name": d.dt.day_name(),
    "is_weekend": d.dt.dayofweek >= 5,
    "week": d.dt.isocalendar().week,
    "quarter": d.dt.quarter,
    "month_start": d.dt.to_period("M").dt.start_time,
    "week_start": d.dt.to_period("W").dt.start_time,
})
print(parts.head(3).T)
```

<!-- result -->
*Результат:*

```output
                                0                    1                    2
date          2026-01-09 00:00:00  2026-03-11 00:00:00  2026-02-28 00:00:00
year                         2026                 2026                 2026
month                           1                    3                    2
day                             9                   11                   28
weekday                         4                    2                    5
weekday_name               Friday            Wednesday             Saturday
is_weekend                  False                False                 True
week                            2                   11                    9
quarter                         1                    1                    1
month_start   2026-01-01 00:00:00  2026-03-01 00:00:00  2026-02-01 00:00:00
week_start    2026-01-05 00:00:00  2026-03-09 00:00:00  2026-02-23 00:00:00
```
<!-- /result -->



Столбец «начало периода» (`month_start`, `week_start`) — самый удобный ключ группировки по времени: это настоящая дата, она правильно сортируется и корректно ложится на ось графика.

### Арифметика дат

```python
today = pd.Timestamp("2026-04-01")

print((today - df["date"]).dt.days.head(3))                        # дней назад
print((df["date"] + pd.Timedelta(days=30)).head(3))                # плюс 30 дней
print((df["date"] + pd.DateOffset(months=1)).head(3))              # плюс календарный месяц
print(pd.date_range("2026-01-01", "2026-01-10", freq="D"))         # ряд дат
print(pd.date_range("2026-01-01", periods=4, freq="W-MON"))        # четыре понедельника
```

<!-- result -->
*Результат:*

```output
0    82
1    21
2    32
Name: date, dtype: int64
0   2026-02-08
1   2026-04-10
2   2026-03-30
Name: date, dtype: datetime64[us]
0   2026-02-09
1   2026-04-11
2   2026-03-28
Name: date, dtype: datetime64[us]
DatetimeIndex(['2026-01-01', '2026-01-02', '2026-01-03', '2026-01-04', '2026-01-05', '2026-01-06',
               '2026-01-07', '2026-01-08', '2026-01-09', '2026-01-10'],
              dtype='datetime64[us]', freq='D')
DatetimeIndex(['2026-01-05', '2026-01-12', '2026-01-19', '2026-01-26'], dtype='datetime64[us]', freq='W-MON')
```
<!-- /result -->



`Timedelta` прибавляет фиксированное число дней, `DateOffset` — календарные единицы: к 31 января плюс месяц получится последний день февраля.

### Ресемплинг и окна

```python
daily = df.set_index("date")["amount"].resample("D").sum()

frame = pd.DataFrame({
    "revenue": daily,
    "ma_7": daily.rolling(7).mean(),                       # скользящее среднее за 7 дней
    "ma_7_min3": daily.rolling(7, min_periods=3).mean(),   # считать, если есть хотя бы 3 значения
    "cumulative": daily.cumsum(),                          # накопительный итог
    "expanding_mean": daily.expanding().mean(),            # среднее с начала ряда
    "ewm": daily.ewm(span=7).mean(),                       # экспоненциальное сглаживание
    "wow": daily.pct_change(7),                            # изменение к тому же дню прошлой недели
})
print(frame.round(1).tail(5))
```

<!-- result -->
*Результат:*

```output
            revenue     ma_7  ma_7_min3  cumulative  expanding_mean      ewm  wow
date                                                                             
2026-03-27   6696.0  14764.7    14764.7   1409181.0         16385.8  14217.0  1.5
2026-03-28  39444.0  19089.9    19089.9   1448625.0         16650.9  20523.7  3.3
2026-03-29  26046.0  20764.0    20764.0   1474671.0         16757.6  21904.3  0.8
2026-03-30    839.0  17696.7    17696.7   1475510.0         16578.8  16638.0 -1.0
2026-03-31  15704.0  19510.0    19510.0   1491214.0         16569.0  16404.5  4.2
```
<!-- /result -->



- `rolling(n)` — окно фиксированной ширины;
- `expanding()` — окно от начала до текущей строки;
- `ewm` — недавние значения весят больше; быстрее реагирует на изменения, чем обычное скользящее среднее;
- `pct_change(7)` на дневных данных сравнивает с тем же днём недели — честнее, чем сравнение со вчерашним днём.

Окно можно задать и в единицах времени — `rolling("7D")`. Тогда оно корректно работает даже при пропущенных днях.

### Сравнение периодов

```python
monthly = df.set_index("date")["amount"].resample("MS").sum().to_frame("revenue")
monthly["prev_month"] = monthly["revenue"].shift(1)
monthly["mom"] = monthly["revenue"].pct_change()
monthly["share_of_quarter"] = monthly["revenue"] / monthly["revenue"].sum()
print(monthly.round(3))
```

<!-- result -->
*Результат:*

```output
             revenue  prev_month    mom  share_of_quarter
date                                                     
2026-01-01  486390.0         NaN    NaN             0.326
2026-02-01  461167.0    486390.0 -0.052             0.309
2026-03-01  543657.0    461167.0  0.179             0.365
```
<!-- /result -->



Для сравнения с прошлым годом на месячных данных используют `shift(12)` и `pct_change(12)`.

Последний месяц или неделя в данных почти всегда **неполные**. Сравнивать неполный период с полным нельзя — либо отбрось его, либо сравнивай одинаковое число дней.

### Часовые пояса

```python
moment = pd.Series(pd.to_datetime(["2026-03-01 22:30", "2026-03-01 23:45"]))

utc = moment.dt.tz_localize("UTC")                      # «это время в UTC»
moscow = utc.dt.tz_convert("Europe/Moscow")             # перевести в московское
print(moscow.dt.date.tolist())                          # уже 2 марта
```

<!-- result -->
*Результат:*

```output
[datetime.date(2026, 3, 2), datetime.date(2026, 3, 2)]
```
<!-- /result -->



События в базах обычно хранятся в UTC. Если группировать по дням, не переведя время в нужный пояс, вечерние события уедут на другой день, и дневные метрики не сойдутся с отчётами коллег. Источник половины вопросов «почему у нас разные цифры».

## 5А.8. Строки и регулярные выражения

```python
raw = pd.DataFrame({
    "contact": ["Иван Петров <ivan@mail.ru>", "anna.s@yandex.ru", "Пётр (тел. +7 999 123-45-67)", None],
    "sku": ["BK-2024-0015", "TC-2025-0107", "bk-2024-0020", "CL-2023-0003"],
})

raw["email"] = raw["contact"].str.extract(r"([\w.+-]+@[\w-]+\.[\w.]+)")
raw["has_phone"] = raw["contact"].str.contains(r"\+7", na=False)
raw["digits"] = raw["contact"].str.replace(r"\D", "", regex=True)

raw[["sku_type", "sku_year", "sku_num"]] = raw["sku"].str.upper().str.split("-", expand=True)
raw["sku_year"] = raw["sku_year"].astype(int)

print(raw[["email", "has_phone", "sku_type", "sku_year", "sku_num"]])
```

<!-- result -->
*Результат:*

```output
              email  has_phone sku_type  sku_year sku_num
0      ivan@mail.ru      False       BK      2024    0015
1  anna.s@yandex.ru      False       TC      2025    0107
2               NaN       True       BK      2024    0020
3               NaN      False       CL      2023    0003
```
<!-- /result -->



- `str.extract` достаёт часть строки по шаблону; то, что в круглых скобках, становится столбцом;
- `str.contains(..., na=False)` — проверка наличия; `na=False` говорит считать пропуски как «не содержит», иначе в фильтре будет ошибка;
- `str.split(..., expand=True)` разносит части по отдельным столбцам.

Минимум регулярных выражений, которого хватает на 90 % задач:

| Шаблон | Значение | Шаблон | Значение |
|--------|----------|--------|----------|
| `\d` | Цифра | `+` | Один или больше |
| `\D` | Не цифра | `*` | Ноль или больше |
| `\w` | Буква, цифра или `_` | `?` | Ноль или один |
| `\s` | Пробельный символ | `{4}` | Ровно четыре |
| `.` | Любой символ | `^` и `$` | Начало и конец строки |
| `[абв]` | Один из символов | `(...)` | Группа для извлечения |
| `[^абв]` | Любой, кроме этих | `\|` | Или |

Шаблоны пиши в «сырых» строках — с буквой `r` перед кавычками, как в примере.

## 5А.9. Пропуски: продвинутые приёмы

```python
series = pd.Series([10.0, np.nan, np.nan, 40.0, np.nan, 60.0],
                   index=pd.date_range("2026-01-01", periods=6))

print(pd.DataFrame({
    "исходный": series,
    "ffill": series.ffill(),                       # протянуть последнее известное значение
    "bfill": series.bfill(),                       # взять следующее известное
    "ffill_limit": series.ffill(limit=1),          # не дальше чем на один шаг
    "interpolate": series.interpolate(),           # линейно между соседями
}))
```

<!-- result -->
*Результат:*

```output
            исходный  ffill  bfill  ffill_limit  interpolate
2026-01-01      10.0   10.0   10.0         10.0         10.0
2026-01-02       NaN   10.0   40.0         10.0         20.0
2026-01-03       NaN   10.0   40.0          NaN         30.0
2026-01-04      40.0   40.0   40.0         40.0         40.0
2026-01-05       NaN   40.0   60.0         40.0         50.0
2026-01-06      60.0   60.0   60.0         60.0         60.0
```
<!-- /result -->



- `ffill` подходит для состояний, которые сохраняются до изменения: цена, статус, остаток на складе.
- `interpolate` — для плавно меняющихся величин: температура, курс.
- Для событий и денег (заказы, выручка) пропуск обычно означает **ноль**, а не «как вчера».

Заполнение внутри групп — чтобы значения одного пользователя не перетекали к другому:

```python
panel = pd.DataFrame({
    "user_id": [1, 1, 1, 2, 2, 2],
    "plan": ["basic", None, None, None, "pro", None],
})
panel["plan_filled"] = panel.groupby("user_id")["plan"].ffill()
print(panel)
```

<!-- result -->
*Результат:*

```output
   user_id   plan plan_filled
0        1  basic       basic
1        1    NaN       basic
2        1    NaN       basic
3        2    NaN         NaN
4        2    pro         pro
5        2    NaN         pro
```
<!-- /result -->



У второго пользователя первая строка осталась пустой: до неё у него не было известных значений, и это правильно.

## 5А.10. Скорость

### Иерархия способов

От быстрого к медленному:

1. **Векторные операции** pandas и NumPy — `df["a"] * df["b"]`, `np.where`, методы `.str` и `.dt`.
2. **`map`** со словарём.
3. **`apply`** по столбцу.
4. **`apply(axis=1)`** по строкам — медленно.
5. **`iterrows()`** и цикл `for` — очень медленно.

Разница не в процентах, а в сотни раз:

```python
import time

big = pd.DataFrame({
    "price": np.random.default_rng(0).uniform(100, 1000, 200_000),
    "qty": np.random.default_rng(1).integers(1, 10, 200_000),
})

def timed(label, func):
    start = time.perf_counter()
    func()
    print(f"{label:<28} {time.perf_counter() - start:.4f} с")

timed("векторно", lambda: big["price"] * big["qty"])
timed("apply по строкам", lambda: big.head(20_000).apply(lambda r: r["price"] * r["qty"], axis=1))
timed("iterrows", lambda: [r["price"] * r["qty"] for _, r in big.head(20_000).iterrows()])
```

<!-- result -->
*Результат:*

```output
векторно                     0.0007 с
apply по строкам             0.0578 с
iterrows                     0.1696 с
```
<!-- /result -->



Два последних замера сделаны на таблице в десять раз меньше — и всё равно они намного медленнее.

Как переписать типичный `apply(axis=1)`:

```python
# Медленно
# df["label"] = df.apply(lambda r: "крупный в Москве" if r["city"] == "Москва" and r["amount"] > 5000 else "прочее", axis=1)

# Быстро
df["label"] = np.where((df["city"] == "Москва") & (df["amount"] > 5000), "крупный в Москве", "прочее")
```

### Большие файлы

```python
# 1. Читать только нужные столбцы и строки
sample = pd.read_csv("orders.csv", usecols=["city", "amount"], nrows=1000)

# 2. Читать по частям и сразу агрегировать
totals = {}
for chunk in pd.read_csv("orders.csv", usecols=["city", "amount"], chunksize=200):
    for city, value in chunk.groupby("city")["amount"].sum().items():
        totals[city] = totals.get(city, 0) + value
print(pd.Series(totals).round(0))
```

<!-- result -->
*Результат:*

```output
Казань    252482.0
Москва    775234.0
Самара    273076.0
Уфа       190422.0
dtype: float64
```
<!-- /result -->



Обработка по частям работает для операций, которые можно сложить: суммы, количества, минимумы и максимумы. Для медианы и числа уникальных значений она не годится.

### Когда pandas уже мало

- Данные лежат в базе — агрегируй в SQL и забирай готовый результат (раздел 3.9).
- Файл не помещается в память — **DuckDB** позволяет писать SQL прямо к файлам CSV и Parquet на диске, а **Polars** — библиотека с похожими на pandas идеями, но намного быстрее.
- Данных терабайты — это уже Spark и хранилища из главы 11.

Сначала проверь простое: нужные ли столбцы ты читаешь, правильные ли типы, нет ли `apply` по строкам. Обычно этого хватает.

## 5А.11. Ловушки, из-за которых получаются неверные числа

### Изменение копии

```python
moscow = df[df["city"] == "Москва"]
# moscow["discount"] = 0.1            # предупреждение SettingWithCopyWarning: меняем копию или оригинал?

moscow = df[df["city"] == "Москва"].copy()      # явно говорим: это отдельная таблица
moscow["discount"] = 0.1

df.loc[df["city"] == "Москва", "discount"] = 0.1    # а так меняется исходная таблица
```

Правило: вырезал часть таблицы и собираешься её менять — добавь `.copy()`. Хочешь изменить исходную таблицу по условию — используй `df.loc[условие, столбец] = значение`.

### Выравнивание по индексу

pandas совмещает данные **по подписям индекса**, а не по порядку строк. Обычно это удобно, но иногда даёт неожиданный результат:

```python
a = pd.Series([1, 2, 3], index=[0, 1, 2])
b = pd.Series([10, 20, 30], index=[1, 2, 3])
print(a + b)                 # NaN, 12, 23, NaN — сложились только совпавшие подписи
```

<!-- result -->
*Результат:*

```output
0     NaN
1    12.0
2    23.0
3     NaN
dtype: float64
```
<!-- /result -->



Отсюда типичная ошибка: отфильтровал или отсортировал таблицу, потом присвоил столбец из другой — и значения встали не на свои места или превратились в `NaN`. Лекарство — `reset_index(drop=True)` после фильтрации либо присваивание через `.to_numpy()`, когда нужно именно «по порядку».

### Сравнение с NaN

```python
s = pd.Series([1.0, np.nan, 3.0])

print((s == np.nan).sum())      # 0 — так пропуски не найти
print(s.isna().sum())           # 1
print((s > 2).sum(), (s <= 2).sum())   # 1 и 1: пропуск не попал никуда
```

<!-- result -->
*Результат:*

```output
0
1
1 1
```
<!-- /result -->



Строка с пропуском не проходит ни условие, ни его отрицание. Если доли «больше порога» и «не больше порога» не дают в сумме 100 % — ищи пропуски.

### Сравнение дробных чисел

```python
print(0.1 + 0.2 == 0.3)                    # False
print(np.isclose(0.1 + 0.2, 0.3))          # True
```

<!-- result -->
*Результат:*

```output
False
True
```
<!-- /result -->



Дробные числа хранятся приближённо. Для сравнений используй `np.isclose`, для денег — храни суммы в копейках целыми числами или округляй перед сравнением.

### inplace

Параметр `inplace=True` (`df.drop(..., inplace=True)`) не ускоряет код и ломает цепочки методов. Пиши `df = df.drop(...)`.

### Дубликаты в индексе

После `concat` без `ignore_index=True` подписи строк повторяются, и `df.loc[0]` внезапно возвращает несколько строк. Проверка: `df.index.is_unique`.

### Тихое изменение типа

Целочисленный столбец после появления пропусков становится дробным: `user_id` превращается в `101.0`, и соединение по нему с целочисленным ключом может не сработать. Используй тип `"Int64"` (с заглавной буквы) — он умеет хранить пропуски в целых числах:

```python
ids = pd.Series([1, 2, None])
print(ids.dtype, ids.astype("Int64").dtype)     # float64 Int64
```

<!-- result -->
*Результат:*

```output
float64 Int64
```
<!-- /result -->



## 5А.12. Рецепты аналитика

### Парето и ABC-анализ

Какие клиенты дают основную выручку:

```python
abc = (
    df.groupby("user_id")["amount"].sum()
      .sort_values(ascending=False)
      .to_frame("revenue")
)
abc["cum_share"] = abc["revenue"].cumsum() / abc["revenue"].sum()
abc["group"] = np.select([abc["cum_share"] <= 0.8, abc["cum_share"] <= 0.95], ["A", "B"], default="C")

summary = abc.groupby("group").agg(users=("revenue", "count"), revenue=("revenue", "sum"))
summary["users_share"] = summary["users"] / summary["users"].sum()
summary["revenue_share"] = summary["revenue"] / summary["revenue"].sum()
print(summary.round(3))
```

<!-- result -->
*Результат:*

```output
       users    revenue  users_share  revenue_share
group                                              
A         69  1189047.0        0.590          0.797
B         28   226169.0        0.239          0.152
C         20    75998.0        0.171          0.051
```
<!-- /result -->



Группа A — клиенты, дающие первые 80 % выручки, B — следующие 15 %, C — оставшиеся 5 %.

### Топ-N и «Прочие»

Чтобы на графике не было двадцати мелких столбцов:

```python
def top_n_with_other(series: pd.Series, n: int = 3, other: str = "Прочие") -> pd.Series:
    """Оставляет n самых частых значений, остальные заменяет на «Прочие»."""
    top = series.value_counts().nlargest(n).index
    return series.where(series.isin(top), other)

print(top_n_with_other(df["city"].astype(str), n=2).value_counts())
```

<!-- result -->
*Результат:*

```output
city
Москва    254
Прочие    159
Казань     87
Name: count, dtype: int64
```
<!-- /result -->



### Первая и повторная покупка

```python
first_date = df.groupby("user_id")["date"].transform("min")
df["is_first_order"] = df["date"] == first_date
df["days_from_first"] = (df["date"] - first_date).dt.days

print(df.groupby("is_first_order")["amount"].agg(["count", "mean", "median"]).round(0))
```

<!-- result -->
*Результат:*

```output
                count    mean  median
is_first_order                       
False             379  3079.0  2670.0
True              121  2680.0  2295.0
```
<!-- /result -->



`transform("min")` раздаёт дату первой покупки на каждую строку — после этого возраст клиента на момент заказа считается одним вычитанием.

Тонкость: если у пользователя в день первой покупки было два заказа, «первыми» окажутся оба. Поэтому первых заказов в таблице чуть больше, чем пользователей. Когда нужен ровно один первый заказ, используй нумерацию через `cumcount` из раздела 5А.3.

### Сравнение двух периодов

```python
period_a = df[df["date"].between("2026-01-01", "2026-01-31")]
period_b = df[df["date"].between("2026-02-01", "2026-02-28")]

def metrics(data: pd.DataFrame) -> pd.Series:
    return pd.Series({
        "выручка": data["amount"].sum(),
        "заказы": len(data),
        "покупатели": data["user_id"].nunique(),
        "средний чек": data["amount"].mean(),
        "заказов на покупателя": len(data) / data["user_id"].nunique(),
    })

comparison = pd.DataFrame({"январь": metrics(period_a), "февраль": metrics(period_b)})
comparison["изменение, %"] = (comparison["февраль"] / comparison["январь"] - 1) * 100
print(comparison.round(1))
```

<!-- result -->
*Результат:*

```output
                         январь   февраль  изменение, %
выручка                486390.0  461167.0          -5.2
заказы                    174.0     149.0         -14.4
покупатели                 96.0      84.0         -12.5
средний чек              2795.3    3095.1          10.7
заказов на покупателя       1.8       1.8          -2.1
```
<!-- /result -->



Функция `metrics` — единое определение метрик: одинаковый расчёт для любого среза данных. Это приём из главы 2В, и он же готовит к разложению «выручка = покупатели × заказов на покупателя × средний чек».

### Сессии из лога событий

Приём «флаг начала + накопительная сумма» из раздела 3А.10, только в pandas:

```python
log = pd.DataFrame({
    "user_id": [1, 1, 1, 1, 2, 2],
    "time": pd.to_datetime(["2026-03-01 10:00", "2026-03-01 10:05", "2026-03-01 15:30",
                            "2026-03-01 15:32", "2026-03-01 11:00", "2026-03-01 11:50"]),
}).sort_values(["user_id", "time"])

gap = log.groupby("user_id")["time"].diff()
log["new_session"] = gap.isna() | (gap > pd.Timedelta(minutes=30))
log["session_id"] = log.groupby("user_id")["new_session"].cumsum()

print(log)
print(log.groupby(["user_id", "session_id"])["time"].agg(["min", "max", "count"]))
```

<!-- result -->
*Результат:*

```output
   user_id                time  new_session  session_id
0        1 2026-03-01 10:00:00         True           1
1        1 2026-03-01 10:05:00        False           1
2        1 2026-03-01 15:30:00         True           2
3        1 2026-03-01 15:32:00        False           2
4        2 2026-03-01 11:00:00         True           1
5        2 2026-03-01 11:50:00         True           2
                                   min                 max  count
user_id session_id                                               
1       1          2026-03-01 10:00:00 2026-03-01 10:05:00      2
        2          2026-03-01 15:30:00 2026-03-01 15:32:00      2
2       1          2026-03-01 11:00:00 2026-03-01 11:00:00      1
        2          2026-03-01 11:50:00 2026-03-01 11:50:00      1
```
<!-- /result -->



### Проверки качества одной функцией

```python
def check_table(data: pd.DataFrame, key: str) -> None:
    """Быстрая диагностика таблицы перед анализом."""
    print(f"Строк: {len(data):,}, столбцов: {data.shape[1]}")
    print(f"Ключ «{key}» уникален: {data[key].is_unique}")
    print(f"Полных дубликатов: {data.duplicated().sum()}")
    missing = data.isna().mean()
    if missing.any():
        print("Доля пропусков:")
        print(missing[missing > 0].round(3).to_string())
    for column in data.select_dtypes("datetime").columns:
        print(f"{column}: от {data[column].min().date()} до {data[column].max().date()}")

check_table(df, key="order_id")
```

<!-- result -->
*Результат:*

```output
Строк: 500, столбцов: 21
Ключ «order_id» уникален: True
Полных дубликатов: 0
Доля пропусков:
big_amount    0.854
discount      0.492
date: от 2026-01-01 до 2026-03-31
```
<!-- /result -->



Заведи такую функцию в своём модуле и запускай на каждой новой таблице.

## 5А.13. Вывод и экспорт

### Оформление таблицы в ноутбуке

```python
report = df.groupby("city", observed=True).agg(
    orders=("order_id", "count"), revenue=("amount", "sum"), avg_check=("amount", "mean"),
)
report["share"] = report["revenue"] / report["revenue"].sum()

styled = (
    report.sort_values("revenue", ascending=False)
          .style
          .format({"revenue": "{:,.0f}", "avg_check": "{:,.0f}", "share": "{:.1%}"})
          .background_gradient(subset=["revenue"], cmap="Greens")
          .bar(subset=["share"], color="#b8d8cf")
)
styled          # отобразится оформленной таблицей в Jupyter; нужна библиотека: pip install jinja2
```

Форматирование через `.style` меняет только отображение: числа в таблице остаются числами. Не превращай их в строки вручную ради красивого вывода — с такими столбцами потом нельзя считать.

Настройки отображения:

```python
pd.set_option("display.max_columns", 50)            # показывать до 50 столбцов
pd.set_option("display.float_format", "{:,.2f}".format)
pd.reset_option("display.float_format")             # вернуть как было
```

### Экспорт

```python
report.to_csv("report.csv", encoding="utf-8-sig")     # utf-8-sig — чтобы Excel правильно показал кириллицу

with pd.ExcelWriter("report.xlsx") as writer:         # нужна библиотека: pip install openpyxl
    report.to_excel(writer, sheet_name="По городам")
    df.head(100).to_excel(writer, sheet_name="Примеры заказов", index=False)

print(report.round(2).to_markdown())                  # таблица для README; pip install tabulate
```

<!-- result -->
*Результат:*

```output
| city   |   orders |   revenue |   avg_check |   share |
|:-------|---------:|----------:|------------:|--------:|
| Казань |       87 |    252482 |     2902.09 |    0.17 |
| Москва |      254 |    775234 |     3052.1  |    0.52 |
| Самара |       85 |    273076 |     3212.66 |    0.18 |
| Уфа    |       74 |    190422 |     2573.27 |    0.13 |
```
<!-- /result -->



## Практика на GitHub

- [guipsamora/pandas_exercises](https://github.com/guipsamora/pandas_exercises) — разделы про группировку, `apply`, соединения и временные ряды: решай их, сознательно выбирая векторный способ вместо `apply`.
- [jakevdp/PythonDataScienceHandbook](https://github.com/jakevdp/PythonDataScienceHandbook) — в главе 3 ноутбуки про иерархическую индексацию, сводные таблицы, векторные строковые операции, временные ряды и высокопроизводительные `eval` и `query`.
- [wesm/pydata-book](https://github.com/wesm/pydata-book) — ноутбуки `ch07` (очистка и строки), `ch08` (соединения и изменение формы), `ch10` (группировка), `ch11` (временные ряды), `ch12` (категориальные данные и цепочки методов).
- [jvns/pandas-cookbook](https://github.com/jvns/pandas-cookbook) — главы про строковые операции и даты на реальных данных.
- [Yorko/mlcourse.ai](https://github.com/Yorko/mlcourse.ai) — в первой теме курса много приёмов группировки и сводных таблиц на задаче анализа оттока.

## Задания

На `orders.csv`, если не сказано иное:

1. Приведи столбцы к экономным типам и сохрани таблицу в Parquet. Во сколько раз сократилась память? Сравни размеры файлов CSV и Parquet.
2. Через `np.select` раздели заказы на четыре группы по сумме и посчитай для каждой долю в числе заказов и долю в выручке.
3. Для каждого города найди три категории-лидера по выручке и долю каждой в выручке города.
4. Для каждого пользователя посчитай число заказов, средний интервал между заказами в днях и число дней с последнего заказа до 1 апреля 2026 года.
5. Построй отчёт «город × месяц» с выручкой так, чтобы в нём были все комбинации, включая отсутствующие. Проверь, что итог совпадает с общей выручкой.
6. Посчитай выручку по дням, скользящее среднее за 7 дней и изменение к тому же дню предыдущей недели. В какой день недели выручка в среднем максимальна?
7. Проведи ABC-анализ по пользователям. Какую долю клиентов составляет группа A?
8. Дан столбец строк вида `"Заказ №1047 от 15.03.2026, сумма 12 450 руб."`. Извлеки номер, дату (как дату) и сумму (как число).
9. Перепиши без `apply`: `df.apply(lambda r: r["amount"] * 0.9 if r["category"] == "Книги" and r["amount"] > 3000 else r["amount"], axis=1)`.
10. Присоедини к заказам справочник `users` и найди канал привлечения с самым высоким средним числом заказов на пользователя. Убедись, что соединение не изменило число строк.

## Проверь себя

- Что даёт тип `category` и какая у него особенность при группировке?
- Чем `agg`, `transform` и `filter` отличаются друг от друга?
- Почему «среднее средних» даёт неверный результат?
- Что показывает `indicator=True` в `merge`?
- Когда нужен `merge_asof`?
- Чем `pivot` отличается от `pivot_table`?
- Чем `rolling` отличается от `expanding`?
- Почему `apply(axis=1)` медленный и чем его заменять?
- Что такое выравнивание по индексу и как оно может испортить результат?
- Как найти пропуски и почему `== np.nan` не работает?

## Решения

Во всех решениях данные загружаются так:

```python
import numpy as np
import pandas as pd

df = pd.read_csv("orders.csv", parse_dates=["date"])
```

### Задание 1. Типы и Parquet

```python
from pathlib import Path

before = df.memory_usage(deep=True).sum()

compact = df.astype({"city": "category", "category": "category"})
compact["order_id"] = pd.to_numeric(compact["order_id"], downcast="integer")
compact["user_id"] = pd.to_numeric(compact["user_id"], downcast="integer")
compact["amount"] = pd.to_numeric(compact["amount"], downcast="float")

after = compact.memory_usage(deep=True).sum()
print(f"Память: {before / 1024:.0f} → {after / 1024:.0f} КБ, в {before / after:.1f} раза меньше")

compact.to_parquet("orders.parquet")
csv_size = Path("orders.csv").stat().st_size
parquet_size = Path("orders.parquet").stat().st_size
print(f"Файлы: CSV {csv_size / 1024:.0f} КБ, Parquet {parquet_size / 1024:.0f} КБ")
```

<!-- result -->
*Результат:*

```output
Память: 35 → 9 КБ, в 4.1 раза меньше
Файлы: CSV 25 КБ, Parquet 12 КБ
```
<!-- /result -->



Основную экономию памяти дают два текстовых столбца. На таблице в 500 строк Parquet может выиграть у CSV немного или даже проиграть: у формата есть служебные данные фиксированного размера. Преимущество проявляется на сотнях тысяч строк.

### Задание 2. Группы по сумме

```python
conditions = [df["amount"] >= 10000, df["amount"] >= 5000, df["amount"] >= 1000]
df["tier"] = np.select(conditions, ["от 10 тыс.", "5–10 тыс.", "1–5 тыс."], default="до 1 тыс.")

order = ["до 1 тыс.", "1–5 тыс.", "5–10 тыс.", "от 10 тыс."]
tiers = df.groupby("tier").agg(orders=("order_id", "count"), revenue=("amount", "sum")).reindex(order)
tiers["orders_share"] = tiers["orders"] / tiers["orders"].sum()
tiers["revenue_share"] = tiers["revenue"] / tiers["revenue"].sum()
print(tiers.round(3))
```

<!-- result -->
*Результат:*

```output
            orders   revenue  orders_share  revenue_share
tier                                                     
до 1 тыс.       77   47371.0         0.154          0.032
1–5 тыс.       350  929784.0         0.700          0.624
5–10 тыс.       67  444633.0         0.134          0.298
от 10 тыс.       6   69426.0         0.012          0.047
```
<!-- /result -->



Условия в `np.select` идут от самого строгого к самому мягкому: берётся первое истинное. Обычно выясняется, что небольшая доля крупных заказов даёт непропорционально большую долю выручки — с этого наблюдения начинается разговор о сегментации.

### Задание 3. Категории-лидеры по городам

```python
by_city_category = df.groupby(["city", "category"], as_index=False)["amount"].sum()
by_city_category["share"] = (
    by_city_category["amount"] / by_city_category.groupby("city")["amount"].transform("sum")
)

top3 = (
    by_city_category.sort_values(["city", "amount"], ascending=[True, False])
                    .groupby("city")
                    .head(3)
)
print(top3.round(3))
```

<!-- result -->
*Результат:*

```output
      city category    amount  share
1   Казань   Одежда   98108.0  0.389
2   Казань  Техника   79890.0  0.316
0   Казань    Книги   74484.0  0.295
3   Москва    Книги  298748.0  0.385
5   Москва  Техника  266668.0  0.344
4   Москва   Одежда  209818.0  0.271
7   Самара   Одежда  105896.0  0.388
8   Самара  Техника   87062.0  0.319
6   Самара    Книги   80118.0  0.293
9      Уфа    Книги   64635.0  0.339
11     Уфа  Техника   63030.0  0.331
10     Уфа   Одежда   62757.0  0.330
```
<!-- /result -->



Долю считаем **до** отбора лидеров: иначе знаменателем стала бы сумма только по трём категориям. В наших данных категорий всего три, поэтому в результат попадут все — на настоящих данных список будет длиннее.

### Задание 4. Профиль пользователя

```python
REPORT_DATE = pd.Timestamp("2026-04-01")

ordered = df.sort_values(["user_id", "date", "order_id"]).copy()
ordered["gap_days"] = ordered.groupby("user_id")["date"].diff().dt.days

profile = ordered.groupby("user_id").agg(
    orders=("order_id", "count"),
    avg_gap_days=("gap_days", "mean"),
    last_order=("date", "max"),
)
profile["days_since_last"] = (REPORT_DATE - profile["last_order"]).dt.days
profile["avg_gap_days"] = profile["avg_gap_days"].round(1)
print(profile.head())

at_risk = profile[profile["days_since_last"] > 2 * profile["avg_gap_days"]]
print(f"Не покупали дольше двух своих обычных интервалов: {len(at_risk)}")
```

<!-- result -->
*Результат:*

```output
         orders  avg_gap_days last_order  days_since_last
user_id                                                  
1             6          15.2 2026-03-31                1
2             4          20.7 2026-03-22               10
3             2          28.0 2026-02-26               34
4             2          35.0 2026-02-19               41
5             4          15.7 2026-03-25                7
Не покупали дольше двух своих обычных интервалов: 30
```
<!-- /result -->



У пользователя с одним заказом `avg_gap_days` — `NaN`: интервала не существует. В сравнение для `at_risk` такие пользователи не попадут, и это корректно — для них нужен отдельный критерий.

### Задание 5. Полная сетка «город × месяц»

```python
df["month"] = df["date"].dt.to_period("M").astype(str)

grid = (
    pd.DataFrame({"city": df["city"].unique()})
      .merge(pd.DataFrame({"month": sorted(df["month"].unique())}), how="cross")
)
facts = df.groupby(["city", "month"], as_index=False)["amount"].sum()

report = grid.merge(facts, on=["city", "month"], how="left", validate="one_to_one").fillna({"amount": 0})

assert len(report) == df["city"].nunique() * df["month"].nunique()
assert np.isclose(report["amount"].sum(), df["amount"].sum())
print(report.pivot(index="city", columns="month", values="amount").round(0))
```

<!-- result -->
*Результат:*

```output
month    2026-01   2026-02   2026-03
city                                
Казань   80609.0   82804.0   89069.0
Москва  240206.0  221191.0  313837.0
Самара   92835.0  113668.0   66573.0
Уфа      72740.0   43504.0   74178.0
```
<!-- /result -->



Две проверки в конце: число строк равно произведению числа городов на число месяцев, а сумма совпадает с исходной. Сравнение через `np.isclose`, а не `==`: суммы дробных чисел, посчитанные в разном порядке, могут отличаться на погрешность.

### Задание 6. Дневная динамика

```python
daily = df.set_index("date")["amount"].resample("D").sum().to_frame("revenue")
daily["ma_7"] = daily["revenue"].rolling(7).mean()
daily["wow"] = daily["revenue"].pct_change(7)
print(daily.round(2).tail(7))

weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
by_weekday = daily.groupby(daily.index.day_name())["revenue"].mean().reindex(weekday_order)
print(by_weekday.round(0))
print("Максимум:", by_weekday.idxmax())
```

<!-- result -->
*Результат:*

```output
            revenue      ma_7   wow
date                               
2026-03-25  30012.0  12842.00  0.37
2026-03-26  17829.0  14194.29  1.13
2026-03-27   6696.0  14764.71  1.48
2026-03-28  39444.0  19089.86  3.30
2026-03-29  26046.0  20764.00  0.82
2026-03-30    839.0  17696.71 -0.96
2026-03-31  15704.0  19510.00  4.22
date
Monday       19020.0
Tuesday      14165.0
Wednesday    15617.0
Thursday     19831.0
Friday       13112.0
Saturday     15913.0
Sunday       18252.0
Name: revenue, dtype: float64
Максимум: Thursday
```
<!-- /result -->



Средняя выручка по дням недели считается от **дневного ряда**, а не от исходных заказов: нам нужна средняя сумма за день, а не средний чек. `resample` добавил дни без заказов с нулевой выручкой — без него они бы выпали, и среднее оказалось бы завышенным.

В наших данных дни недели различаются только случайно: в генераторе нет недельной сезонности.

### Задание 7. ABC-анализ

```python
abc = df.groupby("user_id")["amount"].sum().sort_values(ascending=False).to_frame("revenue")
abc["cum_share"] = abc["revenue"].cumsum() / abc["revenue"].sum()
abc["group"] = np.select([abc["cum_share"] <= 0.8, abc["cum_share"] <= 0.95], ["A", "B"], default="C")

summary = abc.groupby("group").agg(users=("revenue", "count"), revenue=("revenue", "sum"))
summary["users_share"] = summary["users"] / summary["users"].sum()
summary["revenue_share"] = summary["revenue"] / summary["revenue"].sum()
print(summary.round(3))
```

<!-- result -->
*Результат:*

```output
       users    revenue  users_share  revenue_share
group                                              
A         69  1189047.0        0.590          0.797
B         28   226169.0        0.239          0.152
C         20    75998.0        0.171          0.051
```
<!-- /result -->



Сортировка по убыванию перед `cumsum` обязательна — накопленная доля имеет смысл только в порядке от крупнейшего клиента.

В учебных данных группа A окажется большой — около половины клиентов или больше. Суммы и число заказов сгенерированы без «китов», поэтому выручка распределена довольно равномерно. В настоящем бизнесе группа A обычно составляет 20–30 % клиентов.

### Задание 8. Разбор строк

```python
lines = pd.Series([
    "Заказ №1047 от 15.03.2026, сумма 12 450 руб.",
    "Заказ №1048 от 16.03.2026, сумма 980 руб.",
    "Заказ №1050 от 02.04.2026, сумма 1 205 300 руб.",
])

parsed = lines.str.extract(r"№(?P<number>\d+) от (?P<date>[\d.]+), сумма (?P<amount>[\d ]+) руб")
parsed["number"] = parsed["number"].astype(int)
parsed["date"] = pd.to_datetime(parsed["date"], format="%d.%m.%Y")
parsed["amount"] = parsed["amount"].str.replace(" ", "", regex=False).astype(int)

print(parsed)
print(parsed.dtypes)
```

<!-- result -->
*Результат:*

```output
   number       date   amount
0    1047 2026-03-15    12450
1    1048 2026-03-16      980
2    1050 2026-04-02  1205300
number             int64
date      datetime64[us]
amount             int64
dtype: object
```
<!-- /result -->



Запись `(?P<имя>...)` даёт группе имя — оно становится названием столбца. Формат даты указан явно: строку `02.04.2026` без подсказки можно прочитать и как 2 апреля, и как 4 февраля.

Проверка после разбора: `parsed.isna().sum()`. Если шаблон не подошёл к какой-то строке, в ней будут пропуски — их нужно посмотреть глазами.

### Задание 9. Без apply

```python
is_discounted = (df["category"] == "Книги") & (df["amount"] > 3000)
df["final_amount"] = np.where(is_discounted, df["amount"] * 0.9, df["amount"])

# Проверка: результат совпадает с медленным вариантом
slow = df.apply(lambda r: r["amount"] * 0.9 if r["category"] == "Книги" and r["amount"] > 3000 else r["amount"], axis=1)
assert np.allclose(df["final_amount"], slow)
print(is_discounted.sum(), "заказов со скидкой")
```

<!-- result -->
*Результат:*

```output
66 заказов со скидкой
```
<!-- /result -->



Условие вынесено в отдельную переменную с говорящим именем: его можно проверить отдельно и использовать повторно. Три отличия от версии с `apply`: `and` заменён на `&`, каждое условие в скобках, вместо `if / else` — `np.where`.

### Задание 10. Каналы привлечения

```python
rng = np.random.default_rng(7)
users = pd.DataFrame({
    "user_id": np.arange(1, 121),
    "source": rng.choice(["реклама", "поиск", "друзья"], 120, p=[0.5, 0.3, 0.2]),
})

merged = df.merge(users, on="user_id", how="left", validate="many_to_one", indicator=True)
assert len(merged) == len(df)
print(merged["_merge"].value_counts())

by_source = merged.groupby("source").agg(
    users=("user_id", "nunique"),
    orders=("order_id", "count"),
    revenue=("amount", "sum"),
)
by_source["orders_per_user"] = by_source["orders"] / by_source["users"]
by_source["revenue_per_user"] = by_source["revenue"] / by_source["users"]
print(by_source.round(2))
print("Лидер:", by_source["orders_per_user"].idxmax())
```

<!-- result -->
*Результат:*

```output
_merge
both          500
left_only       0
right_only      0
Name: count, dtype: int64
         users  orders   revenue  orders_per_user  revenue_per_user
source                                                             
друзья      26      98  296352.0             3.77          11398.15
поиск       36     174  515975.0             4.83          14332.64
реклама     55     228  678887.0             4.15          12343.40
Лидер: поиск
```
<!-- /result -->



Три страховки сразу: `validate` проверяет уникальность ключа в справочнике, `assert` — что число строк не изменилось, `indicator` — что всем заказам нашёлся пользователь.

«Среднее число заказов на пользователя» посчитано как отношение сумм: все заказы канала делятся на всех его покупателей. В знаменателе — только те пользователи, у кого есть хотя бы один заказ. Если нужно учесть и тех, кто не купил ничего, знаменатель берётся из справочника: `users["source"].value_counts()`.
