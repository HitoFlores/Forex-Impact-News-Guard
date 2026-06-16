# Operations

## Requisitos

- Python 3.12
- `.env` con credenciales

## Instalar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

## Levantar API

```bash
uvicorn forex_news_guard.main:app --reload
```

Abrir:

- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Levantar worker

En otra terminal:

```bash
python -m forex_news_guard.worker
```

Ese comando corre una sola vez y es el modo productivo actual en GitHub Actions.

Para repeticion continua local o en VPS:

```bash
python -m forex_news_guard.worker_continuous
```

Ese modo instancia `RuntimeSchedulerService`, registra dos jobs internos y mantiene el proceso bloqueado hasta `Ctrl+C`:

- `sync-relevant-events`: corre cada `FOREX_GUARD_SCHEDULER_SYNC_INTERVAL_MINUTES` minutos.
- `dispatch-due-checks`: corre cada `FOREX_GUARD_SCHEDULER_TICK_SECONDS` segundos.

Variables necesarias para el worker continuo:

- `FOREX_GUARD_TELEGRAM_BOT_TOKEN`
- `FOREX_GUARD_TELEGRAM_CHAT_ID`
- `FOREX_GUARD_EVENTS_STATE_PATH`
- `FOREX_GUARD_RUNTIME_STATE_PATH`
- `FOREX_GUARD_SETTINGS_STATE_PATH`
- `FOREX_GUARD_FOREX_FACTORY_COOKIE` si Forex Factory bloquea el scraping sin cookie.

Para detenerlo, usa `Ctrl+C` en local o detiene el servicio del sistema si lo corres con systemd, Docker o un supervisor. Este modo no cambia produccion: `.github/workflows/cron.yml` sigue usando `python -m forex_news_guard.worker`. Su precision depende del uptime real del host; en una laptop se detiene si la sesion duerme o se cierra.

## Endpoints utiles

- `GET /health`
- `GET /api/v1/settings`
- `PUT /api/v1/settings`
- `GET /api/v1/events/relevant`
- `GET /api/v1/events/schedules/upcoming`
- `POST /api/v1/alerts/preview`
- `POST /api/v1/alerts/forex-factory/live-preview`
- `POST /api/v1/alerts/telegram/smoke-test`

## Ejemplo rapido para actualizar settings

En Swagger `/docs` es lo mas sencillo.

Payload base:

```json
{
  "calendar_enabled": true,
  "breaking_enabled": true,
  "high_impact_only": true,
  "allowed_impacts": null,
  "currencies": [],
  "lead_minutes": 15,
  "revalidate_minutes_before_alert": 2,
  "result_check_delay_minutes": 1,
  "result_retry_minutes": [3, 5],
  "include_results": true,
  "daily_summary_enabled": true,
  "risk_window_before_minutes": 15,
  "risk_window_after_minutes": 15,
  "timezone": "America/Chihuahua"
}
```

Ese payload representa el default operativo: sólo alto impacto, todas las monedas, breaking news activo y resumen diario activo.

Nota sobre `currencies`:

- `[]` o vacio no significa un catalogo fijo interno.
- Significa `sin filtro por moneda`.
- Entra cualquier moneda que venga en Forex Factory y pase el filtro de impacto.
- En la practica suele incluir cosas como `USD`, `EUR`, `GBP`, `JPY`, `AUD`, `NZD`, `CAD`, `CHF`, `CNY`, `MXN`, pero no esta limitado a esa lista.

## Archivos locales importantes

- `.env`: secretos locales
- `.state/`: JSON local de trabajo

Ambos deben quedarse fuera de git.

## Variables operativas

- `FOREX_GUARD_SCRAPING_FAILURE_ALERT_THRESHOLD`: fallos consecutivos de scraping necesarios para avisar por Telegram. Default: `3`. Usa `0` para desactivar el aviso.
- `FOREX_GUARD_RUNTIME_DISPATCH_TTL_DAYS`: días de historial de dispatches que conserva `runtime.json`. Default: `7`. Usa `0` para desactivar la poda.

## Auth de lectura del dashboard

GitHub Pages sirve contenido estatico publico. No hay auth de lectura real dentro del dashboard publicado en Pages.

