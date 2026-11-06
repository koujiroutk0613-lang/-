"""ブログ共通デザインのアイキャッチ画像（1200x630）を作る。
使い方: python3 make_eyecatch.py specs.json 作業フォルダ
specs.json: [{"out": 出力png, "cat": love|mind|family|work|body|life, "l1": 上の一言, "l2": 大きい色文字, "l3": マーカー文字, "pill": 下の帯}]
"""
import json
import subprocess
import sys

from PIL import Image

import glob
import shutil

# 環境によってChromiumの場所が違うので、見つかったものを使う
CHROME = (sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")) or [None])[-1] \
    or shutil.which("google-chrome") or shutil.which("chromium")

THEMES = {
    "love":   dict(bg="#ffeede", dot="#ffd9bf", accent="#e5603c", shadow="#f6c9ad", badge_sh="#b8452a", soft="#ffe3d3", soft2="#e5a089"),
    "mind":   dict(bg="#e6f2fb", dot="#c9e2f5", accent="#2f7fc1", shadow="#b9d6ee", badge_sh="#1f5d91", soft="#d6eaf8", soft2="#86b6dc"),
    "family": dict(bg="#e9f5e6", dot="#cfe8c8", accent="#3f9a52", shadow="#bfdcb8", badge_sh="#2c7139", soft="#d8eed3", soft2="#8cc49a"),
    "work":   dict(bg="#e8ebf3", dot="#cfd5e6", accent="#2c3e73", shadow="#c3cadf", badge_sh="#1c2a52", soft="#d9deee", soft2="#8e9cc6"),
    "body":   dict(bg="#fdeef2", dot="#f8d6e0", accent="#d0547a", shadow="#f1c4d2", badge_sh="#a03a5a", soft="#fadbe5", soft2="#e59ab2"),
    "life":   dict(bg="#fff6dc", dot="#fbe7a8", accent="#d9910b", shadow="#f2dca0", badge_sh="#a86d05", soft="#fdefc2", soft2="#e9c470"),
}

ILL = {
    "love": '''<rect x="70" y="20" width="270" height="500" rx="38" fill="#3b2f2a"/><rect x="86" y="58" width="238" height="430" rx="18" fill="#fffaf6"/>
<rect x="108" y="86" width="200" height="60" rx="20" fill="{accent}"/><rect x="128" y="166" width="180" height="60" rx="20" fill="{accent}"/>
<rect x="102" y="262" width="104" height="52" rx="20" fill="{soft}"/><circle cx="130" cy="288" r="7" fill="{soft2}"/><circle cx="154" cy="288" r="7" fill="{soft2}"/><circle cx="178" cy="288" r="7" fill="{soft2}"/>
<path d="M205 440 c-30 -20 -48 -36 -48 -58 a24 24 0 0 1 48 -6 a24 24 0 0 1 48 6 c0 22 -18 38 -48 58z" fill="{accent}"/>''',
    "mind": '''<circle cx="200" cy="250" r="150" fill="{soft}"/>
<path d="M150 400 v-40 a110 110 0 1 1 120 0 v40z" fill="#fff" stroke="#3b2f2a" stroke-width="8" stroke-linejoin="round"/>
<circle cx="210" cy="240" r="46" fill="#ffe066" stroke="#3b2f2a" stroke-width="7"/><rect x="194" y="282" width="32" height="26" rx="6" fill="#3b2f2a"/>
<path d="M210 168 v-24 M262 190 l18 -18 M158 190 l-18 -18 M284 240 h24 M136 240 h-24" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>
<path d="M120 470 q30 -30 60 0 t60 0 t60 0" fill="none" stroke="{soft2}" stroke-width="8" stroke-linecap="round"/>''',
    "family": '''<circle cx="200" cy="290" r="160" fill="{soft}"/>
<path d="M78 420 a52 76 0 0 1 104 0z" fill="{accent}" stroke="#3b2f2a" stroke-width="7"/><circle cx="130" cy="300" r="36" fill="#fff" stroke="#3b2f2a" stroke-width="7"/>
<path d="M218 420 a52 76 0 0 1 104 0z" fill="{soft2}" stroke="#3b2f2a" stroke-width="7"/><circle cx="270" cy="300" r="36" fill="#fff" stroke="#3b2f2a" stroke-width="7"/>
<path d="M160 420 a40 54 0 0 1 80 0z" fill="#ffe066" stroke="#3b2f2a" stroke-width="7"/><circle cx="200" cy="344" r="27" fill="#fff" stroke="#3b2f2a" stroke-width="7"/>
<path d="M200 220 c-24 -16 -38 -29 -38 -46 a19 19 0 0 1 38 -4 a19 19 0 0 1 38 4 c0 17 -14 30 -38 46z" fill="{accent}"/>
<path d="M50 424 h300" stroke="#3b2f2a" stroke-width="7" stroke-linecap="round"/>''',
    "work": '''<circle cx="200" cy="260" r="160" fill="{soft}"/>
<rect x="70" y="200" width="260" height="170" rx="16" fill="#3b2f2a"/><rect x="86" y="216" width="228" height="138" rx="8" fill="#fff"/>
<path d="M40 380 h320 l-24 30 h-272z" fill="#6b5a52"/>
<rect x="106" y="240" width="120" height="12" rx="6" fill="{soft2}"/><rect x="106" y="266" width="170" height="12" rx="6" fill="{soft2}"/><rect x="106" y="292" width="140" height="12" rx="6" fill="{soft2}"/>
<rect x="230" y="70" width="120" height="150" rx="14" fill="#fff" stroke="#3b2f2a" stroke-width="7"/><rect x="262" y="58" width="56" height="24" rx="8" fill="{accent}"/>
<path d="M252 118 l12 12 l22 -24 M252 168 l12 12 l22 -24" fill="none" stroke="{accent}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="110" cy="470" r="40" fill="#ffe066"/><path d="M90 470 l14 14 l26 -28" fill="none" stroke="#3b2f2a" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>''',
}
ILL["body"] = ILL["mind"]
ILL["life"] = ILL["family"]


def html(cat, l1, l2, l3, pill, badge="実体験<br>ブログ"):
    t = THEMES[cat]
    ill = ILL[cat].format(**t)
    return f'''<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@500;800;900&display=block" rel="stylesheet">
<style>
html,body{{margin:0;width:1200px;height:630px;overflow:hidden}}
body{{font-family:"M PLUS Rounded 1c",sans-serif;position:relative;color:#3b2f2a;background-color:{t['bg']};background-image:radial-gradient({t['dot']} 2.5px,transparent 2.6px);background-size:28px 28px}}
.card{{position:absolute;left:44px;top:44px;width:700px;height:542px;background:#fff;border-radius:28px;box-shadow:0 10px 0 {t['shadow']}}}
.badge{{position:absolute;left:18px;top:14px;width:118px;height:118px;border-radius:50%;background:{t['accent']};color:#fff;font-weight:900;font-size:30px;display:flex;align-items:center;justify-content:center;transform:rotate(-12deg);box-shadow:0 5px 0 {t['badge_sh']};z-index:3;line-height:1.1;text-align:center}}
.t{{position:absolute;left:96px;top:118px;font-weight:900;width:620px}}
.l1{{font-size:46px;white-space:nowrap}}
.l2{{font-size:100px;color:{t['accent']};line-height:1.15;margin-top:6px;white-space:nowrap}}
.l3{{font-size:96px;line-height:1.15;white-space:nowrap}}
.l3 span{{background:linear-gradient(transparent 62%,#ffe066 62%)}}
.pill{{position:absolute;left:96px;top:478px;background:#3b2f2a;color:#fff;font-weight:800;font-size:28px;padding:12px 30px;border-radius:40px;white-space:nowrap}}
.ill{{position:absolute;right:34px;top:40px}}
</style></head><body><div class="card"></div><div class="badge">{badge}</div>
<div class="t"><div class="l1">{l1}</div><div class="l2">{l2}</div><div class="l3"><span>{l3}</span></div></div>
<div class="pill">{pill}</div><svg class="ill" width="400" height="560" viewBox="0 0 400 560">{ill}</svg></body></html>'''


def render(spec, out, work):
    h = f"{work}/tmp.html"
    open(h, "w", encoding="utf-8").write(html(**spec))
    subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    "--window-size=1200,800", "--virtual-time-budget=8000",
                    f"--screenshot={work}/tmp.png", "file://" + h], capture_output=True, timeout=90)
    # ヘッドレスは表示領域が窓より短いので、高めに撮ってから切り出す
    Image.open(f"{work}/tmp.png").crop((0, 0, 1200, 630)).convert("RGB").save(out)


if __name__ == "__main__":
    specs = json.load(open(sys.argv[1], encoding="utf-8"))
    for s in specs:
        out = s.pop("out")
        render(s, out, sys.argv[2])
        print("wrote", out)
