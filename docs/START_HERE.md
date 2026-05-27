# Start Here

Si vas a retomar este proyecto en un chat nuevo, lee esto en este orden:

1. [README.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/README.md)
2. [docs/PROJECT_CONTEXT.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/docs/PROJECT_CONTEXT.md)
3. [docs/OPERATIONS.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/docs/OPERATIONS.md)
4. [docs/PENDING.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/docs/PENDING.md)
5. [docs/DEPLOY_RECOMMENDATIONS.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/docs/DEPLOY_RECOMMENDATIONS.md)

## Codigo clave

- API: [src/forex_news_guard/api/router.py](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/src/forex_news_guard/api/router.py)
- Integracion Forex Factory: [src/forex_news_guard/integrations/forex_factory.py](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/src/forex_news_guard/integrations/forex_factory.py)
- Worker: [src/forex_news_guard/worker.py](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/src/forex_news_guard/worker.py)
- Scheduler runtime: [src/forex_news_guard/services/runtime_scheduler.py](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/src/forex_news_guard/services/runtime_scheduler.py)
- Settings: [src/forex_news_guard/services/settings_service.py](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/src/forex_news_guard/services/settings_service.py)
- Persistencia: [src/forex_news_guard/storage](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/src/forex_news_guard/storage)

## Nota importante

Antes de cualquier deploy, rotar el `TELEGRAM_BOT_TOKEN`.
