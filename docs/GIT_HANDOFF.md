# Git Handoff

## Rama actual

- `feature/bootstrap`

## Estado conceptual

El repositorio fue reiniciado y reconstruido desde un scaffold roto hacia una base funcional nueva.

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
3. Hacer commit del estado actual
4. Push a remoto cuando ya tengas token de Telegram rotado
