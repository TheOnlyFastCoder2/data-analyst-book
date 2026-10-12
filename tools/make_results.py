"""Выполняет примеры кода из глав и вставляет после них результаты.

После каждого блока ```python добавляется напечатанный вывод и построенные графики,
после каждого блока ```sql — таблица с результатом запроса. Вставки обрамляются
комментариями <!-- result --> ... <!-- /result -->, поэтому скрипт можно запускать
повторно: старые результаты удаляются и заменяются свежими.

Запуск:  python3 tools/make_results.py РАБОЧАЯ_ПАПКА [глава.md ...]

В рабочей папке должен лежать файл Chinook_Sqlite.sqlite; туда же примеры
записывают свои файлы (orders.csv и другие). Нужны библиотеки из requirements книги.
"""
import contextlib
import io
import os
import re
import shutil
import sqlite3
import sys
import traceback
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BOOK = Path(__file__).resolve().parent.parent
IMG = BOOK / "img"

CHAPTERS = [
    "02-python-osnovy.md", "02a-python-dalshe.md", "02b-oop.md", "02c-chistyj-kod.md",
    "03-sql.md", "03a-sql-priemy.md", "04-numpy.md", "05-pandas.md", "05a-pandas-priemy.md",
    "06-sbor-i-ochistka.md", "07-vizualizaciya.md", "07a-vizualizaciya-bi.md", "08-statistika.md",
    "09-ab-testy.md", "09a-statistika-ab.md", "10-produktovaya-analitika.md", "11-ml-i-big-data.md",
]

# Блоки, которые не выполняются: сеть, внешние файлы, код-иллюстрации
SKIP_MARKERS = (
    "requests.get", "read_html", "plotly", "import pytest", "data/dataset.csv", "from src",
    "import tools", "from style import", "load_dotenv", "../data/", "help(str.split)",
    "DATA_PATH", "orders_with_users", ".pipe(normalize_city)", "df2 = df[",
)
MAX_LINES, MAX_WIDTH, MAX_ROWS = 30, 118, 8
RESULT = re.compile(r"\n<!-- result -->\n.*?<!-- /result -->\n", re.S)
FENCE = re.compile(r"(```(\w*)\n(.*?)```\n)", re.S)


def clip(text):
    lines = text.rstrip().splitlines()
    lines = [line if len(line) <= MAX_WIDTH else line[: MAX_WIDTH - 1] + "…" for line in lines]
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES] + [f"… (ещё {len(lines) - MAX_LINES} строк)"]
    return "\n".join(lines)


def cell(value):
    if value is None:
        return "NULL"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".") if value != int(value) else str(int(value))
    return str(value).replace("|", "\\|").replace("\n", " ")


def sql_result(conn, query):
    """Возвращает Markdown-таблицу с результатом или None, если запрос ничего не возвращает."""
    try:
        cursor = conn.execute(query)
    except (sqlite3.Warning, sqlite3.ProgrammingError):
        conn.executescript(query)
        return None
    if cursor.description is None:
        conn.commit()
        return None
    rows = cursor.fetchall()
    head = [column[0] for column in cursor.description]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(cell(v) for v in row) + " |" for row in rows[:MAX_ROWS]]
    table = "\n".join(lines)
    if not rows:
        table += "\n\n*Запрос вернул 0 строк.*"
    elif len(rows) > MAX_ROWS:
        table += f"\n\n*Показаны первые {MAX_ROWS} строк из {len(rows)}.*"
    return table


