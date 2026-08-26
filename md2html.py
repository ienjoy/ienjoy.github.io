#!/usr/bin/env python3
"""把 LLM白话.md 转成 ienjoy.github.io 风格的单页 HTML（仅用标准库）。

处理顺序很重要：
  1. 先摘出 ``` 代码块  —— 否则代码里的 # 注释会被当成标题
  2. 再摘出 $...$ 数学  —— 交给浏览器端 KaTeX 渲染，中途不能被转义
  3. 然后做块级解析（标题/表格/引用/列表/段落）
  4. 最后做行内解析，并把代码与数学放回去
"""
import html
import re
import sys

CODE_MARK = "\x00C{}\x00"
MATH_MARK = "\x00M{}\x00"
ICODE_MARK = "\x00I{}\x00"

CJK = re.compile(r"[　-〿一-鿿＀-￯]")


# ---------------------------------------------------------------- 行内处理
def inline(text, icode):
    """转义 + 粗体/斜体/行内代码。数学与块级代码此时已是占位符。"""
    def stash(m):
        icode.append(html.escape(m.group(1), quote=False))
        return ICODE_MARK.format(len(icode) - 1)

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def join_lines(lines):
    """段落内换行：中文之间不插空格，其余插空格。"""
    out = lines[0]
    for nxt in lines[1:]:
        if out and nxt and CJK.search(out[-1]) and CJK.search(nxt[0]):
            out += nxt
        else:
            out += " " + nxt
    return out


# ---------------------------------------------------------------- 主转换
def convert(src):
    codes, maths, icode = [], [], []

    # 1. 代码块
    def stash_code(m):
        codes.append((m.group(1).strip(), m.group(2)))
        return "\n" + CODE_MARK.format(len(codes) - 1) + "\n"

    src = re.sub(r"^```([^\n]*)\n(.*?)^```[ \t]*$", stash_code,
                 src, flags=re.S | re.M)

    # 2. 数学（先块级 $$ 再行内 $）
    def stash_math(m):
        maths.append(m.group(0))
        return MATH_MARK.format(len(maths) - 1)

    src = re.sub(r"\$\$.*?\$\$", stash_math, src, flags=re.S)
    src = re.sub(r"\$[^$\n]+\$", stash_math, src)

    # 3. 块级解析
    out, toc = [], []
    para, sec = [], [0]

    def flush():
        if para:
            out.append("<p>" + inline(join_lines(para), icode) + "</p>")
            para.clear()

    lines = src.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        stripped = ln.strip()

        # 代码块占位符
        m = re.fullmatch(r"\x00C(\d+)\x00", stripped)
        if m:
            flush()
            lang, body = codes[int(m.group(1))]
            cls = f' class="language-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>"
                       + html.escape(body.rstrip("\n"), quote=False)
                       + "</code></pre>")
            i += 1
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            flush()
            lvl, txt = len(m.group(1)), m.group(2).strip()
            if lvl <= 2:
                sec[0] += 1
                sid = f"s{sec[0]}"
                toc.append((lvl, sid, txt))
                out.append(f'<h{lvl} id="{sid}">{inline(txt, icode)}</h{lvl}>')
            else:
                out.append(f"<h{lvl}>{inline(txt, icode)}</h{lvl}>")
            i += 1
            continue

        # 分隔线
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            flush()
            out.append("<hr>")
            i += 1
            continue

        # 表格
        if (stripped.startswith("|") and i + 1 < len(lines)
                and re.fullmatch(r"[\s|:\-]+", lines[i + 1].strip())
                and "-" in lines[i + 1]):
            flush()
            def cells(row):
                row = row.strip()
                if row.startswith("|"):
                    row = row[1:]
                if row.endswith("|"):
                    row = row[:-1]
                return [c.strip() for c in row.split("|")]

            head = cells(lines[i])
            i += 2
            body = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                body.append(cells(lines[i]))
                i += 1
            t = ["<table>", "<thead><tr>"]
            t += [f"<th>{inline(c, icode)}</th>" for c in head]
            t.append("</tr></thead><tbody>")
            for row in body:
                row = (row + [""] * len(head))[:len(head)]
                t.append("<tr>" + "".join(
                    f"<td>{inline(c, icode)}</td>" for c in row) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t))
            continue

        # 引用块
        if stripped.startswith(">"):
            flush()
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            inner, chunk = [], []
            for b in buf:
                if b.strip():
                    chunk.append(b.strip())
                elif chunk:
                    inner.append("<p>" + inline(join_lines(chunk), icode) + "</p>")
                    chunk = []
            if chunk:
                inner.append("<p>" + inline(join_lines(chunk), icode) + "</p>")
            out.append("<blockquote>" + "".join(inner) + "</blockquote>")
            continue

        # 列表
        m = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", ln)
        if m:
            flush()
            ordered = bool(re.fullmatch(r"\d+\.", m.group(2)))
            tag = "ol" if ordered else "ul"
            items = []
            while i < len(lines):
                mm = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", lines[i])
                if mm:
                    items.append([mm.group(3).strip()])
                    i += 1
                elif items and lines[i].strip() and lines[i].startswith(("  ", "\t")):
                    items[-1].append(lines[i].strip())   # 续行
                    i += 1
                else:
                    break
            out.append(f"<{tag}>" + "".join(
                "<li>" + inline(join_lines(it), icode) + "</li>" for it in items
            ) + f"</{tag}>")
            continue

        # 空行 / 普通段落
        if not stripped:
            flush()
        else:
            para.append(stripped)
        i += 1

    flush()
    body_html = "\n".join(out)

    # 4. 放回占位符
    # 数学必须转义再放回：像 t_{<i} 里的 "<" 会被浏览器当成标签开始，
    # 吞掉后面的内容。KaTeX 读的是 DOM 的 textContent，&lt; 到它眼里仍是 <。
    maths = [html.escape(m, quote=False) for m in maths]
    for n, mth in enumerate(maths):
        body_html = body_html.replace(MATH_MARK.format(n), mth)
    for n, c in enumerate(icode):
        body_html = body_html.replace(ICODE_MARK.format(n), f"<code>{c}</code>")

    return body_html, toc, maths, icode


