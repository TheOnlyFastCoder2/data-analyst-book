# Глава 3А. SQL: приёмы и трюки

В главе 3 ты выучил язык. Здесь — то, что отличает человека, знающего синтаксис, от аналитика, который уверенно решает задачи: типовые приёмы, ловушки и способы проверить себя. Почти всё из этой главы встречается на собеседованиях и в ежедневной работе.

## 3А.1. Учебная база

Чтобы каждый приём можно было проверить глазами, возьмём крошечную базу. Сохрани этот код как `setup.sql` и выполни в DB Browser for SQLite (вкладка Execute SQL) — или воспользуйся помощником на Python ниже.

```sql
CREATE TABLE users (
    user_id     INTEGER PRIMARY KEY,
    name        TEXT,
    city        TEXT,
    signup_date TEXT,
    referrer_id INTEGER
);

CREATE TABLE orders (
    order_id   INTEGER PRIMARY KEY,
    user_id    INTEGER,
    order_date TEXT,
    amount     REAL,
    status     TEXT
);

CREATE TABLE events (
    user_id    INTEGER,
    event_time TEXT,
    event      TEXT
);

CREATE TABLE employees (
    emp_id     INTEGER PRIMARY KEY,
    name       TEXT,
    manager_id INTEGER,
    dept       TEXT,
    salary     INTEGER
);

INSERT INTO users VALUES
    (1, 'Анна',   'Москва', '2026-01-03', NULL),
    (2, 'Борис',  'Казань', '2026-01-05', 1),
    (3, 'Вера',   'Москва', '2026-01-12', 1),
    (4, 'Глеб',   'Уфа',    '2026-01-20', 2),
    (5, 'Дарья',  NULL,     '2026-02-02', NULL),
    (6, 'Егор',   'Казань', '2026-02-10', 3);

INSERT INTO orders VALUES
    (101, 1, '2026-01-03', 1200, 'paid'),
    (102, 1, '2026-01-10', 800,  'paid'),
    (103, 2, '2026-01-06', 5000, 'paid'),
    (104, 1, '2026-01-25', 300,  'cancelled'),
    (105, 3, '2026-01-14', 2500, 'paid'),
    (106, 2, '2026-02-01', 700,  'paid'),
    (107, 1, '2026-02-07', 1500, 'paid'),
    (108, 4, '2026-02-09', 900,  'refunded'),
    (109, 3, '2026-02-15', 2500, 'paid'),
    (110, 6, '2026-02-20', 400,  'paid'),
    (111, 1, '2026-03-02', 2000, 'paid'),
    (112, 9, '2026-03-05', 100,  'paid');

INSERT INTO events VALUES
    (1, '2026-03-01 10:00:00', 'visit'),
    (1, '2026-03-01 10:05:00', 'view'),
    (1, '2026-03-01 10:07:00', 'cart'),
    (1, '2026-03-01 15:30:00', 'visit'),
    (1, '2026-03-01 15:32:00', 'purchase'),
    (1, '2026-03-02 09:00:00', 'visit'),
    (1, '2026-03-03 09:10:00', 'visit'),
    (2, '2026-03-01 11:00:00', 'visit'),
    (2, '2026-03-01 11:02:00', 'view'),
    (2, '2026-03-03 12:00:00', 'visit'),
    (2, '2026-03-04 12:00:00', 'visit'),
    (2, '2026-03-05 12:30:00', 'view'),
    (2, '2026-03-05 12:35:00', 'purchase'),
    (3, '2026-03-02 18:00:00', 'visit'),
    (3, '2026-03-02 18:03:00', 'view'),
    (3, '2026-03-02 18:04:00', 'cart'),
    (3, '2026-03-02 18:10:00', 'purchase');

INSERT INTO employees VALUES
    (1, 'Ольга',  NULL, 'Дирекция',  300),
    (2, 'Павел',  1,    'Аналитика', 200),
    (3, 'Рита',   1,    'Продажи',   180),
    (4, 'Семён',  2,    'Аналитика', 150),
    (5, 'Таня',   2,    'Аналитика', 150),
    (6, 'Ульяна', 3,    'Продажи',   120),
    (7, 'Фёдор',  4,    'Аналитика', 100);
```

В данных специально оставлены «неудобные» места: пользователь без города, заказ несуществующего пользователя (112), отменённые и возвращённые заказы, два сотрудника с одинаковой зарплатой. На них и ломаются наивные запросы.

Помощник для запуска запросов из Python:

```python
import sqlite3
from pathlib import Path

conn = sqlite3.connect(":memory:")
conn.executescript(Path("setup.sql").read_text(encoding="utf-8"))


def run(query):
    cursor = conn.execute(query)
    print(" | ".join(column[0] for column in cursor.description))
    for row in cursor:
        print(" | ".join(str(value) for value in row))
```

Все запросы главы написаны для SQLite и почти без изменений работают в PostgreSQL. Отличия диалектов собраны в разделе 3А.14.

## 3А.2. Условная агрегация

Главный рабочий приём аналитика: **условие внутри агрегатной функции**. Он позволяет посчитать несколько разных метрик за один проход по таблице.

```sql
SELECT COUNT(*)                                              AS orders_total,
       SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END)      AS orders_paid,
       SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) AS revenue,
       COUNT(DISTINCT CASE WHEN status = 'paid' THEN user_id END) AS buyers,
       ROUND(AVG(CASE WHEN status = 'paid' THEN amount END), 1)   AS avg_paid_check
FROM orders;
```

<!-- result -->
*Результат:*

| orders_total | orders_paid | revenue | buyers | avg_paid_check |
|---|---|---|---|---|
| 12 | 10 | 16700 | 5 | 1670 |
<!-- /result -->



Разбор:

- `SUM(CASE WHEN ... THEN 1 ELSE 0 END)` — количество строк, подходящих под условие.
- `SUM(CASE WHEN ... THEN amount ELSE 0 END)` — сумма по условию.
- `COUNT(DISTINCT CASE WHEN ... THEN user_id END)` — уникальные пользователи по условию. Здесь **нет `ELSE`**: для неподходящих строк `CASE` вернёт `NULL`, а `COUNT` пропуски не считает.
- В `AVG` тоже нельзя писать `ELSE 0` — нули попали бы в среднее и занизили его.

Доля считается как среднее от нулей и единиц:

```sql
SELECT ROUND(AVG(CASE WHEN status = 'paid' THEN 1.0 ELSE 0 END), 3) AS paid_share
FROM orders;
```

<!-- result -->
*Результат:*

| paid_share |
|---|
| 0.833 |
<!-- /result -->



В PostgreSQL и свежих версиях SQLite есть более читаемая запись — `FILTER`:

```sql
SELECT COUNT(*)                                       AS orders_total,
       COUNT(*) FILTER (WHERE status = 'paid')        AS orders_paid,
       SUM(amount) FILTER (WHERE status = 'paid')     AS revenue
FROM orders;
```

<!-- result -->
*Результат:*

| orders_total | orders_paid | revenue |
|---|---|---|
| 12 | 10 | 16700 |
<!-- /result -->



### Разворот таблицы (pivot)

Условная агрегация превращает строки в столбцы — аналог сводной таблицы:

```sql
SELECT strftime('%Y-%m', order_date)                             AS month,
       SUM(CASE WHEN status = 'paid'      THEN amount ELSE 0 END) AS paid,
       SUM(CASE WHEN status = 'cancelled' THEN amount ELSE 0 END) AS cancelled,
       SUM(CASE WHEN status = 'refunded'  THEN amount ELSE 0 END) AS refunded
FROM orders
GROUP BY month
ORDER BY month;
```

<!-- result -->
*Результат:*

| month | paid | cancelled | refunded |
|---|---|---|---|
| 2026-01 | 9500 | 300 | 0 |
| 2026-02 | 5100 | 0 | 900 |
| 2026-03 | 2100 | 0 | 0 |
<!-- /result -->



