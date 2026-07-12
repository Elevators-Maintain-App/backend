# Aislamiento de base de datos para pruebas

Las pruebas de pytest no deben ejecutarse dentro del servicio normal `api`.
Ese servicio carga `.env`, y `.env` puede contener una `DATABASE_URL` remota o de producción.
Ejecutar `docker-compose exec api pytest` está prohibido porque puede insertar, actualizar o borrar datos reales.

## Infraestructura segura

Levanta la infraestructura exclusiva para pruebas:

```bash
docker compose -f docker-compose.test.yml up -d --build
```

Inicializa el esquema de pruebas. La cadena histórica de Alembic no puede crear una base vacía: la revisión inicial `d123c967f10f` inserta países y presupone tablas ya existentes. Temporalmente, solo en `db-test`, el bootstrap seguro usa `Base.metadata.create_all` para crear el esquema actual y luego registra la revisión esperada con `alembic stamp`.

```bash
docker compose -f docker-compose.test.yml exec -T api-test python scripts/bootstrap_test_database.py
docker compose -f docker-compose.test.yml exec -T api-test alembic stamp 7b8d4f2c1a90
docker compose -f docker-compose.test.yml exec -T api-test alembic current
```

No ejecutes `alembic upgrade head` sobre una base vacía en el entorno de tests hasta que exista una baseline Alembic completa. Crear esa baseline queda como deuda técnica separada. El uso de `create_all + stamp` está prohibido en producción y solo es válido dentro de la base efímera `db-test`.

Ejecuta pruebas dentro de `api-test`:

```bash
docker compose -f docker-compose.test.yml exec -T api-test python -m pytest tests/test_database_safety.py -v --no-cov
```

Ejemplo para un subconjunto:

```bash
docker compose -f docker-compose.test.yml exec -T api-test python -m pytest tests/test_api/test_plans/test_subscription_endpoints.py -q --tb=short --no-cov
```

Baja la infraestructura:

```bash
docker compose -f docker-compose.test.yml down
```

No uses `down -v` salvo que sea necesario. El PostgreSQL de pruebas usa `tmpfs` en `/var/lib/postgresql/data`, así que los datos se eliminan al detener el servicio.

## Protecciones automáticas

`api-test` define explícitamente:

- `ENVIRONMENT=test`
- `DATABASE_URL=postgresql+asyncpg://vertione_test_user:...@db-test:5432/vertione_test`

La guardia automática aborta pytest si:

- `ENVIRONMENT` no es exactamente `test`;
- `DATABASE_URL` está ausente o es inválida;
- el host no es `db-test`, `localhost` o `127.0.0.1`;
- el nombre de la base no contiene `test`.

La guardia no imprime contraseñas ni la URL completa. También se ejecuta desde `app/db/session.py` cuando `ENVIRONMENT=test`, antes de crear el engine.

El script `scripts/bootstrap_test_database.py` ejecuta la misma guardia antes de crear el esquema, importa los modelos para poblar `Base.metadata`, no hace `drop_all` y no inserta datos.

## Bases prohibidas

Nunca uses bases remotas para pytest, incluyendo Heroku, Cloud SQL, RDS u otros hosts externos. La única base permitida para pruebas de integración es PostgreSQL local/efímero de `docker-compose.test.yml`.
