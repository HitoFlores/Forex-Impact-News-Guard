# OVERVIEW

## Navegación  
- [[PROJECT]]
## Qué es

Forex-Impact-News-Guard es un sistema de vigilancia de calendario económico que monitorea Forex Factory y envía alertas por Telegram antes y después de noticias de alto impacto. El producto tiene dos superficies: un worker que corre en GitHub Actions y un dashboard estático publicado en GitHub Pages desde donde el operador controla el sistema sin necesidad de infraestructura propia.

## Problema que resuelve

Los traders y cuentas fondeadas deben detener operativa durante ventanas de noticias de alto impacto para evitar invalidación o pérdidas. Hacerlo manualmente requiere estar pendiente del calendario en todo momento. Este sistema automatiza la vigilancia: avisa con anticipación configurable cuándo pausar, revalida el evento justo antes de alertar, y consulta el resultado después del release.

Adicionalmente, Forex Factory bloquea acceso automatizado a sus endpoints estructurados (`calendar/json`, `csv`, `rss`) via Cloudflare. El sistema resuelve esto con un cliente HTTP compatible con Cloudflare que consume HTML directamente sin automatización de navegador.

## Usuario objetivo

Trader individual (o equipo pequeño) que opera cuentas propias o fondeadas en mercados de divisas y necesita gestionar riesgo de noticias sin monitoreo manual constante. El operador no requiere infraestructura propia ni conocimientos de DevOps más allá de configurar GitHub y un bot de Telegram.

## Funcionalidades principales

- **Vigilancia de calendario:** sincroniza Forex Factory periódicamente y filtra eventos por impacto y moneda configurados por el usuario.
- **Alertas pre-noticia:** avisa N minutos antes del evento con una ventana de tolerancia estricta para no enviar avisos tardíos o engañosos.
- **Revalidación antes del envío:** verifica que el evento no se haya movido justo antes de alertar; si cambió, recalcula horarios.
- **Consulta de resultados:** después del release, consulta el resultado del evento y lo reporta por Telegram sólo cuando `Actual` trae un valor real; si sigue en `N/D`, no envía mensajes vacíos ni triples.
- **Resumen diario:** envía una vez por día un resumen de los eventos relevantes del día actual, sólo dentro de la ventana `00:00`-`00:30` local; si hay eventos de alto impacto mañana, agrega una nota corta sin listarlos como si fueran de hoy.
- **Dashboard operativo:** interfaz estática con estado de salud del sistema, próximas ventanas de riesgo, ledger de últimos dispatches y controles para disparar acciones remotas (smoke test, sync, settings básicos).
- **Control remoto desde dashboard:** el operador puede cambiar settings básicos, forzar un sync y hacer smoke test de Telegram directamente desde el dashboard sin acceso a terminal.
- **Timezone configurable:** el dashboard expone un selector IANA para cambiar `AlertPolicy.timezone`, con `America/Chihuahua` como valor actual por default.

## Flujo general del sistema

```
GitHub Actions cron (cada ~5 min)
  └─► worker run_once
        ├─► lee settings desde JSON (.state/)
        ├─► sincroniza Forex Factory (cloudscraper + HTML parsing; timeLabel visible antes que dateline)
        ├─► filtra eventos relevantes → guarda hoy y mañana en .state/
        ├─► calcula timestamps: precheck / alert / result-check por evento
        ├─► resumen diario (00:00-00:30 local) → Telegram
        ├─► precheck: revalida evento antes de alertar
        ├─► alert: envía aviso si está dentro de ventana estricta → Telegram
        └─► result-check: consulta resultado con reintentos; envia sólo si Actual es real → Telegram

GitHub Actions publica .state/ con git add -f
  └─► GitHub Pages sirve dashboard estático
        └─► dashboard lee .state/ para mostrar estado live
              └─► botones disparan workflows vía GitHub API
```

## Dependencias importantes

| Área | Tecnología |
|------|-----------|
| Backend / worker | Python 3.12, FastAPI |
| Acceso a Forex Factory | `cloudscraper` (esquiva Cloudflare sin browser automation) |
| Notificaciones | Telegram Bot API |
| Persistencia | JSON plano en `.state/` (commiteado por el workflow) |
| Ejecución programada | GitHub Actions (cron) |
| Dashboard | GitHub Pages (HTML/JS estático, sin framework) |
| Deploy remoto | GitHub Actions + GitHub Pages (100% gratuito) |
| Seguridad operativa | GitHub Environment `ops-control` para workflows sensibles |

## Estado actual del proyecto

El sistema está operativo en producción sobre GitHub Actions + GitHub Pages en la rama `main`. Los flujos principales están validados:

- `sync-and-publish` corre en cron, persiste estado y publica dashboard.
- `keepalive` evita que GitHub desactive schedules por inactividad (60 días).
- `telegram-smoke-test` permite validar el canal Telegram remotamente sin levantar API local.
- `dashboard-control` permite modificar settings básicos desde el dashboard.
- Alertas y resultados funcionan con lógica de ventana estricta y deduplicación.

**Limitaciones conocidas al momento de esta documentación:**

- GitHub Actions cron no garantiza ejecución exacta al segundo; alertas sub-minuto precisas requieren worker continuo en infraestructura propia.
- El dashboard publicado en GitHub Pages es público; no tiene autenticación de lectura. Las acciones están protegidas por token y el environment `ops-control`, pero el contenido del estado es visible para cualquiera con la URL.
- La observabilidad y el manejo de fallas upstream (Forex Factory down, parsing roto) es básico; hay margen de mejora en alertas de error y recovery automático.