## 3А.3. Ловушки NULL

`NULL` означает «неизвестно», и любая операция с неизвестным даёт неизвестное. Отсюда несколько неочевидных следствий.

### Сравнение

```sql
SELECT COUNT(*)                                        AS all_users,
       SUM(CASE WHEN city = 'Москва'  THEN 1 ELSE 0 END) AS moscow,
       SUM(CASE WHEN city <> 'Москва' THEN 1 ELSE 0 END) AS not_moscow
FROM users;
```

<!-- result -->
*Результат:*

| all_users | moscow | not_moscow |
|---|---|---|
| 6 | 2 | 3 |
<!-- /result -->



Пользователей шесть, а `moscow + not_moscow` даёт пять. Дарья с неизвестным городом не попала **ни в одну** группу: условие `NULL <> 'Москва'` не истинно и не ложно — оно неизвестно.

Правило: если в столбце возможны пропуски, условие «не равно» нужно дополнять: `city <> 'Москва' OR city IS NULL`.

### NOT IN и NULL — самая опасная ловушка

Найдём пользователей, которые никого не пригласили:

```sql
-- Неправильно: вернёт ПУСТОЙ результат
SELECT name
FROM users
WHERE user_id NOT IN (SELECT referrer_id FROM users);
```

<!-- result -->
*Результат:*

| name |
|---|

*Запрос вернул 0 строк.*
<!-- /result -->



Подзапрос возвращает список `NULL, 1, 1, 2, NULL, 3`. Условие `x NOT IN (..., NULL)` никогда не бывает истинным: база не может утверждать, что `x` не равен неизвестному значению. Запрос молча вернёт ноль строк.

```sql
-- Правильно: NOT EXISTS не боится NULL
SELECT u.name
FROM users AS u
WHERE NOT EXISTS (
    SELECT 1
    FROM users AS invited
    WHERE invited.referrer_id = u.user_id
);
```

<!-- result -->
*Результат:*

| name |
|---|
| Глеб |
| Дарья |
| Егор |
<!-- /result -->



Привычка на всю жизнь: **для «нет в списке» используй `NOT EXISTS` или `LEFT JOIN ... IS NULL`, а не `NOT IN`**.

### Полезные функции

```sql
SELECT name,
       COALESCE(city, 'не указан')            AS city,        -- первое не-NULL значение
       NULLIF(city, 'Уфа')                     AS city_no_ufa, -- NULL, если значения равны
       COALESCE(referrer_id, 0)                AS referrer
FROM users;
```

<!-- result -->
*Результат:*

| name | city | city_no_ufa | referrer |
|---|---|---|---|
| Анна | Москва | Москва | 0 |
| Борис | Казань | Казань | 1 |
| Вера | Москва | Москва | 1 |
| Глеб | Уфа | NULL | 2 |
| Дарья | не указан | NULL | 0 |
| Егор | Казань | Казань | 3 |
<!-- /result -->



`NULLIF` — стандартная защита от деления на ноль:

```sql
SELECT 100.0 * 5 / NULLIF(0, 0) AS safe_ratio;      -- NULL вместо ошибки
```

<!-- result -->
*Результат:*

| safe_ratio |
|---|
| NULL |
<!-- /result -->



Запись `x / NULLIF(y, 0)` возвращает `NULL`, когда знаменатель равен нулю. Используй её в любой метрике-отношении.

### NULL в агрегатах и сортировке

- `SUM`, `AVG`, `MIN`, `MAX` пропускают `NULL`.
- `COUNT(*)` считает строки, `COUNT(столбец)` — только непустые значения.
- `SUM` по пустому набору строк даёт `NULL`, а не 0 — оборачивай в `COALESCE(SUM(x), 0)`.
- В `GROUP BY` все `NULL` попадают в одну группу.
- Положение `NULL` при сортировке зависит от базы; в PostgreSQL им управляют через `NULLS FIRST` и `NULLS LAST`.

## 3А.4. Проверки существования: полусоединение и антисоединение

Три способа ответить на вопрос «есть ли у пользователя оплаченные заказы»:

```sql
-- 1. EXISTS: останавливается на первом найденном заказе, не размножает строки
SELECT u.name
FROM users AS u
WHERE EXISTS (
    SELECT 1 FROM orders AS o
    WHERE o.user_id = u.user_id AND o.status = 'paid'
);
```

<!-- result -->
*Результат:*

| name |
|---|
| Анна |
| Борис |
| Вера |
| Егор |
<!-- /result -->



```sql
-- 2. IN: то же самое, читается проще
SELECT name
FROM users
WHERE user_id IN (SELECT user_id FROM orders WHERE status = 'paid');
```

<!-- result -->
*Результат:*

| name |
|---|
| Анна |
| Борис |
| Вера |
| Егор |
<!-- /result -->



```sql
-- 3. JOIN: нужен DISTINCT, иначе Анна появится четыре раза
SELECT DISTINCT u.name
FROM users AS u
JOIN orders AS o ON o.user_id = u.user_id
WHERE o.status = 'paid';
```

<!-- result -->
*Результат:*

| name |
|---|
| Анна |
| Борис |
| Вера |
| Егор |
<!-- /result -->



Обратная задача — «у кого оплаченных заказов нет»:

```sql
SELECT u.name
FROM users AS u
LEFT JOIN orders AS o
       ON o.user_id = u.user_id
      AND o.status = 'paid'          -- условие на правую таблицу стоит в ON
WHERE o.order_id IS NULL;
```

<!-- result -->
*Результат:*

| name |
|---|
| Глеб |
| Дарья |
<!-- /result -->



### Условие в ON или в WHERE

Это место, где ошибаются чаще всего. Сравни:

```sql
-- Условие в WHERE: LEFT JOIN незаметно превращается в INNER JOIN
SELECT u.name, COUNT(o.order_id) AS paid_orders
FROM users AS u
LEFT JOIN orders AS o ON o.user_id = u.user_id
WHERE o.status = 'paid'
GROUP BY u.user_id, u.name;
```

<!-- result -->
*Результат:*

| name | paid_orders |
|---|---|
| Анна | 4 |
| Борис | 2 |
| Вера | 2 |
| Егор | 1 |
<!-- /result -->



```sql
-- Условие в ON: все пользователи остаются, у кого нет оплат — ноль
SELECT u.name, COUNT(o.order_id) AS paid_orders
FROM users AS u
LEFT JOIN orders AS o
       ON o.user_id = u.user_id
      AND o.status = 'paid'
GROUP BY u.user_id, u.name;
```

<!-- result -->
*Результат:*

| name | paid_orders |
|---|---|
| Анна | 4 |
| Борис | 2 |
| Вера | 2 |
| Глеб | 0 |
| Дарья | 0 |
| Егор | 1 |
<!-- /result -->



В первом запросе у пользователей без заказов `o.status` равен `NULL`, условие `WHERE` их отбрасывает, и из шести пользователей остаются четыре. Во втором фильтр применяется к заказам **до** соединения, и в результате все шесть.

Правило: при `LEFT JOIN` условия на **правую** таблицу пиши в `ON`, условия на **левую** — в `WHERE`.

## 3А.5. Дедупликация и «последняя запись»

Задача встречается постоянно: оставить по одной строке на объект — последний заказ пользователя, актуальный статус, свежую версию записи.

```sql
WITH ranked AS (
    SELECT o.*,
           ROW_NUMBER() OVER (
               PARTITION BY user_id
               ORDER BY order_date DESC, order_id DESC
           ) AS rn
    FROM orders AS o
)
SELECT user_id, order_id, order_date, amount, status
FROM ranked
WHERE rn = 1
ORDER BY user_id;
```

<!-- result -->
*Результат:*

