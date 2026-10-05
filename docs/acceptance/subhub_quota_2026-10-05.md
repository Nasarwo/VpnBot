# Протокол: квота трафика 3x-ui → SubHub на реальной панели — 5 октября 2026

Сценарий `ops/acceptance/subhub_quota_e2e.py` на свежем стенде `ops/acceptance/stack.sh`
(префикс контейнеров `sq5`, отдельная Docker-сеть, порты только на `127.0.0.1`):
3x-ui 3.9.0 (обычная и whitelist-панели), файловый сервер, SubHub из исходников
`SingleLinkVpn/subhub`. PostgreSQL стенда сценарием не используется. Production, оплаты
и сообщения пользователям не использовались. Токены подписок в вывод не попадают.

Маскирующее условие снято штатно: `POST /panel/api/server/stopXrayService` на
whitelist-панели после реального трафика. При остановленном Xray задача трафика 3x-ui не
выполняется и `enable=false` исчерпанному клиенту не выставляет; квота, срок и `enable`
меняются через `clients/update`. Контрольный пример создан импортом inbound
(`inbounds/import` сохраняет `clientStats.up/down`).

## Прогон до исправления (SubHub `d9a2c80` + незакоммиченные правки, не относящиеся к задаче)

Файлы в контейнере SubHub (sha256, первые 12 знаков): `link_builder.py` `707314c4652b`,
`normalizer.py` `47152ffb43b9`, `models.py` `a9959972e441` — совпадают с `HEAD`.
**28 OK, 4 FAIL.**

| Состояние панели (Xray остановлен) | `settings.enable` | `totalGB` | `clientStats` up+down | Ожидание | SubHub до исправления |
|---|---|---|---|---|---|
| граница: totalGB = U | true | 8388952 | 8388952 | скрыт | **в подписке — FAIL** |
| ниже квоты: U + 1 | true | 8388953 | 8388952 | в подписке | в подписке — OK |
| выше квоты: U − 1 | true | 8388951 | 8388952 | скрыт | **в подписке — FAIL** |
| безлимит | true | 0 | 8388952 | в подписке | в подписке — OK |
| `enable=false`, остаток 1 ГиБ | false | 1082130776 | 8388952 | скрыт | скрыт — OK |
| истёкший срок, `enable=true`, безлимит | true | 0 | 8388952 | скрыт | скрыт — OK |
| восстановление | true | 1082130776 | 8388952 | в подписке | в подписке — OK |
| контрольный пример | true | 10737418240 | 10737418240 | скрыт, `resolve` 409 | **1 конфиг — FAIL; `resolve` 200 — FAIL** |

Во всех состояниях обычный безлимитный конфиг оставался в подписке, токен не менялся;
`settings.clients[]` не содержал `up/down`, счётчики были только в `clientStats`.

## Финальный прогон после исправления

Файлы в контейнере SubHub совпадают с рабочим деревом: `link_builder.py` `b5152bc1b373`,
`normalizer.py` `82bcd8c3e6d7`, `models.py` `a0fe34791fdf`. Тот же результат (32/32) дал и
промежуточный прогон до косметической правки сценария (уникальные ключи фактов, `or ""`
для mypy).

