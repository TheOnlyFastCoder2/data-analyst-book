# Приложение. Все ресурсы и шпаргалки

## А. Все репозитории книги

| Репозиторий | Что это | Главы |
|-------------|---------|-------|
| [kamranahmedse/developer-roadmap](https://github.com/kamranahmedse/developer-roadmap) | Карта Data Analyst: что и в каком порядке учить | 0, 13 |
| [PavelGrigoryevDS/awesome-data-analysis](https://github.com/PavelGrigoryevDS/awesome-data-analysis) | Каталог из 500+ ресурсов по анализу данных | 0, 2, 13 |
| [academic/awesome-datascience](https://github.com/academic/awesome-datascience) | Каталог ресурсов по Data Science | 0, 11 |
| [lerocha/chinook-database](https://github.com/lerocha/chinook-database) | Учебная база данных музыкального магазина | 3, 5, 12 |
| [jesussantana/sql-data-analysis](https://github.com/jesussantana/sql-data-analysis) | 150+ аналитических задач по SQL | 3, 13 |
| [jakevdp/PythonDataScienceHandbook](https://github.com/jakevdp/PythonDataScienceHandbook) | Книга: IPython, NumPy, pandas, Matplotlib, scikit-learn | 2, 4, 5, 6, 7, 11 |
| [wesm/pydata-book](https://github.com/wesm/pydata-book) | Материалы к книге автора pandas | 2, 4, 5, 7 |
| [guipsamora/pandas_exercises](https://github.com/guipsamora/pandas_exercises) | Упражнения по pandas с решениями | 5, 6, 7, 8, 13 |
| [rougier/numpy-100](https://github.com/rougier/numpy-100) | 100 задач по NumPy | 4 |
| [jvns/pandas-cookbook](https://github.com/jvns/pandas-cookbook) | pandas на реальных «грязных» данных | 5, 6 |
| [AllenDowney/ThinkStats2](https://github.com/AllenDowney/ThinkStats2) | Статистика через Python-код | 8, 9 |
| [AllenDowney/ThinkBayes2](https://github.com/AllenDowney/ThinkBayes2) | Байесовская статистика на Python | 9 |
| [Yorko/mlcourse.ai](https://github.com/Yorko/mlcourse.ai) | Открытый курс машинного обучения от ODS | 7, 8, 11, 13 |
| [DataTalksClub](https://github.com/DataTalksClub) | Бесплатные курсы с домашними заданиями | 10, 11, 13 |
| [awesomedata/awesome-public-datasets](https://github.com/awesomedata/awesome-public-datasets) | Каталог открытых датасетов по темам | 1, 6, 8, 11, 12 |
| [DataAna1ytics/Projects_Data_Analytics](https://github.com/DataAna1ytics/Projects_Data_Analytics) | Учебные проекты Практикума и karpov.courses | 9, 10, 12 |
| [Yourius/Projects_Ya](https://github.com/Yourius/Projects_Ya) | Воронки, A/A/B-тесты, маркетинговые метрики | 8, 9, 10, 12 |
| [Lenupcik/portfolio](https://github.com/Lenupcik/portfolio) | Исследования, дашборд DataLens, SQL | 3, 7, 10, 12 |
| [GonorAndres/data-analyst-path](https://github.com/GonorAndres/data-analyst-path) | Шесть законченных проектов с дашбордами | 7, 8, 9, 10, 12 |
| [AsifRashid01/DataAnalyst_PortfolioProjects](https://github.com/AsifRashid01/DataAnalyst_PortfolioProjects) | SQL, Tableau, очистка данных, pandas | 3, 6, 7, 12 |
| [noztas/DataAnalystProjects](https://github.com/noztas/DataAnalystProjects) | MySQL, дашборд в Excel, pandas | 1, 3, 6, 7, 12 |

Содержимое репозиториев со временем меняется: папки переименовывают, файлы переносят. Если путь из книги не нашёлся — открой README репозитория, там всегда есть актуальное оглавление.

## Б. Шпаргалка по SQL

```sql
-- Скелет запроса
SELECT столбцы, агрегаты
FROM таблица
JOIN другая ON условие
WHERE фильтр_строк
GROUP BY столбцы
HAVING фильтр_групп
ORDER BY столбец DESC
LIMIT n;

-- CTE
WITH имя AS (SELECT ...)
SELECT ... FROM имя;

-- Оконные функции
ROW_NUMBER() OVER (PARTITION BY g ORDER BY x DESC)
SUM(x)       OVER (PARTITION BY g ORDER BY d)                              -- накопительный итог
LAG(x)       OVER (PARTITION BY g ORDER BY d)                              -- предыдущее значение
AVG(x)       OVER (ORDER BY d ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)    -- скользящее среднее

-- Условная агрегация
SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END)
COUNT(DISTINCT CASE WHEN event = 'purchase' THEN user_id END)
```

Порядок выполнения: `FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT`.

## В. Шпаргалка по pandas

```python
# Загрузка и осмотр
df = pd.read_csv("file.csv", parse_dates=["date"])
df.head(); df.info(); df.describe(); df.shape
df["col"].value_counts(); df["col"].nunique(); df.isna().sum()

# Выбор
df[["a", "b"]]
df[(df["a"] > 5) & (df["b"] == "x")]
df.loc[условие, ["a", "b"]]
df.sort_values("a", ascending=False).head(10)

# Новые столбцы
df["c"] = df["a"] / df["b"]
df["flag"] = np.where(df["a"] > 5, "да", "нет")
df["month"] = df["date"].dt.to_period("M")

# Группировка
df.groupby("g").agg(n=("id", "count"), total=("x", "sum")).reset_index()
df.groupby("g")["x"].transform("mean")
df.pivot_table(index="a", columns="b", values="x", aggfunc="sum")

# Соединение
df.merge(other, on="key", how="left", validate="many_to_one")
pd.concat([df1, df2], ignore_index=True)

# Очистка
df.drop_duplicates(); df.dropna(subset=["x"]); df["x"].fillna(значение)
pd.to_numeric(df["x"], errors="coerce"); pd.to_datetime(df["d"], errors="coerce")
df["s"].str.strip().str.lower()

# Время
df.set_index("date")["x"].resample("W").sum()
s.rolling(7).mean(); s.pct_change(); s.shift(1)
```

## Г. Какой статистический тест выбрать

| Ситуация | Тест |
|----------|------|
| Две группы, сравниваем средние | t-тест Уэлча |
| Две группы, данные с выбросами или тяжёлым хвостом | Манна — Уитни или бутстрап |
| Две группы, сравниваем доли (конверсии) | z-тест пропорций или хи-квадрат |
| Одни и те же объекты «до» и «после» | Парный t-тест |
| Три и больше групп | ANOVA, затем попарные сравнения с поправкой |
| Связь двух категориальных признаков | Хи-квадрат |
| Связь двух числовых признаков | Корреляция Пирсона или Спирмена |
| Нестандартная метрика (медиана, перцентиль, отношение) | Бутстрап |

## Д. Формулы метрик

| Метрика | Формула |
|---------|---------|
| Конверсия (CR) | целевые действия / посетители |
| Средний чек (AOV) | выручка / число заказов |
| ARPU | выручка / все пользователи |
| ARPPU | выручка / платящие пользователи |
| Retention N-го периода | вернувшиеся в период N / размер когорты |
| Churn | 1 − retention |
| Sticky factor | DAU / MAU |
| LTV | суммарная выручка когорты / размер когорты |
| CAC | расходы на привлечение / число привлечённых |
| ROMI | (доход − расходы на маркетинг) / расходы на маркетинг |

## Е. Словарь

| Термин | Значение |
|--------|----------|
| A/A-тест | Тест, где обе группы видят одно и то же: проверка системы разбиения |
| A/B-тест | Эксперимент со случайным разделением пользователей на группы |
| API | Программный интерфейс для получения данных с сервера |
| BI | Business Intelligence: системы отчётности и дашбордов |
| CTE | Именованный подзапрос в SQL (`WITH`) |
| DataFrame | Таблица в pandas |
| DWH | Хранилище данных |
| EDA | Разведочный анализ данных |
| ETL | Извлечение, преобразование и загрузка данных |
| IQR | Межквартильный размах |
| JOIN | Соединение таблиц |
| KPI | Ключевой показатель эффективности |
| MDE | Минимальный эффект, который тест способен обнаружить |
| NaN / NULL | Пропущенное значение |
| p-value | Вероятность получить такое же или более сильное различие, если эффекта на самом деле нет |
| SRM | Несоответствие размеров групп в тесте запланированным |
| Бейзлайн | Простейшее решение, с которым сравнивают модель |
| Векторизация | Операция сразу над всем массивом без цикла |
| Воронка | Последовательность шагов с долей дошедших до каждого |
| Выброс | Значение, резко отличающееся от остальных |
| Когорта | Группа пользователей с общим событием в один период |
| Конфаундер | Скрытая переменная, влияющая на обе изучаемые величины |
| Метрика | Числовой показатель состояния продукта или бизнеса |
| Мощность | Вероятность обнаружить эффект, если он есть |
| Переобучение | Модель запомнила обучающие данные и плохо работает на новых |
| Признак | Характеристика объекта, входная переменная модели |
| Сегмент | Часть пользователей, выделенная по признаку |
| Утечка данных | Попадание в признаки информации, недоступной в момент предсказания |
