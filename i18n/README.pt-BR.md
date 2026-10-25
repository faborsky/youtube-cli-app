# YouTube CLI

[🇬🇧 English](../README.md) · [🇨🇿 Čeština](../README.cs.md) · [🇪🇸 Español](README.es.md) · **🇧🇷 Português** · [🇩🇪 Deutsch](README.de.md) · [🇫🇷 Français](README.fr.md) · [🇨🇳 简体中文](README.zh-CN.md) · [🇯🇵 日本語](README.ja.md) · [🇸🇪 Svenska](README.sv.md) · [🇳🇴 Norsk](README.nb.md) · [🇩🇰 Dansk](README.da.md)

Ferramenta de linha de comando em Python para gerenciar seus vídeos do YouTube (YouTube Data API v3) e ler o desempenho do canal (YouTube Analytics API v2). Para quem publica no YouTube com frequência e não quer ficar clicando no YouTube Studio.

Publicar um vídeo dá muito trabalho manual repetitivo: enviar o arquivo, preencher título e descrição, definir a privacidade, adicionar a miniatura, colocar numa playlist. Este CLI automatiza essas etapas para você encadeá-las em scripts ou deixar que o [Claude Code](https://docs.anthropic.com/en/docs/claude-code) ou outro agente de IA cuide delas.

Autor: [Jindřich Fáborský](https://www.faborsky.com)

## O que ele faz

- `upload`: envia vídeos com todos os metadados, miniatura, playlist e publicação agendada. Por padrão como `private`.
- `video-update` e `video-delete`: altera só os campos que você informar; excluir exige `--confirm`.
- `stats` e `analytics`: visualizações, tempo de exibição, retenção, origens de tráfego, Shorts versus vídeos longos.
- Mostra as visualizações pela nova definição (desde 24 de agosto de 2026) e também as `engagedViews` pela antiga.
- `--json` em todos os comandos: no stdout só vão os dados, ideal para scripts e agentes de IA.

## Início rápido

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

A documentação completa (configuração do Google Cloud, todos os comandos, contagem de visualizações) está em inglês: **[README.md](../README.md)**.

## Licença

MIT · [LICENSE](../LICENSE)

## Autor

[Jindřich Fáborský](https://www.faborsky.com), profissional de marketing e educador de Praga. Ensino profissionais de marketing a criar suas próprias ferramentas com IA.
