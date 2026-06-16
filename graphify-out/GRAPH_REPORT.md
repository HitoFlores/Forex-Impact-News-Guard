# Graph Report - Forex-Impact-News-Guard  (2026-06-16)

## Corpus Check
- 82 files · ~34,556 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 678 nodes · 1762 edges · 50 communities (41 shown, 9 thin omitted)
- Extraction: 58% EXTRACTED · 42% INFERRED · 0% AMBIGUOUS · INFERRED: 744 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ed79795b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]

## God Nodes (most connected - your core abstractions)
1. `AlertPolicy` - 71 edges
2. `ForexEvent` - 67 edges
3. `RuntimeSchedulerService` - 60 edges
4. `ZoneInfo` - 56 edges
5. `ImpactLevel` - 52 edges
6. `EventRepository` - 46 edges
7. `EventSchedule` - 45 edges
8. `RuntimeRepository` - 44 edges
9. `$()` - 36 edges
10. `StoredEvent` - 34 edges

## Surprising Connections (you probably didn't know these)
- `test_events_endpoints_return_relevant_data()` --calls--> `ZoneInfo`  [INFERRED]
  tests/test_settings_and_events_api.py → src/forex_news_guard/domain/models.py
- `RuntimeSyncResult` --uses--> `RuntimeSyncResult`  [INFERRED]
  tests/test_worker.py → src/forex_news_guard/domain/runtime.py
- `test_forex_factory_live_preview_endpoint_handles_upstream_block()` --calls--> `ForexFactoryBlockedError`  [INFERRED]
  tests/test_app.py → src/forex_news_guard/integrations/forex_factory.py
- `test_live_preview_reports_blocked_source()` --calls--> `preview_live_alerts()`  [INFERRED]
  tests/test_forex_factory_integration.py → src/forex_news_guard/services/forex_factory_monitor.py
- `ImpactLevel` --uses--> `AlertPolicy`  [INFERRED]
  scripts/apply_dashboard_settings.py → src/forex_news_guard/domain/models.py

## Import Cycles
- 1-file cycle: `scripts/build_dashboard.py -> scripts/build_dashboard.py`
- 1-file cycle: `src/forex_news_guard/app.py -> src/forex_news_guard/app.py`
- 1-file cycle: `src/forex_news_guard/domain/models.py -> src/forex_news_guard/domain/models.py`
- 1-file cycle: `tests/test_runtime_scheduler.py -> tests/test_runtime_scheduler.py`
- 1-file cycle: `src/forex_news_guard/integrations/forex_factory.py -> src/forex_news_guard/integrations/forex_factory.py`
- 1-file cycle: `src/forex_news_guard/services/alert_planner.py -> src/forex_news_guard/services/alert_planner.py`
- 1-file cycle: `src/forex_news_guard/services/forex_factory_monitor.py -> src/forex_news_guard/services/forex_factory_monitor.py`
- 1-file cycle: `src/forex_news_guard/services/notification_formatter.py -> src/forex_news_guard/services/notification_formatter.py`
- 1-file cycle: `src/forex_news_guard/services/runtime_scheduler.py -> src/forex_news_guard/services/runtime_scheduler.py`
- 1-file cycle: `src/forex_news_guard/services/telegram_smoke_test.py -> src/forex_news_guard/services/telegram_smoke_test.py`
- 1-file cycle: `src/forex_news_guard/storage/event_repository.py -> src/forex_news_guard/storage/event_repository.py`
- 1-file cycle: `src/forex_news_guard/storage/runtime_repository.py -> src/forex_news_guard/storage/runtime_repository.py`

## Communities (50 total, 9 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.09
Nodes (49): AlertExecutionKind, EventSchedule, ScheduledEventCheck, StoredEvent, AlertDispatchRecord, AlertExecutionKind, DeliveryChannel, RuntimeObservability (+41 more)

### Community 1 - "Community 1"
Cohesion: 0.11
Nodes (40): RuntimeError, test_preview_builds_calendar_and_breaking_alerts(), test_preview_skips_non_high_impact_when_policy_requires_it(), Path, test_repository_cleanup_removes_old_rows_after_day_rollover(), test_repository_retains_only_today_and_tomorrow(), test_build_event_schedules_creates_precheck_alert_and_result_retries(), test_filter_relevant_events_keeps_breaking_news_with_news_currency() (+32 more)

