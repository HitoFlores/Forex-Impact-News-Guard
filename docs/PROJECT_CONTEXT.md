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
- Persistencia SQLite para:
  - eventos relevantes;
  - settings del usuario;
  - alertas ya enviadas.
- Worker continuo con:
  - sync periodico;
  - resumen diario;
  - alertas previas;
  - consultas de resultado;
  - deduplicacion.
- Mensajes Telegram con banderas, iconos y semaforos visuales.
- Artefactos base de deploy gratis en Oracle Always Free con Docker Compose.
- Prueba real de Telegram ya validada con smoke test.

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

1. Worker lee settings desde SQLite.
2. Sincroniza Forex Factory y filtra eventos relevantes.
3. Guarda solo hoy y manana.
4. Calcula `precheck`, `alert` y `result-check`.
5. Envia resumen diario una vez por dia.
6. Envia alertas y resultados por Telegram.

## Direccion de deploy decidida

- Ruta Oracle Always Free se intento de verdad y fallo por capacidad en `mx-monterrey-1`.
- Siguiente implementacion remota se hara con `GitHub Actions + GitHub Pages`.
- Esto implica migrar de worker continuo + SQLite a ejecucion `run_once` + estado JSON + dashboard estatico.
- Se planea un `keepalive` mensual para evitar que GitHub desactive schedules por 60 dias sin actividad del repo.

## Limitaciones actuales

- `precheck` revalida calendario justo antes del alert, pero todavia conviene mejorar observabilidad y manejo fino de fallas upstream.
- Worker agrupa alertas y resultados por bloque horario, pero no resume por ventana de riesgo mas inteligente.
- No hay UI frontend; solo API y worker.
- Ruta GitHub aun no esta implementada; hoy solo esta decidida y documentada.
