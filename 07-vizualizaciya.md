# Глава 7. Визуализация

График нужен в двух случаях: чтобы **понять** данные самому и чтобы **объяснить** находку другим. Это разные задачи. Для себя достаточно быстрого чернового графика. Для других график должен за пять секунд доносить одну мысль.

## 7.1. Какой график выбрать

Выбор зависит от вопроса, а не от того, что красивее.

| Вопрос | График | На карте roadmap.sh |
|--------|--------|---------------------|
| Как менялось во времени? | Линейный | Line Chart |
| Что больше: сравнение категорий | Столбчатый | Bar Chart |
| Из чего состоит целое? | Столбчатый с накоплением | Stacked Chart |
| Как распределены значения? | Гистограмма, ящик с усами | Histogram |
| Связаны ли два показателя? | Точечный | Scatter Plot |
| Где густо, где пусто в таблице? | Тепловая карта | Heatmap |
| Сколько теряем на каждом шаге? | Воронка | Funnel Chart |
| Доли (не больше 3–4 частей) | Круговая | Pie Chart |

Про круговую диаграмму: человек плохо сравнивает углы и площади и хорошо — длины. Поэтому почти всегда столбчатый график лучше кругового.

## 7.2. Matplotlib: основа

Matplotlib — базовая библиотека; seaborn и встроенные графики pandas построены на ней.

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("orders_clean.csv", parse_dates=["date"])
weekly = df.set_index("date")["amount"].resample("W").sum()

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(weekly.index, weekly.values, marker="o")
ax.set_title("Выручка по неделям")
ax.set_xlabel("Неделя")
ax.set_ylabel("Выручка, руб.")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("weekly_revenue.png", dpi=150)
plt.show()
```

Два объекта, которые нужно различать:

- `fig` (Figure) — весь рисунок целиком, «лист бумаги»;
- `ax` (Axes) — одна область с осями, сам график.

Всегда начинай с `fig, ax = plt.subplots()` и рисуй методами `ax`. Это называется объектным стилем; он работает одинаково и для одного графика, и для нескольких.

Несколько графиков на одном рисунке:

```python
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

city_revenue = df.groupby("city")["amount"].sum().sort_values()
axes[0].barh(city_revenue.index, city_revenue.values)
axes[0].set_title("Выручка по городам")

axes[1].hist(df["amount"], bins=30)
axes[1].set_title("Распределение суммы заказа")

fig.tight_layout()
plt.show()
```

## 7.3. Быстрые графики из pandas

Для черновиков — метод `.plot()` прямо у таблицы:

```python
df.groupby("city")["amount"].sum().sort_values().plot(kind="barh", title="Выручка по городам")
plt.show()

df["amount"].plot(kind="hist", bins=30, title="Сумма заказа")
plt.show()

df["month"] = df["date"].dt.to_period("M").astype(str)
(
    df.pivot_table(index="month", columns="category", values="amount", aggfunc="sum")
      .plot(kind="bar", stacked=True, title="Выручка по месяцам и категориям")
)
plt.show()
```

## 7.4. Seaborn: статистические графики

Seaborn умеет сам группировать данные и рисует аккуратнее по умолчанию. В него передают таблицу в длинном формате и названия столбцов.

```python
import seaborn as sns

sns.set_theme(style="whitegrid")

# Распределение
fig, ax = plt.subplots(figsize=(8, 4))
sns.histplot(data=df, x="amount", bins=30, kde=True, ax=ax)
ax.set_title("Распределение суммы заказа")
plt.show()

# Сравнение распределений по группам
fig, ax = plt.subplots(figsize=(8, 4))
sns.boxplot(data=df, x="city", y="amount", ax=ax)
ax.set_title("Сумма заказа по городам")
plt.show()

# Среднее по категориям с доверительным интервалом
fig, ax = plt.subplots(figsize=(8, 4))
sns.barplot(data=df, x="category", y="amount", hue="city", ax=ax)
plt.show()
```

### Как читать ящик с усами (boxplot)

- линия внутри ящика — медиана;
- края ящика — 25-й и 75-й перцентили, то есть в ящике лежит средняя половина данных;
- усы — до крайних значений в пределах 1,5 × IQR;
- точки за усами — кандидаты в выбросы (то самое правило из главы 6).

### Точечный график и тепловая карта

```python
users = (
    df.groupby("user_id")
      .agg(orders=("order_id", "count"), revenue=("amount", "sum"), avg_check=("amount", "mean"))
      .reset_index()
)

