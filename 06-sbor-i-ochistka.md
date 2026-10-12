# Глава 6. Сбор и очистка данных

Говорят, что аналитик 80 % времени готовит данные и только 20 % анализирует. Цифра условная, но суть верная: реальные данные всегда грязные. Вывод, сделанный на грязных данных, хуже, чем отсутствие вывода, — ему поверят.

## 6.1. Источники данных

На карте roadmap.sh их четыре: базы данных, CSV-файлы, API и веб-скрейпинг.

### Файлы

```python
import numpy as np
import pandas as pd

df = pd.read_csv("orders.csv", parse_dates=["date"])
```

Параметры `read_csv`, которые решают большинство проблем с «кривыми» файлами:

| Параметр | Когда нужен |
|----------|-------------|
| `sep=";"` | Разделитель — не запятая (типично для выгрузок из русского Excel) |
| `encoding="cp1251"` | Вместо русских букв кракозябры |
| `decimal=","` | Дробная часть отделена запятой |
| `parse_dates=["date"]` | Сразу распознать даты |
| `dtype={"user_id": str}` | Задать тип: например, чтобы не потерять нули в начале кода |
| `na_values=["н/д", "-"]` | Что ещё считать пропуском |
| `usecols=[...]`, `nrows=1000` | Прочитать часть большого файла |

Другие форматы читаются так же: `pd.read_excel("file.xlsx", sheet_name="Лист1")`, `pd.read_json(...)`, `pd.read_parquet(...)`.

### Базы данных

Разобрано в разделе 3.9: `pd.read_sql(query, conn)`.

### API

API — способ получить данные с сервера программно. Ответ обычно приходит в формате JSON, который в Python превращается в словари и списки (глава 2).

```python
import requests
import pandas as pd

url = "https://api.github.com/repos/pandas-dev/pandas"
response = requests.get(url, timeout=10)
response.raise_for_status()        # остановиться, если сервер вернул ошибку

data = response.json()             # словарь
print(data["stargazers_count"], data["forks_count"])

# Список словарей превращается в таблицу одной командой
url = "https://api.github.com/users/pandas-dev/repos"
repos = requests.get(url, timeout=10).json()
df_repos = pd.json_normalize(repos)[["name", "stargazers_count", "language"]]
print(df_repos.sort_values("stargazers_count", ascending=False).head())
```

Что нужно знать про API:

- У каждого API есть документация: адреса, параметры, формат ответа.
- Многие требуют ключ (токен). **Никогда не публикуй ключи на GitHub** — храни их в переменных окружения.
- Есть лимиты на число запросов; данные часто отдаются страницами.

### Веб-скрейпинг

Скрейпинг — извлечение данных прямо из HTML-страниц, когда API нет.

```python
import requests
from bs4 import BeautifulSoup

html = requests.get("https://example.com", timeout=10).text
soup = BeautifulSoup(html, "html.parser")

print(soup.find("h1").text)
for link in soup.find_all("a"):
    print(link.get("href"))
```

Если на странице есть обычная HTML-таблица, хватит одной строки: `pd.read_html(url)` вернёт список всех таблиц страницы.

Правила приличия: читай условия использования сайта и файл `robots.txt`, делай паузы между запросами, не собирай персональные данные. Если есть API — используй его.

## 6.2. Испортим данные специально

Чтобы потренироваться, сделаем из чистого `orders.csv` грязный:

```python
rng = np.random.default_rng(7)
dirty = pd.read_csv("orders.csv")

# Пропуски
dirty.loc[rng.choice(dirty.index, 25, replace=False), "amount"] = np.nan
dirty.loc[rng.choice(dirty.index, 15, replace=False), "city"] = np.nan

# Разное написание
idx = rng.choice(dirty.index, 60, replace=False)
dirty.loc[idx[:30], "city"] = "москва "
dirty.loc[idx[30:], "city"] = "МОСКВА"

# Выбросы и ошибки
dirty.loc[rng.choice(dirty.index, 3, replace=False), "amount"] = 990000
dirty.loc[rng.choice(dirty.index, 2, replace=False), "amount"] = -500

# Дубликаты
dirty = pd.concat([dirty, dirty.sample(10, random_state=1)], ignore_index=True)

dirty.to_csv("orders_dirty.csv", index=False)
```

## 6.3. Диагностика

Сначала смотрим, потом чиним.

