import asyncio
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import context

# Import app models
from app.db.session import Base
from app.core.config import settings

# Import all models so Alembic can detect them
from app.db.models.compania import Compania
from app.db.models.plans import Plan
from app.db.models.company_subscriptions import CompanySubscription
from app.db.models.company_usage import CompanyUsage
from app.db.models.overtime_requests import OvertimeRequest, OvertimeRequestEvent
from app.db.models.clientes import Cliente
from app.db.models.enums.tipos_documento import TipoDocumento
from app.db.models.enums.tipos_unidad import TipoUnidad
from app.db.models.enums.tipos_orden import TipoOrden
from app.db.models.enums.estados_orden import EstadoOrden
from app.db.models.enums.prioridades import Prioridad
from app.db.models.enums.tipos_evidencia import TipoEvidencia

# Import other models if they exist
try:
    from app.db.models.ordenes_de_trabajo import OrdenDeTrabajo
except ImportError:
    pass

try:
    from app.db.models.proyectos import Proyecto
except ImportError:
    pass

try:
    from app.db.models.unidades import Unidad
except ImportError:
    pass

try:
    from app.db.models.nivel_tecnico import NivelTecnico
except ImportError:
    pass

try:
    from app.db.models.usuarios import Usuario
except ImportError:
    pass

try:
    from app.db.models.zonas_geograficas import ZonaGeografica
except ImportError:
    pass

try:
    from app.db.models.evidencias_multimedia import EvidenciaMultimedia
except ImportError:
    pass

try:
    from app.db.models.checklists import Checklist
except ImportError:
    pass

try:
    from app.db.models.hojas_de_vida import HojaDeVida
except ImportError:
    pass

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url with the database URL from settings
config.set_main_option("sqlalchemy.url", str(settings.database_url))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online()) 