| user_id | order_id | order_date | amount | status |
|---|---|---|---|---|
| 1 | 111 | 2026-03-02 | 2000 | paid |
| 2 | 106 | 2026-02-01 | 700 | paid |
| 3 | 109 | 2026-02-15 | 2500 | paid |
| 4 | 108 | 2026-02-09 | 900 | refunded |
| 6 | 110 | 2026-02-20 | 400 | paid |
| 9 | 112 | 2026-03-05 | 100 | paid |
<!-- /result -->



Обрати внимание на `order_id DESC` в сортировке окна. Если у пользователя два заказа в один день, без второго ключа база выберет «первый» произвольно — и результат запроса будет меняться от запуска к запуску. **Сортировка внутри окна должна быть однозначной.**

Первая запись получается заменой `DESC` на `ASC`. Первая и последняя сразу — через `FIRST_VALUE`:

```sql
SELECT DISTINCT
       user_id,
       FIRST_VALUE(amount) OVER w AS first_amount,
       LAST_VALUE(amount)  OVER w AS last_amount
FROM orders
WINDOW w AS (
    PARTITION BY user_id
    ORDER BY order_date, order_id
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
);
```

<!-- result -->
*Результат:*

| user_id | first_amount | last_amount |
|---|---|---|
| 1 | 1200 | 2000 |
| 2 | 5000 | 700 |
| 3 | 2500 | 2500 |
| 4 | 900 | 900 |
| 6 | 400 | 400 |
| 9 | 100 | 100 |
<!-- /result -->



Рамка `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` обязательна для `LAST_VALUE`: по умолчанию окно заканчивается на текущей строке, и «последним значением» оказывается сама текущая строка. Конструкция `WINDOW w AS (...)` даёт окну имя, чтобы не повторять его описание.

### Поиск дубликатов

```sql
SELECT user_id, amount, COUNT(*) AS copies
FROM orders
GROUP BY user_id, amount
HAVING COUNT(*) > 1;
```

<!-- result -->
*Результат:*

| user_id | amount | copies |
|---|---|---|
| 3 | 2500 | 2 |
<!-- /result -->



## 3А.6. Ранжирование: топ-N и «второе по величине»

Классика собеседований — вторая по величине зарплата:

```sql
SELECT MAX(salary) AS second_salary
FROM employees
WHERE salary < (SELECT MAX(salary) FROM employees);
```

<!-- result -->
*Результат:*

| second_salary |
|---|
| 200 |
<!-- /result -->



Универсальное решение для N-й по величине — `DENSE_RANK`:

```sql
WITH ranked AS (
    SELECT name, dept, salary,
           DENSE_RANK() OVER (ORDER BY salary DESC) AS salary_rank
    FROM employees
)
SELECT name, salary
FROM ranked
WHERE salary_rank = 3;
```

<!-- result -->
*Результат:*

| name | salary |
|---|---|
| Рита | 180 |
<!-- /result -->



Здесь нужен именно `DENSE_RANK`. Зарплаты: 300, 200, 180, 150, 150… `ROW_NUMBER` пронумеровал бы двух сотрудников с зарплатой 150 как 4 и 5 и «потерял» бы одного из них; `RANK` при совпадениях пропускает номера.

Топ-2 по зарплате в каждом отделе и сравнение со средним по отделу:

```sql
WITH ranked AS (
    SELECT name, dept, salary,
           ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC, emp_id) AS rn,
           ROUND(AVG(salary) OVER (PARTITION BY dept), 1)                     AS dept_avg
    FROM employees
)
SELECT dept, name, salary, dept_avg, salary - dept_avg AS diff_from_avg
FROM ranked
WHERE rn <= 2
ORDER BY dept, rn;
```

<!-- result -->
*Результат:*

| dept | name | salary | dept_avg | diff_from_avg |
|---|---|---|---|---|
| Аналитика | Павел | 200 | 150 | 50 |
| Аналитика | Семён | 150 | 150 | 0 |
| Дирекция | Ольга | 300 | 300 | 0 |
| Продажи | Рита | 180 | 150 | 30 |
| Продажи | Ульяна | 120 | 150 | -30 |
<!-- /result -->



### Разбивка на группы: NTILE

`NTILE(n)` делит строки на `n` примерно равных групп — так получают квартили и децили:

```sql
SELECT user_id,
       SUM(amount)                               AS spent,
       NTILE(3) OVER (ORDER BY SUM(amount) DESC) AS tier
FROM orders
WHERE status = 'paid'
GROUP BY user_id;
```

<!-- result -->
*Результат:*

| user_id | spent | tier |
|---|---|---|
| 2 | 5700 | 1 |
| 1 | 5500 | 1 |
| 3 | 5000 | 2 |
| 6 | 400 | 2 |
| 9 | 100 | 3 |
<!-- /result -->



Оконная функция здесь применяется поверх агрегата: сначала выполняется `GROUP BY`, затем окно работает уже с результатом группировки.

## 3А.7. Доли, накопительные итоги и скользящие окна

`OVER ()` с пустыми скобками — окно на всю таблицу. Так считают долю от итога без подзапроса:

```sql
SELECT city,
       COUNT(*)                                          AS users,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_percent
FROM users
GROUP BY city
ORDER BY users DESC;
```

<!-- result -->
*Результат:*

| city | users | share_percent |
|---|---|---|
| Казань | 2 | 33.3 |
| Москва | 2 | 33.3 |
| NULL | 1 | 16.7 |
| Уфа | 1 | 16.7 |
<!-- /result -->



Накопительный итог и накопительная доля — основа ABC-анализа и правила Парето:

```sql
WITH user_revenue AS (
    SELECT user_id, SUM(amount) AS revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY user_id
)
SELECT user_id,
       revenue,
       SUM(revenue) OVER (ORDER BY revenue DESC, user_id)                    AS running_total,
       ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC, user_id)
             / SUM(revenue) OVER (), 1)                                      AS cumulative_percent
FROM user_revenue
ORDER BY revenue DESC;
```

<!-- result -->
*Результат:*

| user_id | revenue | running_total | cumulative_percent |
|---|---|---|---|
| 2 | 5700 | 5700 | 34.1 |
| 1 | 5500 | 11200 | 67.1 |
| 3 | 5000 | 16200 | 97 |
| 6 | 400 | 16600 | 99.4 |
| 9 | 100 | 16700 | 100 |
<!-- /result -->



### Рамка окна

По умолчанию окно с `ORDER BY` охватывает строки от начала до текущей. Рамку можно задать явно:

| Рамка | Что охватывает |
|-------|----------------|
| `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` | От начала до текущей — накопительный итог |
| `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` | Текущая и две предыдущие — скользящее окно из трёх строк |
| `ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING` | Соседи с обеих сторон |
| `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` | Вся группа |

```sql
SELECT order_date,
       amount,
       ROUND(AVG(amount) OVER (
           ORDER BY order_date, order_id
           ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
       ), 1) AS moving_avg_3
FROM orders
WHERE status = 'paid';
```

<!-- result -->
*Результат:*

| order_date | amount | moving_avg_3 |
|---|---|---|
| 2026-01-03 | 1200 | 1200 |
| 2026-01-06 | 5000 | 3100 |
| 2026-01-10 | 800 | 2333.3 |
| 2026-01-14 | 2500 | 2766.7 |
| 2026-02-01 | 700 | 1333.3 |
| 2026-02-07 | 1500 | 1566.7 |
| 2026-02-15 | 2500 | 1566.7 |
| 2026-02-20 | 400 | 1466.7 |

*Показаны первые 8 строк из 10.*
<!-- /result -->



Важная тонкость: `ROWS` считает **строки**, а не дни. Если в данных пропущен день, «среднее за 7 дней» через `ROWS BETWEEN 6 PRECEDING` захватит больше недели. Сначала нужно получить по строке на каждый день — об этом следующий раздел.

## 3А.8. Календарь и заполнение пропусков в датах

Если в какой-то день не было заказов, `GROUP BY` этот день просто не покажет. На графике такая дыра выглядит как плавная линия, а в скользящем среднем создаёт ошибку.