class Chapter:
    def __init__(self, name, workdir):
        self.name = name
        self.stem = name.split("-")[0]
        self.workdir = workdir
        self.namespace = {"__name__": "__main__"}
        self.figures = []
        self.counter = 0
        self.conn = None
        self.problems = []

    def connection(self, first_sql_block):
        if self.conn is None:
            if self.name.startswith("03a"):
                (self.workdir / "setup.sql").write_text(first_sql_block, encoding="utf-8")
                self.conn = sqlite3.connect(":memory:")
            else:
                copy = self.workdir / "chinook_copy.sqlite"
                shutil.copy(self.workdir / "Chinook_Sqlite.sqlite", copy)
                self.conn = sqlite3.connect(copy)
        return self.conn

    def save_figures(self):
        for number in plt.get_fignums():
            self.counter += 1
            path = IMG / f"{self.stem}-{self.counter:02d}.png"
            plt.figure(number).savefig(path, dpi=110, bbox_inches="tight", facecolor="white")
            self.figures.append(path.name)
        plt.close("all")

    def run_python(self, code, index):
        if any(marker in code for marker in SKIP_MARKERS) or re.search(r"^%", code, re.M):
            return None
        self.figures = []
        buffer = io.StringIO()
        plt.show = lambda *args, **kwargs: self.save_figures()
        try:
            with warnings.catch_warnings(record=True) as caught, \
                    contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                warnings.simplefilter("always")
                exec(compile(code, f"{self.name}[{index}]", "exec"), self.namespace)
            for warning in caught:
                self.problems.append(f"  предупреждение в блоке {index}: {warning.category.__name__}: "
                                     f"{str(warning.message)[:160]}")
        except Exception:
            last = traceback.format_exc().strip().splitlines()[-1]
            self.problems.append(f"  ОШИБКА в блоке {index}: {last[:200]}\n      {code.strip().splitlines()[0][:90]}")
            plt.close("all")
            return None
        plt.close("all")
        parts = []
        if buffer.getvalue().strip():
            parts.append("```output\n" + clip(buffer.getvalue()) + "\n```")
        parts += [f"![Результат]({IMG.name}/{name})" for name in self.figures]
        return "\n\n".join(parts) if parts else None

    def run_sql(self, code, index, first_block):
        try:
            return sql_result(self.connection(first_block), code)
        except Exception as error:
            self.problems.append(f"  ОШИБКА SQL в блоке {index}: {error}\n      {code.strip().splitlines()[0][:90]}")
            return None

    def process(self):
        path = BOOK / self.name
        text = RESULT.sub("\n", path.read_text(encoding="utf-8"))
        for old in IMG.glob(f"{self.stem}-*.png"):
            old.unlink()

        blocks = FENCE.findall(text)
        first_sql = next((body for _, lang, body in blocks if lang == "sql"), "")
        out, position = [], 0
        for index, match in enumerate(FENCE.finditer(text)):
            lang, body = match.group(2), match.group(3)
            out.append(text[position:match.end()])
            position = match.end()
            has_manual_result = re.match(r"\s*(Результат|Получится)[^\n]*:\s*\n\s*```", text[position:])
            if lang == "python":
                result = self.run_python(body, index)
            elif lang == "sql" and self.stem in ("03", "03a"):
                result = self.run_sql(body, index, first_sql)
            else:
                result = None
            if result and not has_manual_result:
                out.append(f"\n<!-- result -->\n*Результат:*\n\n{result}\n<!-- /result -->\n")
        out.append(text[position:])
        path.write_text("".join(out), encoding="utf-8")
        if self.conn is not None:
            self.conn.close()
        return self.problems


def main():
    workdir = Path(sys.argv[1]).resolve()
    chapters = sys.argv[2:] or CHAPTERS
    IMG.mkdir(exist_ok=True)
    plt.figure()            # заранее инициализировать графический бэкенд
    plt.close("all")
    os.chdir(workdir)
    sys.path.insert(0, str(workdir))

    import pandas as pd
    pd.set_option("display.width", 112, "display.max_columns", 12, "display.max_rows", 14)

    for name in chapters:
        problems = Chapter(name, workdir).process()
        print(f"{name}: {'без замечаний' if not problems else ''}")
        for problem in problems:
            print(problem)


if __name__ == "__main__":
    main()
