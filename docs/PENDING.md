# Pending

## Prioridad 1 - siguiente sesion

- Mejorar diseno del dashboard como foco principal.
- Refinar jerarquia visual, espaciado, legibilidad y estados de control para que se vea mas profesional.

## Prioridad alta

- Confirmar al menos una corrida programada posterior de `sync-and-publish` sin intervencion manual.
- Endurecer visibilidad/privacidad real si el dashboard debe dejar de ser publico.
  - Si se quiere ocultar contenido completo, mover UI detras de auth real como Cloudflare Access o app con login.
- Endurecer observabilidad de scraping, Telegram y `precheck` en dashboard.
  - Mostrar ultimo error util y ultimo exito por flujo.
- Revisar si conviene mantener `dashboard-control` abierto a cualquier operador con token o migrarlo a una superficie privada.

## Prioridad media

- Mejorar agrupacion de eventos del mismo bloque para mostrar una sola ventana de riesgo consolidada.
- Agregar logs mas claros del worker para produccion.
- Revisar si settings basicos actuales son suficientes o si hace falta separar modo operador y modo admin.
- Ajustar textos de ayuda `?` y feedbacks del dashboard despues de usarlo unos dias.

## Prioridad baja

- Web Push u otro canal adicional.
- Mas reglas de relevancia por tipo de evento.
- Export o historial de eventos pasados si alguna vez hiciera falta.

## Riesgos tecnicos a recordar

- Forex Factory puede cambiar HTML/JS y romper parsing.
- `cloudscraper` hoy funciona, pero no es garantia eterna.
- GitHub `schedule` puede retrasarse y se desactiva en repos publicos sin actividad por 60 dias si no existe `keepalive`.
- `.state/` sigue ignorado por git; cualquier workflow que lo quiera commitear debe usar `git add -f`.
- `GitHub Pages` publica no oculta contenido; solo se protegen acciones sensibles con token + `environment` approvals.
