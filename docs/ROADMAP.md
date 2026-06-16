# ROADMAP

> **Convenciones:**
> `[doc]` = extraído de documentación existente | `[inferencia]` = derivado del código, no documentado explícitamente
> Las estimaciones de plazo son orientativas; el proyecto es unipersonal y sin fechas comprometidas.

---

## Corto plazo
_Mejoras que añaden valor inmediato con esfuerzo bajo. No cambian la arquitectura._

### Gaps de cobertura de tests

Las funciones que construyen los mensajes de Telegram (resumen diario, alerta individual, alerta agrupada, resultado, resultado agrupado) no tienen tests unitarios propios. `[inferencia]` Son la interfaz directa con el usuario: un cambio de formato silencioso pasa desapercibido hasta que el operador lo nota en Telegram.

**Qué agregar:** tests que verifiquen el texto y estructura HTML de cada tipo de mensaje ante escenarios clave (sin forecast, sin resultado, moneda con bandera conocida, evento sin hora).

---

## Mediano plazo
_Mejoras que amplían capacidades del producto o mejoran resiliencia operativa. Requieren diseño pero no cambian la arquitectura de fondo._

### Estados de salud intermedios (WARN)

El sistema tiene `RuntimeProbeStatus.WARN` definido en el modelo de observabilidad pero ningún código lo emite. `[inferencia]` El estado salta directamente de OK a ERROR. Esto hace que el dashboard muestre verde hasta el momento del fallo total, sin señal de degradación progresiva.

**Qué agregar:** emitir WARN tras 1-2 fallos consecutivos antes de pasar a ERROR. Permite al operador actuar antes de perder alertas reales.

---

### Mejora de la resiliencia al parsing de Forex Factory

Hoy el sistema tiene dos estrategias de parsing (JSON embebido en `window.calendarComponentStates` + fallback HTML con BeautifulSoup). `[doc]` Pero si ambas fallan a la vez (cambio estructural profundo), el sistema falla en silencio.

**Qué añadir:**
- Test de smoke del parsing en cada deploy, contra HTML real archivado como fixture.
- Notificación explícita al operador cuando `ForexFactoryParseError` ocurre, separada del fallo genérico de scraping.

---

### Limitar crecimiento del dashboard en periodos largos

El ledger de dispatches ya tiene scroll interno y `runtime.json` poda dispatches antiguos con `FOREX_GUARD_RUNTIME_DISPATCH_TTL_DAYS`. `[doc]` Aun así, el dashboard publicado puede necesitar un límite explícito de registros renderizados si se quiere mantener el artefacto muy pequeño.

**Qué agregar:** un límite explícito de registros que `build_dashboard.py` incluye en el artefacto publicado.

---

## Largo plazo
_Cambios estructurales que amplían el alcance del producto o cambian la infraestructura base. Alto esfuerzo; sólo justificados si el uso lo demanda._

### Worker continuo para precisión sub-minuto

GitHub Actions cron no garantiza ejecución exacta al segundo. `[doc]` Para la mayoría de noticias de alto impacto, una precisión de ±1-2 minutos es suficiente. Pero en cuentas fondeadas con reglas estrictas de ventana de noticias, el margen importa.

El modo de worker continuo (`BackgroundScheduler`) ya está implementado en el código pero no está validado en producción. `[inferencia]` Requiere infraestructura con uptime real (VPS, contenedor, cualquier host que no sea serverless). Oracle Always Free fue el primer intento y falló por capacidad en la región disponible. `[doc]`

**Cuándo considerar:** si el operador reporta alertas llegando sistemáticamente tarde en días de alta carga de GH Actions.

---

### Canal de notificaciones adicional (Web Push / email)

El README menciona Web Push como idea para "siguientes iteraciones". `[doc]` El modelo de dominio sólo tiene `DeliveryChannel.TELEGRAM`. `[inferencia]`

Web Push requiere un service worker en el dashboard y un servidor de push; añade complejidad de infraestructura significativa. Email es más simple pero menos útil para alertas de tiempo real.

**Cuándo considerar:** si el operador necesita recibir alertas en contextos donde Telegram no está disponible o no es deseable.

---

### Autenticación de lectura para el dashboard

El dashboard publicado en GitHub Pages es completamente público. `[doc]` Las acciones están protegidas por token y el environment `ops-control`, pero el estado operativo (próximas noticias, ventanas de riesgo, timing de alertas) es visible para cualquiera con la URL.

Mientras el uso sea personal esto no es un problema. Si se comparte con un equipo o si la información de la política de trading se considera sensible, mover la UI a una superficie con auth real (Cloudflare Access, GitHub Pages privado con GitHub Pro, cualquier host con auth básica).

---

## Riesgos actuales

### Documentados `[doc]`

| Riesgo | Probabilidad | Impacto |
|---|---|---|
| Forex Factory cambia HTML/JS sin previo aviso | Media (ocurre ~1-2x/año en sitios similares) | Alto: sin alertas hasta que se repare |
| `cloudscraper` incompatible con nueva versión de Cloudflare | Baja-media | Alto: mismo impacto que arriba |
| GitHub desactiva schedule por 60 días de inactividad | Baja (hay keepalive) | Alto si falla keepalive |
| GitHub cron se ejecuta con retraso >5 min | Media en periodos de alta carga de GH | Medio: alertas stale descartadas (comportamiento correcto) |

### Inferidos del código `[inferencia]`

| Riesgo | Probabilidad | Impacto |
|---|---|---|
| Fallo de scraping silencioso para el operador | Baja | Mitigado con alerta Telegram al alcanzar el umbral de fallos consecutivos |
| `runtime.json` muy grande ralentiza ciclos del worker | Baja | Mitigado con poda por TTL de dispatches antiguos |
| Breaking news de Forex Factory usa `currency=NEWS` | Baja | Mitigado: los eventos `is_breaking=True` saltan el filtro de moneda y siguen respetando impacto |

---

## Próximos pasos recomendados

Ordenados por relación impacto / esfuerzo:

1. **Completar tests para mensajes Telegram** — mayor riesgo de regresión silenciosa; parte de la cobertura se valida día a día con escenarios reales.
2. **Estados WARN en observabilidad** — mejora la legibilidad del dashboard en degradación parcial.
3. **Límite de registros renderizados en dashboard** — mantiene pequeño el artefacto publicado si el historial operativo crece.
