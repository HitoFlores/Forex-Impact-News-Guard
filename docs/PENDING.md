# Pending

## Prioridad alta

- Migrar deploy a GitHub Actions + GitHub Pages.
  - convertir worker a `run_once` [hecho]
  - persistir estado en JSON [hecho]
  - crear workflow cron cada 5 minutos [hecho]
  - crear workflow `keepalive` mensual [hecho]
  - publicar dashboard estatico en Pages [hecho]
- Rotar `TELEGRAM_BOT_TOKEN` antes de cualquier deploy.
- Fusionar en `main` el fix de workflow para archivos ignorados.
  - `git add .state` falla porque `.state/` esta en `.gitignore`
  - cambiar a `git add -f .state` en `.github/workflows/cron.yml`
  - cambiar a `git add -f .state/keepalive.json` en `.github/workflows/keepalive.yml`
  - relanzar `sync-and-publish` en `main` despues del merge

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
