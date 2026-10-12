# Глава 11. Машинное обучение и большие данные

На карте roadmap.sh это раздел Advanced Topics. Для первой работы аналитиком он не обязателен, но базовое понимание нужно: ты будешь работать рядом с дата-сайентистами, а простые модели пригодятся и в анализе.

Цель главы — обзор: какие бывают задачи, как устроен процесс и как понять, хороша ли модель.

## 11.1. Что такое машинное обучение

В обычной программе человек пишет правила: «если сумма больше 10 000 — заказ крупный». В машинном обучении правила находит алгоритм — по примерам с известными ответами.

Термины:

- **Признаки (features, X)** — то, что мы знаем об объекте: возраст клиента, число заказов, город.
- **Целевая переменная (target, y)** — то, что хотим предсказать: уйдёт ли клиент.
- **Обучение** — подбор параметров модели по данным.
- **Предсказание** — применение обученной модели к новым объектам.

### Типы машинного обучения

| Тип | Суть | Задачи | Примеры |
|-----|------|--------|---------|
| **С учителем** (supervised) | Есть правильные ответы | Регрессия — предсказать число. Классификация — предсказать класс | Прогноз продаж, отток клиентов, кредитный скоринг |
| **Без учителя** (unsupervised) | Ответов нет, ищем структуру | Кластеризация, снижение размерности | Сегментация клиентов, поиск аномалий |
| **С подкреплением** (reinforcement) | Агент учится на наградах за действия | Управление, игры | Роботы, рекомендательные стратегии |

Аналитику нужны первые два.

## 11.2. Процесс: от данных до оценки

Главная идея: **модель нужно проверять на данных, которых она не видела**. Иначе она может просто «зазубрить» обучающие примеры. Поэтому данные делят на обучающую и тестовую части.

Смоделируем данные об оттоке клиентов и обучим классификатор:

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score, confusion_matrix

rng = np.random.default_rng(42)
n = 2000

data = pd.DataFrame({
    "months_with_us": rng.integers(1, 48, n),
    "orders_last_90d": rng.poisson(3, n),
    "support_tickets": rng.poisson(1, n),
    "avg_check": rng.gamma(2.0, 1500, n).round(0),
})

# Чем меньше стаж и заказов и чем больше обращений в поддержку, тем выше шанс ухода
score = -0.5 - 0.04 * data["months_with_us"] - 0.4 * data["orders_last_90d"] + 0.7 * data["support_tickets"]
data["churn"] = (rng.random(n) < 1 / (1 + np.exp(-score))).astype(int)
print(data["churn"].mean())      # доля ушедших