Решение — сгенерировать полный список дат и присоединить к нему данные. Список строится **рекурсивным CTE**:

```sql
WITH RECURSIVE calendar(day) AS (
    SELECT '2026-01-01'                 -- начало
    UNION ALL
    SELECT date(day, '+1 day')          -- шаг
    FROM calendar
    WHERE day < '2026-01-10'            -- условие остановки
)
SELECT c.day,
       COUNT(o.order_id)          AS orders,
       COALESCE(SUM(o.amount), 0) AS revenue
FROM calendar AS c
LEFT JOIN orders AS o
       ON o.order_date = c.day
      AND o.status = 'paid'
GROUP BY c.day
ORDER BY c.day;
```

<!-- result -->
*Результат:*

| day | orders | revenue |
|---|---|---|
| 2026-01-01 | 0 | 0 |
| 2026-01-02 | 0 | 0 |
| 2026-01-03 | 1 | 1200 |
| 2026-01-04 | 0 | 0 |
| 2026-01-05 | 0 | 0 |
| 2026-01-06 | 1 | 5000 |
| 2026-01-07 | 0 | 0 |
| 2026-01-08 | 0 | 0 |

*Показаны первые 8 строк из 10.*
<!-- /result -->



Рекурсивный CTE состоит из трёх частей: начальная строка, шаг, который ссылается на сам CTE, и условие остановки. Без условия остановки запрос будет работать бесконечно.

Здесь сошлись сразу три приёма главы: календарь, условие на правую таблицу в `ON` и `COALESCE` для нулей.

В PostgreSQL календарь строится одной функцией: `generate_series('2026-01-01'::date, '2026-01-10', '1 day')`. В больших компаниях обычно есть готовая таблица-календарь с признаками рабочих дней и праздников.

## 3А.9. Острова и разрывы: серии подряд идущих дней

Задача: найти у каждого пользователя серии дней подряд, когда он заходил в продукт. Так считают «ударные режимы» и вовлечённость.

Идея решения красивая. Пронумеруем дни активности пользователя по порядку и вычтем номер из даты. Для дней, идущих подряд, разность будет **одинаковой**: дата растёт на единицу и номер растёт на единицу.

| День | Номер | День − номер |
|------|-------|--------------|
| 1 марта | 1 | 28 февраля |
| 2 марта | 2 | 28 февраля |
| 3 марта | 3 | 28 февраля |
| 5 марта | 4 | 1 марта |

Первые три дня образуют одну серию, четвёртый начинает новую.

```sql
WITH days AS (
    SELECT DISTINCT user_id, date(event_time) AS day
    FROM events
),
numbered AS (
    SELECT user_id,
           day,
           date(day, '-' || ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY day) || ' day') AS island
    FROM days
)
SELECT user_id,
       MIN(day) AS streak_start,
       MAX(day) AS streak_end,
       COUNT(*) AS streak_days
FROM numbered
GROUP BY user_id, island
ORDER BY user_id, streak_start;
```

<!-- result -->
*Результат:*

| user_id | streak_start | streak_end | streak_days |
|---|---|---|---|
| 1 | 2026-03-01 | 2026-03-03 | 3 |
| 2 | 2026-03-01 | 2026-03-01 | 1 |
| 2 | 2026-03-03 | 2026-03-05 | 3 |
| 3 | 2026-03-02 | 2026-03-02 | 1 |
<!-- /result -->



Первый CTE обязателен: в один день может быть несколько событий, а нам нужна одна строка на день.

Самая длинная серия каждого пользователя получается ещё одним `MAX(streak_days) ... GROUP BY user_id` поверх этого запроса.

## 3А.10. Сессии

В логе событий нет понятия «сессия» — его вводит аналитик. Обычное определение: новая сессия начинается, если с предыдущего события прошло больше 30 минут.

Приём в три шага: найти предыдущее событие через `LAG`, пометить начала сессий флагом, получить номер сессии накопительной суммой флагов.

```sql
WITH with_prev AS (
    SELECT user_id,
           event_time,
           event,
           LAG(event_time) OVER (PARTITION BY user_id ORDER BY event_time) AS prev_time
    FROM events
),
flagged AS (
    SELECT *,
           CASE
               WHEN prev_time IS NULL THEN 1
               WHEN (julianday(event_time) - julianday(prev_time)) * 24 * 60 > 30 THEN 1
               ELSE 0
           END AS is_new_session
    FROM with_prev
),
sessions AS (
    SELECT *,
           SUM(is_new_session) OVER (PARTITION BY user_id ORDER BY event_time) AS session_num
    FROM flagged
)
SELECT user_id,
       session_num,
       MIN(event_time) AS session_start,
       COUNT(*)        AS events,
       ROUND((julianday(MAX(event_time)) - julianday(MIN(event_time))) * 24 * 60, 1) AS minutes,
       MAX(CASE WHEN event = 'purchase' THEN 1 ELSE 0 END) AS has_purchase
FROM sessions
GROUP BY user_id, session_num
ORDER BY user_id, session_num;
```

<!-- result -->
*Результат:*

| user_id | session_num | session_start | events | minutes | has_purchase |
|---|---|---|---|---|---|
| 1 | 1 | 2026-03-01 10:00:00 | 3 | 7 | 0 |
| 1 | 2 | 2026-03-01 15:30:00 | 2 | 2 | 1 |
| 1 | 3 | 2026-03-02 09:00:00 | 1 | 0 | 0 |
| 1 | 4 | 2026-03-03 09:10:00 | 1 | 0 | 0 |
| 2 | 1 | 2026-03-01 11:00:00 | 2 | 2 | 0 |
| 2 | 2 | 2026-03-03 12:00:00 | 1 | 0 | 0 |
| 2 | 3 | 2026-03-04 12:00:00 | 1 | 0 | 0 |
| 2 | 4 | 2026-03-05 12:30:00 | 2 | 5 | 1 |

*Показаны первые 8 строк из 9.*
<!-- /result -->



Связка **«флаг начала + накопительная сумма флагов»** — универсальный способ нумеровать группы подряд идущих строк. Тем же приёмом находят периоды с одинаковым статусом, непрерывные подписки и серии побед.

## 3А.11. Воронка в SQL

Простая воронка — сколько пользователей совершили каждое событие:

```sql
SELECT COUNT(DISTINCT CASE WHEN event = 'visit'    THEN user_id END) AS visited,
       COUNT(DISTINCT CASE WHEN event = 'view'     THEN user_id END) AS viewed,
       COUNT(DISTINCT CASE WHEN event = 'cart'     THEN user_id END) AS added_to_cart,
       COUNT(DISTINCT CASE WHEN event = 'purchase' THEN user_id END) AS purchased
FROM events;
```

<!-- result -->
*Результат:*

| visited | viewed | added_to_cart | purchased |
|---|---|---|---|
| 3 | 3 | 2 | 3 |
<!-- /result -->



Строгая воронка учитывает порядок: шаг засчитывается, только если он случился **после** предыдущего. Для каждого пользователя находим время первого наступления каждого шага и сравниваем:

```sql
WITH first_times AS (
    SELECT user_id,
           MIN(CASE WHEN event = 'visit'    THEN event_time END) AS t_visit,
           MIN(CASE WHEN event = 'view'     THEN event_time END) AS t_view,
           MIN(CASE WHEN event = 'cart'     THEN event_time END) AS t_cart,
           MIN(CASE WHEN event = 'purchase' THEN event_time END) AS t_purchase
    FROM events
    GROUP BY user_id
)
SELECT COUNT(*)                                                             AS step_1_visit,
       SUM(CASE WHEN t_view > t_visit THEN 1 ELSE 0 END)                    AS step_2_view,
       SUM(CASE WHEN t_view > t_visit AND t_cart > t_view THEN 1 ELSE 0 END) AS step_3_cart,
       SUM(CASE WHEN t_view > t_visit AND t_cart > t_view
                 AND t_purchase > t_cart THEN 1 ELSE 0 END)                 AS step_4_purchase
FROM first_times
WHERE t_visit IS NOT NULL;
```