fig, ax = plt.subplots(figsize=(6, 5))
sns.scatterplot(data=users, x="orders", y="revenue", alpha=0.6, ax=ax)
ax.set_title("Число заказов и выручка с пользователя")
plt.show()

# Тепловая карта корреляций
fig, ax = plt.subplots(figsize=(5, 4))
sns.heatmap(users[["orders", "revenue", "avg_check"]].corr(), annot=True, fmt=".2f",
            cmap="coolwarm", vmin=-1, vmax=1, ax=ax)
plt.show()

# Тепловая карта сводной таблицы
pivot = df.pivot_table(index="city", columns="category", values="amount", aggfunc="mean")
fig, ax = plt.subplots(figsize=(6, 4))
sns.heatmap(pivot, annot=True, fmt=".0f", cmap="Blues", ax=ax)
ax.set_title("Средний чек: город × категория")
plt.show()
```

### Воронка

Готовой функции нет, воронку рисуют горизонтальными столбцами:

```python
steps = ["Зашли на сайт", "Открыли товар", "Добавили в корзину", "Оплатили"]
users_count = [10000, 4200, 1300, 520]

fig, ax = plt.subplots(figsize=(8, 3.5))
bars = ax.barh(steps[::-1], users_count[::-1])
for bar, value in zip(bars, users_count[::-1]):
    ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
            f"  {value:,} ({value / users_count[0]:.0%})", va="center")
ax.set_xlim(0, users_count[0] * 1.25)
ax.set_title("Воронка покупки")
fig.tight_layout()
plt.show()
```

## 7.5. Как сделать график понятным

График для отчёта — это не то, что получилось по умолчанию.

1. **Заголовок — это вывод, а не описание.** Не «Выручка по неделям», а «Выручка растёт третью неделю подряд».
2. **Подпиши оси и единицы измерения.**
3. **Убери лишнее:** ненужную сетку, рамки, легенду из одного пункта, 3D-эффекты.
4. **Отсортируй столбцы** по значению, а не по алфавиту (кроме случаев, когда у категорий есть естественный порядок).
5. **Используй цвет со смыслом:** выдели главное, остальное сделай серым. Не больше 5–6 цветов.
6. **Столбцы начинай с нуля.** Обрезанная ось превращает разницу в 2 % в визуальную пропасть.
7. **Один график — одна мысль.**

Пример выделения цветом:

```python
city_revenue = df.groupby("city")["amount"].sum().sort_values()
colors = ["#b0b0b0"] * len(city_revenue)
colors[-1] = "#d62728"      # лидер — красным

fig, ax = plt.subplots(figsize=(8, 3.5))
ax.barh(city_revenue.index, city_revenue.values, color=colors)
ax.set_title(f"{city_revenue.index[-1]} приносит больше всех остальных городов")
ax.set_xlabel("Выручка, руб.")
for side in ["top", "right"]:
    ax.spines[side].set_visible(False)
