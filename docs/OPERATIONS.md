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

Ese comando ahora corre una sola vez. Para repeticion continua local, usa tu propio cron o loop externo.

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
  "allowed_impacts": ["high"],
  "currencies": [],
  "lead_minutes": 5,
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

## Archivos locales importantes

- `.env`: secretos locales
- `.state/`: JSON local de trabajo

Ambos deben quedarse fuera de git.

## Rotacion de Telegram token

Hacer esto antes de cualquier deploy nuevo o si el token ya paso por chats, capturas o pruebas no confiables.

1. Ir a `@BotFather` en Telegram.
2. Ejecutar `/revoke` sobre el bot actual para invalidar token viejo.
3. Generar token nuevo con `/token`.
4. Actualizar secreto `FOREX_GUARD_TELEGRAM_BOT_TOKEN` en GitHub `Actions secrets` o `Environment secrets`, segun donde viva hoy.
5. Verificar que `FOREX_GUARD_TELEGRAM_CHAT_ID` siga correcto.
6. Si quieres aislar pruebas del grupo real, configurar tambien `FOREX_GUARD_TELEGRAM_SMOKE_CHAT_ID` con tu chat privado.
7. Correr workflow manual `telegram-smoke-test`.
8. Confirmar recepcion de los 5 mensajes sample antes de volver a usar `sync-and-publish`.

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
