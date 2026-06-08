# Forex-Impact-News-Guard

Sistema de avisos para noticias economicas del calendario de Forex Factory y ventanas de riesgo para trading/fondeo.

## Objetivo

Este proyecto busca vigilar eventos publicados en Forex Factory para:

- detectar noticias relevantes en el calendario segun impacto y moneda;
- avisar cuantos minutos antes debe llegar la alerta;
- revalidar el evento poco antes del aviso;
- consultar resultados despues de la noticia si el usuario lo desea;
- leer la fuente real de Forex Factory sin automatizacion de navegador.

## Stack

- Backend: Python + FastAPI
- Scheduler: base de planificacion por evento lista
- Notificaciones: Telegram + Web Push en siguientes iteraciones

## Estado actual

Scaffold reiniciado el 2026-05-26 con:

- configuracion base del servicio;
- modelos de dominio para eventos y alertas;
- motor inicial para planificar alertas de calendario por evento;
- endpoint para previsualizar alertas;
- cliente HTTP real para Forex Factory y endpoint de previsualizacion live;
- persistencia JSON para eventos, runtime y settings;
- scheduler base con precheck, alerta y result-check;
- pruebas unitarias y de API.

## Estructura

```text
src/forex_news_guard/
  api/
  core/
  domain/
  storage/
  services/
tests/
```

## Ejecutar localmente

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
uvicorn forex_news_guard.main:app --reload
```

## Endpoints

- `GET /health`
- `GET /api/v1/settings`
- `PUT /api/v1/settings`
- `GET /api/v1/events/relevant`
- `GET /api/v1/events/schedules/upcoming`
- `POST /api/v1/alerts/preview`
- `POST /api/v1/alerts/forex-factory/live-preview`
- `POST /api/v1/alerts/telegram/smoke-test`

## Operacion remota actual

- `sync-and-publish`: cron principal en GitHub Actions, actualiza `.state/` y publica Pages.
- `keepalive`: workflow manual/mensual para mantener schedules vivos.
- `telegram-smoke-test`: workflow manual para forzar envio real de todos los mensajes sample a Telegram sin levantar API local.
- `public/`: dashboard estatico con salud operativa, proximas ventanas de riesgo y ledger reciente.

## Variables de entorno utiles

- `FOREX_GUARD_DEFAULT_TIMEZONE=America/Chihuahua`
- `FOREX_GUARD_FOREX_FACTORY_BASE_URL=https://www.forexfactory.com`
- `FOREX_GUARD_FOREX_FACTORY_NEWS_URL=https://www.forexfactory.com/news?sc_lang=en`
- `FOREX_GUARD_FOREX_FACTORY_USER_AGENT=...`
- `FOREX_GUARD_STATE_DIR=.state`
- `FOREX_GUARD_EVENTS_STATE_PATH=.state/events.json`
- `FOREX_GUARD_RUNTIME_STATE_PATH=.state/runtime.json`
- `FOREX_GUARD_SETTINGS_STATE_PATH=.state/settings.json`
- `FOREX_GUARD_SCHEDULER_SYNC_INTERVAL_MINUTES=30`
- `FOREX_GUARD_SCHEDULER_TICK_SECONDS=30`
- `FOREX_GUARD_TELEGRAM_BOT_TOKEN=...`
- `FOREX_GUARD_TELEGRAM_CHAT_ID=...`
- `FOREX_GUARD_TELEGRAM_SMOKE_CHAT_ID=...` para mandar solo `telegram-smoke-test` a tu chat privado

Nota Telegram: si grupo productivo migra a `supergroup`, el `chat_id` cambia. En ese caso hay que actualizar `FOREX_GUARD_TELEGRAM_CHAT_ID` con nuevo valor que Telegram devuelve en error/log; normalmente usa formato negativo `-100...`.

`currencies=[]` o vacio = sin filtro por moneda. El sistema no usa una whitelist fija ahi; acepta cualquier moneda que venga en Forex Factory y pase el filtro de impacto.

Nota: al 2026-05-26, `requests` normal devolvio `403` por Cloudflare para rutas como `calendar/json`, `calendar/xml`, `calendar/csv` y `news/rss`. En este proyecto cambiamos a un cliente HTTP no-browser compatible con Cloudflare para consumir el HTML real de Forex Factory sin automatizacion de navegador.

## Flujo pensado

1. sincronizar calendario de Forex Factory en periodos amplios;
2. guardar solo eventos relevantes de hoy y manana;
3. programar `precheck`, `alert` y `result-check` por evento;
4. revalidar antes del aviso y consultar resultados despues del release.

## Deploy gratis recomendado

Ruta principal:

- [docs/DEPLOY_GITHUB_ACTIONS_PAGES.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/docs/DEPLOY_GITHUB_ACTIONS_PAGES.md)

Ruta fallback ya explorada pero no confiable por capacidad:

- [Dockerfile](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/Dockerfile)
- [compose.yml](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/compose.yml)
- [docs/DEPLOY_ORACLE_ALWAYS_FREE.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/docs/DEPLOY_ORACLE_ALWAYS_FREE.md)

## Documentacion de handoff

Para retomar el proyecto en otro chat, empezar por:

1. [docs/START_HERE.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/docs/START_HERE.md)
2. [docs/PROJECT_CONTEXT.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/docs/PROJECT_CONTEXT.md)
3. [docs/PENDING.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/docs/PENDING.md)

## Worker

Para correr el scheduler continuo:

```bash
python -m forex_news_guard.worker
```
