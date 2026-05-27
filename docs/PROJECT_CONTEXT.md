# Project Context

## Objetivo real

El sistema monitorea el calendario de Forex Factory para:

- filtrar noticias relevantes segun configuracion del usuario;
- avisar antes de la noticia para detener operativa;
- consultar el resultado despues del release;
- mandar notificaciones por Telegram.

## Decisiones clave

- La fuente del calendario es Forex Factory.
- No se usa automatizacion de navegador.
- El acceso actual a Forex Factory se hace con `cloudscraper` para esquivar el `403` de `requests` normal.
- La base local solo conserva eventos de hoy y manana.
- El canal actual de notificacion es Telegram.

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

## Configuracion actual del producto

El usuario puede configurar:

- impactos permitidos;
- monedas;
- minutos antes de alertar;
- minutos de revalidacion previa;
- minutos de consulta posterior;
- reintentos de consulta posterior;
- resumen diario activado o no;
- timezone.

## Flujo actual

1. El worker lee settings desde SQLite.
2. Sincroniza Forex Factory y filtra eventos relevantes.
3. Guarda solo hoy y manana.
4. Calcula `precheck`, `alert` y `result-check`.
5. Envia resumen diario una vez por dia.
6. Envia alertas y resultados por Telegram.

## Limitaciones actuales

- `precheck` existe en la agenda, pero todavia no hace una revalidacion real contra Forex Factory justo antes del aviso.
- El worker agrupa alertas y resultados por bloque horario, pero no resume por ventana de riesgo mas inteligente.
- No hay UI frontend; solo API y worker.
- No hay empaquetado de deploy todavia.
