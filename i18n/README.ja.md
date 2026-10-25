# YouTube CLI

[🇬🇧 English](../README.md) · [🇨🇿 Čeština](../README.cs.md) · [🇪🇸 Español](README.es.md) · [🇧🇷 Português](README.pt-BR.md) · [🇩🇪 Deutsch](README.de.md) · [🇫🇷 Français](README.fr.md) · [🇨🇳 简体中文](README.zh-CN.md) · **🇯🇵 日本語** · [🇸🇪 Svenska](README.sv.md) · [🇳🇴 Norsk](README.nb.md) · [🇩🇰 Dansk](README.da.md)

YouTube の動画を管理し（YouTube Data API v3）、チャンネルのパフォーマンスを取得する（YouTube Analytics API v2）Python 製のコマンドラインツールです。YouTube に定期的に投稿していて、YouTube Studio でのクリック作業を減らしたい人向け。

動画の公開には手作業の繰り返しがつきものです。ファイルのアップロード、タイトルと説明文の入力、公開設定、サムネイルの追加、再生リストへの登録。この CLI はこれらを自動化するので、スクリプトでつなげたり、[Claude Code](https://docs.anthropic.com/en/docs/claude-code) などの AI エージェントに任せたりできます。

作者：[Jindřich Fáborský](https://www.faborsky.com)

## できること

- `upload`：メタデータ、サムネイル、再生リスト、予約公開まで含めて動画をアップロード。デフォルトは `private`。
- `video-update` と `video-delete`：指定した項目だけを変更。削除には `--confirm` が必要です。
- `stats` と `analytics`：視聴回数、総再生時間、視聴維持率、トラフィックソース、ショートと長尺動画の比較。
- 新しい定義（2026 年 8 月 24 日以降）の視聴回数と、旧定義の `engagedViews` の両方を表示します。
- 全コマンドで `--json` に対応：stdout にはデータだけを出力するので、スクリプトや AI エージェントで扱いやすい。

## クイックスタート

```bash
git clone https://github.com/faborsky/youtube-cli-app.git
cd youtube-cli-app

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your Google Cloud OAuth credentials

python youtube_cli.py auth
python youtube_cli.py videos
python youtube_cli.py analytics --days 28
```

完全なドキュメント（Google Cloud の設定、全コマンド、視聴回数のカウント方法）は英語です：**[README.md](../README.md)**

## ライセンス

MIT · [LICENSE](../LICENSE)

## 作者

[Jindřich Fáborský](https://www.faborsky.com)、プラハ在住のマーケター・講師。マーケターが AI で自分のツールを作れるよう教えています。
