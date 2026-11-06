"""吹き出し用のアイコン（400x400）を表情ごとに作る。
キャラは monkey（おさるさん。本人が昔「サル顔」と言われていたことから）と human。
使い方: python3 make_avatar.py 出力フォルダ 作業フォルダ [monkey|human]
"""
import subprocess
import sys

from PIL import Image

from make_eyecatch import CHROME

INK = "#3b2f2a"
SKIN = "#f7d7bf"
HAIR = "#4a3528"

EYES = {
    "normal": f'<circle cx="164" cy="200" r="8" fill="{INK}"/><circle cx="236" cy="200" r="8" fill="{INK}"/>',
    "smile": f'<path d="M150 204 q14 -16 28 0 M222 204 q14 -16 28 0" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>',
    "trouble": f'<circle cx="164" cy="204" r="8" fill="{INK}"/><circle cx="236" cy="204" r="8" fill="{INK}"/>',
    "think": f'<circle cx="170" cy="194" r="8" fill="{INK}"/><circle cx="242" cy="194" r="8" fill="{INK}"/>',
}
BROWS = {
    "normal": f'<path d="M148 176 q16 -8 32 0 M220 176 q16 -8 32 0" fill="none" stroke="{HAIR}" stroke-width="6" stroke-linecap="round"/>',
    "smile": f'<path d="M148 174 q16 -8 32 0 M220 174 q16 -8 32 0" fill="none" stroke="{HAIR}" stroke-width="6" stroke-linecap="round"/>',
    "trouble": f'<path d="M148 182 q18 -4 30 -14 M252 182 q-18 -4 -30 -14" fill="none" stroke="{HAIR}" stroke-width="6" stroke-linecap="round"/>',
    "think": f'<path d="M150 172 q16 -8 32 0 M222 168 q16 -10 32 -2" fill="none" stroke="{HAIR}" stroke-width="6" stroke-linecap="round"/>',
}
MOUTH = {
    "normal": f'<path d="M184 246 q16 12 32 0" fill="none" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>',
    "smile": f'<path d="M176 240 q24 30 48 0z" fill="#d9665a" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>',
    "trouble": f'<path d="M182 252 q9 -8 18 0 t18 0" fill="none" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>',
    "think": f'<path d="M192 250 h22" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>',
}
EXTRA = {
    "normal": "",
    "smile": "",
    "trouble": '<path d="M300 150 q16 26 0 36 q-16 -10 0 -36z" fill="#7cc4e8" stroke="#3b2f2a" stroke-width="4"/>',
    "think": '<circle cx="320" cy="100" r="30" fill="#ffe066" stroke="#3b2f2a" stroke-width="5"/><path d="M309 92 q0 -14 12 -14 q12 0 12 11 q0 8 -11 13 v8" fill="none" stroke="#3b2f2a" stroke-width="6" stroke-linecap="round"/><circle cx="322" cy="121" r="4" fill="#3b2f2a"/>',
}


def svg(face):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
<circle cx="200" cy="200" r="196" fill="#ffeede"/>
<clipPath id="c"><circle cx="200" cy="200" r="196"/></clipPath>
<g clip-path="url(#c)">
 <path d="M70 420 q0 -110 130 -110 q130 0 130 110z" fill="#8cc4b4" stroke="{INK}" stroke-width="7"/>
 <path d="M168 314 l32 32 l32 -32" fill="#fff" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>
 <rect x="178" y="270" width="44" height="50" fill="{SKIN}" stroke="{INK}" stroke-width="6"/>
 <circle cx="104" cy="210" r="20" fill="{SKIN}" stroke="{INK}" stroke-width="6"/>
 <circle cx="296" cy="210" r="20" fill="{SKIN}" stroke="{INK}" stroke-width="6"/>
 <ellipse cx="200" cy="200" rx="96" ry="102" fill="{SKIN}" stroke="{INK}" stroke-width="7"/>
 <path d="M104 192 q-6 -108 96 -110 q102 2 96 110 q-10 -32 -32 -44 q-28 16 -64 12 q-30 -3 -50 -16 q-30 12 -46 48z" fill="{HAIR}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>
 <ellipse cx="146" cy="232" rx="16" ry="9" fill="#f4a3a0" opacity=".7"/>
 <ellipse cx="254" cy="232" rx="16" ry="9" fill="#f4a3a0" opacity=".7"/>
 {BROWS[face]}{EYES[face]}{MOUTH[face]}
</g>{EXTRA[face]}</svg>'''


FUR = "#8a5a3c"
MASK = "#f7dcc3"


def svg_monkey(face):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
<circle cx="200" cy="200" r="196" fill="#ffeede"/>
<clipPath id="c"><circle cx="200" cy="200" r="196"/></clipPath>
<g clip-path="url(#c)">
 <path d="M70 420 q0 -110 130 -110 q130 0 130 110z" fill="#8cc4b4" stroke="{INK}" stroke-width="7"/>
 <path d="M168 314 l32 32 l32 -32" fill="#fff" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>
 <circle cx="88" cy="196" r="40" fill="{FUR}" stroke="{INK}" stroke-width="7"/><circle cx="88" cy="196" r="22" fill="#f4b8a4"/>
 <circle cx="312" cy="196" r="40" fill="{FUR}" stroke="{INK}" stroke-width="7"/><circle cx="312" cy="196" r="22" fill="#f4b8a4"/>
 <circle cx="200" cy="196" r="112" fill="{FUR}" stroke="{INK}" stroke-width="7"/>
 <path d="M186 86 q6 -26 30 -20 q-18 4 -14 24" fill="{FUR}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>
 <circle cx="164" cy="178" r="48" fill="{MASK}"/><circle cx="236" cy="178" r="48" fill="{MASK}"/>
 <ellipse cx="200" cy="236" rx="80" ry="58" fill="{MASK}"/>
 <ellipse cx="192" cy="214" rx="5" ry="4" fill="{INK}"/><ellipse cx="208" cy="214" rx="5" ry="4" fill="{INK}"/>
 <ellipse cx="140" cy="232" rx="15" ry="9" fill="#f4a3a0" opacity=".8"/>
 <ellipse cx="260" cy="232" rx="15" ry="9" fill="#f4a3a0" opacity=".8"/>
 <g transform="translate(0,-16)">{BROWS[face]}{EYES[face]}</g>
 <g transform="translate(0,-6)">{MOUTH[face]}</g>
</g>{EXTRA[face]}</svg>'''


def render(face, out, work, char="monkey"):
    h = f"{work}/avatar_{face}.html"
    open(h, "w", encoding="utf-8").write(
        '<!doctype html><meta charset="utf-8"><link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@900&display=block" rel="stylesheet">'
        f'<style>html,body{{margin:0;background:transparent}}</style>{(svg_monkey if char == "monkey" else svg)(face)}')
    png = f"{work}/avatar_{face}.png"
    subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    "--default-background-color=00000000", "--window-size=400,600",
                    "--virtual-time-budget=6000", f"--screenshot={png}", "file://" + h],
                   capture_output=True, timeout=90)
    Image.open(png).crop((0, 0, 400, 400)).save(out)


if __name__ == "__main__":
    char = sys.argv[3] if len(sys.argv) > 3 else "monkey"
    for face in EYES:
        render(face, f"{sys.argv[1]}/avatar_{char}_{face}.png", sys.argv[2], char)
        print("wrote", char, face)