### Community 2 - "Community 2"
Cohesion: 0.15
Nodes (31): BaseSettings, get_settings(), Settings, _coerce_datetime(), _coerce_int(), _extract_calendar_events_from_component_state(), _extract_text(), _first_non_empty() (+23 more)

### Community 3 - "Community 3"
Cohesion: 0.13
Nodes (32): date, NotificationMessage, MonkeyPatch, main(), build_daily_summary_message(), build_grouped_pre_alert_message(), build_grouped_result_message(), build_pre_alert_message() (+24 more)

### Community 5 - "Community 5"
Cohesion: 0.10
Nodes (28): $(), bindActions(), buildDemoState(), collectSettingsInputs(), copySettingsPayload(), DEFAULT_STATE, dispatchWorkflow(), escapeHtml() (+20 more)

### Community 6 - "Community 6"
Cohesion: 0.16
Nodes (6): SettingsRepository, AlertPolicy, AlertPolicy, SettingsRepository, Path, test_settings_service_persists_policy()

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (9): FastAPI, create_app(), get_relevant_events(), get_upcoming_schedules(), get_settings(), update_settings(), AlertPolicy, test_forex_factory_live_preview_endpoint_handles_upstream_block() (+1 more)

### Community 8 - "Community 8"
Cohesion: 0.32
Nodes (12): build_automation_summary(), build_dashboard_payload(), build_observability_diagnostics(), build_risk_blocks(), build_workflow_meta(), impact_rank(), load_json(), main() (+4 more)

### Community 9 - "Community 9"
Cohesion: 0.13
Nodes (11): run_worker_continuous(), _wait_forever(), run_worker(), sync-and-publish Workflow, Static Dashboard, .state/ JSON Files, FakeContinuousSchedulerService, FakeSchedulerService (+3 more)

### Community 10 - "Community 10"
Cohesion: 0.09
Nodes (51): AlertPreviewRequest, BaseModel, AlertKind, AlertPolicy, AlertPreviewRequest, AlertPreviewResponse, ForexEvent, ImpactLevel (+43 more)

### Community 11 - "Community 11"
Cohesion: 0.48
Nodes (6): Path, _sandbox_tmp_dir(), test_build_policy_from_env_defaults_to_all_impacts_when_not_high_only(), test_build_policy_from_env_parses_dashboard_inputs(), test_build_policy_from_env_rejects_empty_currency_list_when_not_all(), test_build_policy_from_env_uses_empty_currencies_for_all_currencies()

### Community 12 - "Community 12"
Cohesion: 0.36
Nodes (9): build_policy_from_env(), load_existing_policy(), main(), _parse_bool(), _parse_csv(), _parse_impacts(), _parse_int(), AlertPolicy (+1 more)

### Community 24 - "Community 24"
Cohesion: 0.08
Nodes (23): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+15 more)

### Community 25 - "Community 25"
Cohesion: 0.09
Nodes (21): Alta prioridad, API local `[código]`, Baja prioridad / largo plazo, Configuracion productiva actual, Control de calidad de alertas `[código]`, CURRENT STATUS, Dashboard `[doc]`, Documentados explícitamente `[doc]` (+13 more)

### Community 26 - "Community 26"
Cohesion: 0.12
Nodes (15): Autenticación de lectura para el dashboard, Canal de notificaciones adicional (Web Push / email), Corto plazo, Documentados `[doc]`, Estados de salud intermedios (WARN), Gaps de cobertura de tests, Inferidos del código `[inferencia]`, Largo plazo (+7 more)

### Community 27 - "Community 27"
Cohesion: 0.11
Nodes (18): API (FastAPI), ARCHITECTURE, Componentes principales, Configuración en dos capas, Dashboard (GitHub Pages), Decisiones de diseño relevantes, Dependencias importantes, EventScheduler / AlertPlanner (+10 more)

### Community 28 - "Community 28"
Cohesion: 0.12
Nodes (15): Antes, Arquitectura objetivo, Cambio de arquitectura esperado, Deploy Plan: GitHub Actions + Pages, Despues, Flujo objetivo, Implementacion local ya montada, Keepalive (+7 more)

### Community 29 - "Community 29"
Cohesion: 0.14
Nodes (13): Deploy gratis recomendado, Documentacion de handoff, Ejecutar localmente, Endpoints, Estado actual, Estructura, Flujo pensado, Forex-Impact-News-Guard (+5 more)