X = data.drop(columns="churn")
y = data["churn"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

pred = model.predict(X_test)                  # класс: 0 или 1
proba = model.predict_proba(X_test)[:, 1]     # вероятность ухода
```

<!-- result -->
*Результат:*

```output
0.1705
```
<!-- /result -->



В библиотеке scikit-learn у всех моделей одинаковый интерфейс: `fit` — обучить, `predict` — предсказать. Поменять алгоритм — это поменять одну строку.

## 11.3. Как оценивать модель

### Классификация

Начинают с **матрицы ошибок**:

```python
print(confusion_matrix(y_test, pred))
print("accuracy:", round(accuracy_score(y_test, pred), 3))
print("precision:", round(precision_score(y_test, pred), 3))
print("recall:", round(recall_score(y_test, pred), 3))
print("ROC AUC:", round(roc_auc_score(y_test, proba), 3))
```

<!-- result -->
*Результат:*

```output
[[403  12]
 [ 73  12]]
accuracy: 0.83
precision: 0.5
recall: 0.141
ROC AUC: 0.775
```
<!-- /result -->



| Метрика | Вопрос, на который отвечает |
|---------|-----------------------------|
| **Accuracy** | Какая доля предсказаний верна? |
| **Precision** (точность) | Из тех, кого модель назвала уходящими, сколько действительно ушли? |
| **Recall** (полнота) | Из тех, кто действительно ушёл, скольких модель нашла? |
| **F1** | Среднее гармоническое precision и recall |
| **ROC AUC** | Насколько хорошо модель в целом отделяет один класс от другого (0,5 — случайно, 1 — идеально) |

**Ловушка accuracy.** Если уходит 5 % клиентов, то модель, которая всем предсказывает «останется», получит accuracy 95 % — и будет абсолютно бесполезной. При несбалансированных классах смотри на precision, recall и ROC AUC.

Выбор между precision и recall — это вопрос бизнеса: что дороже — зря дать скидку лояльному клиенту или пропустить уходящего?

### Регрессия

| Метрика | Смысл |
|---------|-------|
| **MAE** | Средняя абсолютная ошибка — в единицах целевой переменной: «ошибаемся в среднем на 300 рублей» |
| **RMSE** | Корень из среднего квадрата ошибки — сильнее штрафует за большие промахи |
| **R²** | Доля разброса, объяснённая моделью |

### Базовая модель

Любую модель сравнивай с самым простым решением — бейзлайном: для регрессии — предсказывать среднее, для классификации — самый частый класс. Если сложная модель не лучше бейзлайна, она не нужна.

## 11.4. Переобучение

**Переобучение (overfitting)** — модель запомнила обучающие данные вместе с шумом и плохо работает на новых. Признак: на обучающей выборке качество намного выше, чем на тестовой.

```python
for depth in [2, 5, None]:
    tree = DecisionTreeClassifier(max_depth=depth, random_state=42)
    tree.fit(X_train, y_train)
    train_auc = roc_auc_score(y_train, tree.predict_proba(X_train)[:, 1])
    test_auc = roc_auc_score(y_test, tree.predict_proba(X_test)[:, 1])
    print(depth, round(train_auc, 3), round(test_auc, 3))
```

<!-- result -->
*Результат:*

```output
2 0.698 0.643
5 0.79 0.713
None 1.0 0.611
```
<!-- /result -->



Дерево без ограничения глубины показывает идеальный результат на обучении и заметно худший на тесте — оно заучило данные.

Более надёжная оценка — **кросс-валидация**: данные делят на несколько частей, по очереди каждая служит тестовой, результат усредняют. В scikit-learn это функция `cross_val_score`.

## 11.5. Алгоритмы с карты

| Алгоритм | Задача | Идея в одном предложении |
|----------|--------|--------------------------|
| **Линейная регрессия** | Регрессия | Подбирает прямую (плоскость), минимизируя квадраты ошибок |
| **Логистическая регрессия** | Классификация | Линейная модель, выход которой превращён в вероятность от 0 до 1 |
| **Дерево решений** | Обе | Последовательность вопросов «признак больше порога?» |
| **KNN** (k ближайших соседей) | Обе | Смотрит на k самых похожих объектов и берёт их ответ |
| **Наивный Байес** | Классификация | Считает вероятности классов по теореме Байеса, предполагая независимость признаков |
| **K-means** | Кластеризация | Делит объекты на k групп вокруг центров |

На практике лучшие результаты на табличных данных дают ансамбли деревьев — случайный лес и градиентный бустинг. Но начинать всегда стоит с простой интерпретируемой модели.

### Что модель говорит о данных

Аналитику модель часто нужна не для предсказаний, а для понимания: какие факторы связаны с результатом.

```python
coefs = pd.Series(model.coef_[0], index=X.columns).sort_values()
print(coefs.round(3))
```

<!-- result -->
*Результат:*

```output
orders_last_90d   -0.339
months_with_us    -0.039
avg_check         -0.000
support_tickets    0.743
dtype: float64
```
<!-- /result -->



Знак коэффициента показывает направление связи: отрицательный у `orders_last_90d` — чем больше заказов, тем ниже вероятность ухода. Сравнивать величины коэффициентов между собой можно только после приведения признаков к одному масштабу (`StandardScaler`).

### Кластеризация

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

features = data[["months_with_us", "orders_last_90d", "avg_check"]]
scaled = StandardScaler().fit_transform(features)

kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
data["cluster"] = kmeans.fit_predict(scaled)

print(data.groupby("cluster")[features.columns.tolist()].mean().round(1))
print(data["cluster"].value_counts())
```

<!-- result -->
*Результат:*

```output
         months_with_us  orders_last_90d  avg_check
cluster                                            
0                  36.3              2.7     2244.2
1                  23.4              3.2     6581.3
2                  12.2              3.1     2175.1
cluster
2    835
0    816
1    349
Name: count, dtype: int64
```
<!-- /result -->



Масштабирование обязательно: K-means работает с расстояниями, и без него признак с большими числами (средний чек в тысячах) полностью подавит остальные.

Алгоритм найдёт кластеры всегда, даже в полностью случайных данных. Осмысленны ли они — решает аналитик, глядя на средние значения признаков в каждой группе. Сравни этот подход с RFM-сегментацией из главы 10.

## 11.6. Типичные ошибки

- **Утечка данных (data leakage).** В признаки попала информация, которой в момент предсказания ещё не будет. Пример: признак «дата расторжения договора» в модели оттока. Качество получается фантастическим — и бесполезным.
- **Оценка на обучающих данных.**
- **Случайное разбиение временных данных.** Если данные упорядочены во времени, тест должен быть позже обучения, иначе модель «подглядывает в будущее».
- **Сложная модель там, где хватило бы группировки.** Сначала попробуй решить задачу средствами глав 5–10.

## 11.7. Глубокое обучение: что нужно знать

Нейронная сеть — модель из слоёв простых элементов, способная находить очень сложные зависимости.

- **CNN** (свёрточные сети) — изображения.
- **RNN** и трансформеры — последовательности: текст, временные ряды.
- **TensorFlow** и **PyTorch** — основные библиотеки.

На карте этот раздел помечен как необязательный, и это справедливо. Глубокое обучение нужно для картинок, текста и звука. С таблицами, с которыми работает аналитик, лучше справляются модели из раздела 11.5.

## 11.8. Большие данные: что нужно знать

Когда данные не помещаются в память одного компьютера, pandas перестаёт работать, и нужны распределённые системы — они делят данные и вычисления между многими машинами.

| Термин | Что это |
|--------|---------|
| **Hadoop** | Экосистема для хранения (HDFS) и обработки больших данных на кластере |
| **MapReduce** | Модель вычислений: разбить задачу на части (map), выполнить параллельно, собрать результат (reduce) |
| **Spark** | Современный и быстрый движок распределённых вычислений; есть Python-интерфейс PySpark |
| **MPI** | Стандарт обмена сообщениями для параллельных вычислений, в основном в научных расчётах |
| **Хранилище данных (DWH)** | База, оптимизированная под аналитические запросы: ClickHouse, BigQuery, Snowflake, Greenplum |

Хорошая новость: для аналитика большие данные выглядят почти так же, как маленькие. В ClickHouse и BigQuery пишут обычный SQL, а PySpark похож на pandas — та же логика «отфильтровал, сгруппировал, соединил». Идея MapReduce — это split–apply–combine из главы 5, только на многих машинах.

Что действительно меняется: нельзя бездумно писать `SELECT *`, нужно фильтровать как можно раньше и помнить, что запрос стоит денег и времени.

## Практика на GitHub

- [Yorko/mlcourse.ai](https://github.com/Yorko/mlcourse.ai) — открытый курс машинного обучения от сообщества ODS. Первые темы посвящены анализу и визуализации данных, дальше идут деревья решений и kNN, линейные модели, ансамбли. К каждой теме — статья, ноутбук и домашнее задание. Лучший следующий шаг после этой главы.
- [jakevdp/PythonDataScienceHandbook](https://github.com/jakevdp/PythonDataScienceHandbook) — глава 5 (ноутбуки с префиксом `05`): введение в scikit-learn, проверка моделей, обзор основных алгоритмов.
- [DataTalksClub](https://github.com/DataTalksClub) — бесплатные курсы с домашними заданиями: по машинному обучению и по инженерии данных (хранилища, Spark, конвейеры обработки).
- [academic/awesome-datascience](https://github.com/academic/awesome-datascience) — каталог: открывай, когда решишь идти глубже в Data Science.

## Задания

1. Обучи на данных из раздела 11.2 дерево решений глубины 3 и сравни ROC AUC с логистической регрессией.
2. Посчитай бейзлайн: какой accuracy у модели, всегда предсказывающей «останется»?
3. Меняй порог вероятности, выше которого клиент считается уходящим (0,2; 0,3; 0,5). Как меняются precision и recall?
4. Оцени логистическую регрессию через `cross_val_score` на пяти частях.
5. Сделай K-means на RFM-признаках из главы 10 и сравни результат с сегментами, полученными вручную.
6. Найди в [awesome-public-datasets](https://github.com/awesomedata/awesome-public-datasets) табличный датасет с понятной целевой переменной и пройди весь путь: EDA → бейзлайн → модель → оценка → выводы.

## Проверь себя

- Чем обучение с учителем отличается от обучения без учителя?
- Чем регрессия отличается от классификации?
- Зачем делить данные на обучающую и тестовую части?
- Что такое переобучение и как его заметить?
- Почему accuracy — плохая метрика при несбалансированных классах?
- Чем precision отличается от recall?
- Что такое утечка данных?

## Решения

Решения продолжают код раздела 11.2: предполагается, что `data`, `X`, `y`, `X_train`, `X_test`, `y_train`, `y_test`, `model` и `proba` уже созданы.

### Задание 1. Дерево против логистической регрессии

```python
from sklearn.tree import DecisionTreeClassifier, export_text

tree = DecisionTreeClassifier(max_depth=3, random_state=42)
tree.fit(X_train, y_train)
tree_proba = tree.predict_proba(X_test)[:, 1]

print("ROC AUC, логистическая регрессия:", round(roc_auc_score(y_test, proba), 3))
print("ROC AUC, дерево глубины 3:", round(roc_auc_score(y_test, tree_proba), 3))
print(export_text(tree, feature_names=list(X.columns)))
```

<!-- result -->
*Результат:*

```output
ROC AUC, логистическая регрессия: 0.775
ROC AUC, дерево глубины 3: 0.674
|--- support_tickets <= 1.50
|   |--- months_with_us <= 14.50
|   |   |--- orders_last_90d <= 1.50
|   |   |   |--- class: 0
|   |   |--- orders_last_90d >  1.50
|   |   |   |--- class: 0
|   |--- months_with_us >  14.50
|   |   |--- orders_last_90d <= 3.50
|   |   |   |--- class: 0
|   |   |--- orders_last_90d >  3.50
|   |   |   |--- class: 0
|--- support_tickets >  1.50
|   |--- months_with_us <= 19.50
|   |   |--- orders_last_90d <= 3.50
|   |   |   |--- class: 1
|   |   |--- orders_last_90d >  3.50
|   |   |   |--- class: 0
|   |--- months_with_us >  19.50
|   |   |--- support_tickets <= 3.50
|   |   |   |--- class: 0
|   |   |--- support_tickets >  3.50
|   |   |   |--- class: 1
```
<!-- /result -->



Логистическая регрессия здесь, скорее всего, окажется лучше. Это ожидаемо: данные мы сами сгенерировали по логистической формуле, и линейная модель описывает их идеально. Дерево глубины 3 делит пространство всего на восемь областей и приближает плавную зависимость «ступеньками».

`export_text` печатает правила дерева — главное достоинство этого алгоритма: его можно прочитать и объяснить менеджеру.

Вывод шире конкретного примера: нет «лучшего алгоритма вообще», есть алгоритм, подходящий под структуру данных.

### Задание 2. Бейзлайн

```python
from sklearn.dummy import DummyClassifier

baseline = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)

print("Доля ушедших:", round(y_test.mean(), 3))
print("Accuracy бейзлайна:", round(accuracy_score(y_test, baseline.predict(X_test)), 3))
print("Accuracy модели:", round(accuracy_score(y_test, pred), 3))
print("Recall бейзлайна:", recall_score(y_test, baseline.predict(X_test)))      # 0.0
```

<!-- result -->
*Результат:*

```output
Доля ушедших: 0.17
Accuracy бейзлайна: 0.83
Accuracy модели: 0.83
Recall бейзлайна: 0.0
```
<!-- /result -->



Accuracy бейзлайна равна `1 − доля ушедших`. Модель, которая никого не находит (recall = 0), получает высокую accuracy просто потому, что ушедших мало. Если accuracy нашей модели лишь немного выше — это не значит, что модель плохая: это значит, что accuracy здесь ни о чём не говорит. Смотрим на recall, precision и ROC AUC.

### Задание 3. Порог вероятности

```python
rows = []
for threshold in (0.2, 0.3, 0.5):
    predicted = (proba >= threshold).astype(int)
    rows.append({
        "порог": threshold,
        "помечено уходящими": int(predicted.sum()),
        "precision": round(precision_score(y_test, predicted, zero_division=0), 3),
        "recall": round(recall_score(y_test, predicted), 3),
    })

print(pd.DataFrame(rows))
```

<!-- result -->
*Результат:*

```output
   порог  помечено уходящими  precision  recall
0    0.2                 153      0.346   0.624
1    0.3                  88      0.489   0.506
2    0.5                  24      0.500   0.141
```
<!-- /result -->



Чем ниже порог, тем больше клиентов модель помечает как уходящих: recall растёт (находим больше настоящих уходящих), precision падает (больше ложных тревог). Улучшить обе метрики одновременно сдвигом порога нельзя.

Какой порог выбрать — решает экономика. Если удержание — это дешёвое письмо, выгоден низкий порог: лучше написать лишним, чем пропустить уходящего. Если удержание — дорогая скидка или звонок менеджера, порог поднимают.

Метод `predict` всегда использует порог 0,5. Для несбалансированных классов он почти никогда не оптимален, поэтому работать нужно с `predict_proba`.

### Задание 4. Кросс-валидация

```python
from sklearn.model_selection import cross_val_score

scores = cross_val_score(LogisticRegression(max_iter=1000), X, y, cv=5, scoring="roc_auc")

print(scores.round(3))
print(f"ROC AUC: {scores.mean():.3f} ± {scores.std():.3f}")
```

<!-- result -->
*Результат:*

```output
[0.759 0.762 0.78  0.792 0.737]
ROC AUC: 0.766 ± 0.019
```
<!-- /result -->



Получаем пять оценок вместо одной. Среднее — более надёжная оценка качества, а разброс показывает, насколько результат зависит от того, какие объекты попали в тест. Если бы оценка на одном разбиении сильно отличалась от среднего по пяти, мы бы знали, что нам просто повезло или не повезло с разбиением.

### Задание 5. K-means на RFM-признаках

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

events = pd.read_csv("events.csv", parse_dates=["date"])
purchases = events[events["event"] == "purchase"]
today = purchases["date"].max() + pd.Timedelta(days=1)

rfm = purchases.groupby("user_id").agg(
    recency=("date", lambda d: (today - d.max()).days),
    frequency=("date", "count"),
    monetary=("amount", "sum"),
)

features = rfm[["recency", "frequency", "monetary"]].copy()
features["monetary"] = np.log1p(features["monetary"])          # сжать длинный хвост
scaled = StandardScaler().fit_transform(features)

rfm["cluster"] = KMeans(n_clusters=4, n_init=10, random_state=42).fit_predict(scaled)

profile = rfm.groupby("cluster").agg(
    users=("monetary", "count"),
    recency=("recency", "mean"),
    frequency=("frequency", "mean"),
    monetary=("monetary", "mean"),
    revenue_share=("monetary", lambda m: m.sum() / rfm["monetary"].sum()),
)
print(profile.round(2))
```

<!-- result -->
*Результат:*

```output
         users  recency  frequency  monetary  revenue_share
cluster                                                    
0          212    28.60       1.00   3991.30           0.48
1          136    41.45       1.00    911.06           0.07
2          177    66.15       1.00   3379.81           0.34
3           34    29.74       2.03   5844.94           0.11
```
<!-- /result -->



Два шага подготовки обязательны: логарифм для суммы покупок (иначе несколько крупных клиентов образуют отдельный кластер) и стандартизация (иначе рубли в тысячах задавят частоту в единицах).

Кластеры нужно **назвать**, глядя на таблицу `profile`: например, «недавние разовые», «давно ушедшие», «постоянные крупные». Если кластеру не получается дать осмысленное имя и предложить для него действие — он бесполезен, и число кластеров стоит поменять.

Сравнение с ручной RFM-сегментацией:

| | Ручные RFM-сегменты | K-means |
|---|---|---|
| Границы | Задаёшь сам, их легко объяснить | Находит алгоритм |
| Объяснимость | «Покупал в последние 30 дней» | «Ближе к центру кластера 2» |
| Устойчивость | Не меняются при обновлении данных | Могут сдвинуться при переобучении |
| Когда выбирать | Почти всегда для RFM | Когда признаков много и границы неочевидны |

Для трёх понятных признаков ручная сегментация обычно практичнее.

### Задание 6. Полный цикл на своём датасете

Каркас решения. Ключевая идея — объединить подготовку признаков и модель в `Pipeline`: это тот самый паттерн «конвейер» из главы 2В, и он защищает от утечки данных.

```python
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_model(numeric: list[str], categorical: list[str]) -> Pipeline:
    """Подготовка признаков и модель в одном объекте."""
    numeric_steps = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical_steps = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("encode", OneHotEncoder(handle_unknown="ignore")),
    ])
    preprocess = ColumnTransformer([
        ("num", numeric_steps, numeric),
        ("cat", categorical_steps, categorical),
    ])
    return Pipeline([("preprocess", preprocess), ("model", LogisticRegression(max_iter=1000))])
```

Использование:

```python
TARGET = "target"                       # замени на имя своей целевой переменной
df = pd.read_csv("data/dataset.csv")

X, y = df.drop(columns=TARGET), df[TARGET]
numeric = X.select_dtypes("number").columns.tolist()
categorical = X.select_dtypes(exclude="number").columns.tolist()

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

baseline = DummyClassifier(strategy="prior").fit(X_train, y_train)
model = build_model(numeric, categorical).fit(X_train, y_train)

print("ROC AUC бейзлайна:", round(roc_auc_score(y_test, baseline.predict_proba(X_test)[:, 1]), 3))   # 0.5
print("ROC AUC модели:", round(roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]), 3))
```

Почему `Pipeline` защищает от утечки: медианы для заполнения пропусков и параметры масштабирования вычисляются только по обучающей части при вызове `fit`, а к тестовой лишь применяются. Если посчитать медиану по всей таблице до разбиения, в обучение просочится информация из теста, и оценка качества окажется завышенной.

Чек-лист проекта:

- EDA по плану из раздела 8.7, отдельно — распределение целевой переменной;
- проверка на утечку: нет ли признаков, которые становятся известны только после события;
- бейзлайн посчитан, модель сравнивается с ним;
- метрика выбрана под задачу, а не «accuracy по привычке»;
- есть раздел о том, какие признаки важны и что это значит для бизнеса;
- в выводах — что модель позволяет сделать и какие у неё ограничения.