<!-- result -->
*Результат:*

| step_1_visit | step_2_view | step_3_cart | step_4_purchase |
|---|---|---|---|
| 3 | 3 | 2 | 2 |
<!-- /result -->



В простой воронке покупателей трое, в строгой — двое. Борис купил, ни разу не добавив товар в корзину: например, через кнопку «Купить в один клик». Расхождение простой и строгой воронок — не ошибка, а находка: оно показывает, что часть пользователей идёт к покупке другим путём, и воронку стоит рисовать с учётом этого.

## 3А.12. Когорты и удержание в SQL

Когорта — месяц первой оплаченной покупки. Для каждого заказа считаем, на какой по счёту месяц жизни пользователя он пришёлся.

```sql
WITH paid AS (
    SELECT user_id, order_date
    FROM orders
    WHERE status = 'paid'
),
first_order AS (
    SELECT user_id, MIN(order_date) AS first_date
    FROM paid
    GROUP BY user_id
),
activity AS (
    SELECT p.user_id,
           strftime('%Y-%m', f.first_date) AS cohort,
           (CAST(strftime('%Y', p.order_date) AS INTEGER) - CAST(strftime('%Y', f.first_date) AS INTEGER)) * 12
         + (CAST(strftime('%m', p.order_date) AS INTEGER) - CAST(strftime('%m', f.first_date) AS INTEGER)) AS month_number
    FROM paid AS p
    JOIN first_order AS f ON f.user_id = p.user_id
)
SELECT cohort,
       COUNT(DISTINCT CASE WHEN month_number = 0 THEN user_id END) AS m0,
       COUNT(DISTINCT CASE WHEN month_number = 1 THEN user_id END) AS m1,
       COUNT(DISTINCT CASE WHEN month_number = 2 THEN user_id END) AS m2,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN month_number = 1 THEN user_id END)
             / COUNT(DISTINCT CASE WHEN month_number = 0 THEN user_id END), 1) AS retention_m1
FROM activity
GROUP BY cohort
ORDER BY cohort;
```

<!-- result -->
*Результат:*

| cohort | m0 | m1 | m2 | retention_m1 |
|---|---|---|---|---|
| 2026-01 | 3 | 3 | 1 | 100 |
| 2026-02 | 1 | 0 | 0 | 0 |
| 2026-03 | 1 | 0 | 0 | 0 |
<!-- /result -->



Структура одинакова для любого когортного расчёта: дата первого события → номер периода для каждого события → условная агрегация по номерам периодов.

В PostgreSQL разность в месяцах пишется короче — через `DATE_TRUNC` и `AGE`.

## 3А.13. Соединение таблицы с самой собой и иерархии

### Self-join

Таблицу можно соединить с самой собой, дав ей два псевдонима. Кто кого пригласил:

```sql
SELECT u.name                                  AS user,
       COALESCE(r.name, '— пришёл сам —')       AS invited_by
FROM users AS u
LEFT JOIN users AS r ON r.user_id = u.referrer_id;
```

<!-- result -->
*Результат:*

| user | invited_by |
|---|---|
| Анна | — пришёл сам — |
| Борис | Анна |
| Вера | Анна |
| Глеб | Борис |
| Дарья | — пришёл сам — |
| Егор | Вера |
<!-- /result -->



Сколько человек пригласил каждый:

```sql
SELECT r.name, COUNT(u.user_id) AS invited
FROM users AS r
LEFT JOIN users AS u ON u.referrer_id = r.user_id
GROUP BY r.user_id, r.name
ORDER BY invited DESC, r.name;
```

<!-- result -->
*Результат:*

| name | invited |
|---|---|
| Анна | 2 |
| Борис | 1 |
| Вера | 1 |
| Глеб | 0 |
| Дарья | 0 |
| Егор | 0 |
<!-- /result -->



Сотрудники, которые зарабатывают больше половины зарплаты своего руководителя:

```sql
SELECT e.name, e.salary, m.name AS manager, m.salary AS manager_salary
FROM employees AS e
JOIN employees AS m ON m.emp_id = e.manager_id
WHERE e.salary > m.salary * 0.5;
```

<!-- result -->
*Результат:*

| name | salary | manager | manager_salary |
|---|---|---|---|
| Павел | 200 | Ольга | 300 |
| Рита | 180 | Ольга | 300 |
| Семён | 150 | Павел | 200 |
| Таня | 150 | Павел | 200 |
| Ульяна | 120 | Рита | 180 |
| Фёдор | 100 | Семён | 150 |
<!-- /result -->



### Все пары

Соединение с условием-неравенством даёт все пары без повторов — пригодится для попарных сравнений:

```sql
SELECT a.name AS first, b.name AS second
FROM employees AS a
JOIN employees AS b ON a.emp_id < b.emp_id
WHERE a.dept = b.dept;
```

<!-- result -->
*Результат:*

| first | second |
|---|---|
| Павел | Семён |
| Павел | Таня |
| Павел | Фёдор |
| Рита | Ульяна |
| Семён | Таня |
| Семён | Фёдор |
| Таня | Фёдор |
<!-- /result -->



Условие `a.emp_id < b.emp_id` убирает и пары «сам с собой», и зеркальные дубли (Семён–Таня и Таня–Семён).

### Иерархия: рекурсивный обход

Self-join показывает один уровень подчинения. Чтобы пройти всё дерево, нужен рекурсивный CTE:

```sql
WITH RECURSIVE tree AS (
    SELECT emp_id, name, manager_id, 1 AS level, name AS path
    FROM employees
    WHERE manager_id IS NULL                  -- начинаем с директора

    UNION ALL

    SELECT e.emp_id, e.name, e.manager_id, t.level + 1, t.path || ' → ' || e.name
    FROM employees AS e
    JOIN tree AS t ON e.manager_id = t.emp_id  -- подчинённые тех, кто уже в дереве
)
SELECT level, name, path
FROM tree
ORDER BY path;
```

<!-- result -->
*Результат:*

| level | name | path |
|---|---|---|
| 1 | Ольга | Ольга |
| 2 | Павел | Ольга → Павел |
| 3 | Семён | Ольга → Павел → Семён |
| 4 | Фёдор | Ольга → Павел → Семён → Фёдор |
| 3 | Таня | Ольга → Павел → Таня |
| 2 | Рита | Ольга → Рита |
| 3 | Ульяна | Ольга → Рита → Ульяна |
<!-- /result -->



Так же обходят категории товаров, структуру подразделений и цепочки рефералов.

## 3А.14. Медиана, перцентили и отличия диалектов

В стандартном SQL нет функции `MEDIAN`. В PostgreSQL медиану и перцентили считают так:

```
SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount) AS median,
       PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY amount) AS p90
FROM orders;
```

В SQLite этой функции нет, поэтому медиану собирают вручную — хорошее упражнение на оконные функции:

```sql
WITH ordered AS (
    SELECT amount,
           ROW_NUMBER() OVER (ORDER BY amount) AS rn,
           COUNT(*) OVER ()                    AS total
    FROM orders
    WHERE status = 'paid'
)
SELECT AVG(amount) AS median
FROM ordered
WHERE rn IN ((total + 1) / 2, (total + 2) / 2);
```

<!-- result -->
*Результат:*

| median |
|---|
| 1350 |
<!-- /result -->



При нечётном количестве оба выражения в `IN` дают один и тот же средний номер, при чётном — два соседних, и `AVG` усредняет их.

### Шпаргалка по диалектам

Логика запросов везде одинаковая, отличаются в основном функции дат и строк.

