# Pending

## Prioridad alta

- Implementar revalidacion real en `precheck`.
  - Hoy el scheduler agenda `precheck`, pero no vuelve a consultar Forex Factory justo antes del alert.
- Preparar deploy.
  - Dockerfile
  - archivo para plataforma elegida
  - health/start commands
- Rotar `TELEGRAM_BOT_TOKEN` antes de cualquier deploy.

## Prioridad media

- Mejorar agrupacion de eventos del mismo bloque para mostrar una sola ventana de riesgo consolidada.
- Agregar logs mas claros del worker para produccion.
- Agregar endpoint o comando para forzar reenvio de resumen diario.
- Agregar endpoint o flag para enviar mensaje de prueba a Telegram.

## Prioridad baja

- UI web o extension de navegador para administrar settings.
- Web Push u otro canal adicional.
- Mas reglas de relevancia por tipo de evento.
- Export o historial de eventos pasados si alguna vez hiciera falta.

## Riesgos tecnicos a recordar

- Forex Factory puede cambiar HTML/JS y romper parsing.
- `cloudscraper` hoy funciona, pero no es garantia eterna.
- El timezone debe revisarse bien en entorno remoto.