```text

== Стенд
  · 3x-ui = 3.9.0
  · SubHub в контейнере (sha256) = {'app/link_builder.py': 'b5152bc1b373', 'app/normalizer.py': '82bcd8c3e6d7', 'app/models.py': 'a0fe34791fdf'}

== Исходная подписка и реальный трафик
  [OK] одна ссылка подписки: обычный и whitelist-конфиг — конфигов 2
  [OK] обычный конфиг передаёт трафик — 200 8388608
  [OK] whitelist-конфиг передаёт трафик (попытка 1) — 200 8388608
  [OK] панель учла расход whitelist-клиента — up+down=8388952
  · inbounds/list при работающем Xray = {'inbound': 1, 'settings.enable': True, 'settings.totalGB': 1073741824, 'settings.expiryTime': 0, 'settings has up/down': False, 'clientStats.up+down': 8388952, 'clientStats.total': 1073741824, 'clientStats.enable': True}
  [OK] up/down приходят в clientStats, а не в settings.clients — {'inbound': 1, 'settings.enable': True, 'settings.totalGB': 1073741824, 'settings.expiryTime': 0, 'settings has up/down': False, 'clientStats.up+down': 8388952, 'clientStats.total': 1073741824, 'clientStats.enable': True}

== Остановка Xray whitelist-панели (снятие маскирующего enable=false)
  [OK] Xray whitelist-панели остановлен — stop
  · U = up+down whitelist-клиента = 8388952

== на границе: totalGB = U, enable=true
  · панель: на границе: totalGB = U, enable=true = {'inbound': 1, 'settings.enable': True, 'settings.totalGB': 8388952, 'settings.expiryTime': 0, 'settings has up/down': False, 'clientStats.up+down': 8388952, 'clientStats.total': 8388952, 'clientStats.enable': True}
  [OK] whitelist-конфиг скрыт — в подписке: False
  [OK] обычный безлимитный конфиг в подписке
  [OK] токен подписки не изменился

== ниже квоты: totalGB = U + 1
  · панель: ниже квоты: totalGB = U + 1 = {'inbound': 1, 'settings.enable': True, 'settings.totalGB': 8388953, 'settings.expiryTime': 0, 'settings has up/down': False, 'clientStats.up+down': 8388952, 'clientStats.total': 8388953, 'clientStats.enable': True}
  [OK] whitelist-конфиг в подписке — в подписке: True
  [OK] обычный безлимитный конфиг в подписке
  [OK] токен подписки не изменился

== выше квоты: totalGB = U − 1
  · панель: выше квоты: totalGB = U − 1 = {'inbound': 1, 'settings.enable': True, 'settings.totalGB': 8388951, 'settings.expiryTime': 0, 'settings has up/down': False, 'clientStats.up+down': 8388952, 'clientStats.total': 8388951, 'clientStats.enable': True}
  [OK] whitelist-конфиг скрыт — в подписке: False
  [OK] обычный безлимитный конфиг в подписке
  [OK] токен подписки не изменился

== безлимит: totalGB = 0
  · панель: безлимит: totalGB = 0 = {'inbound': 1, 'settings.enable': True, 'settings.totalGB': 0, 'settings.expiryTime': 0, 'settings has up/down': False, 'clientStats.up+down': 8388952, 'clientStats.total': 0, 'clientStats.enable': True}
  [OK] whitelist-конфиг в подписке — в подписке: True
  [OK] обычный безлимитный конфиг в подписке
  [OK] токен подписки не изменился

== enable=false при остатке (totalGB = U + 1 ГиБ)
  · панель: enable=false при остатке (totalGB = U + 1 ГиБ) = {'inbound': 1, 'settings.enable': False, 'settings.totalGB': 1082130776, 'settings.expiryTime': 0, 'settings has up/down': False, 'clientStats.up+down': 8388952, 'clientStats.total': 1082130776, 'clientStats.enable': False}
  [OK] whitelist-конфиг скрыт — в подписке: False
  [OK] обычный безлимитный конфиг в подписке
  [OK] токен подписки не изменился

== истёкший срок, enable=true, totalGB = 0
  · панель: истёкший срок, enable=true, totalGB = 0 = {'inbound': 1, 'settings.enable': True, 'settings.totalGB': 0, 'settings.expiryTime': 1791123002518, 'settings has up/down': False, 'clientStats.up+down': 8388952, 'clientStats.total': 0, 'clientStats.enable': True}
  [OK] whitelist-конфиг скрыт — в подписке: False
  [OK] обычный безлимитный конфиг в подписке
  [OK] токен подписки не изменился

== восстановление: totalGB = U + 1 ГиБ, срок 0
  · панель: восстановление: totalGB = U + 1 ГиБ, срок 0 = {'inbound': 1, 'settings.enable': True, 'settings.totalGB': 1082130776, 'settings.expiryTime': 0, 'settings has up/down': False, 'clientStats.up+down': 8388952, 'clientStats.total': 1082130776, 'clientStats.enable': True}
  [OK] whitelist-конфиг в подписке — в подписке: True
  [OK] обычный безлимитный конфиг в подписке
  [OK] токен подписки не изменился

== Контрольный пример: totalGB=10737418240, up+down=10737418240, enable=true
  · панель: контрольный пример = {'inbound': 2, 'settings.enable': True, 'settings.totalGB': 10737418240, 'settings.expiryTime': 0, 'settings has up/down': False, 'clientStats.up+down': 10737418240, 'clientStats.total': 10737418240, 'clientStats.enable': True}
  [OK] панель хранит пример без enable=false — {'inbound': 2, 'settings.enable': True, 'settings.totalGB': 10737418240, 'settings.expiryTime': 0, 'settings has up/down': False, 'clientStats.up+down': 10737418240, 'clientStats.total': 10737418240, 'clientStats.enable': True}
  [OK] исчерпанный клиент контрольного примера скрыт — конфигов 0
  [OK] resolve: подписка без активных конфигов (409) — HTTP 409
  [OK] после увеличения квоты на 1 байт конфиг возвращается по той же ссылке — конфигов 1
  · inbound контрольного примера = 2

== Маскирующее условие при работающем Xray (справочно)
  [OK] работающая панель сама выставляет enable=false исчерпанному клиенту — {'inbound': 2, 'settings.enable': False, 'settings.totalGB': 10737418240, 'settings.expiryTime': 0, 'settings has up/down': False, 'clientStats.up+down': 10737418240, 'clientStats.total': 10737418240, 'clientStats.enable': False}

Итого: 32 OK, 0 FAIL, 46 с
```
