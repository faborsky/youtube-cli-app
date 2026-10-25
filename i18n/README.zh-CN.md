# YouTube CLI

[🇬🇧 English](../README.md) · [🇨🇿 Čeština](../README.cs.md) · [🇪🇸 Español](README.es.md) · [🇧🇷 Português](README.pt-BR.md) · [🇩🇪 Deutsch](README.de.md) · [🇫🇷 Français](README.fr.md) · **🇨🇳 简体中文** · [🇯🇵 日本語](README.ja.md) · [🇸🇪 Svenska](README.sv.md) · [🇳🇴 Norsk](README.nb.md) · [🇩🇰 Dansk](README.da.md)

一个 Python 命令行工具，用来管理你的 YouTube 视频（YouTube Data API v3）并读取频道数据（YouTube Analytics API v2）。适合经常在 YouTube 上发布内容、不想总在 YouTube Studio 里点来点去的人。

发布一个视频有很多重复的手工操作：上传文件、填写标题和描述、设置公开范围、添加缩略图、加入播放列表。这个 CLI 把这些步骤自动化，你可以在脚本里串起来，也可以交给 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 或其他 AI 代理来做。

作者：[Jindřich Fáborský](https://www.faborsky.com)

## 功能

- `upload`：上传视频，支持全部元数据、缩略图、播放列表和定时发布。默认设为 `private`。
- `video-update` 和 `video-delete`：只修改你指定的字段；删除必须加 `--confirm`。
- `stats` 和 `analytics`：观看次数、观看时长、留存率、流量来源、Shorts 与长视频对比。
- 同时显示新定义下的观看次数（自 2026 年 8 月 24 日起）和旧定义下的 `engagedViews`。
- 所有命令都支持 `--json`：stdout 只输出数据，方便脚本和 AI 代理使用。

## 快速开始

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

完整文档（Google Cloud 配置、全部命令、观看次数统计方式）为英文：**[README.md](../README.md)**。

## 许可证

MIT · [LICENSE](../LICENSE)

## 作者

[Jindřich Fáborský](https://www.faborsky.com)，来自布拉格的营销人和讲师，教营销人员用 AI 自己做工具。
