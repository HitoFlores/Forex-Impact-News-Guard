# Deploy Plan: GitHub Actions + Pages

Ruta elegida para publicar proyecto con costo `0`, sin depender de capacidad de VMs gratis.

## Motivo del cambio

Intento en Oracle Always Free bloqueado por capacidad en `mx-monterrey-1` para `VM.Standard.A1.Flex`, y en esta cuenta/region no aparecio `VM.Standard.E2.1.Micro` como fallback usable.

Conclusion: no conviene seguir apostando deploy a disponibilidad de VM gratuita.

## Arquitectura objetivo

- `GitHub Actions` como scheduler
- `GitHub Pages` como dashboard publico
- `Telegram` como canal real de alertas
- estado persistido en JSON dentro de `.state/`

## Cambio de arquitectura esperado

### Antes

- API FastAPI viva
- worker continuo
- SQLite local
- VM/contenedor remoto

### Despues

- job `run_once` ejecutado por cron en GitHub Actions
- dashboard estatico publicado en GitHub Pages
- persistencia en archivos JSON
- sin proceso continuo 24/7 en servidor propio

## Flujo objetivo

1. Workflow principal corre cada 5 minutos.
2. Descarga calendario de Forex Factory con Python + `cloudscraper`.
3. Lee estado previo desde JSON.
4. Calcula alertas vencidas y evita duplicados.
5. Manda Telegram.
6. Actualiza JSON de estado y resumen.
7. Publica o actualiza dashboard en GitHub Pages.

## Keepalive

GitHub desactiva `scheduled workflows` en repos publicos sin actividad de repo por 60 dias.

Para evitarlo:

- crear workflow `keepalive` mensual;
- el workflow actualiza un archivo minimo, por ejemplo `meta/keepalive.json`;
- hace commit con mensaje `chore: keepalive [skip ci]`;
- el workflow `keepalive` no debe escuchar `push`, solo `schedule` y `workflow_dispatch`.

Esto evita loop infinito porque su propio commit no dispara el mismo workflow.

## Limitaciones aceptadas

- cron minimo de GitHub: 5 minutos
- los schedules pueden retrasarse en horas pico
- el repo probablemente debe quedar publico para mantener costo `0`
- la primera version publicada ya no sera una API always-on; sera dashboard + workflows + Telegram

## Tareas de implementacion

### Prioridad alta

- refactorizar worker a `run_once`
- reemplazar SQLite por estado JSON compatible con GitHub Actions
- crear workflow de chequeo programado
- crear workflow de keepalive mensual
- crear dashboard estatico para GitHub Pages
- preparar publicacion automatica de Pages

## Implementacion local ya montada

- `src/forex_news_guard/worker.py` corre una sola vez.
- `src/forex_news_guard/storage/*.py` usan JSON atomico.
- `.github/workflows/cron.yml` sincroniza, publica y persiste estado.
- `.github/workflows/keepalive.yml` toca `.state/keepalive.json`.
- `public/` contiene dashboard estatico para Pages.

### Prioridad media

- agregar resumen visible de ultimos envios
- exponer ultimos eventos y proximo bloque de riesgo en dashboard
- mejorar trazas de error para fallos de scraping y Telegram

## Referencias operativas

- GitHub schedule corre solo en branch por defecto
- repos publicos pueden perder el schedule tras 60 dias sin actividad
- Pages sirve bien como salida publica estatica del proyecto
