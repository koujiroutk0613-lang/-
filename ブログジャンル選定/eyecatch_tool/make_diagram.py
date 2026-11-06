"""記事に入れる図解（1200x675）を作る。アイキャッチと同じタッチ・カテゴリ色。
使い方: python3 make_diagram.py spec.json 作業フォルダ
spec.json: {"out": 出力png, "cat": love|mind|..., "title": 見出し,
            "items": [{"head": 短い見出し, "body": 説明}, ...（3つまで）], "conclusion": まとめの一言}
"""
import html
import json
import subprocess
import sys

from PIL import Image

from make_eyecatch import CHROME, THEMES


def page(cat, title, items, conclusion):
    t = THEMES[cat]
    e = html.escape
    cards = "".join(
        f'<div class="card"><div class="num">{i + 1}</div><div class="head">{e(it["head"])}</div>'
        f'<div class="body">{e(it["body"])}</div></div>'
        for i, it in enumerate(items))
    return f'''<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@500;800;900&display=block" rel="stylesheet">
<style>
html,body{{margin:0;width:1200px;height:675px;overflow:hidden}}
body{{font-family:"M PLUS Rounded 1c",sans-serif;color:#3b2f2a;background-color:{t['bg']};
 background-image:radial-gradient({t['dot']} 2.5px,transparent 2.6px);background-size:28px 28px}}
.title{{margin:40px auto 0;width:max-content;background:#3b2f2a;color:#fff;font-weight:900;font-size:38px;padding:12px 40px;border-radius:40px}}
.row{{display:flex;gap:28px;justify-content:center;margin-top:62px}}
.card{{width:330px;height:250px;background:#fff;border-radius:24px;box-shadow:0 8px 0 {t['shadow']};position:relative;text-align:center;box-sizing:border-box;padding:62px 22px 0}}
.num{{position:absolute;left:50%;top:-30px;transform:translateX(-50%);width:62px;height:62px;border-radius:50%;background:{t['accent']};color:#fff;font-weight:900;font-size:34px;line-height:62px;box-shadow:0 4px 0 {t['badge_sh']}}}
.head{{font-weight:900;font-size:32px;color:{t['accent']};line-height:1.3}}
.body{{font-weight:800;font-size:23px;line-height:1.6;margin-top:16px;white-space:pre-line}}
.arrow{{width:0;height:0;margin:34px auto 0;border-left:34px solid transparent;border-right:34px solid transparent;border-top:34px solid {t['accent']}}}
.conc{{margin:22px auto 0;width:max-content;background:#fff;border:5px solid {t['accent']};border-radius:20px;font-weight:900;font-size:36px;padding:14px 44px}}
.conc span{{background:linear-gradient(transparent 62%,#ffe066 62%)}}
</style></head><body>
<div class="title">{e(title)}</div><div class="row">{cards}</div><div class="arrow"></div>
<div class="conc"><span>{e(conclusion)}</span></div></body></html>'''


def render(spec, work):
    out = spec.pop("out")
    h = f"{work}/diagram.html"
    open(h, "w", encoding="utf-8").write(page(**spec))
    subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    "--window-size=1200,900", "--virtual-time-budget=8000",
                    f"--screenshot={work}/diagram.png", "file://" + h], capture_output=True, timeout=90)
    Image.open(f"{work}/diagram.png").crop((0, 0, 1200, 675)).convert("RGB").save(out)
    return out


if __name__ == "__main__":
    print("wrote", render(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2]))
