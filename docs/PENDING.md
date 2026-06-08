# Pending

Sin pendientes activos al cierre de esta sesion.

## Riesgos tecnicos a recordar

- Forex Factory puede cambiar HTML/JS y romper parsing.
- `cloudscraper` hoy funciona, pero no es garantia eterna.
- GitHub `schedule` puede retrasarse y se desactiva en repos publicos sin actividad por 60 dias si no existe `keepalive`.
- `.state/` sigue ignorado por git; cualquier workflow que lo quiera commitear debe usar `git add -f`.
- `GitHub Pages` publica no oculta contenido; solo se protegen acciones sensibles con token + `environment` approvals.
