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
- `telegram-smoke-test` ya fue validado desde GitHub Actions con exito.
- El dashboard fue rehecho y publicado con:
  - salud del cron;
  - proxima alerta/evento;
  - keepalive;
  - policy y ledger reciente;
  - modo `Live / Demo`;
  - ayuda inline con `?`;
  - `Smoke Telegram`;
  - `Sync + Publish`;
  - `Settings basicos` via workflow;
  - bloque de seguridad;
  - ledger de ultimos dispatches con scroll interno para evitar crecimiento infinito de la pantalla.
- Se agrego `scripts/apply_dashboard_settings.py`.
- Se agrego workflow `.github/workflows/dashboard-control.yml`.
- Los workflows sensibles ya usan environment `ops-control` para approval si se configura reviewer en GitHub.
- El ledger de ultimos dispatches ya no crece la pantalla indefinidamente; conserva counters visibles y desplaza solo el historial reciente.

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
3. Abrir Pages y confirmar que siga en `Live`
4. Confirmar que `ops-control` exista y tenga reviewers si se quiere approval manual
5. Si vas a tocar UI, validar desktop/mobile para que los paneles largos mantengan scroll interno donde aplique
6. Si se requiere validar flujo real, correr `telegram-smoke-test` y luego revisar approval/resultado en GitHub Actions
