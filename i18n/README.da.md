# YouTube CLI

[🇬🇧 English](../README.md) · [🇨🇿 Čeština](../README.cs.md) · [🇪🇸 Español](README.es.md) · [🇧🇷 Português](README.pt-BR.md) · [🇩🇪 Deutsch](README.de.md) · [🇫🇷 Français](README.fr.md) · [🇨🇳 简体中文](README.zh-CN.md) · [🇯🇵 日本語](README.ja.md) · [🇸🇪 Svenska](README.sv.md) · [🇳🇴 Norsk](README.nb.md) · **🇩🇰 Dansk**

Et kommandolinjeværktøj i Python til at administrere dine YouTube-videoer (YouTube Data API v3) og hente kanalens resultater (YouTube Analytics API v2). Til dig, der udgiver på YouTube jævnligt og ikke vil klikke rundt i YouTube Studio hele tiden.

At udgive en video kræver meget gentaget manuelt arbejde: uploade filen, udfylde titel og beskrivelse, vælge synlighed, tilføje thumbnail, lægge den i en playliste. Dette CLI automatiserer trinene, så du kan kæde dem sammen i scripts eller lade [Claude Code](https://docs.anthropic.com/en/docs/claude-code) eller en anden AI-agent klare dem.

Forfatter: [Jindřich Fáborský](https://www.faborsky.com)

## Hvad det gør

- `upload`: uploader videoer med alle metadata, thumbnail, playliste og planlagt udgivelse. Som standard `private`.
- `video-update` og `video-delete`: ændrer kun de felter, du angiver; sletning kræver `--confirm`.
- `stats` og `analytics`: visninger, visningstid, fastholdelse, trafikkilder, Shorts sammenlignet med lange videoer.
- Viser visninger efter den nye definition (siden 24. august 2026) og desuden `engagedViews` efter den gamle.
- `--json` på alle kommandoer: kun data går til stdout, godt til scripts og AI-agenter.

## Hurtig start

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

Den fulde dokumentation (opsætning af Google Cloud, alle kommandoer, hvordan visninger tælles) er på engelsk: **[README.md](../README.md)**.

## Licens

MIT · [LICENSE](../LICENSE)

## Forfatter

[Jindřich Fáborský](https://www.faborsky.com), marketingmand og underviser fra Prag. Jeg lærer marketingfolk at bygge deres egne værktøjer med AI.
