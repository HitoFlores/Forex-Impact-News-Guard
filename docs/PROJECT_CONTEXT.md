# Project Context

## Objetivo real

El sistema monitorea calendario de Forex Factory para:

- filtrar noticias relevantes segun configuracion del usuario;
- avisar antes de noticia para detener operativa;
- consultar resultado despues del release;
- mandar notificaciones por Telegram.

## Decisiones clave

- Fuente de calendario: Forex Factory.
- No se usa automatizacion de navegador.
- Acceso actual a Forex Factory: `cloudscraper` para esquivar `403` de `requests` normal.
- Base local actual solo conserva eventos de hoy y manana.
- Canal actual de notificacion: Telegram.

## Lo que ya funciona

- API FastAPI con docs en `/docs`.
- Persistencia JSON para:
  - eventos relevantes;
  - settings del usuario;
  - alertas ya enviadas.
- Worker ahora corre `run_once` y deja el cron a GitHub Actions.
- Mensajes Telegram con banderas, iconos y semaforos visuales.
- Alertas pre-news ahora tienen ventana estricta de envio: toleran hasta 30s temprano y hasta 5 min tarde contra `alert_at`; fuera de esa ventana se saltan como stale para no avisar con timing enganoso.
- El texto de alerta usa minutos reales restantes al evento en el momento de envio, no solo el `lead_minutes` configurado.
- Resultados post-news no se repiten cuando ya existe `Actual`; al primer resultado final se marcan los retries pendientes como cubiertos. Si `Actual` sigue `N/D`, los retries siguen activos.
- Mensajes de resultado muestran hora del release del evento, no hora del retry/scrape.
- Resumen diario de Telegram separa eventos de hoy y manana: el calendario diario lista solo la fecha actual y, si detecta alto impacto para manana, agrega una nota corta sin listar esos eventos como si fueran de hoy.
- `GitHub Actions + GitHub Pages` ya quedo desplegado en `main`.
- `sync-and-publish` y `keepalive` ya fueron validados manualmente.
- Workflow manual `telegram-smoke-test` ya existe para prueba remota bajo demanda y ya fue validado desde GitHub.
- Prueba real de Telegram ya validada con 5 mensajes sample.
- Dashboard publicado con modos `Live` y `Demo`.
- Dashboard puede disparar:
  - `telegram-smoke-test`;
  - `sync-and-publish`;
  - `dashboard-control` para settings basicos.
- Los workflows sensibles usan environment `ops-control`.
- El token del dashboard ya no se guarda persistente; solo en sesion del navegador.

## Configuracion actual del producto

Usuario puede configurar:

- impactos permitidos;
- monedas;
- minutos antes de alertar;
- minutos de revalidacion previa;
- minutos de consulta posterior;
- reintentos de consulta posterior;
- resumen diario activado o no;
- timezone.

## Flujo actual

1. Worker lee settings desde JSON.
2. Sincroniza Forex Factory y filtra eventos relevantes.
3. Guarda solo hoy y manana.
4. Calcula `precheck`, `alert` y `result-check`.
5. Envia resumen diario una vez por dia, con detalle solo de hoy y aviso agregado de manana si aplica.
6. Revalida antes del alert; si el evento se movio, reconstruye horarios antes de enviar.
7. Envia alertas solo dentro de la ventana precisa y resultados por Telegram con dedupe final.

## Direccion de deploy decidida

- Ruta Oracle Always Free se intento de verdad y fallo por capacidad en `mx-monterrey-1`.
- Implementacion remota activa: `GitHub Actions + GitHub Pages`.
- Esto ya reemplazo worker continuo remoto por ejecucion `run_once` + estado JSON + dashboard estatico.
- `keepalive` mensual/manual ya existe para evitar que GitHub desactive schedules por 60 dias sin actividad del repo.

## Limitaciones actuales

- `precheck` revalida calendario justo antes del alert, pero todavia conviene mejorar observabilidad y manejo fino de fallas upstream.
- Worker agrupa alertas y resultados por bloque horario, pero no resume por ventana de riesgo mas inteligente.
- GitHub Actions cron no garantiza ejecucion exacta al segundo; por eso el worker ahora rechaza alertas stale, pero para precision sub-minuto real conviene un worker continuo en infraestructura propia.
- Dashboard ya existe y es util para operacion, pero todavia puede crecer en diagnostico, consolidacion de riesgo y calidad visual.
- GitHub Pages sigue siendo publica; aunque las acciones ya exigen token y pueden exigir approval en `ops-control`, el contenido publicado sigue siendo visible para cualquiera con la URL.
- Si se quiere privacidad real de lectura, toca mover la UI a una superficie con auth real.