# ---------------------------------------------------------------- 页面模板
HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="从 Embedding 到概率论：LLM 计算过程的白话拆解，附两个可动手复现的实验">
<title>LLM 白话：概率论在大模型里到底起什么作用</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.css">
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js"></script>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body, {
    delimiters: [
      {left: '$$', right: '$$', display: true},
      {left: '$', right: '$', display: false}
    ],
    ignoredTags: ['script','noscript','style','textarea','pre','code'],
    throwOnError: false
  });"></script>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --border: #2a2d3a;
    --text: #e2e4ed;
    --muted: #8b8fa8;
    --accent: #5b8af0;
    --accent2: #a78bfa;
    --green: #34d399;
    --yellow: #fbbf24;
    --code-bg: #12151f;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Georgia', 'Noto Serif SC', serif;
    font-size: 16px;
    line-height: 1.8;
    padding: 2rem 1rem;
  }
  .container { max-width: 860px; margin: 0 auto; }
  .back-link {
    display: inline-block;
    margin-bottom: 1.4rem;
    color: var(--muted);
    text-decoration: none;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 0.9rem;
  }
  .back-link:hover { color: var(--accent); }
  h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #fff;
    border-bottom: 2px solid var(--accent);
    padding-bottom: 0.6rem;
    margin: 2.6rem 0 0.4rem;
    line-height: 1.3;
  }
  h1:first-of-type { margin-top: 0; }
  h2 {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--accent);
    margin: 2.4rem 0 0.8rem;
    padding-left: 0.8rem;
    border-left: 3px solid var(--accent);
  }
  h3 {
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--accent2);
    margin: 1.8rem 0 0.6rem;
  }
  h4 {
    font-size: 1rem;
    font-weight: 600;
    color: var(--yellow);
    margin: 1.4rem 0 0.4rem;
  }
  p { margin: 0.7rem 0; }
  blockquote {
    border-left: 3px solid var(--green);
    background: #0d1f17;
    color: var(--green);
    padding: 0.8rem 1.2rem;
    margin: 1.2rem 0;
    border-radius: 0 6px 6px 0;
  }
  blockquote p { margin: 0.3rem 0; color: var(--green); }
  blockquote strong { color: #6ee7b7; }
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.2rem 0;
    font-size: 0.92rem;
  }
  .table-wrap { overflow-x: auto; }
  th {
    background: var(--surface);
    color: var(--accent);
    padding: 0.55rem 0.9rem;
    text-align: left;
    border: 1px solid var(--border);
    font-weight: 600;
  }
  td {
    padding: 0.5rem 0.9rem;
    border: 1px solid var(--border);
    color: var(--text);
  }
  tr:nth-child(even) td { background: #13161f; }
  code {
    background: var(--code-bg);
    color: #7dd3fc;
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
    font-size: 0.88em;
  }
  pre {
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.1rem 1.3rem;
    overflow-x: auto;
    margin: 1.1rem 0;
  }
  pre code {
    background: none;
    color: #94a3b8;
    padding: 0;
    font-size: 0.85rem;
    line-height: 1.55;
    white-space: pre;
  }
  hr { border: none; border-top: 1px solid var(--border); margin: 2rem 0; }
  ul, ol { padding-left: 1.6rem; margin: 0.6rem 0; }
  li { margin: 0.3rem 0; }
  strong { color: #fff; }
  em { color: var(--muted); font-style: italic; }
  .katex-display { overflow-x: auto; overflow-y: hidden; padding: 0.4rem 0; }
  .subtitle {
    color: var(--muted);
    font-size: 0.95rem;
    margin-bottom: 2rem;
    font-style: italic;
  }
  .toc {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 1.4rem;
    margin: 1.5rem 0 2.5rem;
    font-size: 0.93rem;
    max-height: 460px;
    overflow-y: auto;
  }
  .toc-title {
    color: var(--accent);
    font-weight: 700;
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
  }
  .toc a { color: var(--muted); text-decoration: none; display: block; padding: 0.15rem 0; }
  .toc a:hover { color: var(--text); }
  .toc a.lv1 { color: var(--text); font-weight: 600; margin-top: 0.5rem; }
  .toc a.lv2 { padding-left: 1.2rem; font-size: 0.88rem; }
  @media (max-width: 680px) {
    body { padding: 1rem 0.6rem; font-size: 15px; }
    table { font-size: 0.84rem; }
  }
</style>
</head>
<body>
<div class="container">
<nav aria-label="站点导航"><a class="back-link" href="index.html">&larr; 返回文章首页</a></nav>

<h1 style="margin-top:0">LLM 白话</h1>
<p class="subtitle">从 Embedding、前向与反向传播，到概率论究竟在大模型里起什么作用。
含四轮反自欺式自我审查，以及九个附录——最后两个附录给出两个可以在自己电脑上跑通的实验：
校准曲线，和用一台自造的「说话机器」检验网络到底有没有学到真实概率。</p>
"""

TAIL = """
<hr>
<p class="subtitle" style="margin-top:2rem">iEnjoy &middot; GPU &amp; LLM Learning Notes</p>
</div>
</body>
</html>
"""


def main():
    md_path, out_path = sys.argv[1], sys.argv[2]
    src = open(md_path, encoding="utf-8").read()
    body, toc, maths, icode = convert(src)

    nav = ['<div class="toc">', '<div class="toc-title">目录</div>']
    for lvl, sid, txt in toc:
        txt = txt.replace("**", "").replace("`", "")
        txt = html.escape(txt, quote=False)
        # 标题里的数学与行内代码此时仍是占位符，转义之后再放回
        for n, mth in enumerate(maths):
            txt = txt.replace(MATH_MARK.format(n), mth)
        for n, c in enumerate(icode):
            txt = txt.replace(ICODE_MARK.format(n), c)
        nav.append(f'<a class="lv{lvl}" href="#{sid}">{txt}</a>')
    nav.append("</div>")

    # 宽表格加横向滚动壳
    body = re.sub(r"<table>", '<div class="table-wrap"><table>', body)
    body = re.sub(r"</table>", "</table></div>", body)

    open(out_path, "w", encoding="utf-8").write(
        HEAD + "\n".join(nav) + "\n" + body + TAIL)
    print(f"写出 {out_path}")
    print(f"目录条目 {len(toc)} 条")


if __name__ == "__main__":
    main()
