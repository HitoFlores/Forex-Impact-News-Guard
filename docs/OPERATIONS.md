# Operations

## Requisitos

- Python 3.12
- `.env` con credenciales

## Instalar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

## Levantar API

```bash
uvicorn forex_news_guard.main:app --reload
```

Abrir:

- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Levantar worker

En otra terminal:

```bash
python -m forex_news_guard.worker
```

## Endpoints utiles

- `GET /health`
- `GET /api/v1/settings`
- `PUT /api/v1/settings`
- `GET /api/v1/events/relevant`
- `GET /api/v1/events/schedules/upcoming`
- `POST /api/v1/alerts/preview`
- `POST /api/v1/alerts/forex-factory/live-preview`

## Ejemplo rapido para actualizar settings

En Swagger `/docs` es lo mas sencillo.

Payload base:

```json
{
  "calendar_enabled": true,
  "breaking_enabled": true,
  "high_impact_only": true,
  "allowed_impacts": ["high"],
  "currencies": [],
  "lead_minutes": 5,
  "revalidate_minutes_before_alert": 2,
  "result_check_delay_minutes": 1,
  "result_retry_minutes": [3, 5],
  "include_results": true,
  "daily_summary_enabled": true,
  "risk_window_before_minutes": 15,
  "risk_window_after_minutes": 15,
  "timezone": "America/Chihuahua"
}
```

## Archivos locales importantes

- `.env`: secretos locales
- `.state/forex_news_guard.db`: SQLite local de trabajo

Ambos deben quedarse fuera de git.