### Community 30 - "Community 30"
Cohesion: 0.13
Nodes (14): Archivos locales importantes, Auth de lectura del dashboard, Ejemplo rapido para actualizar settings, Endpoints utiles, Instalar, Levantar API, Levantar worker, Nota de transicion (+6 more)

### Community 31 - "Community 31"
Cohesion: 0.17
Nodes (11): Archivos de deploy incluidos, Arquitectura, Deploy Oracle Always Free, Operacion basica, Paso 1. Crear VM, Paso 2. Instalar Docker en VM, Paso 3. Subir repo y configurar entorno, Paso 4. Levantar stack (+3 more)

### Community 32 - "Community 32"
Cohesion: 0.36
Nodes (3): datetime, ForexEvent, StoredEvent

### Community 33 - "Community 33"
Cohesion: 0.20
Nodes (9): Antes de cualquier deploy, Configuracion clave para ruta GitHub, Deploy Recommendations, GitHub Actions + GitHub Pages, Modo de ejecucion remoto elegido, Oracle Cloud Always Free, Plataformas evaluadas, Render (+1 more)

### Community 34 - "Community 34"
Cohesion: 0.20
Nodes (9): Dependencias importantes, Estado actual del proyecto, Flujo general del sistema, Funcionalidades principales, Navegación, OVERVIEW, Problema que resuelve, Qué es (+1 more)

### Community 35 - "Community 35"
Cohesion: 0.22
Nodes (8): Configuracion actual del producto, Decisiones clave, Direccion de deploy decidida, Flujo actual, Limitaciones actuales, Lo que ya funciona, Objetivo real, Project Context

### Community 36 - "Community 36"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 37 - "Community 37"
Cohesion: 0.25
Nodes (7): Estado conceptual, Estado real de la ultima sesion, Git Handoff, Lo que deberia entrar a git, Lo que no deberia entrar a git manualmente, Rama actual, Sugerencia cuando retomes git

### Community 38 - "Community 38"
Cohesion: 0.33
Nodes (5): Documentación, Estado, Forex Impact News Guard, Propósito, Tecnologías

### Community 39 - "Community 39"
Cohesion: 0.40
Nodes (4): Codigo clave, Nota importante, Start Here, Ultimo estado

### Community 40 - "Community 40"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 41 - "Community 41"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 42 - "Community 42"
Cohesion: 0.50
Nodes (3): For /graphify explain, For /graphify path, graphify reference: query, path, explain

### Community 43 - "Community 43"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 44 - "Community 44"
Cohesion: 0.50
Nodes (3): Mejoras cerradas recientemente, Pending, Riesgos tecnicos a recordar

### Community 49 - "Community 49"
Cohesion: 0.40
Nodes (4): Forex Factory time parsing, GitHub Actions timing, Lessons Learned, Result updates

## Knowledge Gaps
- **174 isolated node(s):** `run-on-vm.sh script`, `DEFAULT_STATE`, `TIMEZONE_OPTIONS`, `Path`, `Usage` (+169 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AlertPolicy` connect `Community 10` to `Community 0`, `Community 1`, `Community 4`, `Community 6`, `Community 7`, `Community 8`, `Community 12`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `ZoneInfo` connect `Community 1` to `Community 2`, `Community 3`, `Community 4`, `Community 7`, `Community 8`, `Community 9`, `Community 10`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `ImpactLevel` connect `Community 10` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 6`, `Community 12`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 61 inferred relationships involving `AlertPolicy` (e.g. with `AlertPreviewRequest` and `RuntimeProbeState`) actually correct?**
  _`AlertPolicy` has 61 INFERRED edges - model-reasoned connections that need verification._
- **Are the 65 inferred relationships involving `ForexEvent` (e.g. with `date` and `ForexFactoryBlockedError`) actually correct?**
  _`ForexEvent` has 65 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `RuntimeSchedulerService` (e.g. with `run_worker()` and `AlertPolicy`) actually correct?**
  _`RuntimeSchedulerService` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 42 inferred relationships involving `ZoneInfo` (e.g. with `test_preview_builds_calendar_and_breaking_alerts()` and `test_preview_skips_non_high_impact_when_policy_requires_it()`) actually correct?**
  _`ZoneInfo` has 42 INFERRED edges - model-reasoned connections that need verification._