Decision actual: no configurar Cloudflare Access todavia. Mientras no haya dominio o host propio, el dashboard queda como esta: Pages publico para lectura, con acciones sensibles protegidas por token de GitHub en sesion y environment `ops-control`.

Si el estado operativo se considera sensible, usa una capa externa:

1. Configurar un dominio propio para el dashboard.
2. Pasar el dominio por Cloudflare con proxy activo.
3. Crear una aplicacion de Cloudflare Access para la ruta del dashboard.
4. Definir una politica de acceso por emails permitidos.
5. Usar y compartir solo el dominio protegido.

Importante: `public/state.json` y el dashboard siguen siendo accesibles por la URL directa de GitHub Pages si alguien la conoce. Para proteccion real, no compartas la URL publica de Pages y opera desde el dominio protegido por Cloudflare Access.

Las acciones sensibles permanecen protegidas como hasta ahora: token de GitHub en sesion del navegador y workflow `dashboard-control` bajo el environment `ops-control`.

Nota de costo: Cloudflare Access puede ser viable en plan gratis para uso personal o equipos pequenos, pero aun asi normalmente requiere un dominio propio. Reabrir esta tarea cuando se decida comprar/conectar dominio o mover el dashboard a un host propio.

## Rotacion de Telegram token

Hacer esto antes de cualquier deploy nuevo o si el token ya paso por chats, capturas o pruebas no confiables.

1. Ir a `@BotFather` en Telegram.
2. Ejecutar `/revoke` sobre el bot actual para invalidar token viejo.
3. Generar token nuevo con `/token`.
4. Actualizar secreto `FOREX_GUARD_TELEGRAM_BOT_TOKEN` en GitHub `Actions secrets` o `Environment secrets`, segun donde viva hoy.
5. Verificar que `FOREX_GUARD_TELEGRAM_CHAT_ID` siga correcto.
6. Si Telegram migro grupo productivo a `supergroup`, actualizar `FOREX_GUARD_TELEGRAM_CHAT_ID` al nuevo `chat_id` reportado por Telegram. Suele cambiar a formato negativo `-100...`.
7. Si quieres aislar pruebas del grupo real, configurar tambien `FOREX_GUARD_TELEGRAM_SMOKE_CHAT_ID` con tu chat privado.
8. Correr workflow manual `telegram-smoke-test`.
9. Confirmar recepcion de los 5 mensajes sample antes de volver a usar `sync-and-publish`.

No guardar token nuevo en commits, screenshots, notas de handoff ni chats.

## Prueba manual de Telegram

Para forzar envio de mensajes sample:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/alerts/telegram/smoke-test
```

Eso manda:

- resumen diario;
- alerta individual;
- alerta agrupada;
- resultado individual;
- resultado agrupado.

## Prueba forzada remota de Telegram

Sin API local, usa workflow manual `telegram-smoke-test` en GitHub Actions.

Ese workflow:

- instala dependencias;
- usa `FOREX_GUARD_TELEGRAM_BOT_TOKEN`;
- usa `FOREX_GUARD_TELEGRAM_SMOKE_CHAT_ID` si existe;
- si no existe, cae a `FOREX_GUARD_TELEGRAM_CHAT_ID`;
- si Telegram responde `group upgraded to a supergroup` o devuelve nuevo `chat_id`, actualizar secreto `FOREX_GUARD_TELEGRAM_CHAT_ID` al valor nuevo;
- ejecuta `python scripts/send_telegram_smoke_test.py`;
- deja resumen en el job y envia todos los mensajes sample al chat de smoke o al chat default.

Uso:

1. Abrir `Actions`.
2. Elegir `telegram-smoke-test`.
3. `Run workflow` sobre `main`.
4. Verificar job en verde y mensajes recibidos en Telegram.

Despues de la prueba no hay que revertir nada: es workflow manual, no altera `sync-and-publish`.

## Nota de transicion

Esta operacion sigue describiendo el modo local/API actual.

La estrategia remota decidida para siguiente iteracion ya no es VM continua, sino:

- GitHub Actions para ejecucion programada
- GitHub Pages para dashboard publico
