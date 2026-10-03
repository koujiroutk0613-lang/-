#!/usr/bin/env python3
"""Markdown記事をWordPressに「下書き」として投稿するスクリプト。

認証情報は環境変数 WP_URL / WP_USERNAME / WP_APP_PASSWORD から読む。
値はコードにも画面にも出さない。

使い方:
    python3 wp_post_draft.py 記事.md [アイキャッチ画像.png]
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


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    md = open(sys.argv[1], encoding="utf-8").read()
    title_match = re.match(r"^#\s+(.*)", md)
    if not title_match:
        sys.exit("1行目に「# タイトル」が必要です")
    title = title_match.group(1).strip()
    body = md_to_html(md[title_match.end():])

    post = {"title": title, "content": body, "status": "draft"}

    if len(sys.argv) > 2:
        image_path = sys.argv[2]
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
