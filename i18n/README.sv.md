# YouTube CLI

[🇬🇧 English](../README.md) · [🇨🇿 Čeština](../README.cs.md) · [🇪🇸 Español](README.es.md) · [🇧🇷 Português](README.pt-BR.md) · [🇩🇪 Deutsch](README.de.md) · [🇫🇷 Français](README.fr.md) · [🇨🇳 简体中文](README.zh-CN.md) · [🇯🇵 日本語](README.ja.md) · **🇸🇪 Svenska** · [🇳🇴 Norsk](README.nb.md) · [🇩🇰 Dansk](README.da.md)

Ett kommandoradsverktyg i Python för att hantera dina YouTube-videor (YouTube Data API v3) och läsa ut kanalens resultat (YouTube Analytics API v2). För dig som publicerar på YouTube regelbundet och inte vill klicka runt i YouTube Studio hela tiden.

Att publicera en video innebär mycket upprepat handarbete: ladda upp filen, fylla i titel och beskrivning, ställa in synlighet, lägga till miniatyrbild, lägga den i en spellista. Det här CLI:t automatiserar stegen så att du kan kedja ihop dem i skript eller låta [Claude Code](https://docs.anthropic.com/en/docs/claude-code) eller en annan AI-agent sköta dem.

Författare: [Jindřich Fáborský](https://www.faborsky.com)

## Vad det gör

- `upload`: laddar upp videor med all metadata, miniatyrbild, spellista och schemalagd publicering. Som standard `private`.
- `video-update` och `video-delete`: ändrar bara de fält du anger; radering kräver `--confirm`.
- `stats` och `analytics`: visningar, visningstid, tittarlojalitet, trafikkällor, Shorts jämfört med långa videor.
- Visar visningar enligt den nya definitionen (sedan 24 augusti 2026) och även `engagedViews` enligt den gamla.
- `--json` på alla kommandon: bara data går till stdout, bra för skript och AI-agenter.

## Snabbstart

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

Den fullständiga dokumentationen (Google Cloud-inställning, alla kommandon, hur visningar räknas) finns på engelska: **[README.md](../README.md)**.

## Licens

MIT · [LICENSE](../LICENSE)

## Författare

[Jindřich Fáborský](https://www.faborsky.com), marknadsförare och utbildare från Prag. Jag lär marknadsförare att bygga egna verktyg med AI.