```python
df = pd.read_csv("orders_dirty.csv")

df.info()
print(df.isna().sum())                  # пропуски
print(df.duplicated().sum())            # полные дубликаты строк
print(df["city"].value_counts(dropna=False))   # варианты написания
print(df["amount"].describe())          # min и max выдают ошибки
```

Чек-лист вопросов к любому датасету:

1. Правильные ли типы столбцов?
2. Где и сколько пропусков?
3. Есть ли дубликаты?
4. Одинаково ли записаны категории?
5. Правдоподобны ли минимум и максимум?
6. Покрывают ли даты весь нужный период, нет ли дыр?

## 6.4. Типы данных

```python
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
```

`errors="coerce"` превращает то, что не удалось преобразовать, в пропуск — вместо остановки с ошибкой. После этого обязательно проверь, сколько пропусков добавилось.

Типичный случай — числа, записанные как текст: `"1 200,50 руб."`. Чистится цепочкой строковых методов:

```python
raw = pd.Series(["1 200,50 руб.", "980 руб.", "н/д"])
clean = (
    raw.str.replace("руб.", "", regex=False)
       .str.replace(" ", "", regex=False)
       .str.replace(",", ".", regex=False)
)
print(pd.to_numeric(clean, errors="coerce"))
```

## 6.5. Текстовые категории

```python
df["city"] = df["city"].str.strip().str.lower().str.capitalize()
print(df["city"].value_counts(dropna=False))
```

Для более сложных случаев (опечатки, синонимы) составляют словарь замен:

```python
mapping = {"Мск": "Москва", "Спб": "Санкт-Петербург"}
df["city"] = df["city"].replace(mapping)
```

## 6.6. Дубликаты

```python
print(len(df))
df = df.drop_duplicates()
print(len(df))

# Дубликаты по ключу: один order_id должен встречаться один раз
print(df["order_id"].duplicated().sum())
df = df.drop_duplicates(subset="order_id", keep="first")
```

Прежде чем удалять, спроси себя: это точно ошибка? Два одинаковых заказа одного человека в один день могут быть настоящими.

## 6.7. Пропуски

Сначала выясни **причину** пропуска — от неё зависит решение.

| Стратегия | Код | Когда подходит |
|-----------|-----|----------------|
| Удалить строки | `df.dropna(subset=["amount"])` | Пропусков мало, и они случайны |
| Заполнить константой | `df["city"].fillna("Не указан")` | Категории; пропуск сам несёт информацию |
| Заполнить медианой | `df["amount"].fillna(df["amount"].median())` | Числа, пропусков немного |
| Заполнить по группе | `groupby(...).transform("median")` | Значение зависит от группы |
| Оставить как есть | — | Большинство функций pandas пропуски игнорирует |

```python
df["city"] = df["city"].fillna("Не указан")
df = df.dropna(subset=["amount"])
```

Чего делать нельзя:

- **Заполнять нулём** то, что нулём не является. Неизвестная сумма заказа ≠ заказ на 0 рублей: среднее сразу поедет вниз.
- **Заполнять молча.** Любое заполнение — это выдуманные данные. Запиши, что и сколько заполнил.

## 6.8. Выбросы

Выброс — значение, сильно отличающееся от остальных. Он бывает двух видов, и это принципиально:

- **ошибка** (сумма −500, возраст 200 лет) — исправить или удалить;
- **редкое, но настоящее значение** (крупный корпоративный заказ) — удалять нельзя, но можно анализировать отдельно.

Сначала убираем заведомо невозможное:

```python
df = df[df["amount"] > 0]
```

Затем ищем подозрительное. Стандартный способ — правило межквартильного размаха (IQR), на нём же построен «ящик с усами» из главы 7:

```python
q1 = df["amount"].quantile(0.25)
q3 = df["amount"].quantile(0.75)
iqr = q3 - q1
lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr

outliers = df[(df["amount"] < lower) | (df["amount"] > upper)]
print(len(outliers))
print(outliers.sort_values("amount", ascending=False).head())
```

Что делать с найденным:

- посмотреть глазами — часто причина очевидна;
- удалить, если это ошибка;
- оставить, но считать медиану вместо среднего;
- ограничить сверху: `df["amount"].clip(upper=df["amount"].quantile(0.99))`.

Правило IQR — не закон. В денежных данных распределение всегда с длинным хвостом, и под «выбросы» формально попадёт много нормальных крупных заказов. Решение принимаешь ты, а не формула.

```python
df = df[df["amount"] < 100000]
df.to_csv("orders_clean.csv", index=False)
```

