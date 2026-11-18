#!/usr/bin/env bash
# Modelo de aviso pelo Telegram para o zelador: avisar-telegram.sh "mensagem"
# Use: aviso.comando = ["bash", "/caminho/avisar-telegram.sh"]
# Lê ZELADOR_TELEGRAM_TOKEN e ZELADOR_TELEGRAM_CHAT de ~/.config/zelador/telegram.env (fora de qualquer repo).
# Nunca imprime o token.
set -uo pipefail
ENV="${ZELADOR_TELEGRAM_ENV:-$HOME/.config/zelador/telegram.env}"
[ -f "$ENV" ] && . "$ENV"
: "${ZELADOR_TELEGRAM_TOKEN:?defina ZELADOR_TELEGRAM_TOKEN em $ENV}"
: "${ZELADOR_TELEGRAM_CHAT:?defina ZELADOR_TELEGRAM_CHAT em $ENV}"
CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 \
  "https://api.telegram.org/bot${ZELADOR_TELEGRAM_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${ZELADOR_TELEGRAM_CHAT}" --data-urlencode "text=${1:?mensagem}" \
  --data-urlencode "disable_web_page_preview=true")"
echo "telegram: HTTP ${CODE}"
