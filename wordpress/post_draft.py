#!/usr/bin/env python3
"""MarkdownファイルをWordPressに「下書き」として保存する。

認証情報は環境変数から読む(コードやチャットに書かない):
  WP_URL / WP_USERNAME / WP_APP_PASSWORD

使い方:
  python3 wordpress/post_draft.py articles/sample.md --dry-run   # 送信せず確認だけ
  python3 wordpress/post_draft.py articles/sample.md             # 下書き作成
  python3 wordpress/post_draft.py --check                        # 接続確認(読み取りのみ)

記事の先頭にfront matterを書ける:
  ---
  title: 記事タイトル
  slug: english-slug        (任意)
  categories: [体験談]       (任意・既存カテゴリ名のみ)
  tags: [ADHD, マッチングアプリ] (任意・既存タグ名のみ)
  excerpt: 抜粋              (任意)
  ---
安全のため、status は常に draft 固定(公開は行わない)。
"""
import argparse
import base64
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


def load_config():
    missing = [k for k in ("WP_URL", "WP_USERNAME", "WP_APP_PASSWORD") if not os.environ.get(k)]
    if missing:
        sys.exit("環境変数が未設定です: " + ", ".join(missing))
    url = os.environ["WP_URL"].rstrip("/")
    if not url.startswith("https://"):
        sys.exit("WP_URL は https:// で始まる必要があります(通信の暗号化のため)。")
    # アプリケーションパスワードは表示時に空白入りのことがあるため除去
    password = os.environ["WP_APP_PASSWORD"].replace(" ", "")
    token = base64.b64encode(f"{os.environ['WP_USERNAME']}:{password}".encode()).decode()
    return url, token


def api(url, token, path, method="GET", body=None, query=None):
    full = f"{url}/wp-json/wp/v2/{path}"
    if query:
        full += "?" + urllib.parse.urlencode(query)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(full, data=data, method=method, headers={
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
        "User-Agent": "blog-draft-poster/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        # 認証ヘッダーは出力しない。エラー本文のメッセージだけ表示
        try:
            msg = json.load(e).get("message", "")
        except Exception:
            msg = ""
        sys.exit(f"WordPress APIエラー {e.code}: {msg}")
    except urllib.error.URLError as e:
        sys.exit(f"接続エラー: {e.reason}")


def parse_front_matter(text):
    meta = {}
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    if not m:
        return meta, text
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
        else:
            v = v.strip("'\"")
        meta[k] = v
    return meta, text[m.end():]


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"\[(.+?)\]\((https?://[^)\s]+)\)",
               r'<a href="\2" rel="noopener">\1</a>', s)
    return s


def md_to_html(md):
    """見出し・段落・箇条書き・引用・区切り線に対応した最小限の変換。"""
    out, para, items, quote = [], [], None, []

    def flush():
        nonlocal para, items, quote
        if para:
            out.append("<p>" + "<br>".join(inline(x) for x in para) + "</p>")
            para = []
        if items:
            tag, lis = items
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in lis) + f"</{tag}>")
            items = None
        if quote:
            out.append("<blockquote><p>" + "<br>".join(inline(x) for x in quote) + "</p></blockquote>")
            quote = []

    for line in md.splitlines():
        s = line.rstrip()
        h = re.match(r"^(#{1,6})\s+(.*)", s)
        ul = re.match(r"^[-*]\s+(.*)", s)
        ol = re.match(r"^\d+\.\s+(.*)", s)
        bq = re.match(r"^>\s?(.*)", s)
        if not s.strip():
            flush()
        elif h:
            flush()
            n = len(h.group(1))
            out.append(f"<h{n}>{inline(h.group(2))}</h{n}>")
        elif re.match(r"^(-{3,}|\*{3,})$", s):
            flush()
            out.append("<hr>")
        elif ul or ol:
            tag = "ul" if ul else "ol"
            if items and items[0] != tag:
                flush()
            if not items:
                if para or quote:
                    flush()
                items = (tag, [])
            items[1].append((ul or ol).group(1))
        elif bq:
            if para or items:
                flush()
            quote.append(bq.group(1))
        else:
            if items or quote:
                flush()
            para.append(s.strip())
    flush()
    return "\n".join(out)


def resolve_terms(url, token, kind, names):
    """既存のカテゴリ/タグ名をIDに変換。存在しない名前は警告して無視(勝手に作らない)。"""
    ids = []
    for name in names:
        found = api(url, token, kind, query={"search": name, "per_page": 100})
        hit = next((t for t in found if t["name"] == name), None)
        if hit:
            ids.append(hit["id"])
        else:
            print(f"  警告: {kind} '{name}' はサイトに存在しないため付与しません", file=sys.stderr)
    return ids


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="Markdownファイル")
    ap.add_argument("--dry-run", action="store_true", help="送信せず内容だけ表示")
    ap.add_argument("--check", action="store_true", help="接続・認証の確認のみ(読み取り)")
    args = ap.parse_args()

    if args.check:
        url, token = load_config()
        me = api(url, token, "users/me", query={"context": "edit"})
        print(f"接続OK: {url} / ユーザー表示名: {me.get('name')}")
        return
    if not args.file:
        ap.error("Markdownファイルを指定してください")

    with open(args.file, encoding="utf-8") as f:
        meta, body = parse_front_matter(f.read())
    title = meta.get("title")
    if not title:
        sys.exit("front matter に title が必要です")
    content = md_to_html(body)
    payload = {"title": title, "content": content, "status": "draft"}
    for k in ("slug", "excerpt"):
        if meta.get(k):
            payload[k] = meta[k]

    if args.dry_run:
        print(f"[dry-run] タイトル: {title}\n[dry-run] status: draft\n--- HTML ---\n{content}")
        return

    url, token = load_config()
    for key, kind in (("categories", "categories"), ("tags", "tags")):
        if meta.get(key):
            names = meta[key] if isinstance(meta[key], list) else [meta[key]]
            payload[key] = resolve_terms(url, token, kind, names)
    res = api(url, token, "posts", method="POST", body=payload)
    print(f"下書きを作成しました(ID {res['id']}, status={res['status']})")
    print(f"編集画面: {url}/wp-admin/post.php?post={res['id']}&action=edit")


if __name__ == "__main__":
    main()
