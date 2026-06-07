# Git Handoff

## Rama actual

- `feature/bootstrap`

## Estado conceptual

El repositorio fue reiniciado y reconstruido desde un scaffold roto hacia una base funcional nueva.

## Estado real de la ultima sesion

- La migracion a `GitHub Actions + GitHub Pages` ya existe en codigo.
- `public/app.js` ya tolera falta de `state.json` usando `public/state.example.json`.
- El workflow de `sync-and-publish` fallo en `main` porque `git add .state` choca con `.gitignore`.
- Fix necesario: usar `git add -f .state` en `.github/workflows/cron.yml` y `git add -f .state/keepalive.json` en `.github/workflows/keepalive.yml`.
- Pendiente inmediato: llevar ese fix a `main`, push, y relanzar `sync-and-publish`.

## Lo que deberia entrar a git

- `README.md`
- `pyproject.toml`
- `src/`
- `tests/`
- `docs/`
- `.gitignore`

## Lo que no deberia entrar a git

- `.env`
- `.state/`
- `.pytest_cache/`
- `__pycache__/`
- `*.egg-info/`

## Sugerencia cuando retomes git

1. Revisar `git status`
2. Confirmar que `.env` y `.state` no esten staged
3. Confirmar que el fix de workflows esta en `main`
4. Hacer commit del estado actual
5. Push a remoto cuando ya tengas token de Telegram rotado
