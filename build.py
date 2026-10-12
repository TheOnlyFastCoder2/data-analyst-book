"""Собирает HTML-версию книги из Markdown-глав.

Запуск:  python3 build.py
Результат: папка site/, открывать site/index.html.
Сторонние библиотеки не нужны.
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "site"

# Порядок чтения: (файл, метка в оглавлении, краткое описание)
CHAPTERS = [
    ("00-vvedenie.md", "0", "Кто такой аналитик, типы аналитики, быстрая настройка компьютера"),
    ("ustanovka.md", "⚙", "Python, pip, виртуальное окружение, Jupyter, VS Code, Git, проект с нуля, файл .env"),
    ("01-excel.md", "1", "Функции, ВПР, сводные таблицы, первые графики"),
    ("02-python-osnovy.md", "2", "Переменные, коллекции, условия, циклы, функции, файлы, ошибки"),
    ("02a-python-dalshe.md", "2А", "Распаковка, генераторы, декораторы, менеджеры контекста, исключения, типы, модули"),
    ("02b-oop.md", "2Б", "Классы, свойства, наследование и композиция, dataclass, магические методы"),
    ("02c-chistyj-kod.md", "2В", "PEP 8, имена, функции, рефакторинг, тесты, паттерны проектирования"),
    ("03-sql.md", "3", "SELECT, GROUP BY, JOIN, CTE и оконные функции на базе Chinook"),
    ("04-numpy.md", "4", "Массивы, векторные операции, маски, оси"),
    ("05-pandas.md", "5", "Главный инструмент: фильтры, группировки, сводные, соединения, даты"),
    ("06-sbor-i-ochistka.md", "6", "CSV, API, парсинг; пропуски, дубликаты, выбросы"),
    ("07-vizualizaciya.md", "7", "Выбор графика, Matplotlib, seaborn, дашборды"),
    ("08-statistika.md", "8", "Среднее и медиана, разброс, распределения, корреляция, план EDA"),
    ("09-ab-testy.md", "9", "p-value, доверительные интервалы, размер выборки, ошибки A/B-тестов"),
    ("10-produktovaya-analitika.md", "10", "Метрики, воронки, когорты, удержание, LTV, RFM"),
    ("11-ml-i-big-data.md", "11", "Регрессия, классификация, кластеризация, оценка моделей, обзор Big Data"),
    ("12-portfolio.md", "12", "Разбор проектов-образцов и четыре проекта для своего GitHub"),
    ("13-rabota.md", "13", "Резюме, этапы отбора, вопросы на собеседованиях"),
    ("prilozhenie.md", "＋", "Все репозитории, шпаргалки по SQL и pandas, формулы метрик, словарь"),
]


# ── Markdown → HTML ──────────────────────────────────────────────────────────

def slugify(text):
    """Якорь заголовка по правилам GitHub."""
    text = re.sub(r"[`*]", "", text).strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s", "-", text)


def fix_href(url):
    if re.match(r"^(https?:|#|mailto:)", url):
        return url
    url = url.replace("README.md", "index.html")
    return re.sub(r"\.md(?=$|#)", ".html", url)


def inline(text):
    spans = []

    def stash(match):
        spans.append("<code>" + html.escape(match.group(2).strip(" ") or match.group(2)) + "</code>")
        return f"\x00{len(spans) - 1}\x00"

    text = re.sub(r"(`+)(.+?)\1", stash, text)
    text = html.escape(text, quote=False)

    def link(match):
        url = fix_href(match.group(2))
        external = ' target="_blank" rel="noopener"' if url.startswith("http") else ""
        return f'<a href="{url}"{external}>{match.group(1)}</a>'

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![*\w])\*(?!\s)([^*]+?)(?<!\s)\*(?![*\w])", r"<em>\1</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], text)


def split_row(line):
    """Делит строку таблицы на ячейки, не трогая | внутри `кода`."""
    cells, current, in_code = [], "", False
    for char in line.strip().strip("|"):
        if char == "`":
            in_code = not in_code
        if char == "|" and not in_code:
            cells.append(current.strip())
            current = ""
        else:
            current += char
    cells.append(current.strip())
    return cells



# ── Подсветка синтаксиса ─────────────────────────────────────────────────────

PY_KEYWORDS = set("""and as assert async await break class continue def del elif else except finally for from
global if import in is lambda nonlocal not or pass raise return try while with yield match case""".split())
PY_CONSTS = {"True", "False", "None", "self", "cls"}
PY_BUILTINS = set("""abs all any bool dict enumerate filter float format frozenset getattr hasattr int isinstance
issubclass iter len list map max min next object open print property range repr reversed round set setattr
sorted staticmethod classmethod str sum super tuple type zip Exception ValueError TypeError KeyError IndexError
ZeroDivisionError FileNotFoundError NotImplementedError RuntimeError StopIteration AttributeError""".split())
PY_TOKEN = re.compile(r"""
    (?P<com>\#.*)
  | (?P<str>[rRbBfFuU]{0,2}(?:\"\"\"[\s\S]*?\"\"\"|\'\'\'[\s\S]*?\'\'\'|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'))
  | (?P<dec>@[A-Za-z_][\w.]*)
  | (?P<num>\b\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?\b)
  | (?P<word>[A-Za-z_]\w*)
""", re.X)

SQL_KEYWORDS = set("""select from where group by having order limit join inner left right full cross outer on as
and or not in between like is null distinct case when then else end with over partition rows preceding
current row following union all desc asc insert into values update set delete create table exists""".split())
SQL_FUNCS = set("""count sum avg min max round row_number rank dense_rank lag lead strftime date_trunc coalesce
cast ntile first_value last_value julianday date abs length lower upper substr""".split())
SQL_TOKEN = re.compile(r"""
    (?P<com>--.*)
  | (?P<str>'(?:''|[^'])*')
  | (?P<num>\b\d+(?:\.\d+)?\b)
  | (?P<word>[A-Za-z_]\w*)
""", re.X)

SH_TOKEN = re.compile(r"""
    (?P<com>(?:^|(?<=\s))\#.*)
  | (?P<str>"[^"\n]*"|'[^'\n]*')
  | (?P<cmd>^[ \t]*[\w.\\/-]+)
  | (?P<flag>(?<=\s)--?[A-Za-z][\w-]*)
""", re.X | re.M)


def span(kind, text):
    return f'<span class="t-{kind}">{html.escape(text)}</span>'


def highlight(code, lang):
    lang = lang.lower()
    if lang in ("python", "py"):
        token, after_def = PY_TOKEN, False
    elif lang == "sql":
        token = SQL_TOKEN
    elif lang in ("bash", "sh", "powershell"):
        token = SH_TOKEN
    else:
        return html.escape(code)

    out, pos, after_def = [], 0, False
    for m in token.finditer(code):
        out.append(html.escape(code[pos:m.start()]))
        pos, kind, text = m.end(), m.lastgroup, m.group()
        if kind == "word":
            if lang == "sql":
                low = text.lower()
                kind = "kw" if low in SQL_KEYWORDS else "fn" if low in SQL_FUNCS else None
            elif after_def:
                kind = "def"
            elif text in PY_KEYWORDS:
                kind = "kw"
            elif text in PY_CONSTS:
                kind = "num"
            elif text in PY_BUILTINS:
                kind = "fn"
            else:
                kind = None
            after_def = text in ("def", "class") and lang != "sql"
        elif kind == "cmd":
            kind = "fn"
        elif kind == "flag":
            kind = "num"
        elif kind == "dec":
            kind = "def"
        out.append(span(kind, text) if kind else html.escape(text))
    out.append(html.escape(code[pos:]))
    return "".join(out)


LIST_ITEM = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")


def render_list(lines):
    base = len(LIST_ITEM.match(lines[0]).group(1))
    first_marker = LIST_ITEM.match(lines[0]).group(2)
    ordered = first_marker[0].isdigit()
    items = []          # [текст, вложенные строки]
    for line in lines:
        match = LIST_ITEM.match(line)
        if match and len(match.group(1)) == base:
            items.append([match.group(3), []])
        elif match:
            items[-1][1].append(line)
        elif items[-1][1]:
            items[-1][1][-1] += " " + line.strip()
        else:
            items[-1][0] += " " + line.strip()
    tag = "ol" if ordered else "ul"
    start = f' start="{first_marker[:-1]}"' if ordered and first_marker != "1." else ""
    out = [f"<{tag}{start}>"]
    for text, nested in items:
        text = re.sub(r"^\[ \] ", "☐ ", text)
        out.append("<li>" + inline(text) + (render_list(nested) if nested else "") + "</li>")
    out.append(f"</{tag}>")
    return "\n".join(out)


def convert(markdown):
    lines = markdown.split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]

        if not line.strip():
            i += 1

        elif line.startswith("```"):
            lang = line[3:].strip()
            i += 1
            code = []
            while not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            label = f'<span class="lang">{lang}</span>' if lang else ""
            button = '<button class="copy" type="button">Копировать</button>'
            out.append(f'<div class="code">{label}{button}<pre><code>{highlight(chr(10).join(code), lang)}</code></pre></div>')

        elif re.match(r"^#{1,6} ", line):
            level = len(line) - len(line.lstrip("#"))
            text = line[level:].strip()
            out.append(f'<h{level} id="{slugify(text)}">{inline(text)}</h{level}>')
            i += 1

        elif re.match(r"^-{3,}\s*$", line):
            out.append("<hr>")
            i += 1

        elif line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = split_row(line)
            i += 2
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            table = ["<div class=\"table\"><table><thead><tr>"]
            table += [f"<th>{inline(c)}</th>" for c in head]
            table.append("</tr></thead><tbody>")
            for row in rows:
                table.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
            table.append("</tbody></table></div>")
            out.append("".join(table))

        elif line.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(re.sub(r"^> ?", "", lines[i]))
                i += 1
            out.append("<blockquote>" + convert("\n".join(quote)) + "</blockquote>")

        elif LIST_ITEM.match(line):
            block = []
            while i < len(lines) and lines[i].strip() and (LIST_ITEM.match(lines[i]) or lines[i].startswith(" ")):
                block.append(lines[i])
                i += 1
            out.append(render_list(block))

        else:
            para = []
            while i < len(lines) and lines[i].strip() and not re.match(r"^(```|#{1,6} |\||>)", lines[i]) \
                    and not LIST_ITEM.match(lines[i]):
                para.append(lines[i].strip())
                i += 1
            out.append("<p>" + inline(" ".join(para)) + "</p>")
    return "\n".join(out)


def convert_chapter(markdown):
    """Глава целиком: раздел «Решения» превращается в раскрывающиеся блоки."""
    marker = "\n## Решения"
    if marker not in markdown:
        return convert(markdown)
    main, solutions = markdown.split(marker, 1)
    intro, *items = re.split(r"\n### ", solutions)
    out = [convert(main), '<h2 id="решения">Решения</h2>', convert(intro.split("\n", 1)[-1])]
    for item in items:
        title, _, body = item.partition("\n")
        out.append(f'<details class="sol"><summary>{inline(title)}</summary>{convert(body)}</details>')
    return "\n".join(out)


# ── Шаблон страницы ──────────────────────────────────────────────────────────

CSS = """
:root{--bg:#fbfaf7;--panel:#fff;--text:#22262b;--muted:#6b7280;--line:#e4e1d9;--accent:#1f6f5c;
--accent-soft:#e4f1ed;--code-bg:#f3f1eb;--pre-bg:#1e242b;--pre-text:#e6e9ee}
@media(prefers-color-scheme:dark){:root{--bg:#15191e;--panel:#1c2128;--text:#e3e6ea;--muted:#9aa3ad;
--line:#2e353e;--accent:#5fc4a8;--accent-soft:#1d332e;--code-bg:#262c34;--pre-bg:#0f1317;--pre-text:#dfe3e8}}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);
font:17px/1.65 "Segoe UI",system-ui,-apple-system,Roboto,Arial,sans-serif}
a{color:var(--accent)}
.bar{position:sticky;top:0;z-index:5;background:var(--panel);border-bottom:1px solid var(--line)}
.bar-in{max-width:860px;margin:0 auto;padding:10px 16px;display:flex;align-items:center;gap:12px}
.bar .home{font-weight:600;text-decoration:none;white-space:nowrap}
.bar .where{flex:1;color:var(--muted);font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.progress{height:3px;background:var(--line)}
.progress i{display:block;height:100%;background:var(--accent)}
main{max-width:860px;margin:0 auto;padding:8px 16px 40px}
h1{font-size:2em;line-height:1.2;margin:1.1em 0 .6em;text-wrap:balance}
h2{font-size:1.4em;line-height:1.3;margin:2em 0 .6em;padding-top:.5em;border-top:1px solid var(--line)}
h3{font-size:1.12em;margin:1.6em 0 .4em}
h1,h2,h3{scroll-margin-top:64px}
p,ul,ol{margin:.7em 0}
li{margin:.25em 0}
hr{border:0;border-top:1px solid var(--line);margin:2em 0}
code{font:.88em/1.5 Consolas,"Cascadia Code",Menlo,monospace;background:var(--code-bg);
padding:.12em .35em;border-radius:4px;overflow-wrap:anywhere}
.code{position:relative;margin:1em 0}
.code pre{margin:0;background:var(--pre-bg);color:var(--pre-text);padding:16px;border-radius:8px;overflow-x:auto}
.code pre code{background:none;padding:0;color:inherit;font-size:14.5px;overflow-wrap:normal}
.code .lang{position:absolute;top:6px;right:10px;font-size:11px;color:#8b95a1;text-transform:uppercase;
letter-spacing:.05em;pointer-events:none}
.code .copy{position:absolute;top:6px;right:8px;font:12px/1 inherit;color:#aeb7c2;background:#2b333c;
border:1px solid #3a444f;border-radius:6px;padding:5px 8px;cursor:pointer;opacity:0;transition:opacity .15s}
.code:hover .copy,.code .copy:focus-visible{opacity:1}
.code:hover .lang{opacity:0}
.t-kw{color:#c792ea}.t-str{color:#c3e88d}.t-com{color:#8791a0;font-style:italic}.t-num{color:#f78c6c}
.t-fn{color:#82aaff}.t-def{color:#ffcb6b}
details.sol{border:1px solid var(--line);border-radius:10px;background:var(--panel);margin:10px 0;padding:0 16px}
details.sol summary{cursor:pointer;font-weight:600;padding:12px 0;color:var(--accent)}
details.sol[open]{padding-bottom:8px}
details.sol[open] summary{border-bottom:1px solid var(--line);margin-bottom:8px}
.table{overflow-x:auto;margin:1em 0}
table{border-collapse:collapse;width:100%;font-size:.94em}
th,td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
th{background:var(--code-bg);font-weight:600}
blockquote{margin:1em 0;padding:.2em 1em;border-left:4px solid var(--accent);background:var(--accent-soft);
border-radius:0 8px 8px 0}
.nav{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:28px 0}
.nav a{display:block;padding:12px 16px;border:1px solid var(--line);border-radius:10px;background:var(--panel);
text-decoration:none;color:var(--text);transition:border-color .15s,transform .15s}
.nav a:hover{border-color:var(--accent);transform:translateY(-1px)}
.nav a:focus-visible,.toc a:focus-visible,.cta:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.nav small{display:block;color:var(--muted);font-size:13px}
.nav b{font-weight:600;color:var(--accent)}
.nav .next{text-align:right;grid-column:2}
.nav.top{margin:16px 0 0}
.nav.top a{padding:8px 14px}
.hero{padding:36px 0 8px}
.hero h1{font-size:2.4em;margin:0 0 .3em}
.hero p{font-size:1.1em;color:var(--muted);max-width:60ch;margin:0 0 1.2em}
.cta{display:inline-block;background:var(--accent);color:var(--bg);font-weight:600;text-decoration:none;
padding:11px 20px;border-radius:10px}
.toc{list-style:none;padding:0;margin:1em 0;display:grid;gap:8px}
.toc a{display:grid;grid-template-columns:44px 1fr;gap:12px;align-items:center;padding:12px 14px;
border:1px solid var(--line);border-radius:10px;background:var(--panel);text-decoration:none;color:var(--text);
transition:border-color .15s}
.toc a:hover{border-color:var(--accent)}
.toc .num{width:44px;height:44px;border-radius:10px;background:var(--accent-soft);color:var(--accent);
display:grid;place-items:center;font-weight:700;font-variant-numeric:tabular-nums}
.toc b{display:block;font-weight:600}
.toc small{color:var(--muted);font-size:14px;line-height:1.4;display:block}
footer{color:var(--muted);font-size:13px;text-align:center;padding:0 16px 32px}
@media(max-width:560px){body{font-size:16px}.hero h1{font-size:1.9em}.nav{grid-template-columns:1fr}
.nav .next{grid-column:1}}
@media(prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
@media print{.bar,.nav,footer{display:none}body{background:#fff}}
"""

KEYS = """
document.addEventListener('keydown', function (e) {
  if (e.altKey || e.ctrlKey || e.metaKey || /input|textarea/i.test(e.target.tagName)) return;
  var id = e.key === 'ArrowLeft' ? 'prev' : e.key === 'ArrowRight' ? 'next' : null;
  var link = id && document.getElementById(id);
  if (link) location.href = link.href;
});
document.addEventListener('click', function (e) {
  if (!e.target.classList.contains('copy')) return;
  var btn = e.target, code = btn.parentNode.querySelector('code').innerText;
  function done() {
    btn.textContent = 'Скопировано';
    setTimeout(function () { btn.textContent = 'Копировать'; }, 1500);
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(code).then(done);
  } else {
    var area = document.createElement('textarea');
    area.value = code;
    document.body.appendChild(area);
    area.select();
    document.execCommand('copy');
    document.body.removeChild(area);
    done();
  }
});
"""


def page(title, body, where="", progress=None):
    bar = f'<div class="progress"><i style="width:{progress}%"></i></div>' if progress is not None else ""
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
<header class="bar"><div class="bar-in">
<a class="home" href="index.html">☰ Содержание</a><span class="where">{html.escape(where)}</span>
</div>{bar}</header>
<main>
{body}
</main>
<footer>Аналитик данных: от нуля до первой работы · стрелки ← → на клавиатуре листают главы</footer>
<script>{KEYS}</script>
</body>
</html>
"""


def nav(prev, nxt, extra=""):
    parts = [f'<nav class="nav {extra}">']
    if prev:
        parts.append(f'<a class="prev" href="{prev[0]}"{" id=prev" if not extra else ""}>'
                     f'<small>← Назад</small><b>{html.escape(prev[1])}</b></a>')
    if nxt:
        parts.append(f'<a class="next" href="{nxt[0]}"{" id=next" if not extra else ""}>'
                     f'<small>Вперёд →</small><b>{html.escape(nxt[1])}</b></a>')
    parts.append("</nav>")
    return "".join(parts)


def build():
    OUT.mkdir(exist_ok=True)
    pages = []
    for name, label, about in CHAPTERS:
        text = (ROOT / name).read_text(encoding="utf-8")
        title = re.search(r"^# (.+)$", text, re.M).group(1)
        pages.append({"file": name[:-3] + ".html", "label": label, "about": about, "title": title, "text": text})

    home = ("index.html", "Содержание")
    for n, p in enumerate(pages):
        prev = (pages[n - 1]["file"], pages[n - 1]["title"]) if n else home
        nxt = (pages[n + 1]["file"], pages[n + 1]["title"]) if n + 1 < len(pages) else home
        body = nav(prev, nxt, "top") + convert_chapter(p["text"]) + nav(prev, nxt)
        where = f"{n + 1} из {len(pages)} · {p['title']}"
        (OUT / p["file"]).write_text(
            page(p["title"], body, where, round((n + 1) / len(pages) * 100)), encoding="utf-8")

    # Главная: обложка, оглавление и вводные разделы из README (без таблицы оглавления)
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme = re.sub(r"^# .+\n", "", readme, count=1)
    lead, rest = readme.split("\n## ", 1)
    sections = ["## " + s for s in rest.split("\n## ") if not s.startswith("Оглавление")]

    toc = ['<h2 id="toc">Содержание</h2><ol class="toc">']
    for p in pages:
        title = re.sub(r"^(Глава \d+|Приложение)\.\s*", "", p["title"])
        toc.append(f'<li><a href="{p["file"]}"><span class="num">{p["label"]}</span>'
                   f'<span><b>{html.escape(title)}</b><small>{html.escape(p["about"])}</small></span></a></li>')
    toc.append("</ol>")

    body = (
        '<section class="hero"><h1>Аналитик данных: от нуля до первой работы</h1>'
        f"<p>{inline(lead.strip())}</p>"
        f'<a class="cta" href="{pages[0]["file"]}" id="next">Начать читать →</a></section>'
        + "".join(toc)
        + convert("\n".join(sections))
    )
    (OUT / "index.html").write_text(page("Аналитик данных: от нуля до первой работы", body), encoding="utf-8")
    print(f"Готово: {len(pages) + 1} страниц в {OUT}")


if __name__ == "__main__":
    build()