| Задача | SQLite | PostgreSQL | ClickHouse |
|--------|--------|------------|------------|
| Начало месяца | `strftime('%Y-%m-01', d)` | `DATE_TRUNC('month', d)` | `toStartOfMonth(d)` |
| Год | `strftime('%Y', d)` | `EXTRACT(YEAR FROM d)` | `toYear(d)` |
| День недели | `strftime('%w', d)` | `EXTRACT(DOW FROM d)` | `toDayOfWeek(d)` |
| Прибавить день | `date(d, '+1 day')` | `d + INTERVAL '1 day'` | `d + INTERVAL 1 DAY` |
| Разница в днях | `julianday(a) - julianday(b)` | `a - b` | `dateDiff('day', b, a)` |
| Сегодня | `date('now')` | `CURRENT_DATE` | `today()` |
| Склейка строк | `a \|\| b` | `a \|\| b` | `concat(a, b)` |
| Приведение типа | `CAST(x AS INTEGER)` | `x::int` | `toInt32(x)` |
| Склеить значения группы | `GROUP_CONCAT(x, ', ')` | `STRING_AGG(x, ', ')` | `arrayStringConcat(groupArray(x), ', ')` |
| Уникальные значения | `COUNT(DISTINCT x)` | `COUNT(DISTINCT x)` | `uniqExact(x)` |
| Ряд дат | рекурсивный CTE | `generate_series(...)` | `arrayJoin(range(...))` |

Не заучивай таблицу. Запомни, что такие функции существуют, и ищи точное название в документации своей базы.

Пример склейки значений группы — список заказов каждого пользователя в одной ячейке:

```sql
SELECT user_id,
       COUNT(*)                     AS orders,
       GROUP_CONCAT(order_id, ', ') AS order_ids
FROM orders
GROUP BY user_id;
```

<!-- result -->
*Результат:*

| user_id | orders | order_ids |
|---|---|---|
| 1 | 5 | 101, 102, 104, 107, 111 |
| 2 | 2 | 103, 106 |
| 3 | 2 | 105, 109 |
| 4 | 1 | 108 |
| 6 | 1 | 110 |
| 9 | 1 | 112 |
<!-- /result -->



## 3А.15. Агрегируй до соединения

Вернёмся к ловушке размножения строк. Посчитаем для каждого пользователя число оплаченных заказов и число событий:

```sql
-- Неправильно: заказы и события перемножаются
SELECT u.name,
       COUNT(o.order_id)   AS orders,
       COUNT(e.event_time) AS events
FROM users AS u
LEFT JOIN orders AS o ON o.user_id = u.user_id AND o.status = 'paid'
LEFT JOIN events AS e ON e.user_id = u.user_id
GROUP BY u.user_id, u.name;
```

<!-- result -->
*Результат:*

| name | orders | events |
|---|---|---|
| Анна | 28 | 28 |
| Борис | 12 | 12 |
| Вера | 8 | 8 |
| Глеб | 0 | 0 |
| Дарья | 0 | 0 |
| Егор | 1 | 0 |
<!-- /result -->



У Анны 4 оплаченных заказа и 7 событий. Запрос вернёт 28 и 28: каждая строка заказа соединилась с каждой строкой события.

```sql
-- Правильно: сначала свернуть каждую таблицу до одной строки на пользователя
WITH order_stats AS (
    SELECT user_id, COUNT(*) AS orders, SUM(amount) AS revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY user_id
),
event_stats AS (
    SELECT user_id, COUNT(*) AS events
    FROM events
    GROUP BY user_id
)
SELECT u.name,
       COALESCE(o.orders, 0)  AS orders,
       COALESCE(o.revenue, 0) AS revenue,
       COALESCE(e.events, 0)  AS events
FROM users AS u
LEFT JOIN order_stats AS o ON o.user_id = u.user_id
LEFT JOIN event_stats AS e ON e.user_id = u.user_id
ORDER BY u.user_id;
```

<!-- result -->
*Результат:*

| name | orders | revenue | events |
|---|---|---|---|
| Анна | 4 | 5500 | 7 |
| Борис | 2 | 5700 | 6 |
| Вера | 2 | 5000 | 4 |
| Глеб | 0 | 0 | 0 |
| Дарья | 0 | 0 | 0 |
| Егор | 1 | 400 | 0 |
<!-- /result -->



Правило: **если к одной таблице присоединяются две таблицы «один ко многим», каждую нужно сначала агрегировать до ключа соединения.** Заодно такой запрос работает быстрее.

Думай в терминах **зерна таблицы** — того, что означает одна строка. У `users` зерно — пользователь, у `orders` — заказ, у `events` — событие. Перед каждым `JOIN` спрашивай себя: какое зерно будет у результата?

## 3А.16. Производительность

На учебной базе всё работает мгновенно. На таблице в миллиард строк плохой запрос выполняется часами и мешает коллегам.

### Что делать всегда

1. **Фильтруй как можно раньше.** Особенно по дате: большие таблицы обычно разбиты на части (партиции) по дате, и условие на дату позволяет прочитать только нужные.
2. **Выбирай только нужные столбцы.** В колоночных базах (ClickHouse, BigQuery) `SELECT *` читает с диска все столбцы, а запрос с двумя столбцами — только их.
3. **Агрегируй до соединения** (раздел 3А.15).
4. **Отлаживай на малом.** Пиши запрос на одном дне данных или с `LIMIT`, на полный период запускай готовый.
5. **Не оборачивай столбец в функцию в условии.**

Последний пункт подробнее:

```sql
-- Плохо: функция вычисляется для каждой строки, индекс по order_date не работает
SELECT COUNT(*) FROM orders
WHERE strftime('%Y-%m', order_date) = '2026-02';
```

<!-- result -->
*Результат:*

| COUNT(*) |
|---|
| 5 |
<!-- /result -->



```sql
-- Хорошо: столбец сравнивается с константами, индекс работает
SELECT COUNT(*) FROM orders
WHERE order_date >= '2026-02-01'
  AND order_date <  '2026-03-01';
```

<!-- result -->
*Результат:*

| COUNT(*) |
|---|
| 5 |
<!-- /result -->



Полуоткрытый интервал `>= начало AND < следующее начало` — самый надёжный способ фильтровать по периоду. Он не зависит от числа дней в месяце и правильно работает со временем. Запись `BETWEEN '2026-02-01' AND '2026-02-28'` потеряет заказы 28 февраля после полуночи, если в столбце хранится время.

### Индексы

Индекс — вспомогательная структура, позволяющая находить строки без просмотра всей таблицы; как алфавитный указатель в книге.

```sql
CREATE INDEX idx_orders_user ON orders (user_id);
```

Аналитик редко создаёт индексы сам, но должен понимать: фильтр и соединение по индексированному столбцу быстрые, по неиндексированному — медленные.

### План запроса

Команда `EXPLAIN` показывает, как база собирается выполнять запрос:

```sql
EXPLAIN QUERY PLAN
SELECT * FROM orders WHERE user_id = 1;
```

<!-- result -->
*Результат:*

| id | parent | notused | detail |
|---|---|---|---|
| 3 | 0 | 61 | SEARCH orders USING INDEX idx_orders_user (user_id=?) |
<!-- /result -->



В SQLite слово `SEARCH ... USING INDEX` означает поиск по индексу, `SCAN` — полный просмотр таблицы. В PostgreSQL используют `EXPLAIN ANALYZE` и ищут `Seq Scan` по большим таблицам.

### Прочее

- `UNION ALL` быстрее `UNION`: второй дополнительно убирает дубликаты. Если дубликатов быть не может — пиши `UNION ALL`.
- `COUNT(DISTINCT ...)` на огромных таблицах дорог. В ClickHouse и BigQuery есть приближённые функции (`uniq`, `APPROX_COUNT_DISTINCT`) с ошибкой в доли процента.
- `ORDER BY` без `LIMIT` на большом результате — лишняя работа. Сортируй только итог.

## 3А.17. Как проверить, что запрос верный

Запрос, который выполнился без ошибки, не обязательно верен. Набор проверок, которые стоит делать всегда:

