# Глава 3. SQL

SQL — язык запросов к базам данных. Почти все данные компании лежат в базах, поэтому любой анализ начинается с SQL-запроса. На собеседовании junior-аналитика его спрашивают всегда.

## 3.1. Учебная база Chinook

Вся глава построена на базе из репозитория [lerocha/chinook-database](https://github.com/lerocha/chinook-database). Это данные вымышленного магазина цифровой музыки: исполнители, альбомы, треки, клиенты и счета.

Проще всего начать с SQLite — эта база живёт в одном файле и не требует сервера:

1. В репозитории открой папку `ChinookDatabase/DataSources`.
2. Скачай файл `Chinook_Sqlite.sqlite`.
3. Открой его в программе DB Browser for SQLite или DBeaver — либо прямо из Python (раздел 3.9). Обе программы есть для macOS; через Homebrew они ставятся командами `brew install --cask db-browser-for-sqlite` и `brew install --cask dbeaver-community`.

Скачанный файл окажется в `~/Downloads`. Перенеси его в папку проекта: `mv ~/Downloads/Chinook_Sqlite.sqlite data/`.

Основные таблицы (имена даны для SQLite-версии; в версии для PostgreSQL они записаны в нижнем регистре с подчёркиванием — `invoice_line`, `customer_id`):

| Таблица | Что хранит | Ключевые столбцы |
|---------|-----------|------------------|
| `Artist` | Исполнители | `ArtistId`, `Name` |
| `Album` | Альбомы | `AlbumId`, `Title`, `ArtistId` |
| `Track` | Треки | `TrackId`, `Name`, `AlbumId`, `GenreId`, `Milliseconds`, `UnitPrice` |
| `Genre` | Жанры | `GenreId`, `Name` |
| `Customer` | Клиенты | `CustomerId`, `FirstName`, `LastName`, `Country`, `SupportRepId` |
| `Invoice` | Счета (заказы) | `InvoiceId`, `CustomerId`, `InvoiceDate`, `BillingCountry`, `Total` |
| `InvoiceLine` | Позиции в счёте | `InvoiceLineId`, `InvoiceId`, `TrackId`, `UnitPrice`, `Quantity` |
| `Employee` | Сотрудники | `EmployeeId`, `LastName`, `ReportsTo` |

Таблицы связаны ключами: у альбома есть `ArtistId`, по которому находится исполнитель, у счёта — `CustomerId`, и так далее. Прежде чем писать запросы, нарисуй эту схему на бумаге.

## 3.2. SELECT: выбор данных

```sql
SELECT FirstName, LastName, Country
FROM Customer
WHERE Country = 'Brazil'
ORDER BY LastName
LIMIT 5;
```

- `SELECT` — какие столбцы показать (`*` — все);
- `FROM` — из какой таблицы;
- `WHERE` — какие строки оставить;
- `ORDER BY` — как отсортировать (`DESC` — по убыванию);
- `LIMIT` — сколько строк вернуть.

Условия в `WHERE`:

```sql
SELECT Name, Milliseconds / 60000.0 AS minutes, UnitPrice
FROM Track
WHERE UnitPrice > 0.99
  AND Milliseconds BETWEEN 180000 AND 300000
  AND Name LIKE '%Love%'
  AND Composer IS NOT NULL;
```

| Оператор | Смысл |
|----------|-------|
| `=`, `<>`, `>`, `<` | Сравнение |
| `AND`, `OR`, `NOT` | Логика |
| `IN ('USA', 'Canada')` | Значение из списка |
| `BETWEEN a AND b` | В диапазоне, границы включены |
| `LIKE '%Love%'` | Поиск по шаблону: `%` — любые символы |
| `IS NULL` / `IS NOT NULL` | Проверка на пустое значение |

`NULL` — это «значение неизвестно». С ним нельзя сравнивать через `=`: условие `Composer = NULL` никогда не истинно. Только `IS NULL`.

`DISTINCT` оставляет уникальные значения:

```sql
SELECT DISTINCT Country FROM Customer ORDER BY Country;
```

## 3.3. Агрегация и GROUP BY

Агрегатные функции сворачивают много строк в одно число: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`.

```sql
SELECT COUNT(*)   AS invoices,
       SUM(Total) AS revenue,
       AVG(Total) AS avg_check
FROM Invoice;
```

`GROUP BY` считает агрегаты отдельно для каждой группы — это сводная таблица из главы 1:

```sql
SELECT BillingCountry,
       COUNT(*)             AS invoices,
       ROUND(SUM(Total), 2) AS revenue
FROM Invoice
GROUP BY BillingCountry
ORDER BY revenue DESC
LIMIT 10;
```

Правило: в `SELECT` при группировке могут стоять только столбцы из `GROUP BY` и агрегатные функции.

`HAVING` фильтрует **группы** — так же, как `WHERE` фильтрует строки:

```sql
SELECT BillingCountry, COUNT(*) AS invoices
FROM Invoice
WHERE InvoiceDate >= '2010-01-01'   -- фильтр строк ДО группировки
GROUP BY BillingCountry
HAVING COUNT(*) >= 10               -- фильтр групп ПОСЛЕ группировки
ORDER BY invoices DESC;
```

Три варианта `COUNT`, которые любят спрашивать на собеседованиях:

- `COUNT(*)` — все строки;
- `COUNT(Composer)` — строки, где `Composer` не `NULL`;
- `COUNT(DISTINCT Composer)` — число уникальных значений.

## 3.4. Порядок выполнения запроса

Пишем мы запрос в одном порядке, а база выполняет в другом:

```
FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
```

Отсюда понятны два правила: в `WHERE` нельзя использовать агрегаты (группировки ещё не было) и нельзя использовать псевдонимы из `SELECT` (он ещё не выполнен).

## 3.5. JOIN: соединение таблиц

Данные разложены по разным таблицам, `JOIN` собирает их обратно.

```sql
SELECT ar.Name  AS artist,
       al.Title AS album
FROM Album AS al
JOIN Artist AS ar ON ar.ArtistId = al.ArtistId
ORDER BY ar.Name
LIMIT 10;
```

`al` и `ar` — псевдонимы таблиц, чтобы не писать полные имена.

Виды соединений:

| Вид | Что попадает в результат |
|-----|--------------------------|
| `INNER JOIN` (или просто `JOIN`) | Только строки, у которых есть пара в обеих таблицах |
| `LEFT JOIN` | Все строки левой таблицы; если пары нет — справа `NULL` |
| `RIGHT JOIN` | Зеркально `LEFT` |
| `FULL JOIN` | Все строки обеих таблиц |
| `CROSS JOIN` | Каждая строка с каждой |

В работе 95 % соединений — это `INNER` и `LEFT`.

Классическая задача на `LEFT JOIN` — найти то, чего нет. Исполнители без альбомов:

```sql
SELECT ar.Name
FROM Artist AS ar
LEFT JOIN Album AS al ON al.ArtistId = ar.ArtistId
WHERE al.AlbumId IS NULL;
```

Соединять можно сколько угодно таблиц. Выручка по жанрам:

```sql
SELECT g.Name                                   AS genre,
       ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS revenue
FROM InvoiceLine AS il
JOIN Track AS t ON t.TrackId = il.TrackId
JOIN Genre AS g ON g.GenreId = t.GenreId
GROUP BY g.Name
ORDER BY revenue DESC
LIMIT 5;
```

**Главная ловушка JOIN — размножение строк.** Если соединить `Invoice` с `InvoiceLine` и посчитать `SUM(Invoice.Total)`, сумма счёта учтётся столько раз, сколько в нём позиций. Привычка: после каждого `JOIN` проверяй через `COUNT(*)`, что строк столько, сколько ты ожидаешь.

### JOIN на маленьком примере

На большой базе трудно увидеть, что именно делает соединение. Разберём на двух таблицах по три строки — их можно удержать в голове. Пример запускается из Python и не требует Chinook.

```python
import sqlite3

conn = sqlite3.connect(":memory:")
conn.executescript("""
    CREATE TABLE customers (customer_id INTEGER, name TEXT);
    CREATE TABLE orders (order_id INTEGER, customer_id INTEGER, amount INTEGER);

    INSERT INTO customers VALUES (1, 'Анна'), (2, 'Борис'), (3, 'Вера');
    INSERT INTO orders VALUES (10, 1, 500), (11, 1, 300), (12, 2, 700), (13, 9, 100);
""")


def show(title, query):
    print(title)
    for row in conn.execute(query):
        print("  ", row)
```

Что лежит в таблицах:

- у Анны два заказа, у Бориса один, у Веры ни одного;
- заказ 13 принадлежит клиенту 9, которого нет в таблице клиентов (такое случается: клиента удалили, а заказ остался).

```python
show("INNER JOIN — только совпавшие пары:", """
    SELECT c.name, o.order_id, o.amount
    FROM customers AS c
    JOIN orders AS o ON o.customer_id = c.customer_id
""")

show("LEFT JOIN — все клиенты, даже без заказов:", """
    SELECT c.name, o.order_id, o.amount
    FROM customers AS c
    LEFT JOIN orders AS o ON o.customer_id = c.customer_id
""")
```

Результат:

```
INNER JOIN — только совпавшие пары:
   ('Анна', 10, 500)
   ('Анна', 11, 300)
   ('Борис', 12, 700)
LEFT JOIN — все клиенты, даже без заказов:
   ('Анна', 10, 500)
   ('Анна', 11, 300)
   ('Борис', 12, 700)
   ('Вера', None, None)
```

Три наблюдения, на которых держится всё понимание JOIN:

1. **Анна появилась дважды.** Соединение не «подклеивает столбцы», а создаёт строку для каждой совпавшей пары. Один клиент с двумя заказами — две строки. Это и есть размножение строк.
2. **Вера исчезла из INNER JOIN** и осталась в LEFT JOIN с `None` (это `NULL`) на месте заказа.
3. **Заказ 13 не попал никуда**: для него нет клиента, а «главной» таблицей в LEFT JOIN были клиенты.

Теперь типичные вопросы:

```python
show("Сколько заказов и на какую сумму у каждого клиента:", """
    SELECT c.name,
           COUNT(o.order_id)          AS orders,
           COALESCE(SUM(o.amount), 0) AS total
    FROM customers AS c
    LEFT JOIN orders AS o ON o.customer_id = c.customer_id
    GROUP BY c.customer_id, c.name
""")

show("Клиенты без заказов:", """
    SELECT c.name
    FROM customers AS c
    LEFT JOIN orders AS o ON o.customer_id = c.customer_id
    WHERE o.order_id IS NULL
""")

show("Заказы без клиента (меняем таблицы местами):", """
    SELECT o.order_id
    FROM orders AS o
    LEFT JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE c.customer_id IS NULL
""")
```

Обрати внимание на первый запрос:

- `COUNT(o.order_id)`, а не `COUNT(*)`. У Веры после LEFT JOIN есть одна строка — с пустым заказом. `COUNT(*)` посчитал бы её и выдал 1, а `COUNT(o.order_id)` пропускает `NULL` и честно даёт 0.
- `COALESCE(x, 0)` подставляет 0 вместо `NULL`: сумма по «никаким» заказам — это `NULL`, а в отчёте нужен ноль.

Как выбрать вид соединения: спроси себя, **строки какой таблицы нельзя потерять**. Её ставят слева и используют `LEFT JOIN`. Если потерять не жалко ни те, ни другие — `INNER JOIN`.

## 3.6. CASE, даты, подзапросы и CTE

### CASE — условие внутри запроса

```sql
SELECT CASE
           WHEN Total >= 10 THEN 'крупный'
           WHEN Total >= 5  THEN 'средний'
           ELSE 'мелкий'
       END      AS segment,
       COUNT(*) AS invoices
FROM Invoice
GROUP BY segment;
```

### Даты

Функции дат — самое разное место в диалектах SQL. Выручка по месяцам:

```sql
-- SQLite
SELECT strftime('%Y-%m', InvoiceDate) AS month,
       ROUND(SUM(Total), 2)           AS revenue
FROM Invoice
GROUP BY month
ORDER BY month;
```

В PostgreSQL вместо `strftime` используют `DATE_TRUNC('month', invoice_date)`.

### Подзапрос

Запрос внутри запроса. Счета дороже среднего:

```sql
SELECT InvoiceId, Total
FROM Invoice
WHERE Total > (SELECT AVG(Total) FROM Invoice)
ORDER BY Total DESC;
```

### CTE (WITH)

CTE — именованный подзапрос, вынесенный в начало. Он превращает сложный запрос в последовательность понятных шагов. Привыкай писать именно так:

```sql
WITH customer_revenue AS (
    SELECT CustomerId,
           SUM(Total) AS revenue
    FROM Invoice
    GROUP BY CustomerId
)
SELECT c.FirstName || ' ' || c.LastName AS customer,
       c.Country,
       ROUND(cr.revenue, 2)             AS revenue
FROM customer_revenue AS cr
JOIN Customer AS c ON c.CustomerId = cr.CustomerId
ORDER BY cr.revenue DESC
LIMIT 10;
```

## 3.7. Оконные функции

Тема, которая отделяет новичка от уверенного пользователя. `GROUP BY` схлопывает строки группы в одну. Оконная функция считает то же самое, но **оставляет все строки на месте**.

```sql
SELECT InvoiceId,
       BillingCountry,
       Total,
       SUM(Total) OVER (PARTITION BY BillingCountry) AS country_revenue
FROM Invoice;
```

Конструкция `OVER (...)` задаёт окно:

- `PARTITION BY` — на какие группы делить (аналог `GROUP BY`);
- `ORDER BY` — в каком порядке идти внутри группы.

### Ранжирование

| Функция | При значениях 10, 10, 8 даст |
|---------|------------------------------|
| `ROW_NUMBER()` | 1, 2, 3 |
| `RANK()` | 1, 1, 3 |
| `DENSE_RANK()` | 1, 1, 2 |

Задача «топ-N в каждой группе» — самая частая на собеседованиях. Три самых крупных счёта в каждой стране:

```sql
WITH ranked AS (
    SELECT BillingCountry,
           InvoiceId,
           Total,
           ROW_NUMBER() OVER (
               PARTITION BY BillingCountry
               ORDER BY Total DESC
           ) AS rn
    FROM Invoice
)
SELECT *
FROM ranked
WHERE rn <= 3;
```

Фильтровать по `rn` в том же запросе нельзя — оконные функции вычисляются после `WHERE`. Поэтому нужен CTE.

### Накопительный итог и сравнение с прошлым периодом

```sql
WITH monthly AS (
    SELECT strftime('%Y-%m', InvoiceDate) AS month,
           SUM(Total)                     AS revenue
    FROM Invoice
    GROUP BY month
)
SELECT month,
       ROUND(revenue, 2)                                  AS revenue,
       ROUND(SUM(revenue) OVER (ORDER BY month), 2)       AS running_total,
       ROUND(LAG(revenue) OVER (ORDER BY month), 2)       AS prev_month,
       ROUND(revenue - LAG(revenue) OVER (ORDER BY month), 2) AS diff
FROM monthly
ORDER BY month;
```

- `SUM(...) OVER (ORDER BY ...)` — накопительная сумма;
- `LAG(x)` — значение из предыдущей строки, `LEAD(x)` — из следующей.

Скользящее среднее за три месяца получается добавлением рамки окна: `AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`.

## 3.8. Как писать читаемый SQL

- Ключевые слова — заглавными, каждое с новой строки.
- Сложный запрос — через CTE с осмысленными именами, а не через вложенные подзапросы.
- Каждому вычисляемому столбцу — псевдоним через `AS`.
- Не используй `SELECT *` в итоговых запросах: перечисляй столбцы.
- Пиши запрос по шагам и проверяй результат каждого шага.

## 3.9. SQL из Python

Аналитик обычно достаёт данные запросом и дальше работает в pandas. Для SQLite всё нужное уже встроено в Python:

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("Chinook_Sqlite.sqlite")

query = """
SELECT BillingCountry AS country,
       COUNT(*)       AS invoices,
       SUM(Total)     AS revenue
FROM Invoice
GROUP BY BillingCountry
ORDER BY revenue DESC
"""

df = pd.read_sql(query, conn)
print(df.head())
conn.close()
```

Правило разделения труда: отбор, соединение и группировку больших таблиц делай в SQL (база справится быстрее), а расчёты, статистику и графики — в pandas.

## Практика на GitHub

1. [lerocha/chinook-database](https://github.com/lerocha/chinook-database) — выполни все запросы главы и задания ниже.
2. [jesussantana/sql-data-analysis](https://github.com/jesussantana/sql-data-analysis) — больше 150 аналитических задач. Решай по порядку, по 5–7 в день. Сначала свой запрос, потом сверка с решением.
3. [AsifRashid01/DataAnalyst_PortfolioProjects](https://github.com/AsifRashid01/DataAnalyst_PortfolioProjects) и [noztas/DataAnalystProjects](https://github.com/noztas/DataAnalystProjects) — посмотри, как выглядит законченный проект на SQL: исследование данных и очистка с CTE и оконными функциями.
4. [Lenupcik/portfolio](https://github.com/Lenupcik/portfolio) — примеры запросов к демо-базе PostgreSQL «Авиаперевозки». Хороший следующий шаг после Chinook: база крупнее и на русском.

## Задания

На базе Chinook:

1. Сколько клиентов в каждой стране? Отсортируй по убыванию.
2. Найди 10 самых длинных треков, длительность выведи в минутах.
3. Какие 5 исполнителей выпустили больше всего альбомов?
4. Посчитай выручку по годам.
5. Найди клиентов, которые потратили больше 40 долларов.
6. Какой жанр самый популярный в каждой стране по числу купленных треков? (CTE + `ROW_NUMBER`.)
7. Для каждого клиента выведи дату первой покупки и число дней между первой и последней.
8. Посчитай, на сколько процентов выручка каждого месяца отличается от предыдущего.
9. Найди треки, которые ни разу не купили.
10. Для каждого сотрудника поддержки посчитай число клиентов и суммарную выручку с них.

## Проверь себя

- Чем `WHERE` отличается от `HAVING`?
- Чем `LEFT JOIN` отличается от `INNER JOIN`? Приведи задачу, где нужен именно `LEFT`.
- В каком порядке выполняются части запроса?
- Чем отличаются `ROW_NUMBER`, `RANK` и `DENSE_RANK`?
- Почему `COUNT(*)` и `COUNT(column)` могут дать разные числа?
- Как после `JOIN` получить завышенную сумму и как это заметить?

## Решения

Запросы написаны для SQLite-версии Chinook. Сначала реши сам и сравни **результат**, а не текст запроса: одну задачу можно решить по-разному.

### Задание 1. Клиенты по странам

```sql
SELECT Country,
       COUNT(*) AS customers
FROM Customer
GROUP BY Country
ORDER BY customers DESC, Country;
```

Вторая колонка сортировки (`Country`) нужна, чтобы страны с одинаковым числом клиентов шли в предсказуемом порядке.

### Задание 2. Десять самых длинных треков

```sql
SELECT Name,
       ROUND(Milliseconds / 60000.0, 1) AS minutes
FROM Track
ORDER BY Milliseconds DESC
LIMIT 10;
```

Делим на `60000.0`, а не на `60000`: при делении целого на целое SQLite отбросит дробную часть. Сортируем по исходному столбцу, а не по округлённому — так точнее.

### Задание 3. Исполнители с наибольшим числом альбомов

```sql
SELECT ar.Name,
       COUNT(al.AlbumId) AS albums
FROM Artist AS ar
JOIN Album AS al ON al.ArtistId = ar.ArtistId
GROUP BY ar.ArtistId, ar.Name
ORDER BY albums DESC
LIMIT 5;
```

Группируем по `ArtistId`, а не только по имени: два разных исполнителя могут называться одинаково, и по имени они склеились бы в одного.

### Задание 4. Выручка по годам

```sql
SELECT strftime('%Y', InvoiceDate) AS year,
       ROUND(SUM(Total), 2)        AS revenue,
       COUNT(*)                    AS invoices
FROM Invoice
GROUP BY year
ORDER BY year;
```

Число счетов добавлено намеренно: по нему видно, изменилась выручка из-за количества заказов или из-за их размера.

### Задание 5. Клиенты, потратившие больше 40 долларов

```sql
SELECT c.FirstName || ' ' || c.LastName AS customer,
       ROUND(SUM(i.Total), 2)           AS spent
FROM Customer AS c
JOIN Invoice AS i ON i.CustomerId = c.CustomerId
GROUP BY c.CustomerId, c.FirstName, c.LastName
HAVING SUM(i.Total) > 40
ORDER BY spent DESC;
```

Условие на сумму стоит в `HAVING`, а не в `WHERE`: мы отбираем группы по результату агрегации. `WHERE Total > 40` означало бы совсем другое — «оставить отдельные счета дороже 40».

### Задание 6. Самый популярный жанр в каждой стране

```sql
WITH genre_sales AS (
    SELECT i.BillingCountry AS country,
           g.Name           AS genre,
           SUM(il.Quantity) AS tracks_sold
    FROM InvoiceLine AS il
    JOIN Invoice AS i ON i.InvoiceId = il.InvoiceId
    JOIN Track   AS t ON t.TrackId = il.TrackId
    JOIN Genre   AS g ON g.GenreId = t.GenreId
    GROUP BY i.BillingCountry, g.Name
),
ranked AS (
    SELECT country,
           genre,
           tracks_sold,
           ROW_NUMBER() OVER (PARTITION BY country ORDER BY tracks_sold DESC) AS rn
    FROM genre_sales
)
SELECT country, genre, tracks_sold
FROM ranked
WHERE rn = 1
ORDER BY country;
```

Два шага — два CTE: сначала считаем продажи по парам «страна — жанр», потом нумеруем жанры внутри страны. Если хочешь при равенстве показать все жанры-лидеры, замени `ROW_NUMBER` на `RANK`.

### Задание 7. Первая покупка и «срок жизни» клиента

```sql
SELECT CustomerId,
       MIN(InvoiceDate)                                         AS first_purchase,
       MAX(InvoiceDate)                                         AS last_purchase,
       CAST(julianday(MAX(InvoiceDate)) - julianday(MIN(InvoiceDate)) AS INTEGER) AS days_between
FROM Invoice
GROUP BY CustomerId
ORDER BY days_between DESC;
```

В SQLite даты хранятся текстом, поэтому вычитать их напрямую нельзя: `julianday` переводит дату в число дней. В PostgreSQL то же самое пишется проще: `MAX(invoice_date) - MIN(invoice_date)`.

### Задание 8. Изменение выручки к предыдущему месяцу

```sql
WITH monthly AS (
    SELECT strftime('%Y-%m', InvoiceDate) AS month,
           SUM(Total)                     AS revenue
    FROM Invoice
    GROUP BY month
)
SELECT month,
       ROUND(revenue, 2) AS revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
             / LAG(revenue) OVER (ORDER BY month), 1) AS change_percent
FROM monthly
ORDER BY month;
```

У первого месяца `change_percent` будет `NULL` — предыдущего месяца нет, и это правильный ответ, а не ошибка. Множитель `100.0` (с точкой) снова защищает от целочисленного деления.

### Задание 9. Треки, которые ни разу не купили

```sql
SELECT t.TrackId,
       t.Name
FROM Track AS t
LEFT JOIN InvoiceLine AS il ON il.TrackId = t.TrackId
WHERE il.InvoiceLineId IS NULL
ORDER BY t.Name;
```

Классический приём «найти то, чего нет»: `LEFT JOIN` сохраняет все треки, а у непроданных в правой части оказывается `NULL`. Тот же результат даёт `WHERE NOT EXISTS (SELECT 1 FROM InvoiceLine AS il WHERE il.TrackId = t.TrackId)`.

### Задание 10. Клиенты и выручка сотрудников поддержки

```sql
SELECT e.FirstName || ' ' || e.LastName AS employee,
       COUNT(DISTINCT c.CustomerId)     AS customers,
       ROUND(SUM(i.Total), 2)           AS revenue
FROM Employee AS e
JOIN Customer AS c ON c.SupportRepId = e.EmployeeId
JOIN Invoice  AS i ON i.CustomerId = c.CustomerId
GROUP BY e.EmployeeId, e.FirstName, e.LastName
ORDER BY revenue DESC;
```

Здесь обязателен `COUNT(DISTINCT ...)`. После соединения с `Invoice` каждый клиент повторяется столько раз, сколько у него счетов, и обычный `COUNT(*)` посчитал бы счета, а не клиентов. Это та самая ловушка размножения строк из раздела 3.5.
