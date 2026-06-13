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

### Alerta Telegram cuando el scraping falla repetidamente

El sistema registra fallos de scraping en `runtime.json` con contador de fallos consecutivos. `[inferencia]` Sin embargo, nadie actúa sobre ese contador: si Forex Factory bloquea o cambia estructura, el operador sólo lo descubre mirando el dashboard.

**Qué agregar:** cuando los fallos consecutivos de scraping superen un umbral configurable (ej. 3 ciclos), enviar un mensaje de alerta al canal Telegram del operador. Cierra el loop de observabilidad sin necesidad de infraestructura adicional.

---

### Limpieza periódica del historial de dispatches

El archivo `runtime.json` guarda cada mensaje enviado con su timestamp. `[inferencia]` No hay mecanismo de expiración: en uso continuo crece indefinidamente. Un sistema que lleva meses activo acumulará miles de registros irrelevantes.

**Qué agregar:** en cada ciclo del worker, descartar registros con más de N días (ej. 7). Operación simple; no requiere cambios de esquema.

---

### Pin de versión para `cloudscraper`

`cloudscraper` es la dependencia más crítica del sistema: sin ella no hay acceso a Forex Factory. `[inferencia]` Si no está fijada con rango estricto en `pyproject.toml`, una actualización automática puede romper la compatibilidad con Cloudflare sin aviso.

**Qué fijar:** versión mínima y máxima conocida como estable (`>=X.Y.Z,<X+1`).

---

## Mediano plazo
_Mejoras que amplían capacidades del producto o mejoran resiliencia operativa. Requieren diseño pero no cambian la arquitectura de fondo._

### Activar o descartar el canal de breaking news

`AlertPolicy.breaking_enabled` existe, `ForexFactoryClient` puede parsear breaking news, y los modelos de dominio ya soportan el tipo `is_breaking=True`. `[inferencia]` Sin embargo, el worker nunca invoca ese canal en producción: sólo aparece en la ruta de preview de la API local.

**Decidir:** integrar breaking news al ciclo productivo con su propia lógica de dispatch, o eliminarlo del código y del modelo para evitar confusión sobre qué está activo.

---

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

El ledger de dispatches ya tiene scroll interno. `[doc]` Pero el archivo `runtime.json` que alimenta el dashboard puede crecer mucho en periodos prolongados, aumentando el tiempo de carga y el tamaño del commit de estado.

Esto se resuelve combinando la limpieza periódica del historial (corto plazo) con un límite explícito de registros que `build_dashboard.py` incluye en el artefacto publicado.

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
| Fallo de scraping silencioso para el operador | Media | Alto: sin alertas, sin notificación |
| `runtime.json` muy grande ralentiza ciclos del worker | Baja a corto plazo, crece con el tiempo | Bajo-medio |
| Actualización de `cloudscraper` sin pin rompe scraping | Baja | Alto |
| Breaking news activo en config pero no en worker genera confusión en diagnóstico | Baja | Bajo |

---

## Próximos pasos recomendados

Ordenados por relación impacto / esfuerzo:

1. **Tests para mensajes Telegram** — mayor riesgo de regresión silenciosa, menor esfuerzo.
2. **Alerta de scraping fallido al operador** — cierra el loop de observabilidad con ~20 líneas de código.
3. **Limpieza de `runtime.json`** — previene problema de crecimiento antes de que sea visible.
4. **Pin de `cloudscraper`** — una línea en `pyproject.toml`; protege la dependencia más crítica.
5. **Decidir sobre breaking news** — activar o eliminar; el estado actual genera ambigüedad.
6. **Estados WARN en observabilidad** — mejora la legibilidad del dashboard en degradación parcial.