**1. Сверь число строк до и после соединения.**

```sql
SELECT (SELECT COUNT(*) FROM orders)                                             AS before_join,
       (SELECT COUNT(*) FROM orders AS o JOIN users AS u ON u.user_id = o.user_id) AS after_join;
```

<!-- result -->
*Результат:*

| before_join | after_join |
|---|---|
| 12 | 11 |
<!-- /result -->



Было 12, стало 11: заказ 112 принадлежит несуществующему пользователю и пропал при `INNER JOIN`. Если бы стало больше — в `users` были бы дубликаты ключа.

**2. Проверь уникальность ключа.**

```sql
SELECT user_id, COUNT(*) AS copies
FROM users
GROUP BY user_id
HAVING COUNT(*) > 1;
```

<!-- result -->
*Результат:*

| user_id | copies |
|---|---|

*Запрос вернул 0 строк.*
<!-- /result -->



Пустой результат означает, что ключ уникален.

**3. Сверь итог с известным числом.** Сумма по группам должна равняться общей сумме, выручка в твоём запросе — совпадать с цифрой на дашборде.

**4. Проверь на одном объекте вручную.** Возьми одного пользователя, посмотри все его строки глазами и убедись, что запрос даёт для него правильный ответ.

**5. Посмотри на крайние значения.** `MIN`, `MAX`, число `NULL`: отрицательные суммы, даты из будущего и 1970 года выдают проблемы в данных.

**6. Собирай запрос по шагам.** Каждый CTE можно выполнить отдельно, заменив финальный `SELECT` на `SELECT * FROM имя_cte LIMIT 20`.

## 3А.18. Временные таблицы и представления

Когда промежуточный результат нужен в нескольких запросах, его можно сохранить.

```sql
CREATE TEMP TABLE paid_orders AS
SELECT * FROM orders WHERE status = 'paid';
```

```sql
CREATE VIEW user_revenue AS
SELECT user_id, COUNT(*) AS orders, SUM(amount) AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY user_id;
```

| | CTE | Временная таблица | Представление (VIEW) |
|---|---|---|---|
| Живёт | Один запрос | До конца сеанса | Постоянно |
| Хранит данные | Нет | Да | Нет: это сохранённый запрос |
| Когда использовать | Разбить запрос на шаги | Тяжёлый промежуточный результат нужен много раз | Общее определение метрики для всей команды |

Представления особенно полезны для единых определений: если «оплаченный заказ» описан в одном месте, двадцать аналитиков не напишут двадцать разных условий.

## Практика на GitHub

