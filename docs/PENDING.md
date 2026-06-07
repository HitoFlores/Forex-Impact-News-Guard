# Pending

## Prioridad alta

- Rotar `TELEGRAM_BOT_TOKEN` antes de cualquier deploy.
- Correr `sync-and-publish` manual sobre `main` para publicar en Pages el dashboard nuevo.
- Correr `telegram-smoke-test` manual sobre `main` para validar flujo 100% GitHub -> Telegram.
- Confirmar al menos una corrida automatica posterior de `sync-and-publish` sin intervencion manual.

## Prioridad media

- Endurecer observabilidad del `precheck`.
  - Agregar logs y, si hace falta, metricas/retries mas visibles cuando Forex Factory falle justo antes del alert.
- Decidir si configuracion de usuario se congela en archivos del repo o si se expone una forma segura de editarla sin API viva.
- Mejorar agrupacion de eventos del mismo bloque para mostrar una sola ventana de riesgo consolidada.
- Agregar logs mas claros del worker para produccion.
- Exponer mas diagnostico de fallos de scraping/Telegram en dashboard si hiciera falta.

## Prioridad baja

- UI web o extension de navegador para administrar settings.
- Web Push u otro canal adicional.
- Mas reglas de relevancia por tipo de evento.
- Export o historial de eventos pasados si alguna vez hiciera falta.

## Riesgos tecnicos a recordar

- Forex Factory puede cambiar HTML/JS y romper parsing.
- `cloudscraper` hoy funciona, pero no es garantia eterna.
- GitHub `schedule` puede retrasarse y se desactiva en repos publicos sin actividad por 60 dias si no existe `keepalive`.
- `.state/` sigue ignorado por git; cualquier workflow que lo quiera commitear debe usar `git add -f`.
