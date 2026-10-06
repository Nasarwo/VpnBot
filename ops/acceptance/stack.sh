#!/usr/bin/env bash
# Изолированный стенд приёмки «Обход белых списков»: PostgreSQL 16, две реальные
# панели 3x-ui (обычная и whitelist), файловый сервер для трафика и тестовый
# SubHub. Всё — в отдельной Docker-сети, порты опубликованы только на 127.0.0.1.
# Production-панели, production-SubHub и Telegram не используются.
#
# SubHub запускается двумя экземплярами одного образа над теми же панелями:
#   ${PREFIX}-subhub      — его адрес получает бот (быстрый триггер POST /admin/sync);
#                           резервный опрос раз в час, поэтому за время сценария
#                           изменения в нём появляются только по триггеру;
#   ${PREFIX}-subhub-poll — бот о нём не знает; изменения он видит только своим
#                           резервным опросом (WLACC_SUBHUB_POLL_SECONDS, 30 с — минимум SubHub).
# Оба пишут журнал запросов (INFO): каждый POST /admin/sync виден с кодом ответа.
#
#   ops/acceptance/stack.sh up   <state-dir> <subhub-src-dir>
#   ops/acceptance/stack.sh down <state-dir>
#
# <state-dir> получает panel.env (тестовые учётные данные, 0600), конфигурацию
# SubHub и файл трафика. Повторный `up` переиспользует запущенные контейнеры.
set -euo pipefail

CMD=${1:?up|down}
STATE=${2:?state dir}
PREFIX=${WLACC_PREFIX:-wlacc}
NET=${PREFIX}-net
XUI_IMAGE=${WLACC_XUI_IMAGE:-ghcr.io/mhsanaei/3x-ui:v3.9.0}
PG_PORT=${WLACC_PG_PORT:-55439}
WL_PORT=${WLACC_WL_PORT:-52053}
STD_PORT=${WLACC_STD_PORT:-52054}
SUB_PORT=${WLACC_SUBHUB_PORT:-58080}
SUB_POLL_PORT=${WLACC_SUBHUB_POLL_PORT:-58081}
POLL_SECONDS=${WLACC_SUBHUB_POLL_SECONDS:-30}

if [ "$CMD" = down ]; then
  docker rm -f ${PREFIX}-pg ${PREFIX}-xui-wl ${PREFIX}-xui-std ${PREFIX}-files \
    ${PREFIX}-subhub ${PREFIX}-subhub-poll >/dev/null 2>&1 || true
  docker network rm "$NET" >/dev/null 2>&1 || true
  echo "стенд удалён (образы и $STATE сохранены)"
  exit 0
fi