## 6.9. Проверки после очистки

Хорошая очистка заканчивается проверками, которые упадут, если что-то не так:

```python
assert df["order_id"].is_unique
assert df["amount"].gt(0).all()
assert df["amount"].notna().all()
print("Проверки пройдены, строк:", len(df))
```

И запиши итог: было 510 строк — стало столько-то, удалено дубликатов, пропусков, ошибок. Эти строки пойдут в отчёт.

## 6.10. Принципы очистки

1. **Не трогай исходный файл.** Сырые данные лежат отдельно, очистка — это код, который делает из них чистые.
2. **Вся очистка — в коде, не руками.** Иначе её нельзя повторить и проверить.
3. **Каждое решение объясняй** комментарием: почему удалил, почему заполнил.
4. **Считай потери.** Если после очистки пропало 30 % строк — это повод остановиться.

## Практика на GitHub

- [jvns/pandas-cookbook](https://github.com/jvns/pandas-cookbook) — главы про очистку «грязных» данных: реальные обращения в городскую службу Нью-Йорка, где в одном столбце перемешаны числа, текст и пропуски. Главное упражнение этой главы.
- [guipsamora/pandas_exercises](https://github.com/guipsamora/pandas_exercises) — раздел про удаление данных и раздел про создание Series и DataFrame.
- [jakevdp/PythonDataScienceHandbook](https://github.com/jakevdp/PythonDataScienceHandbook) — ноутбуки главы 3 про пропущенные значения и векторные операции со строками.
- [AsifRashid01/DataAnalyst_PortfolioProjects](https://github.com/AsifRashid01/DataAnalyst_PortfolioProjects) и [noztas/DataAnalystProjects](https://github.com/noztas/DataAnalystProjects) — проекты по очистке данных на SQL. Повтори те же шаги в pandas: это отличная тренировка в обоих инструментах.
- [awesomedata/awesome-public-datasets](https://github.com/awesomedata/awesome-public-datasets) — выбери датасет по интересной тебе теме и пройди по чек-листу из раздела 6.3.

## Задания

1. Очисти `orders_dirty.csv` самостоятельно, не подглядывая в главу, и сравни число строк с результатом из главы.
2. Сравни среднее и медиану `amount` до и после удаления выбросов. Что изменилось сильнее?
3. Заполни пропуски в `amount` медианой по категории товара через `groupby().transform()`.
4. Получи через API GitHub список репозиториев любого пользователя и построй таблицу: название, язык, звёзды.
5. Найди в Википедии страницу с таблицей (например, список городов по населению), загрузи её через `pd.read_html` и приведи числа к числовому типу.

## Проверь себя

- Почему нельзя заполнять пропуски нулём?
- Чем выброс-ошибка отличается от настоящего редкого значения?
- Как работает правило IQR?
- Что делает `errors="coerce"`?
- Почему очистку нужно делать кодом, а не руками в Excel?

## Решения

### Задание 1. Полная очистка

Оформим очистку функцией, которая ведёт журнал потерь:

```python
import numpy as np
import pandas as pd

MAX_REAL_AMOUNT = 100_000       # суммы выше считаем ошибкой ввода


def clean_orders(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()                                   # сырые данные не трогаем
    log = {"исходно": len(df)}

    df = df.drop_duplicates()
    log["после удаления полных дубликатов"] = len(df)

    df = df.drop_duplicates(subset="order_id", keep="first")
    log["после удаления дубликатов по order_id"] = len(df)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    df["city"] = df["city"].str.strip().str.lower().str.capitalize().fillna("Не указан")

    df = df.dropna(subset=["amount"])
    log["после удаления пропусков в amount"] = len(df)

    df = df[df["amount"] > 0]
    log["после удаления неположительных сумм"] = len(df)

    df = df[df["amount"] < MAX_REAL_AMOUNT]
    log["после удаления аномально больших сумм"] = len(df)

    for step, rows in log.items():
        print(f"{step:<42} {rows}")
    return df.reset_index(drop=True)


raw = pd.read_csv("orders_dirty.csv")
clean = clean_orders(raw)

assert clean["order_id"].is_unique
assert clean["amount"].between(0, MAX_REAL_AMOUNT, inclusive="neither").all()
print(clean["city"].value_counts())
```

Порядок шагов выбран не случайно: сначала дубликаты (чтобы не чистить одно и то же дважды), потом типы, потом текст, потом пропуски и выбросы.

Число строк в конце зависит от случайных пересечений: например, строка с пропуском в `amount` могла попасть и в дубликаты. Важно не точное число, а то, что ты можешь объяснить каждый шаг журнала.

### Задание 2. Среднее и медиана до и после

```python
before = pd.to_numeric(raw["amount"], errors="coerce")
after = clean["amount"]

comparison = pd.DataFrame({
    "до очистки": [before.mean(), before.median()],
    "после очистки": [after.mean(), after.median()],
}, index=["среднее", "медиана"]).round(0)

comparison["изменение, %"] = ((comparison["после очистки"] / comparison["до очистки"] - 1) * 100).round(1)
print(comparison)
```

Среднее изменится в разы: три значения по 990 000 на 500 строк добавляют к нему почти 6000. Медиана сдвинется на считаные проценты. Это наглядная причина, по которой для «грязных» и денежных данных смотрят на медиану.

### Задание 3. Заполнение медианой по категории

```python
df = pd.read_csv("orders_dirty.csv")
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
df = df[(df["amount"].isna()) | ((df["amount"] > 0) & (df["amount"] < 100_000))]   # сначала убрать ошибки

missing_before = df["amount"].isna().sum()
category_median = df.groupby("category")["amount"].transform("median")
df["amount_filled"] = df["amount"].fillna(category_median)
df["amount_was_missing"] = df["amount"].isna()

print("Заполнено пропусков:", missing_before)
print(df.groupby("category")[["amount", "amount_filled"]].median())
```

Три важные детали:

- **выбросы убираются до расчёта медианы**, иначе заполнять будем искажённым значением;
- `transform("median")` возвращает столбец той же длины, что и таблица, поэтому его можно передать прямо в `fillna`;
- столбец-флаг `amount_was_missing` сохраняет информацию о том, какие значения придуманы. Без него заполненные строки потом не отличить от настоящих.

### Задание 4. Репозитории через API GitHub

```python
import requests

USER = "pandas-dev"             # подставь любого пользователя или организацию

response = requests.get(
    f"https://api.github.com/users/{USER}/repos",
    params={"per_page": 100, "sort": "updated"},
    timeout=10,
)
response.raise_for_status()

repos = (
    pd.json_normalize(response.json())
      [["name", "language", "stargazers_count", "forks_count", "updated_at"]]
      .rename(columns={"stargazers_count": "stars", "forks_count": "forks"})
      .assign(updated_at=lambda d: pd.to_datetime(d["updated_at"]).dt.date)
      .sort_values("stars", ascending=False)
      .reset_index(drop=True)
)
print(repos.head(10))
print(repos["language"].value_counts(dropna=False))
```

Параметры запроса передаются словарём `params`, а не вклеиваются в адрес руками. API отдаёт не больше 100 репозиториев за раз: если их больше, нужен цикл по страницам с параметром `page`. Без авторизации GitHub разрешает около 60 запросов в час — для учёбы хватает.

### Задание 5. Таблица из Википедии

```python
url = "https://ru.wikipedia.org/wiki/Список_городов_России_с_населением_более_100_тысяч_жителей"

tables = pd.read_html(url)                 # нужна библиотека lxml: pip install lxml
print("Таблиц на странице:", len(tables))

for i, table in enumerate(tables[:5]):     # посмотреть, какая из таблиц нужная
    print(i, table.shape, list(table.columns)[:4])
```

Дальше действия зависят от того, как сейчас свёрстана страница, поэтому алгоритм, а не готовый код:

1. Выбери нужную таблицу по размеру и столбцам: `cities = tables[N]`.
2. Посмотри `cities.head()` и `cities.dtypes`. Числа почти наверняка прочитались как текст: в них пробелы-разделители и сноски вида `[3]`.
3. Очисти числовой столбец той же цепочкой, что в разделе 6.4:

```python
def to_number(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
              .str.replace(r"\[.*?\]", "", regex=True)     # сноски
              .str.replace(r"[^\d,.-]", "", regex=True)    # всё, кроме цифр и разделителей
              .str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(cleaned, errors="coerce")

print(to_number(pd.Series(["1 234 567[3]", "980 000", "н/д"])))
```

4. Проверь, сколько значений стало `NaN`, и посмотри на них глазами.

Если Википедия отвечает ошибкой 403, добавь заголовок `User-Agent`: скачай страницу через `requests.get(url, headers={"User-Agent": "Mozilla/5.0"})` и передай текст в `pd.read_html(io.StringIO(response.text))`.
