# YouTube CLI

[🇬🇧 English](../README.md) · [🇨🇿 Čeština](../README.cs.md) · [🇪🇸 Español](README.es.md) · [🇧🇷 Português](README.pt-BR.md) · [🇩🇪 Deutsch](README.de.md) · [🇫🇷 Français](README.fr.md) · [🇨🇳 简体中文](README.zh-CN.md) · [🇯🇵 日本語](README.ja.md) · [🇸🇪 Svenska](README.sv.md) · **🇳🇴 Norsk** · [🇩🇰 Dansk](README.da.md)

Et kommandolinjeverktøy i Python for å administrere YouTube-videoene dine (YouTube Data API v3) og lese ut kanalens resultater (YouTube Analytics API v2). For deg som publiserer på YouTube jevnlig og ikke vil klikke rundt i YouTube Studio hele tiden.

Å publisere en video betyr mye gjentatt manuelt arbeid: laste opp filen, fylle inn tittel og beskrivelse, sette synlighet, legge til miniatyrbilde, legge den i en spilleliste. Dette CLI-et automatiserer stegene, så du kan kjede dem sammen i skript eller la [Claude Code](https://docs.anthropic.com/en/docs/claude-code) eller en annen AI-agent ta seg av dem.

Forfatter: [Jindřich Fáborský](https://www.faborsky.com)

## Hva det gjør

- `upload`: laster opp videoer med all metadata, miniatyrbilde, spilleliste og planlagt publisering. Som standard `private`.
- `video-update` og `video-delete`: endrer bare feltene du oppgir; sletting krever `--confirm`.
- `stats` og `analytics`: visninger, visningstid, seerlojalitet, trafikkilder, Shorts sammenlignet med lange videoer.
- Viser visninger etter den nye definisjonen (siden 24. august 2026) og i tillegg `engagedViews` etter den gamle.
- `--json` på alle kommandoer: bare data går til stdout, fint for skript og AI-agenter.

## Hurtigstart

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

Den fullstendige dokumentasjonen (oppsett av Google Cloud, alle kommandoer, hvordan visninger telles) er på engelsk: **[README.md](../README.md)**.

## Lisens

MIT · [LICENSE](../LICENSE)

## Forfatter

[Jindřich Fáborský](https://www.faborsky.com), markedsfører og underviser fra Praha. Jeg lærer markedsførere å bygge egne verktøy med AI.