fig.tight_layout()
plt.show()
```

### Как графиком обманывают

Знай эти приёмы, чтобы не применять случайно и замечать у других:

- обрезанная ось Y у столбчатого графика;
- две оси Y с подобранными масштабами — «связь» можно нарисовать между чем угодно;
- специально выбранный период («с марта всё растёт» — а до марта падало);
- накопительный итог вместо значений по периодам — он растёт всегда.

## 7.6. BI-инструменты и дашборды

Дашборд — интерактивная страница с ключевыми показателями, которая обновляется сама. Его делают не в Python, а в BI-системах:

| Инструмент | Особенности |
|------------|-------------|
| **Power BI** | Самый распространённый в корпорациях. Настольная программа есть **только для Windows** — на Mac её не поставить |
| **Tableau** | Сильная визуализация, есть бесплатная версия Tableau Public |
| **Yandex DataLens** | Бесплатный, работает в браузере, популярен в России |
| **Apache Superset**, **Metabase** | Открытые, часто встречаются в IT-компаниях |

На macOS бери **Yandex DataLens** (работает в браузере) или **Tableau Public** (есть версия для Mac). Сделай в одном из них один дашборд — этого достаточно для начала. Power BI пригодится знать по названию: если он понадобится на работе, тебе дадут компьютер с Windows или доступ к веб-версии. Принципы у всех одинаковые: подключил источник → собрал графики → добавил фильтры.

Как построить дашборд:

1. Сверху — 3–5 главных чисел (выручка, заказы, средний чек, конверсия) со сравнением с прошлым периодом.
2. Ниже — динамика во времени.
3. Ещё ниже — разрезы: по городам, категориям, каналам.
4. Фильтры — в одном месте.
5. Проверка: понимает ли человек за 10 секунд, всё хорошо или плохо?

## Что дальше

Когда освоишься с материалом этой главы, переходи к углублённой: [Глава 7А. Визуализация и BI: глубже](07a-vizualizaciya-bi.md).

## Практика на GitHub

- [jakevdp/PythonDataScienceHandbook](https://github.com/jakevdp/PythonDataScienceHandbook) — глава 4 (ноутбуки с префиксом `04`): Matplotlib от простых линий до настройки оформления, в конце — seaborn.
- [guipsamora/pandas_exercises](https://github.com/guipsamora/pandas_exercises) — раздел с упражнениями по визуализации.
- [wesm/pydata-book](https://github.com/wesm/pydata-book) — ноутбук `ch09` про построение графиков.
- [Yorko/mlcourse.ai](https://github.com/Yorko/mlcourse.ai) — вторая тема курса посвящена визуальному анализу данных на pandas, matplotlib и seaborn.
- Образцы дашбордов: [Lenupcik/portfolio](https://github.com/Lenupcik/portfolio) (Yandex DataLens), [AsifRashid01/DataAnalyst_PortfolioProjects](https://github.com/AsifRashid01/DataAnalyst_PortfolioProjects) (Tableau), [noztas/DataAnalystProjects](https://github.com/noztas/DataAnalystProjects) (Excel), [GonorAndres/data-analyst-path](https://github.com/GonorAndres/data-analyst-path) (дашборды к каждому проекту).

## Задания

На `orders_clean.csv`:

1. Построй линейный график числа заказов по дням и добавь на него скользящее среднее за 7 дней.
2. Построй гистограмму суммы заказа. На что похоже распределение? Построй её же для `np.log(amount)`.
3. Сравни распределение суммы заказа по категориям через boxplot.
4. Построй тепловую карту: день недели × город, в ячейках — число заказов.
5. Возьми любой свой график и доведи до уровня отчёта по семи правилам из раздела 7.5.
6. Собери дашборд в DataLens или Tableau Public на `orders_clean.csv`: три числа сверху, динамика, два разреза, фильтр по городу.

## Проверь себя

- Какой график выбрать, чтобы показать связь двух числовых показателей?
- Что показывают ящик и усы на boxplot?
- Чем `fig` отличается от `ax`?
- Почему столбчатый график должен начинаться с нуля?
- Чем заголовок-вывод отличается от заголовка-описания?

## Решения

Общая подготовка для всех решений:

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")
df = pd.read_csv("orders_clean.csv", parse_dates=["date"])
```

### Задание 1. Заказы по дням и скользящее среднее

```python
daily = df.set_index("date")["order_id"].resample("D").count()
rolling = daily.rolling(7).mean()

fig, ax = plt.subplots(figsize=(11, 4))
ax.plot(daily.index, daily.values, color="#b0b0b0", linewidth=1, label="Заказов в день")
ax.plot(rolling.index, rolling.values, color="#d62728", linewidth=2.5, label="Среднее за 7 дней")
ax.set_title("Число заказов по дням")
ax.set_ylabel("Заказов")
ax.legend()
fig.tight_layout()
plt.show()
```

Дневной ряд шумный, поэтому он нарисован серым и тонким, а сглаженная линия — яркой: глаз сразу видит тренд. Окно в 7 дней выбрано не случайно — оно гасит недельную сезонность. Первые шесть значений скользящего среднего пустые: для них ещё не набралось семи дней.

### Задание 2. Гистограмма суммы и её логарифма

```python
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

sns.histplot(df["amount"], bins=40, ax=axes[0])
axes[0].axvline(df["amount"].mean(), color="red", linestyle="--", label="среднее")
axes[0].axvline(df["amount"].median(), color="black", linestyle="--", label="медиана")
axes[0].set_title("Сумма заказа")
axes[0].legend()

sns.histplot(np.log(df["amount"]), bins=40, ax=axes[1])
axes[1].set_title("Логарифм суммы заказа")
axes[1].set_xlabel("log(amount)")

fig.tight_layout()
plt.show()
```

Исходное распределение скошено вправо: большинство заказов небольшие, и есть длинный хвост крупных. Среднее лежит правее медианы — это видно по двум вертикальным линиям. После логарифмирования распределение становится заметно симметричнее. Такая форма типична для денег: доходов, чеков, цен.

