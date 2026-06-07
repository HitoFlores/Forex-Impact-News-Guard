# Deploy Oracle Always Free

Ruta recomendada para este proyecto si quieres mantener API + worker corriendo gratis 24/7 en una sola VM.

## Arquitectura

- 1 VM Oracle Always Free
- 2 contenedores Docker sobre misma VM:
  - `api`: FastAPI en puerto `8000`
  - `worker`: scheduler continuo
- 1 volumen local `.state/` para SQLite

## Archivos de deploy incluidos

- [Dockerfile](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/Dockerfile)
- [compose.yml](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/compose.yml)
- [deploy/oracle-always-free/run-on-vm.sh](/C:/Users/rullo/Documents/Proyectos%20IA/Forex-Impact-News-Guard/deploy/oracle-always-free/run-on-vm.sh)

## Recomendacion de VM

- Prioridad 1: `VM.Standard.A1.Flex`
  - mejor margen para correr API + worker juntos
- Fallback: `VM.Standard.E2.1.Micro`
  - usable, pero mucho mas justo en RAM/CPU

## Paso 1. Crear VM

En Oracle Cloud:

1. Crear instancia Always Free en tu `home region`.
2. Elegir Ubuntu 24.04 o Ubuntu 22.04.
3. Asignar IP publica.
4. Abrir al menos:
   - `22/tcp` para SSH
   - `8000/tcp` para API

## Paso 2. Instalar Docker en VM

Instala Docker Engine y Docker Compose plugin con metodo oficial de Docker o con paquetes de Ubuntu.

Verifica:

```bash
docker --version
docker compose version
```

## Paso 3. Subir repo y configurar entorno

```bash
git clone <tu_repo> forex-impact-news-guard
cd forex-impact-news-guard
mkdir -p .state
```

Crear `.env` con minimo:

```env
FOREX_GUARD_TELEGRAM_BOT_TOKEN=...
FOREX_GUARD_TELEGRAM_CHAT_ID=...
FOREX_GUARD_DEFAULT_TIMEZONE=America/Chihuahua
FOREX_GUARD_EVENTS_DB_PATH=/app/.state/forex_news_guard.db
FOREX_GUARD_SCHEDULER_SYNC_INTERVAL_MINUTES=30
FOREX_GUARD_SCHEDULER_TICK_SECONDS=30
```

Opcional pero recomendado si Forex Factory vuelve a endurecer acceso:

```env
FOREX_GUARD_FOREX_FACTORY_COOKIE=...
```

## Paso 4. Levantar stack

```bash
chmod +x deploy/oracle-always-free/run-on-vm.sh
./deploy/oracle-always-free/run-on-vm.sh
```

## Paso 5. Verificar

Salud API:

```bash
curl http://127.0.0.1:8000/health
curl http://TU_IP_PUBLICA:8000/health
```

Logs:

```bash
docker compose logs -f api
docker compose logs -f worker
```

Prueba real de Telegram:

```bash
docker compose exec api python -c "from forex_news_guard.services.telegram_smoke_test import send_telegram_smoke_test; print(send_telegram_smoke_test().model_dump_json())"
```

## Operacion basica

Actualizar:

```bash
git pull
docker compose up -d --build
```

Parar:

```bash
docker compose down
```

## Riesgos a recordar

- SQLite vive en `.state/`; respalda ese directorio si importa historial.
- Si Oracle marca VM como idle, puede reclamarla.
- Si publicas `8000` directo, no hay TLS. Sirve para empezar; despues puedes poner reverse proxy.