SUBHUB_SRC=${3:?subhub source dir}
mkdir -p "$STATE/files"
chmod 700 "$STATE"
running() { [ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null)" = true ]; }

if [ ! -f "$STATE/panel.env" ]; then
  gen() { python3 -c 'import secrets; print(secrets.token_urlsafe(18))'; }
  umask 077
  cat >"$STATE/panel.env" <<EOF
XUI_USER=accadmin
XUI_PASS=$(gen)
XUI_PATH=/accpanel/
SUBHUB_ADMIN_TOKEN=$(gen)
PG_URL=postgresql+asyncpg://wlacc:wlacc@127.0.0.1:${PG_PORT}
WL_PANEL=http://127.0.0.1:${WL_PORT}/accpanel
STD_PANEL=http://127.0.0.1:${STD_PORT}/accpanel
SUBHUB_URL=http://127.0.0.1:${SUB_PORT}
XUI_IMAGE=${XUI_IMAGE}
NET=${NET}
EOF
fi
if ! grep -q '^SUBHUB_POLL_URL=' "$STATE/panel.env"; then
  printf 'SUBHUB_POLL_URL=http://127.0.0.1:%s\nSUBHUB_POLL_SECONDS=%s\n' \
    "$SUB_POLL_PORT" "$POLL_SECONDS" >>"$STATE/panel.env"
fi
# shellcheck disable=SC1091
. "$STATE/panel.env"

docker network inspect "$NET" >/dev/null 2>&1 || docker network create "$NET" >/dev/null

if ! running ${PREFIX}-pg; then
  docker rm -f ${PREFIX}-pg >/dev/null 2>&1 || true
  docker run -d --name ${PREFIX}-pg --network "$NET" -e POSTGRES_USER=wlacc \
    -e POSTGRES_PASSWORD=wlacc -e POSTGRES_DB=wlacc_test \
    -p 127.0.0.1:${PG_PORT}:5432 postgres:16-alpine >/dev/null
  for _ in $(seq 1 30); do
    docker exec ${PREFIX}-pg pg_isready -U wlacc -d wlacc_test >/dev/null 2>&1 && break
    sleep 1
  done
  docker exec ${PREFIX}-pg pg_isready -U wlacc -d wlacc_test >/dev/null
fi

start_panel() {  # name alias host-port
  if running "$1"; then return; fi
  docker rm -f "$1" >/dev/null 2>&1 || true
  docker run -d --name "$1" --network "$NET" --network-alias "$2" \
    -p 127.0.0.1:"$3":2053 "$XUI_IMAGE" >/dev/null
  sleep 4
  docker exec "$1" /app/x-ui setting -username "$XUI_USER" -password "$XUI_PASS" \
    -webBasePath "$XUI_PATH" >/dev/null
  docker restart "$1" >/dev/null
}
start_panel ${PREFIX}-xui-wl wl.acc.test "$WL_PORT"
start_panel ${PREFIX}-xui-std std.acc.test "$STD_PORT"

if [ ! -f "$STATE/files/blob8m" ]; then
  dd if=/dev/urandom of="$STATE/files/blob8m" bs=1048576 count=8 2>/dev/null
fi
chmod 755 "$STATE/files"
chmod 644 "$STATE/files/blob8m"
# Файловый сервер: HTTP-источник трафика и локальная TLS 1.3 цель REALITY
# (inbound'ы стенда не обращаются к сайтам в интернете).
if [ ! -f "$STATE/tls/cert.pem" ]; then
  mkdir -p "$STATE/tls"
  openssl req -x509 -nodes -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 \
    -keyout "$STATE/tls/key.pem" -out "$STATE/tls/cert.pem" -days 30 \
    -subj /CN=files.acc.test -addext subjectAltName=DNS:files.acc.test >/dev/null 2>&1
  chmod 644 "$STATE/tls/key.pem"
fi
cat >"$STATE/nginx.conf" <<'EOF'
server { listen 80; root /usr/share/nginx/html; }
server {
  listen 443 ssl; http2 on; server_name files.acc.test;
  ssl_certificate /etc/nginx/tls/cert.pem; ssl_certificate_key /etc/nginx/tls/key.pem;
  ssl_protocols TLSv1.3; root /usr/share/nginx/html;
}
EOF
if ! running ${PREFIX}-files; then
  docker rm -f ${PREFIX}-files >/dev/null 2>&1 || true
  # Copy fixtures: Docker Desktop need not share the host state directory.
  docker create --name ${PREFIX}-files --network "$NET" --network-alias files.acc.test \
    nginx:alpine >/dev/null
  docker cp "$STATE/files/." ${PREFIX}-files:/usr/share/nginx/html/
  docker cp "$STATE/tls" ${PREFIX}-files:/etc/nginx/tls
  docker cp "$STATE/nginx.conf" ${PREFIX}-files:/etc/nginx/conf.d/default.conf
  docker start ${PREFIX}-files >/dev/null
fi

subhub_config() {  # refresh-seconds base-url
  local path=${XUI_PATH%/}
  cat <<EOF
servers:
  - id: std
    name: "Обычный"
    panel_url: "http://std.acc.test:2053${path}"
    username: "\${PANEL_USER}"
    password: "\${PANEL_PASS}"
    public_host: "std.acc.test"
    node_emoji: "🟢"
    enabled: true
    verify_tls: false
  - id: wl
    name: "Обход белых списков"
    panel_url: "http://wl.acc.test:2053${path}"
    username: "\${PANEL_USER}"
    password: "\${PANEL_PASS}"
    public_host: "wl.acc.test"
    node_emoji: "⚪"
    enabled: true
    verify_tls: false
subscription:
  base_url: "$2"
  output_format: "base64"
  refresh_interval_seconds: $1
  token_strategy: "by_email"
  default_client_match_key: "email"
  profile_title_template: "ACC - {{DAYS_LEFT}}d"
  auto_profiles: {enabled: false}
  auto_selection: {enabled: false}
admin: {token: "\${ADMIN_TOKEN}", docs_enabled: false}
client_identity: {primary_key: "email", fallback_keys: ["subId", "id", "auth"]}
api: {login_path: "/login", inbounds_path: "/panel/api/inbounds/list", timeout_seconds: 10, retries: 1}
database: {url: "sqlite+aiosqlite:///./data/subhub.db"}
logging: {level: "INFO"}
rate_limit: {subscription_per_minute: 600, admin_per_minute: 600, max_entries: 10000, trusted_proxy: false}
reality_overrides: {}
EOF
}

start_subhub() {  # name host-port config-file refresh-seconds
  if running "$1"; then return; fi
  subhub_config "$4" "http://127.0.0.1:$2" >"$STATE/$3"
  chmod 644 "$STATE/$3" # credentials are environment references, not YAML values
  (umask 077; printf 'PANEL_USER=%s\nPANEL_PASS=%s\nADMIN_TOKEN=%s\n' \
    "$XUI_USER" "$XUI_PASS" "$SUBHUB_ADMIN_TOKEN" >"$STATE/subhub.env")
  docker rm -f "$1" >/dev/null 2>&1 || true
  docker create --name "$1" --network "$NET" -p 127.0.0.1:"$2":8080 \
    --env-file "$STATE/subhub.env" -e SUBHUB_CONFIG=/app/config.yaml \
    ${PREFIX}-subhub:src >/dev/null
  docker cp "$STATE/$3" "$1":/app/config.yaml
  docker start "$1" >/dev/null
}

if ! running ${PREFIX}-subhub || ! running ${PREFIX}-subhub-poll; then
  # Штатная сборка из исходников SubHub: greenlet приходит через SQLAlchemy[asyncio]
  # в requirements.txt (дефект D-2 исправлен 2026-10-05); производных образов нет.
  docker build -q -t ${PREFIX}-subhub:src "$SUBHUB_SRC" >/dev/null
fi
start_subhub ${PREFIX}-subhub "$SUB_PORT" subhub.yaml 3600
start_subhub ${PREFIX}-subhub-poll "$SUB_POLL_PORT" subhub-poll.yaml "$POLL_SECONDS"
for url in "$SUBHUB_URL" "http://127.0.0.1:${SUB_POLL_PORT}"; do
  for _ in $(seq 1 30); do
    curl -sf "$url/health" >/dev/null 2>&1 && break
    sleep 1
  done
  curl -sf "$url/health" >/dev/null
done
echo "стенд готов: PG 127.0.0.1:${PG_PORT}, whitelist ${WL_PANEL}, обычная ${STD_PANEL}," \
  "SubHub ${SUBHUB_URL} (триггер бота), http://127.0.0.1:${SUB_POLL_PORT} (только опрос, ${POLL_SECONDS} с)"