### Задание 3. Сравнение категорий

```python
order = df.groupby("category")["amount"].median().sort_values(ascending=False).index

fig, ax = plt.subplots(figsize=(8, 4))
sns.boxplot(data=df, x="category", y="amount", order=order, ax=ax)
ax.set_title("Сумма заказа по категориям")
ax.set_xlabel("")
ax.set_ylabel("Сумма, руб.")
plt.show()

print(df.groupby("category")["amount"].describe().round(0))
```

Категории отсортированы по медиане. Смотри на три вещи: положение линии медианы, высоту ящика (разброс) и точки-выбросы. Если ящики сильно перекрываются, уверенно говорить о различии категорий нельзя — нужна проверка из главы 9.

### Задание 4. Тепловая карта: день недели × город

```python
weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

heat = (
    pd.crosstab(df["date"].dt.day_name(), df["city"])
      .reindex(weekdays)
)

fig, ax = plt.subplots(figsize=(7, 4.5))
sns.heatmap(heat, annot=True, fmt="d", cmap="Blues", ax=ax)
ax.set_title("Число заказов: день недели × город")
ax.set_xlabel("")
ax.set_ylabel("")
plt.show()
```

На такой карте в первую очередь бросается в глаза самый крупный город: у него всё темнее просто из-за объёма. Чтобы сравнить **структуру** по дням, пронормируй столбцы — тогда в каждом городе сумма будет 100 %:

```python
share = heat / heat.sum()
sns.heatmap(share, annot=True, fmt=".0%", cmap="Blues")
plt.show()
```

### Задание 5. График уровня отчёта

Берём график выручки по городам и проходим по семи правилам раздела 7.5:

```python
city_revenue = df.groupby("city")["amount"].sum().sort_values()        # правило 4: сортировка
leader = city_revenue.index[-1]
leader_share = city_revenue.iloc[-1] / city_revenue.sum()

colors = ["#c8c8c8"] * len(city_revenue)                               # правило 5: цвет со смыслом
colors[-1] = "#1f6f5c"

fig, ax = plt.subplots(figsize=(8, 3.8))
bars = ax.barh(city_revenue.index, city_revenue.values / 1000, color=colors)   # правило 6: ось от нуля

ax.set_title(f"{leader} даёт {leader_share:.0%} всей выручки",          # правило 1: заголовок-вывод
             loc="left", fontsize=14, fontweight="bold")
ax.set_xlabel("Выручка, тыс. руб.")                                    # правило 2: единицы
ax.bar_label(bars, fmt="%.0f", padding=4)

ax.grid(False)                                                         # правило 3: убрать лишнее
for side in ["top", "right", "bottom"]:
    ax.spines[side].set_visible(False)
ax.set_xticks([])

fig.tight_layout()
fig.savefig("revenue_by_city.png", dpi=150)
plt.show()
```

Значения подписаны прямо на столбцах, поэтому ось и сетка стали не нужны и убраны. Правило 7 (одна мысль) выполнено: график говорит только о доле лидера.

### Задание 6. Дашборд

Готового кода здесь нет — дашборд собирается мышкой. План для Yandex DataLens (в Power BI и Tableau шаги те же, названия другие):

1. **Подключение.** Создай подключение типа «Файлы» и загрузи `orders_clean.csv`.
2. **Датасет.** Проверь типы полей: `date` — дата, `amount` — дробное число, `city` и `category` — строки.
3. **Вычисляемые поля.** Добавь: «Выручка» = `SUM([amount])`, «Заказы» = `COUNT([order_id])`, «Средний чек» = `SUM([amount]) / COUNT([order_id])`, «Покупатели» = `COUNTD([user_id])`.
4. **Чарты.**
   - три индикатора: выручка, заказы, средний чек;
   - линейный график: выручка по неделям;
   - столбчатый: выручка по городам, отсортированный;
   - столбчатый с накоплением: выручка по месяцам в разрезе категорий.
5. **Дашборд.** Индикаторы — сверху в ряд, динамика — под ними на всю ширину, два разреза — внизу рядом.
6. **Селекторы.** Добавь фильтры по городу и диапазону дат и убедись, что они влияют на все чарты.

Самопроверка: общая выручка на дашборде должна совпасть с `df["amount"].sum()` из pandas. Если не совпадает — ищи причину (обычно это тип поля или агрегация), иначе дашборду нельзя верить.

Опубликуй дашборд по публичной ссылке и добавь её в README своего репозитория.
