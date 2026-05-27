# Deploy Recommendations

Este tema se dejo fuera de este chat, pero estas son las recomendaciones acumuladas.

## Antes de deploy

1. Rotar el `TELEGRAM_BOT_TOKEN`.
2. No subir `.env`.
3. No subir `.state`.
4. Preparar variables de entorno del provider.

## Plataformas recomendadas

### Render

Buena opcion si quieres algo rapido de subir.

- Worker dedicado
- Config simple
- Menos friccion inicial

### Oracle Cloud Always Free

Buena opcion si quieres mantenerlo 24/7 con costo minimo o cero y aceptas mas trabajo manual.

- VM propia
- Mas control
- Mejor opcion si quieres independencia

## Modo de ejecucion recomendado en remoto

- Un servicio para API
- Un servicio para worker

Si quieres ahorrar al inicio, el worker es mas importante que la API.

## Variables de entorno minimas

- `FOREX_GUARD_TELEGRAM_BOT_TOKEN`
- `FOREX_GUARD_TELEGRAM_CHAT_ID`
- `FOREX_GUARD_DEFAULT_TIMEZONE`
- `FOREX_GUARD_EVENTS_DB_PATH`
- `FOREX_GUARD_SCHEDULER_SYNC_INTERVAL_MINUTES`
- `FOREX_GUARD_SCHEDULER_TICK_SECONDS`

## Validacion post-deploy

1. Confirmar que el worker arranca.
2. Confirmar que puede consultar Forex Factory.
3. Confirmar mensaje manual de Telegram.
4. Confirmar resumen diario.
5. Confirmar una alerta y un resultado reales.
