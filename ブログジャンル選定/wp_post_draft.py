#!/usr/bin/env python3
"""Markdown記事をWordPressに「下書き」として投稿するスクリプト。

認証情報は環境変数 WP_URL / WP_USERNAME / WP_APP_PASSWORD から読む。
値はコードにも画面にも出さない。

使い方:
    python3 wp_post_draft.py 記事.md [アイキャッチ画像.png]
    python3 wp_post_draft.py --update 投稿ID 記事.md [アイキャッチ画像.png]
        (既存の投稿のタイトルと本文を上書き。画像を指定したときだけアイキャッチも差し替える)
"""
import base64
import html
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.request
import uuid


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


def upload_image(image_path):
    # 生のバイナリ送信はサーバーのWAFに拒否されるため、管理画面と同じmultipart形式で送る
    filename = os.path.basename(image_path).replace('"', "")
    mime = mimetypes.guess_type(image_path)[0] or "application/octet-stream"
    boundary = uuid.uuid4().hex
    with open(image_path, "rb") as f:
        data = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: {mime}\r\n\r\n"
        ).encode() + f.read() + f"\r\n--{boundary}--\r\n".encode()
    media = request("POST", "/media", data=data, headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    })
    print(f"画像をアップロードしました (メディアID: {media['id']})")
    return media["id"]


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
    args = sys.argv[1:]
    update_id = None
    if args[:1] == ["--update"]:
        if len(args) < 3:
            sys.exit(__doc__)
        update_id, args = args[1], args[2:]
    if not args:
        sys.exit(__doc__)
    md = open(args[0], encoding="utf-8").read()
    title_match = re.match(r"^#\s+(.*)", md)
    if not title_match:
        sys.exit("1行目に「# タイトル」が必要です")
    title = title_match.group(1).strip()
    body = md_to_html(md[title_match.end():])

    if update_id:
        # 状態(下書き/公開)は変えない。アイキャッチ画像は指定されたときだけ差し替える
        fields = {"title": title, "content": body}
        if len(args) > 1:
            fields["featured_media"] = upload_image(args[1])
        updated = request("POST", f"/posts/{update_id}",
                          data=json.dumps(fields).encode(),
                          headers={"Content-Type": "application/json"})
        print(f"投稿を更新しました (投稿ID: {updated['id']}, 状態: {updated['status']})")
        return

    post = {"title": title, "content": body, "status": "draft"}

    if len(args) > 1:
        post["featured_media"] = upload_image(args[1])

    created = request("POST", "/posts", data=json.dumps(post).encode(),
                      headers={"Content-Type": "application/json"})
    print(f"下書きを作成しました (投稿ID: {created['id']}, 状態: {created['status']})")


if __name__ == "__main__":
    main()
