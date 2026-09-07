# YouTube CLI

**v2.0.0** · [Changelog](CHANGELOG.md) · [Poznámky k API](docs/api-notes.md)

Python nástroj do příkazové řádky na správu videí na [YouTube](https://www.youtube.com/) přes YouTube Data API v3 a na čtení výkonu kanálu přes YouTube Analytics API v2. Nahrávání videí, správa metadat, thumbnaily, playlisty, statistiky, watch time i retence, všechno z terminálu. Postavený tak, aby ho mohl řídit [Claude Code](https://docs.anthropic.com/en/docs/claude-code) nebo jiný AI agent.

> [!TIP]
> **Appka je zdarma a je tvoje.** Naklonuj si ji, používej ji, přestav si ji po svém.
>
> Nevíš, jak ji rozjet? Nebo chceš AI v marketingu používat systematicky: řídit z jednoho místa všechny kanály, automatizovat rutinu, postavit si vlastní znalostní bázi a vibe codovat si nástroje na míru své firmě? To učím v kurzu **[AI First](https://aifirst.cz)**. Tahle appka je v něm vysvětlená i s tím, jak si postavit vlastní.

> **📊 Od 24. 8. 2026 se zhlédnutí počítají jinak.** YouTube počítá zhlédnutí od okamžiku, kdy se spustí přehrávání, bez minimální doby sledování, a to u **všech** formátů (u Shorts to tak funguje od 31. 3. 2025). Původní definice zmizela z veřejného Data API a přežívá jako **engaged views** v Analytics API. Tohle CLI ukazuje obojí, viz [Počítání zhlédnutí](#počítání-zhlédnutí-24-8-2026).

## Proč to vzniklo

Publikování videa na YouTube je spousta opakované ruční práce: nahrát soubor přes webové rozhraní, vyplnit titulek a popis, nastavit soukromí, přidat thumbnail, zařadit do playlistu. Tohle CLI ty operace automatizuje, takže se dají skriptovat nebo řetězit s dalšími nástroji.

Takhle třeba vypadá publikace podcastu řízená přes Claude Code:

1. **Přepis** audia přes [whisper-cz-en](https://github.com/faborsky/whisper-cz-en)
2. **Vygenerování metadat** (titulek, popis, kapitoly) z přepisu
3. **Nahrání audia** na Podbean přes [podbean-app](https://github.com/faborsky/podbean-app)
4. **Nahrání videa** na YouTube tímhle CLI
5. **Nastavení thumbnailu** a zařazení do playlistu, automaticky

Všechno v jedné konverzaci. Ty tvoříš obsah, AI dělá administrativu.

## Co budeš potřebovat

- **Python 3.9+**
- **Kanál na YouTube** propojený s účtem Google
- **Projekt v Google Cloud** s povoleným YouTube Data API v3 a OAuth 2.0 credentials
- Pro příkaz `analytics`: **YouTube Analytics API** povolené ve stejném projektu

## Nastavení Google Cloud

Než CLI použiješ, musíš si založit projekt v Google Cloud a vytvořit OAuth credentials. Je to jednorázová věc.

### 1. Založ projekt v Google Cloud

1. Jdi do [Google Cloud Console](https://console.cloud.google.com/)
2. Klikni na rozbalovátko projektů (horní lišta) → **New Project**
3. Pojmenuj ho (třeba `youtube-cli`) → **Create**
4. Vyber nový projekt v rozbalovátku

### 2. Povol API

1. Jdi do **APIs & Services → Library** ([přímý odkaz](https://console.cloud.google.com/apis/library))
2. Najdi **YouTube Data API v3** → klikni na něj → **Enable**
3. Najdi **YouTube Analytics API** → klikni na něj → **Enable** (potřebuješ ho pro příkaz `analytics` a pro `stats --engaged`; přeskoč, pokud budeš jenom publikovat videa)

### 3. Nastav OAuth consent screen

1. Jdi do **APIs & Services → OAuth consent screen**
2. Vyber typ uživatele **External** → **Create**
3. Vyplň povinná pole:
   - **App name:** jakýkoliv název (třeba `Video Manager CLI`)
   - **User support email:** tvůj e-mail
   - **Developer contact:** tvůj e-mail
4. Klikni na **Save and Continue**
5. Na stránce **Scopes** → **Add or Remove Scopes** → přidej `https://www.googleapis.com/auth/youtube` a `https://www.googleapis.com/auth/yt-analytics.readonly` → **Save and Continue**
6. Na stránce **Test users** → **Add Users** → přidej svou gmailovou adresu → **Save and Continue**

> **Pozor na expiraci tokenu:** V režimu „Testing“ vyprší OAuth refresh tokeny po **7 dnech**. Dlouhodobě platné tokeny dostaneš, když na stránce OAuth consent screen klikneš na **Publish App**. U appek pro vlastní potřebu, kde je jenom tvůj vlastní účet, Google obvykle žádné další ověřování nechce.

### 4. Vytvoř OAuth credentials

1. Jdi do **APIs & Services → Credentials** ([přímý odkaz](https://console.cloud.google.com/apis/credentials))
2. Klikni na **Create Credentials → OAuth client ID**
3. Typ aplikace: **Desktop app**
4. Název: jakýkoliv (třeba `YouTube CLI`)
5. Klikni na **Create**
6. Zkopíruj si **Client ID** a **Client Secret**

Teď máš všechno, co potřebuješ. Client ID vypadá jako `123456789-abc.apps.googleusercontent.com`, Client Secret je krátký alfanumerický řetězec.

## Instalace

```bash
git clone https://github.com/faborsky/youtube-cli-app.git
cd youtube-cli-app

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Uprav .env a vlož svoje Google Cloud OAuth credentials
```

## Konfigurace

Do `.env` vlož OAuth credentials z nastavení Google Cloud:

```
YOUTUBE_CLIENT_ID=your-client-id-here
YOUTUBE_CLIENT_SECRET=your-client-secret-here
```

Pak se jednorázově přihlas (otevře se ti prohlížeč):

```bash
python youtube_cli.py auth
```

Uloží se dlouhodobě platný refresh token do `~/.youtube-cli-token.json`. Další příkazy si ho vezmou samy, prohlížeč už není potřeba.

## Používání

Vždycky si nejdřív aktivuj virtuální prostředí:

```bash
source venv/bin/activate
```

### Výpis videí

```bash
python youtube_cli.py videos
python youtube_cli.py videos --limit 10 --json
```

### Detail videa

```bash
python youtube_cli.py video-get --video-id VIDEO_ID
python youtube_cli.py video-get --video-id VIDEO_ID --json
```

### Nahrání videa

Videa se pro jistotu nahrávají jako **private** (soukromá).

```bash
# Základní nahrání (private)
python youtube_cli.py upload \
  --file /path/to/video.mp4 \
  --title "My Video Title"

# Nahrání se všemi metadaty
python youtube_cli.py upload \
  --file /path/to/video.mp4 \
  --title "My Video Title" \
  --description "Video description with details" \
  --tags "tag1,tag2,tag3" \
  --category 22 \
  --privacy private \
  --thumbnail /path/to/thumbnail.jpg \
  --playlist PLAYLIST_ID \
  --language en \
  --json

# Naplánované zveřejnění
python youtube_cli.py upload \
  --file /path/to/video.mp4 \
  --title "Scheduled Video" \
  --publish-at "2026-04-10T15:00:00Z"
```

Nahrávání běží resumable přenosem po blocích zhruba 12,5&nbsp;MB a při chybách serveru se automaticky opakuje s exponenciálním backoffem.

### Úprava metadat videa

Změní se jenom pole, která zadáš, zbytek zůstane, jak byl:

```bash
python youtube_cli.py video-update --video-id VIDEO_ID --title "New Title"
python youtube_cli.py video-update --video-id VIDEO_ID --privacy public
python youtube_cli.py video-update --video-id VIDEO_ID --thumbnail /path/to/new-thumb.jpg
python youtube_cli.py video-update --video-id VIDEO_ID \
  --title "Updated" \
  --description "New description" \
  --tags "new,tags" \
  --json
```

### Smazání videa

Kvůli bezpečnosti vyžaduje flag `--confirm`:

```bash
python youtube_cli.py video-delete --video-id VIDEO_ID --confirm
```

### Statistiky kanálu a videí

```bash
# Přehled kanálu
python youtube_cli.py stats

# Statistiky konkrétního videa
python youtube_cli.py stats --video-id VIDEO_ID
python youtube_cli.py stats --video-id VIDEO_ID --json

# Přidá engaged views za celou dobu (definice zhlédnutí platná do 24. 8. 2026)
python youtube_cli.py stats --engaged
python youtube_cli.py stats --video-id VIDEO_ID --engaged
```

### Analytika

Watch time, retence a zdroje návštěvnosti přes YouTube Analytics API, jenom pro tvůj vlastní kanál.
Vyžaduje povolené YouTube Analytics API a scope `yt-analytics.readonly` (pokud jsi přístup udělil
dřív, než jsi API povolil, spusť `auth` znovu).

```bash
# Souhrn za kanál za posledních 28 dní
python youtube_cli.py analytics --days 28

# Denní vývoj
python youtube_cli.py analytics --days 28 --dimensions day --sort day

# Nejsledovanější videa
python youtube_cli.py analytics --dimensions video --sort -views --max-results 10

# Odkud zhlédnutí chodí
python youtube_cli.py analytics --dimensions insightTrafficSourceType --sort -views

# Shorts vs. dlouhá videa
python youtube_cli.py analytics --days 90 --dimensions creatorContentType

# Jedno video, konkrétní rozsah dat, surové JSON z API
python youtube_cli.py analytics --video-id VIDEO_ID \
  --start-date 2026-07-01 --end-date 2026-07-31 --json
```

Výchozí metriky: `views`, `engagedViews`, `estimatedMinutesWatched`, `averageViewDuration`,
`averageViewPercentage` (retence), `subscribersGained`, `subscribersLost`, `likes`, `comments`,
`shares`. Změníš je přes `--metrics` ([celý seznam](https://developers.google.com/youtube/analytics/metrics)).

Analytics API obsluhuje jenom [pevně dané kombinace dimenzí a metrik](https://developers.google.com/youtube/analytics/v2/available_reports), takže CLI doplní, co nezadáš: u dimenzí, které umí jenom metriky zhlédnutí (zdroj návštěvnosti, zařízení, stav odběru…), zúží výchozí sadu metrik, u top-N dimenzí (`video`, `playlist` a dalších) přidá povinné řazení a limit výsledků a u `--dimensions month` zarovná data na celé měsíce. Každou úpravu vypíše na stderr, takže výstup s `--json` zůstane čistý. A cokoliv zadáš sám, má přednost.

### Počítání zhlédnutí (24. 8. 2026)

**24. 8. 2026** YouTube [sjednotil počítání zhlédnutí](https://support.google.com/youtube/thread/433409976)
napříč všemi formáty: zhlédnutí se počítá hned, jak se spustí přehrávání, bez minimální doby sledování.
U Shorts to tak funguje od 31. 3. 2025.

| Metrika | Kde | Co počítá |
|---------|-----|-----------|
| `viewCount` | Data API (`stats`, `videos`, `video-get`) | Nová definice, každé spuštění přehrávání |
| `views` | Analytics API (`analytics`) | Nová definice |
| `engagedViews` | Analytics API (`analytics`, `stats --engaged`) | **Stará** definice, zhlédnutí po prvních sekundách |

Staré číslo už ve veřejném Data API nikde není a `engagedViews` si přečte jenom vlastník kanálu.
**Skok ve zhlédnutích kolem 24. 8. 2026 není růst, ale změna definice.** Pro srovnání přes tuhle
hranici používej `engagedViews`. Víc detailů v [docs/api-notes.md](docs/api-notes.md).

### Výpis playlistů

```bash
python youtube_cli.py playlists
python youtube_cli.py playlists --json
```

### Výstup v JSON

Všechny příkazy umí `--json`, tedy strojově čitelný výstup. Hodí se na skriptování a na řízení AI agentem. V režimu JSON jde na stdout jenom samotná data, poznámky a varování pro člověka odcházejí na stderr:

```bash
python youtube_cli.py videos --json
python youtube_cli.py analytics --days 28 --json    # doslovná resultTable z API
```

## Přehled příkazů

| Příkaz | Co dělá | Hlavní flagy |
|--------|---------|--------------|
| `auth` | Jednorázové nastavení OAuth (otevře prohlížeč) | žádné |
| `videos` | Výpis posledních videí | `--limit`, `--json` |
| `video-get` | Detail videa | `--video-id` (povinný), `--json` |
| `upload` | Nahrání videa s metadaty | `--file`, `--title` (povinné), `--description`, `--tags`, `--category`, `--privacy`, `--thumbnail`, `--playlist`, `--language`, `--publish-at`, `--json` |
| `video-update` | Úprava existujícího videa | `--video-id` (povinný), `--title`, `--description`, `--tags`, `--category`, `--privacy`, `--thumbnail`, `--json` |
| `video-delete` | Smazání videa | `--video-id` (povinný), `--confirm` (povinný) |
| `stats` | Statistiky zhlédnutí | `--video-id` (volitelný), `--engaged`, `--json` |
| `analytics` | Watch time, retence, zdroje návštěvnosti (Analytics API) | `--days`, `--start-date`, `--end-date`, `--metrics`, `--dimensions`, `--sort`, `--video-id`, `--max-results`, `--json` |
| `playlists` | Výpis playlistů | `--json` |

Nainstalovanou verzi vypíše `python youtube_cli.py --version`.

## Flagy pro nahrávání

| Flag | Povinný | Výchozí | Co dělá |
|------|---------|---------|---------|
| `--file` | ano | nemá | Cesta k souboru s videem (MP4, MOV a další) |
| `--title` | ano | nemá | Titulek videa |
| `--description` | ne | prázdný | Popis videa |
| `--tags` | ne | žádné | Tagy oddělené čárkou |
| `--category` | ne | `22` | [ID kategorie](https://developers.google.com/youtube/v3/docs/videoCategories/list) na YouTube (22 = People & Blogs) |
| `--privacy` | ne | `private` | `private`, `unlisted`, nebo `public` |
| `--thumbnail` | ne | žádný | Cesta k obrázku thumbnailu (JPG/PNG) |
| `--playlist` | ne | žádné | ID playlistu, do kterého se video přidá |
| `--language` | ne | žádný | Kód jazyka (třeba `en`, `cs`, `de`) |
| `--publish-at` | ne | žádné | Naplánované zveřejnění (ISO 8601, vynutí privacy `private`) |

## Bezpečnost

- **Ve výchozím stavu private.** Nahraná videa jsou `private`. Zveřejnit je musíš sám, buď přes `--privacy public`, nebo později přes `video-update`.
- **Mazání vyžaduje potvrzení.** Flag `--confirm` je u `video-delete` povinný.
- **Credentials zůstávají u tebe.** `.env` je v gitignore, OAuth token leží v tvém domovském adresáři (`~/.youtube-cli-token.json`).
- **Žádné klíče v kódu.** Všechny přístupy jdou z proměnných prostředí.

## Když něco nefunguje

**Chyba „Not authenticated“:**
Spusť `python youtube_cli.py auth` a dokonči OAuth přihlášení.

**Chyba „Token has been expired or revoked“:**
Vypršel ti refresh token (v režimu „Testing“ se to stane po 7 dnech). Spusť znovu `auth`. Abys tomu předešel, publikuj appku v Google Cloud Console.

**Chyba „YouTube API quota exceeded“:**
Výchozí kvóta je 10&nbsp;000 jednotek na den, jedno nahrání videa stojí zhruba 1&nbsp;600 jednotek. Spotřebu zkontroluješ v [Google Cloud Quotas](https://console.cloud.google.com/iam-admin/quotas).

**Varování „Google hasn't verified this app“:**
U appek pro vlastní potřebu je to normální. Klikni na **Continue** a pokračuj.

**Nahrání thumbnailu selže:**
Vlastní thumbnaily vyžadují [ověřený účet na YouTube](https://support.google.com/youtube/answer/171664) (ověření telefonním číslem).

**`analytics` hlásí chybu se scopem nebo s oprávněním:**
Povol v projektu Google Cloud **YouTube Analytics API** a pak jednou spusť `python youtube_cli.py auth`. Existující token nový scope sám od sebe nezíská. Analytika funguje jenom pro kanály, které vlastníš.

**Zhlédnutí najednou vyskočila:**
Nemusí to být růst. Od 24. 8. 2026 se zhlédnutí počítá od spuštění přehrávání, bez minimální doby sledování. Abys porovnával stejné se stejným, koukej na `engagedViews` (příkaz `analytics` nebo `stats --engaged`).

## Struktura projektu

```
youtube_cli.py        # Hlavní CLI (jeden soubor)
.env.example          # Šablona pro OAuth credentials
.env                  # Tvoje credentials (v gitignore)
requirements.txt      # Python závislosti
CLAUDE.md             # Instrukce pro Claude Code
CHANGELOG.md          # Historie verzí (Keep a Changelog, SemVer)
docs/api-notes.md     # Jak se YouTube API reálně chová
```

## Řetěz automatizace

Tohle CLI je stavěné jako součást větší obsahové linky poháněné AI:

| Krok | Nástroj | Co dělá |
|------|---------|---------|
| Přepis | [whisper-cz-en](https://github.com/faborsky/whisper-cz-en) | Lokální přepis přes Whisper Large V3 |
| Poznámky k epizodě | Claude Code | Vygeneruje titulky, popisy, kapitoly |
| Cover | [nanobanana-agent](https://github.com/faborsky/nanobonana-agent-public) | Vygeneruje grafiku pomocí AI |
| Publikace audia | [podbean-app](https://github.com/faborsky/podbean-app) | Nahraje audio podcasty |
| Publikace videa | **youtube-cli-app** (tenhle repozitář) | Nahraje videa na YouTube |

## O projektu

Postavil [Jindřich Fáborský](https://github.com/faborsky) jako součást své sady nástrojů na automatizaci obsahu. V produkci se s ním spravuje český podcast na YouTube.

Nástroj je zároveň součástí kurikula mezinárodního kurzu **[Vibe Coding for Marketers](https://vibecodingformarketers.com)**, kde se marketéři učí stavět si nástroje s AI.

---

## Licence

MIT
