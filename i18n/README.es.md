# YouTube CLI

[🇬🇧 English](../README.md) · [🇨🇿 Čeština](../README.cs.md) · **🇪🇸 Español** · [🇧🇷 Português](README.pt-BR.md) · [🇩🇪 Deutsch](README.de.md) · [🇫🇷 Français](README.fr.md) · [🇨🇳 简体中文](README.zh-CN.md) · [🇯🇵 日本語](README.ja.md) · [🇸🇪 Svenska](README.sv.md) · [🇳🇴 Norsk](README.nb.md) · [🇩🇰 Dansk](README.da.md)

Herramienta de línea de comandos en Python para gestionar tus vídeos de YouTube (YouTube Data API v3) y leer el rendimiento del canal (YouTube Analytics API v2). Para quien publica en YouTube con regularidad y no quiere pasarse el día haciendo clic en YouTube Studio.

Subir un vídeo implica mucho trabajo manual repetitivo: subir el archivo, rellenar título y descripción, ajustar la privacidad, añadir la miniatura, meterlo en una lista. Este CLI automatiza esos pasos para que puedas encadenarlos en scripts o dejar que los maneje [Claude Code](https://docs.anthropic.com/en/docs/claude-code) u otro agente de IA.

Autor: [Jindřich Fáborský](https://www.faborsky.com)

## Qué hace

- `upload`: sube vídeos con todos los metadatos, miniatura, lista y publicación programada. Por defecto como `private`.
- `video-update` y `video-delete`: cambia solo los campos que indiques; borrar exige `--confirm`.
- `stats` y `analytics`: visualizaciones, tiempo de visualización, retención, fuentes de tráfico, Shorts frente a vídeos largos.
- Muestra las visualizaciones con la nueva definición (desde el 24 de agosto de 2026) y también las `engagedViews` con la antigua.
- `--json` en todos los comandos: en stdout solo van los datos, ideal para scripts y agentes de IA.

## Inicio rápido

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

La documentación completa (configuración de Google Cloud, todos los comandos, recuento de visualizaciones) está en inglés: **[README.md](../README.md)**.

## Licencia

MIT · [LICENSE](../LICENSE)

## Autor

[Jindřich Fáborský](https://www.faborsky.com), marketer y formador de Praga. Enseño a los marketers a crear sus propias herramientas con IA.
