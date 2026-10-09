#!/usr/bin/env python3
"""Markdown記事をWordPressに「下書き」として投稿するスクリプト。

認証情報は環境変数 WP_URL / WP_USERNAME / WP_APP_PASSWORD から読む。
値はコードにも画面にも出さない。

使い方:
    python3 wp_post_draft.py 記事.md [アイキャッチ画像.png]
    python3 wp_post_draft.py --update 投稿ID 記事.md   (既存の投稿のタイトルと本文だけを上書き)
    python3 wp_post_draft.py   (引数なしで実行すると、記事と画像を番号で選べる)
"""
import base64
import html
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


def env(name):
    value = os.environ.get(name)
    if not value:
        sys.exit(f"環境変数 {name} が設定されていません")
    return value


BASE = env("WP_URL").rstrip("/") + "/wp-json/wp/v2"
AUTH = "Basic " + base64.b64encode(
    f"{env('WP_USERNAME')}:{env('WP_APP_PASSWORD')}".encode()
).decode()


def request(method, path, data=None, headers=None):
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Authorization", AUTH)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        sys.exit(f"WordPressがエラーを返しました: HTTP {e.code} {e.read()[:300]!r}")


def md_to_html(md):
    """見出し・段落・箇条書き・HTMLコメントだけを扱う簡易変換。"""
    out, para, items = [], [], []

    def flush():
        if para:
            out.append("<p>" + "".join(para) + "</p>")
            para.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
            items.clear()

    for line in md.splitlines():
        s = line.strip()
        if not s:
            flush()
        elif s.startswith("<"):
            # HTMLコメントやボタンなどのHTMLはそのまま通す
            flush()
            out.append(line)
        elif m := re.match(r"^(#{2,6})\s+(.*)", s):
            flush()
            level = len(m.group(1))
            out.append(f"<h{level}>{html.escape(m.group(2))}</h{level}>")
        elif s.startswith("- "):
            if para:
                flush()
            items.append(html.escape(s[2:]))
        else:
            if items:
                flush()
            para.append(html.escape(s))
    flush()
    return "\n".join(out)


def choose(label, paths, allow_none=False):
    """候補を番号付きで表示し、選ばれたパスを返す(「なし」は None)。"""
    if not paths and not allow_none:
        sys.exit(f"{label}が見つかりません")
    print(f"{label}を選んでください:")
    if allow_none:
        print("  0: なし")
    for i, path in enumerate(paths, 1):
        print(f"  {i}: {path}")
    while True:
        answer = input("番号> ").strip()
        if answer.isdigit():
            n = int(answer)
            if allow_none and n == 0:
                return None
            if 1 <= n <= len(paths):
                return paths[n - 1]
        print("一覧の番号を入力してください")


def pick_files():
    """スクリプトと同じフォルダから記事とアイキャッチ画像を選ばせる。"""
    folder = os.path.dirname(os.path.abspath(__file__))
    names = sorted(os.listdir(folder))
    articles = [n for n in names if n.endswith(".md") and n not in ("CLAUDE.md", "profile.md")]
    images = [n for n in names if n.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))]
    article = choose("記事", articles)
    image = choose("アイキャッチ画像", images, allow_none=True)
    return [os.path.join(folder, n) for n in (article, image) if n]


def main():
    args = sys.argv[1:]
    update_id = None
    if args[:1] == ["--update"]:
        if len(args) < 3:
            sys.exit(__doc__)
        update_id, args = args[1], args[2:]
    if not args:
        args = pick_files()
    md = open(args[0], encoding="utf-8").read()
    title_match = re.match(r"^#\s+(.*)", md)
    if not title_match:
        sys.exit("1行目に「# タイトル」が必要です")
    title = title_match.group(1).strip()
    body = md_to_html(md[title_match.end():])

    if update_id:
        # 状態(下書き/公開)とアイキャッチ画像は変えない
        updated = request("POST", f"/posts/{update_id}",
                          data=json.dumps({"title": title, "content": body}).encode(),
                          headers={"Content-Type": "application/json"})
        print(f"投稿を更新しました (投稿ID: {updated['id']}, 状態: {updated['status']})")
        return

    post = {"title": title, "content": body, "status": "draft"}

    if len(args) > 1:
        image_path = args[1]
        filename = urllib.parse.quote(os.path.basename(image_path))
        mime = mimetypes.guess_type(image_path)[0] or "application/octet-stream"
        with open(image_path, "rb") as f:
            media = request("POST", "/media", data=f.read(), headers={
                "Content-Type": mime,
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
            })
        post["featured_media"] = media["id"]
        print(f"画像をアップロードしました (メディアID: {media['id']})")

    created = request("POST", "/posts", data=json.dumps(post).encode(),
                      headers={"Content-Type": "application/json"})
    print(f"下書きを作成しました (投稿ID: {created['id']}, 状態: {created['status']})")


if __name__ == "__main__":
    main()
