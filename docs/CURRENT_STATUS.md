
## Navegación  
- [[PROJECT]]

# CURRENT STATUS

> **Fuentes:** Las secciones indican entre paréntesis el origen de cada afirmación:
> `[doc]` = extraído de documentación existente (README, docs/*, commits) |
> `[código]` = inferencia directa del código fuente | `[test]` = evidenciado por suite de tests

---

## Estado actual

El sistema está **operativo en producción** sobre GitHub Actions + GitHub Pages en la rama `main`. `[doc]`

- Cron `sync-and-publish` corre cada 5 minutos, persiste estado en `.state/` y publica dashboard. `[doc]`
- Último redeploy manual validado: run `27214972059`. `[doc]`
- `keepalive` mensual validado; genera commit automático para evitar que GH desactive schedules. `[doc]`
- Dashboard publicado en modo `Live` y `Demo`. `[doc]`
- Canal Telegram activo y validado con 5 mensajes sample reales. `[doc]`
- Todos los tests pasan: **46/46** (`pytest tests/`). `[test]`

---

## Funcionalidades implementadas

### Pipeline principal `[doc + código]`

- Sincronización periódica del calendario de Forex Factory (HTML scraping con `cloudscraper`)
- Filtrado de eventos por impacto y moneda según `AlertPolicy` del usuario
- Retención de eventos de hoy y mañana únicamente en `.state/events.json`
- Cálculo de timestamps `precheck`, `alert` y `result_check` por evento
- Deduplicación completa: cada dispatch se registra en `runtime.json`; ningún mensaje se duplica entre re-ejecuciones del cron

### Notificaciones Telegram `[doc + código]`

- **Resumen diario** (`FOREX FACTORY DAILY`): se envía una vez por día; lista solo eventos de hoy; agrega nota agregada de mañana si hay alto impacto
- **Alerta pre-noticia individual** (`FOREX IMPACT ALERT`): muestra minutos reales restantes al evento en el momento de envío, no el `lead_minutes` configurado
- **Alerta pre-noticia agrupada** (`NEWS BLOCK`): consolida eventos simultáneos en un solo mensaje
- **Resultado post-noticia individual** (`FOREX RESULT UPDATE`): muestra hora del release, Actual/Forecast/Previous con badge visual
- **Resultado post-noticia agrupado** (`POST-NEWS UPDATE`): consolida resultados simultáneos

### Control de calidad de alertas `[código]`

- Ventana estricta de envío: `[alert_at - 30s, alert_at + 5min]`; fuera de ese rango la alerta se descarta como stale
- Revalidación pre-alerta (precheck): re-fetcha Forex Factory antes de cada grupo de alertas vencidas; si el evento se movió, recalcula schedules
- Finalizacion de resultados: cuando `Actual` llega, marca todos los retries pendientes del mismo evento como cubiertos; no sigue reintentando
- Resultados sin `Actual` real (`N/D`, vacío, `NA`) no se envían a Telegram aunque los retries estén vencidos
- Resumen diario acotado a medianoche local: sólo se envía entre `00:00` y `00:30` según `AlertPolicy.timezone`
- Parser de Forex Factory prioriza `timeLabel` visible sobre `dateline` para alinear el bot con la hora mostrada en la tabla web

### Dashboard `[doc]`

- Panel de salud del cron con timestamps de último sync y probes (scraping, telegram, precheck)
- Próximas ventanas de riesgo
- Política activa visible
- Ledger de últimos dispatches con scroll interno (no crece la pantalla)
- Modos `Live` y `Demo`
- Tooltips `?` de ayuda inline
- Controles: `Smoke Telegram`, `Sync + Publish`, `Settings básicos`
- Selector de timezone IANA en Settings, con `America/Chihuahua` como valor actual por default

### Seguridad operativa `[doc]`

- Workflows sensibles (`telegram-smoke-test`, `dashboard-control`) amarrados al environment `ops-control`
- Token del dashboard no se persiste; solo en sesión del navegador
- `.state/` ignorado en git para trabajo local; los workflows lo commitean con `git add -f`

### API local `[código]`

- `GET /health`, `GET/PUT /api/v1/settings`, `GET /api/v1/events/relevant`
- `GET /api/v1/events/schedules/upcoming`, `POST /api/v1/alerts/preview`
- `POST /api/v1/alerts/forex-factory/live-preview`, `POST /api/v1/alerts/telegram/smoke-test`

---

## Funcionalidades en pruebas

No hay funcionalidades en estado experimental explícito al cierre de la última sesión. `[doc: PENDING.md sin pendientes activos]`

**Nota de inferencia `[código]`:** El modelo `AlertPolicy.breaking_enabled = True` existe y `ForexFactoryClient.fetch_breaking_news_events()` está implementado, pero no hay evidencia en el código de que el worker llame a `fetch_breaking_news_events` en el ciclo productivo actual. Sólo se invoca en `preview_live_alerts` de la API local. El canal de breaking news podría estar parcialmente implementado pero no activo en producción.

---

## Pendientes conocidos

`[doc: PENDING.md]` — Al cierre de la última sesión: **sin pendientes activos**.

**Pendientes inferidos del código `[código]`:**

- `build_pre_alert_message`, `build_result_message`, `build_grouped_pre_alert_message`, `build_grouped_result_message` no tienen tests unitarios propios. Son las funciones que construyen exactamente lo que el usuario recibe en Telegram.
- `preview_forex_factory_live_preview` (ruta API live) no tiene test de integración.
- `RuntimeProbeStatus.WARN` está definido en el enum pero ningún código lo emite. La observabilidad interna sólo distingue OK/ERROR/IDLE.
- Worker para modo continuo (`BackgroundScheduler.start()`) está implementado pero no usado en producción. Si se quiere precisión sub-minuto, ese modo necesita validación real.
- `DeliveryChannel` sólo tiene `TELEGRAM`. El README menciona "Web Push en siguientes iteraciones" como idea no implementada.

---

## Riesgos actuales

### Documentados explícitamente `[doc]`

| Riesgo | Impacto | Mitigación actual |
|---|---|---|
| Forex Factory cambia HTML/JS | Parsing se rompe, sin alertas | Dos estrategias de parsing (JSON embebido + BS4 fallback); no hay más |
| `cloudscraper` deja de funcionar | Sin acceso a Forex Factory | Soporte de cookie manual (`FOREX_GUARD_FOREX_FACTORY_COOKIE`) como fallback |
| GitHub cron se retrasa o desactiva | Alertas tardías o sistema silencioso | `keepalive` mensual; ventana ±tolerancia rechaza alerts stale |
| `.state/` con `git add -f` accidental | Corrupción de historial | Comentado en docs; convención establecida |
| Dashboard público en Pages | Estado operativo visible para cualquiera | Acciones protegidas por token + `ops-control`; sólo lectura es pública |

### Inferidos del código `[código]`

| Riesgo | Impacto |
|---|---|
| Fallo de scraping silencioso para el operador | `RuntimeRepository` registra el error pero no hay alerta automática a Telegram cuando `consecutive_failures` supera un umbral |
| Sin límite de rate para Telegram Bot API | En semanas con muchos eventos simultáneos podría alcanzar el límite de 30 msg/s de la API |
| `runtime.json` puede crecer indefinidamente | No hay TTL ni compactación del historial de dispatches; en uso prolongado el archivo crece sin límite |
| Dependencia de `cloudscraper` sin pin de versión explícita | Actualización automática podría introducir regresión de compatibilidad con Cloudflare |

---

## Próximos pasos recomendados

Ordenados por impacto / esfuerzo estimado:

### Alta prioridad

1. **Tests para `notification_formatter`** — las 5 funciones que construyen mensajes Telegram no tienen cobertura. Un cambio de formato silencioso afecta directamente al usuario.

2. **Alerta Telegram cuando scraping falla consecutivamente** — `RuntimeProbeState.consecutive_failures` existe pero nadie actúa sobre él. Agregar un umbral configurable (ej. 3 fallos) que dispare un mensaje de error al operador cierra el loop de observabilidad.

3. **TTL / compactación de `runtime.json`** — sin límite, el historial de dispatches crece indefinidamente. Implementar limpieza de registros con más de N días (ej. 7) en cada ciclo.

### Media prioridad

4. **Activar o remover `breaking_enabled`** — la funcionalidad existe en el cliente y en el modelo de política, pero el worker no la invoca. Decidir si se integra al ciclo productivo o se elimina para evitar confusión.

5. **Emitir `WARN` en `RuntimeProbeStatus`** — el estado existe pero no se usa. Implementar umbral intermedio (ej. 1-2 fallos consecutivos = WARN, 3+ = ERROR) para dar visibilidad antes de que el sistema falle del todo.

6. **Pin de versión para `cloudscraper`** — la dependencia crítica para acceso a Forex Factory no tiene versión fija en `pyproject.toml`. Un `cloudscraper>=1.2.71,<2` evita regresiones silenciosas.

### Baja prioridad / largo plazo

7. **Worker continuo con infraestructura propia** — GitHub Actions no garantiza precisión sub-minuto. Si se necesita esa precisión, el modo `BackgroundScheduler.start()` ya existe en código y sólo necesita validación en un entorno con uptime real.

8. **Auth de lectura para el dashboard** — si el estado operativo (ventanas de riesgo, timing de alertas) se vuelve sensible, mover la UI a una superficie con auth real.

---

## Nivel de madurez del proyecto

**MVP en producción, funcional para uso personal.**

| Dimensión | Estado |
|---|---|
| Flujo principal (sync → alert → result) | ✅ Operativo y validado |
| Notificaciones Telegram | ✅ Validadas con mensajes reales |
| Dashboard operativo | ✅ Publicado en Pages |
| Cobertura de tests | ⚠️ 46 tests pasan, pero el formateador de mensajes (interfaz con el usuario) no tiene cobertura |
| Observabilidad | ⚠️ Probes registran estado pero no alertan activamente al operador |
| Resiliencia a cambios upstream | ⚠️ Dos estrategias de parsing, pero sin fallback si ambas fallan |
| Escalabilidad | ➡️ Diseño para uso individual; sin rate limiting ni compactación de estado |
| Modo continuo (sub-minuto) | ➡️ Implementado pero no validado en producción |

El proyecto está listo para uso diario de trading personal. No está listo para operar como servicio multi-usuario ni para entornos donde la precisión de alertas sea crítica a nivel de segundos.
