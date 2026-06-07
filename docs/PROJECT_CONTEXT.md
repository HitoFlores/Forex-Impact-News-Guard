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
- `GitHub Actions + GitHub Pages` ya quedo desplegado en `main`.
- `sync-and-publish` y `keepalive` ya fueron validados manualmente.
- Workflow manual `telegram-smoke-test` ya existe para prueba remota bajo demanda.
- Prueba real local de Telegram ya validada con 5 mensajes sample.

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
5. Envia resumen diario una vez por dia.
6. Envia alertas y resultados por Telegram.

## Direccion de deploy decidida

- Ruta Oracle Always Free se intento de verdad y fallo por capacidad en `mx-monterrey-1`.
- Implementacion remota activa: `GitHub Actions + GitHub Pages`.
- Esto ya reemplazo worker continuo remoto por ejecucion `run_once` + estado JSON + dashboard estatico.
- `keepalive` mensual/manual ya existe para evitar que GitHub desactive schedules por 60 dias sin actividad del repo.

## Limitaciones actuales

- `precheck` revalida calendario justo antes del alert, pero todavia conviene mejorar observabilidad y manejo fino de fallas upstream.
- Worker agrupa alertas y resultados por bloque horario, pero no resume por ventana de riesgo mas inteligente.
- Dashboard ya existe y es util para operacion, pero todavia puede crecer en diagnostico y consolidacion de riesgo.
- Falta validar manana el workflow `telegram-smoke-test` ejecutado desde GitHub y relanzar `sync-and-publish` para publicar la nueva UI.
