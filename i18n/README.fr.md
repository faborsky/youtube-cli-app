# YouTube CLI

[🇬🇧 English](../README.md) · [🇨🇿 Čeština](../README.cs.md) · [🇪🇸 Español](README.es.md) · [🇧🇷 Português](README.pt-BR.md) · [🇩🇪 Deutsch](README.de.md) · **🇫🇷 Français** · [🇨🇳 简体中文](README.zh-CN.md) · [🇯🇵 日本語](README.ja.md) · [🇸🇪 Svenska](README.sv.md) · [🇳🇴 Norsk](README.nb.md) · [🇩🇰 Dansk](README.da.md)

Outil en ligne de commande en Python pour gérer tes vidéos YouTube (YouTube Data API v3) et lire les performances de ta chaîne (YouTube Analytics API v2). Pour tous ceux qui publient régulièrement sur YouTube et n'ont pas envie de passer leur temps à cliquer dans YouTube Studio.

Publier une vidéo, c'est beaucoup de travail manuel répétitif : envoyer le fichier, remplir le titre et la description, régler la visibilité, ajouter la miniature, la ranger dans une playlist. Ce CLI automatise ces étapes pour que tu puisses les enchaîner dans des scripts ou laisser [Claude Code](https://docs.anthropic.com/en/docs/claude-code) ou un autre agent IA s'en charger.

Auteur: [Jindřich Fáborský](https://www.faborsky.com)

## Ce qu'il fait

- `upload` : envoie des vidéos avec toutes les métadonnées, la miniature, la playlist et la publication programmée. En `private` par défaut.
- `video-update` et `video-delete` : modifie uniquement les champs indiqués ; la suppression exige `--confirm`.
- `stats` et `analytics` : vues, durée de visionnage, rétention, sources de trafic, Shorts face aux vidéos longues.
- Affiche les vues selon la nouvelle définition (depuis le 24 août 2026) et aussi les `engagedViews` selon l'ancienne.
- `--json` sur toutes les commandes : seules les données vont sur stdout, idéal pour les scripts et les agents IA.

## Démarrage rapide

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

La documentation complète (configuration de Google Cloud, toutes les commandes, comptage des vues) est en anglais : **[README.md](../README.md)**.

## Licence

MIT · [LICENSE](../LICENSE)

## Auteur

[Jindřich Fáborský](https://www.faborsky.com), marketeur et formateur à Prague. J'apprends aux marketeurs à créer leurs propres outils avec l'IA.
