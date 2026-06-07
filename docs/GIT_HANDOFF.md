# Git Handoff

## Rama actual

- `main`

## Estado conceptual

El repositorio fue reiniciado y reconstruido desde un scaffold roto hacia una base funcional nueva.

## Estado real de la ultima sesion

- `GitHub Actions + GitHub Pages` ya quedo operando en `main`.
- `sync-and-publish` ya corre, persiste `.state/` con `git add -f`, y Pages ya publica dashboard.
- `keepalive` ya se corrio manual y paso en verde, generando commit automatico.
- Se agrego workflow manual `telegram-smoke-test` para forzar desde GitHub el envio real de todos los mensajes sample.
- Se agrego script `scripts/send_telegram_smoke_test.py` y se probo localmente con envio real de 5 mensajes a Telegram.
- El dashboard fue rehecho para mostrar salud del cron, proxima alerta/evento, keepalive, policy y ledger reciente.
- Pendiente inmediato para manana: correr `sync-and-publish` manual sobre `main` para publicar nuevo dashboard y luego correr `telegram-smoke-test` manual desde GitHub para validar flujo 100% remoto.

## Lo que deberia entrar a git

- `README.md`
- `pyproject.toml`
- `src/`
- `tests/`
- `docs/`
- `.gitignore`

## Lo que no deberia entrar a git manualmente

- `.env`
- `.pytest_cache/`
- `__pycache__/`
- `*.egg-info/`

Nota:

- `.state/` sigue ignorado para trabajo manual/local.
- Los workflows si lo commitean a proposito usando `git add -f` para persistir estado remoto.

## Sugerencia cuando retomes git

1. Revisar `git status`
2. Confirmar que `.env` no este staged
3. Correr `sync-and-publish` manual en GitHub para desplegar dashboard nuevo
4. Abrir Pages y confirmar que UI nueva ya quedo publicada
5. Correr `telegram-smoke-test` manual en GitHub sobre `main`
6. Confirmar recepcion en Telegram y, si hace falta, volver a correr `sync-and-publish`
