# YouTube CLI

[🇬🇧 English](../README.md) · [🇨🇿 Čeština](../README.cs.md) · [🇪🇸 Español](README.es.md) · [🇧🇷 Português](README.pt-BR.md) · **🇩🇪 Deutsch** · [🇫🇷 Français](README.fr.md) · [🇨🇳 简体中文](README.zh-CN.md) · [🇯🇵 日本語](README.ja.md) · [🇸🇪 Svenska](README.sv.md) · [🇳🇴 Norsk](README.nb.md) · [🇩🇰 Dansk](README.da.md)

Python-Kommandozeilentool, mit dem du deine YouTube-Videos verwaltest (YouTube Data API v3) und die Performance deines Kanals ausliest (YouTube Analytics API v2). Für alle, die regelmäßig auf YouTube veröffentlichen und nicht ständig durch YouTube Studio klicken wollen.

Ein Video zu veröffentlichen ist viel wiederkehrende Handarbeit: Datei hochladen, Titel und Beschreibung ausfüllen, Sichtbarkeit einstellen, Thumbnail hinzufügen, in eine Playlist packen. Dieses CLI automatisiert diese Schritte, damit du sie in Skripten verketten oder [Claude Code](https://docs.anthropic.com/en/docs/claude-code) bzw. einen anderen KI-Agenten damit arbeiten lassen kannst.

Autor: [Jindřich Fáborský](https://www.faborsky.com)

## Was es kann

- `upload`: lädt Videos mit allen Metadaten, Thumbnail, Playlist und geplanter Veröffentlichung hoch. Standardmäßig als `private`.
- `video-update` und `video-delete`: ändert nur die Felder, die du angibst; Löschen verlangt `--confirm`.
- `stats` und `analytics`: Aufrufe, Wiedergabezeit, Zuschauerbindung, Traffic-Quellen, Shorts im Vergleich zu langen Videos.
- Zeigt Aufrufe nach der neuen Definition (seit 24. August 2026) und zusätzlich `engagedViews` nach der alten.
- `--json` bei allen Befehlen: auf stdout landen nur die Daten, ideal für Skripte und KI-Agenten.

## Schnellstart

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

Die vollständige Dokumentation (Google-Cloud-Einrichtung, alle Befehle, Zählung der Aufrufe) gibt es auf Englisch: **[README.md](../README.md)**.

## Lizenz

MIT · [LICENSE](../LICENSE)

## Autor

[Jindřich Fáborský](https://www.faborsky.com), Marketer und Dozent aus Prag. Ich bringe Marketern bei, mit KI eigene Tools zu bauen.
