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
- Ultimo redeploy manual validado: run `27214972059` de `sync-and-publish`, completado con exito.
- `keepalive` ya se valido manualmente y genera commit automatico correcto.
- `telegram-smoke-test` ya fue probado desde GitHub Actions con exito; ultimo run validado: `27215982457`.
- `dashboard-control` ya existe y permite cambiar settings basicos desde el dashboard via GitHub API + workflow.
- El dashboard nuevo ya esta publicado y validado en modo `Live` y `Demo`.
- El dashboard ahora incluye:
  - toggle `Live / Demo`;
  - tooltips `?` de ayuda;
  - `Smoke Telegram`;
  - `Sync + Publish`;
  - `Settings basicos`;
  - bloque visible de seguridad;
  - bloqueo de controles hasta pegar token;
  - ledger de ultimos dispatches con scroll interno para mantener estable el alto de pantalla.
- Los workflows sensibles `telegram-smoke-test` y `dashboard-control` ya quedaron amarrados al environment `ops-control`.
- La prueba real de Telegram ya mando 5 mensajes sample:
  - `FOREX FACTORY DAILY`
  - `FOREX IMPACT ALERT`
  - `FOREX IMPACT ALERT`
  - `FOREX RESULT UPDATE`
  - `FOREX RESULT UPDATE`
- El resumen diario de Telegram ya separa eventos por fecha local:
  - lista solo eventos de hoy;
  - si hay eventos de manana, agrega solo una nota tipo `Manana se esperan X noticias de alto impacto.`;
  - no muestra titulos de manana dentro del calendario de hoy.
- Se corrigio precision operativa de alertas/resultados:
  - alertas pre-news solo salen dentro de margen estricto alrededor de `alert_at`;
  - el mensaje calcula minutos reales hasta el evento;
  - resultados muestran hora del release, no hora del retry;
  - retries de resultado ya no duplican mensajes si `Actual` ya llego.
- Proxima prioridad clara: mover runtime critico a worker continuo si se necesita precision mejor que la que GitHub Actions cron puede garantizar.
