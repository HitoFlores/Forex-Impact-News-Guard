# Deploy Recommendations

La ruta activa ya no es Oracle como principal.

## Antes de cualquier deploy

1. Rotar `TELEGRAM_BOT_TOKEN`.
2. No subir `.env`.
3. No subir `.state`.
4. Verificar que el provider elegido siga dentro de costo `0`.

## Plataformas evaluadas

### GitHub Actions + GitHub Pages

Ruta principal elegida ahora.

- costo `0`
- publicado sin depender de VMs gratis con capacidad variable
- compatible con scraping actual en Python
- requiere migrar a `run_once` + estado JSON + dashboard estatico

Ver guia concreta:

- [docs/DEPLOY_GITHUB_ACTIONS_PAGES.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/docs/DEPLOY_GITHUB_ACTIONS_PAGES.md)

### Oracle Cloud Always Free

Queda como fallback documentado, no como ruta activa.

- intento real fallido por capacidad de `A1.Flex` en `mx-monterrey-1`
- `E2.1.Micro` no aparecio disponible en esta cuenta/region durante el intento
- se conserva documentacion por si en el futuro vuelve a ser viable

- [docs/DEPLOY_ORACLE_ALWAYS_FREE.md](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/docs/DEPLOY_ORACLE_ALWAYS_FREE.md)

### Render

Solo util como preview o demo corta del API.

- no es buena ruta principal si quieres worker continuo gratis
- filesystem free es efimero
- SQLite local no sobrevive redeploy/spin-down

## Modo de ejecucion remoto elegido

- GitHub Actions como scheduler
- GitHub Pages como salida publica
- Telegram como canal operativo

## Configuracion clave para ruta GitHub

- `FOREX_GUARD_TELEGRAM_BOT_TOKEN`
- `FOREX_GUARD_TELEGRAM_CHAT_ID`
- timezone de operacion
- archivos JSON de estado
- workflow cron
- workflow `keepalive`

## Validacion post-deploy

1. Confirmar que workflow programado corre.
2. Confirmar que puede consultar Forex Factory.
3. Confirmar smoke test real de Telegram.
4. Confirmar que se actualiza el JSON de estado.
5. Confirmar que Pages publica el dashboard.
6. Confirmar que existe keepalive mensual.
