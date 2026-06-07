# Start Here

Si vas a retomar este proyecto en un chat nuevo, lee esto en este orden:

1. [README.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/README.md)
2. [docs/PROJECT_CONTEXT.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/docs/PROJECT_CONTEXT.md)
3. [docs/OPERATIONS.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/docs/OPERATIONS.md)
4. [docs/PENDING.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/docs/PENDING.md)
5. [docs/DEPLOY_RECOMMENDATIONS.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/docs/DEPLOY_RECOMMENDATIONS.md)
6. [docs/DEPLOY_GITHUB_ACTIONS_PAGES.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/docs/DEPLOY_GITHUB_ACTIONS_PAGES.md)
7. [docs/DEPLOY_ORACLE_ALWAYS_FREE.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/docs/DEPLOY_ORACLE_ALWAYS_FREE.md)

## Codigo clave

- API: [src/forex_news_guard/api/router.py](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/src/forex_news_guard/api/router.py)
- Integracion Forex Factory: [src/forex_news_guard/integrations/forex_factory.py](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/src/forex_news_guard/integrations/forex_factory.py)
- Worker: [src/forex_news_guard/worker.py](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/src/forex_news_guard/worker.py)
- Scheduler runtime: [src/forex_news_guard/services/runtime_scheduler.py](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/src/forex_news_guard/services/runtime_scheduler.py)
- Settings: [src/forex_news_guard/services/settings_service.py](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/src/forex_news_guard/services/settings_service.py)
- Persistencia: [src/forex_news_guard/storage](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/src/forex_news_guard/storage)

## Nota importante

Antes de cualquier deploy, rotar el `TELEGRAM_BOT_TOKEN`.

## Ultimo estado

Si retomas desde cero, el estado real actual es este:

- `sync-and-publish` ya pasa en `main` y Pages ya esta publicado.
- `keepalive` ya se valido manualmente y genera commit automatico correcto.
- El workflow nuevo `telegram-smoke-test` ya existe en repo pero falta correrlo manualmente desde GitHub.
- El dashboard nuevo ya esta en codigo, pero falta relanzar `sync-and-publish` para verlo publicado en Pages.
- La prueba local real de Telegram ya mando 5 mensajes sample:
  - `FOREX FACTORY DAILY`
  - `FOREX IMPACT ALERT`
  - `FOREX IMPACT ALERT`
  - `FOREX RESULT UPDATE`
  - `FOREX RESULT UPDATE`