- [jesussantana/sql-data-analysis](https://github.com/jesussantana/sql-data-analysis) — теперь решай задачи, сознательно применяя приёмы главы: условную агрегацию, `ROW_NUMBER` для дедупликации, оконные рамки.
- [lerocha/chinook-database](https://github.com/lerocha/chinook-database) — задания ниже рассчитаны на учебную базу главы, но каждое стоит повторить на Chinook: там больше данных и результат менее очевиден.
- [noztas/DataAnalystProjects](https://github.com/noztas/DataAnalystProjects) и [AsifRashid01/DataAnalyst_PortfolioProjects](https://github.com/AsifRashid01/DataAnalyst_PortfolioProjects) — посмотри, как в проектах очистки данных применяются CTE и оконные функции для поиска дубликатов.
- [Lenupcik/portfolio](https://github.com/Lenupcik/portfolio) — запросы к демо-базе «Авиаперевозки»: попробуй написать для неё запросы на сессии, серии и когорты.

## Задания

На учебной базе главы:

1. Одним запросом посчитай по каждому пользователю: число всех заказов, число оплаченных, сумму оплаченных и долю отменённых или возвращённых. В результате должны быть все шесть пользователей.
2. Найди заказы, у которых нет пользователя в таблице `users`, и пользователей, у которых нет ни одного заказа.
3. Для каждого пользователя выведи его первый и последний оплаченный заказ (дату и сумму) в одной строке.
4. Найди сотрудников, получающих больше среднего по своему отделу.
5. Посчитай выручку по каждому дню февраля 2026 года, включая дни без заказов, и накопительную выручку с начала месяца.
6. Для каждого оплаченного заказа посчитай, сколько дней прошло с предыдущего оплаченного заказа того же пользователя. Найди средний интервал между покупками.
7. Определи самую длинную серию дней подряд с активностью для каждого пользователя.
8. Для каждого сотрудника выведи число всех его подчинённых — прямых и непрямых.
9. Найди пользователей, которые сделали покупку в течение 7 дней после регистрации.

## Проверь себя

- Зачем в `COUNT(DISTINCT CASE WHEN ... THEN user_id END)` не пишут `ELSE`?
- Почему `NOT IN` с подзапросом может вернуть пустой результат?
- Чем условие в `ON` отличается от условия в `WHERE` при `LEFT JOIN`?
- Почему сортировка внутри окна должна быть однозначной?
- Как найти серии подряд идущих дней?
- Как пронумеровать сессии пользователя?
- Что такое зерно таблицы и почему агрегировать нужно до соединения?
- Почему `WHERE strftime('%Y', d) = '2026'` хуже, чем сравнение с границами периода?
- Какие проверки ты делаешь, прежде чем отдать результат запроса?

## Решения

### Задание 1. Сводка по пользователям

```sql
SELECT u.name,
       COUNT(o.order_id)                                              AS orders_total,
       SUM(CASE WHEN o.status = 'paid' THEN 1 ELSE 0 END)             AS orders_paid,
       COALESCE(SUM(CASE WHEN o.status = 'paid' THEN o.amount END), 0) AS revenue,
       ROUND(AVG(CASE WHEN o.status IN ('cancelled', 'refunded') THEN 1.0
                      WHEN o.status IS NOT NULL THEN 0 END), 2)       AS bad_share
FROM users AS u
LEFT JOIN orders AS o ON o.user_id = u.user_id
GROUP BY u.user_id, u.name
ORDER BY u.user_id;
```

<!-- result -->
*Результат:*

| name | orders_total | orders_paid | revenue | bad_share |
|---|---|---|---|---|
| Анна | 5 | 4 | 5500 | 0.2 |
| Борис | 2 | 2 | 5700 | 0 |
| Вера | 2 | 2 | 5000 | 0 |
| Глеб | 1 | 0 | 0 | 1 |
| Дарья | 0 | 0 | 0 | NULL |
| Егор | 1 | 1 | 400 | 0 |
<!-- /result -->



`LEFT JOIN` сохраняет пользователей без заказов. У Дарьи `orders_total` равно нулю, потому что считается `COUNT(o.order_id)`, а не `COUNT(*)`. Доля для неё — `NULL`: у человека без заказов доля отменённых не определена, и это честнее, чем ноль. Именно для этого во втором условии `CASE` стоит проверка `IS NOT NULL` вместо `ELSE 0`.

### Задание 2. Сироты с обеих сторон

```sql
SELECT 'заказ без пользователя' AS problem, o.order_id AS id
FROM orders AS o
LEFT JOIN users AS u ON u.user_id = o.user_id
WHERE u.user_id IS NULL

UNION ALL

SELECT 'пользователь без заказов', u.user_id
FROM users AS u
LEFT JOIN orders AS o ON o.user_id = u.user_id
WHERE o.order_id IS NULL;
```

<!-- result -->
*Результат:*

| problem | id |
|---|---|
| заказ без пользователя | 112 |
| пользователь без заказов | 5 |
<!-- /result -->



Два антисоединения, склеенные через `UNION ALL`. В PostgreSQL то же самое делается одним `FULL JOIN` с условием `WHERE u.user_id IS NULL OR o.order_id IS NULL`.

Такой запрос — стандартная проверка целостности данных перед анализом.

### Задание 3. Первый и последний заказ в одной строке

```sql
WITH ranked AS (
    SELECT user_id, order_date, amount,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY order_date, order_id)           AS rn_first,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY order_date DESC, order_id DESC) AS rn_last
    FROM orders
    WHERE status = 'paid'
)
SELECT user_id,
       MAX(CASE WHEN rn_first = 1 THEN order_date END) AS first_date,
       MAX(CASE WHEN rn_first = 1 THEN amount END)     AS first_amount,
       MAX(CASE WHEN rn_last = 1  THEN order_date END) AS last_date,
       MAX(CASE WHEN rn_last = 1  THEN amount END)     AS last_amount
FROM ranked
GROUP BY user_id
ORDER BY user_id;
```

<!-- result -->
*Результат:*

| user_id | first_date | first_amount | last_date | last_amount |
|---|---|---|---|---|
| 1 | 2026-01-03 | 1200 | 2026-03-02 | 2000 |
| 2 | 2026-01-06 | 5000 | 2026-02-01 | 700 |
| 3 | 2026-01-14 | 2500 | 2026-02-15 | 2500 |
| 6 | 2026-02-20 | 400 | 2026-02-20 | 400 |
| 9 | 2026-03-05 | 100 | 2026-03-05 | 100 |
<!-- /result -->



Две нумерации в противоположных направлениях и условная агрегация, которая «вытаскивает» нужную строку в столбец. `MAX` здесь не ищет максимум — в каждой группе под условие попадает ровно одно значение, и `MAX` просто его возвращает.

### Задание 4. Больше среднего по отделу

```sql
WITH with_avg AS (
    SELECT name, dept, salary,
           AVG(salary) OVER (PARTITION BY dept) AS dept_avg
    FROM employees
)
SELECT name, dept, salary, ROUND(dept_avg, 1) AS dept_avg
FROM with_avg
WHERE salary > dept_avg
ORDER BY dept, salary DESC;
```

<!-- result -->
*Результат:*

| name | dept | salary | dept_avg |
|---|---|---|---|
| Павел | Аналитика | 200 | 150 |
| Рита | Продажи | 180 | 150 |
<!-- /result -->



Оконная функция добавляет среднее по отделу к каждой строке, не сворачивая таблицу. CTE нужен, потому что результат оконной функции нельзя использовать в `WHERE` того же запроса.

### Задание 5. Выручка по дням февраля с накоплением

```sql
WITH RECURSIVE calendar(day) AS (
    SELECT '2026-02-01'
    UNION ALL
    SELECT date(day, '+1 day') FROM calendar WHERE day < '2026-02-28'
),
daily AS (
    SELECT c.day,
           COALESCE(SUM(o.amount), 0) AS revenue
    FROM calendar AS c
    LEFT JOIN orders AS o
           ON o.order_date = c.day
          AND o.status = 'paid'
    GROUP BY c.day
)
SELECT day,
       revenue,
       SUM(revenue) OVER (ORDER BY day) AS revenue_mtd
FROM daily
ORDER BY day;
```

<!-- result -->
*Результат:*

| day | revenue | revenue_mtd |
|---|---|---|
| 2026-02-01 | 700 | 700 |
| 2026-02-02 | 0 | 700 |
| 2026-02-03 | 0 | 700 |
| 2026-02-04 | 0 | 700 |
| 2026-02-05 | 0 | 700 |
| 2026-02-06 | 0 | 700 |
| 2026-02-07 | 1500 | 2200 |
| 2026-02-08 | 0 | 2200 |

*Показаны первые 8 строк из 28.*
<!-- /result -->



Порядок шагов важен: сначала календарь и одна строка на день, затем накопительная сумма. Если считать накопление прямо по таблице заказов, дни без заказов выпадут из результата.

### Задание 6. Интервалы между покупками

```sql
WITH with_prev AS (
    SELECT user_id,
           order_date,
           LAG(order_date) OVER (PARTITION BY user_id ORDER BY order_date, order_id) AS prev_date
    FROM orders
    WHERE status = 'paid'
),
gaps AS (
    SELECT user_id,
           order_date,
           CAST(julianday(order_date) - julianday(prev_date) AS INTEGER) AS days_since_prev
    FROM with_prev
)
SELECT ROUND(AVG(days_since_prev), 1) AS avg_gap_days,
       COUNT(days_since_prev)         AS intervals
FROM gaps;
```

<!-- result -->
*Результат:*

| avg_gap_days | intervals |
|---|---|
| 23.2 | 5 |
<!-- /result -->



У первого заказа каждого пользователя `prev_date` равен `NULL`, и интервал тоже `NULL`. `AVG` такие строки пропускает, и это ровно то, что нужно: у первой покупки нет «интервала с предыдущей».

Средний интервал между покупками — основа для определения оттока: если клиент не покупал заметно дольше обычного интервала, его пора возвращать.

### Задание 7. Самая длинная серия

```sql
WITH days AS (
    SELECT DISTINCT user_id, date(event_time) AS day
    FROM events
),
numbered AS (
    SELECT user_id, day,
           date(day, '-' || ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY day) || ' day') AS island
    FROM days
),
streaks AS (
    SELECT user_id, MIN(day) AS streak_start, COUNT(*) AS streak_days
    FROM numbered
    GROUP BY user_id, island
)
SELECT user_id, MAX(streak_days) AS longest_streak
FROM streaks
GROUP BY user_id
ORDER BY user_id;
```

<!-- result -->
*Результат:*

| user_id | longest_streak |
|---|---|
| 1 | 3 |
| 2 | 3 |
| 3 | 1 |
<!-- /result -->



Результат: у первого пользователя три дня подряд (1–3 марта), у второго тоже три (3–5 марта, а 1 марта стоит отдельно), у третьего — один.

### Задание 8. Все подчинённые

```sql
WITH RECURSIVE chain AS (
    SELECT emp_id AS boss_id, emp_id AS member_id
    FROM employees

    UNION ALL

    SELECT c.boss_id, e.emp_id
    FROM chain AS c
    JOIN employees AS e ON e.manager_id = c.member_id
)
SELECT b.name,
       COUNT(*) - 1 AS subordinates
FROM chain AS c
JOIN employees AS b ON b.emp_id = c.boss_id
GROUP BY b.emp_id, b.name
ORDER BY subordinates DESC, b.name;
```

<!-- result -->
*Результат:*

| name | subordinates |
|---|---|
| Ольга | 6 |
| Павел | 3 |
| Рита | 1 |
| Семён | 1 |
| Таня | 0 |
| Ульяна | 0 |
| Фёдор | 0 |
<!-- /result -->



Каждый сотрудник начинает цепочку как «начальник самого себя», затем на каждом шаге к цепочке добавляются подчинённые уже найденных людей. В конце вычитаем единицу — самого сотрудника. У Ольги получится шесть подчинённых, у Павла — три (Семён, Таня и Фёдор, подчинённый Семёна).

### Задание 9. Покупка в первые 7 дней

```sql
SELECT u.name,
       u.signup_date,
       MIN(o.order_date) AS first_purchase
FROM users AS u
JOIN orders AS o
  ON o.user_id = u.user_id
 AND o.status = 'paid'
 AND o.order_date >= u.signup_date
 AND o.order_date <  date(u.signup_date, '+7 day')
GROUP BY u.user_id, u.name, u.signup_date
ORDER BY u.user_id;
```

<!-- result -->
*Результат:*

| name | signup_date | first_purchase |
|---|---|---|
| Анна | 2026-01-03 | 2026-01-03 |
| Борис | 2026-01-05 | 2026-01-06 |
| Вера | 2026-01-12 | 2026-01-14 |
<!-- /result -->



Условие на окно в семь дней стоит прямо в соединении, границы заданы полуоткрытым интервалом. Чтобы получить конверсию в покупку за первую неделю, раздели число строк результата на общее число пользователей — или замени `JOIN` на `LEFT JOIN` и посчитай `AVG(CASE WHEN o.order_id IS NOT NULL THEN 1.0 ELSE 0 END)` по уникальным пользователям.
