# Estado actual del proyecto

> Última actualización: 12 de julio de 2026.
>
> Este documento debe actualizarse al cerrar cada sesión relevante. Debe reflejar únicamente estados comprobados mediante Git, código, migraciones, pruebas o validación manual.

## Resumen

VertiOne está compuesto por:

* una API FastAPI ubicada en `app/`;
* un frontend web Next.js ubicado en `apps/web/`;
* una aplicación mobile React Native mantenida en un repositorio independiente.

El backend se despliega en Google Cloud Run. El frontend web se configura y despliega de forma independiente en Vercel. La aplicación mobile consume los contratos protegidos de la API.

## Estado Git validado

* Rama base: `main`.
* Commit actual: `a8ed5b5`.
* `main` local sincronizada con `origin/main`.
* No se identificaron commits remotos pendientes al momento de la revisión.
* Los únicos cambios locales observados corresponden a la actualización de instrucciones y documentación de trabajo asistido por IA.

## Estado del backend

* FastAPI con arquitectura organizada mediante rutas, servicios, repositorios, modelos y schemas.
* SQLAlchemy async con PostgreSQL.
* Migraciones administradas mediante Alembic.
* Autenticación con Firebase.
* Autorización basada en roles y compañía.
* Base de datos aislada para pruebas mediante `docker-compose.test.yml`.
* Guardas automáticas que impiden ejecutar pytest contra una base no autorizada.
* Generación de reportes mediante Jinja2 y WeasyPrint.
* Contratos compartidos con frontend web y aplicación mobile.

### Migraciones

Las migraciones recientes incluyen:

* planes, suscripciones y uso;
* eventos de generación de reportes PDF;
* solicitudes de horas extra;
* corrección de referencias de clientes con UUID.

La cabeza efectiva del grafo debe confirmarse mediante:

```bash
docker compose -f docker-compose.test.yml exec -T api-test alembic heads
```

La cadena histórica de migraciones todavía no permite reconstruir de forma confiable una base completamente vacía. En pruebas se utiliza temporalmente `create_all + stamp`, exclusivamente dentro de la base efímera `db-test`.

## Estado del frontend web

* Next.js App Router en `apps/web`.
* React 19 y TypeScript.
* Autenticación mediante Firebase Auth.
* Guards y navegación por roles.
* React Query para estado del servidor.
* Axios mediante cliente API centralizado.
* Formularios con Zod y React Hook Form.
* Design system inicial basado en Tailwind y componentes compatibles con shadcn/ui.
* Áreas observadas:

  * autenticación;
  * dashboards por rol;
  * portal de cliente;
  * administración de usuarios;
  * planes y suscripciones.

Los endpoints web deben usar `/api/web/*` por defecto o endpoints core protegidos y documentados.

## Funcionalidades recientes confirmadas

### Solicitudes de horas extra

La implementación backend fue integrada en `main` mediante:

* `6cae4c2` — persistencia y fundamentos de cálculo;
* `ef73f68` — API y flujo de aprobación;
* `42449f6` — integración de la rama de horas extra.

Componentes observados:

* modelo y migración;
* schemas;
* servicio de solicitudes;
* calculadora de horas;
* endpoints;
* autorización y visibilidad por roles;
* pruebas unitarias, de repositorio y de API;
* documentación de arquitectura.

Estado actual:

* backend integrado en `main`;
* pruebas específicas presentes;
* suite completa posterior al merge pendiente de confirmar;
* despliegue en producción pendiente de confirmar;
* frontend mobile desarrollado en su repositorio independiente y pendiente de reconciliar con el contrato backend actual.

### Planes y suscripciones

La implementación de planes y suscripciones está integrada en `main`.

Componentes observados:

* modelos y migración;
* servicios de suscripción, límites, uso y enforcement;
* endpoints administrativos y de consulta;
* seeds;
* pruebas de servicios y contratos API;
* primera versión del frontend web;
* estabilización de fechas en pruebas de suscripción.

Estado actual:

* backend integrado;
* primera versión web integrada;
* pruebas específicas estabilizadas;
* documentación técnica extensa disponible;
* roadmap histórico pendiente de marcar como completado, parcial o reemplazado.

## Estado de las pruebas

Existen pruebas para:

* aislamiento y seguridad de la base de datos;
* contratos API;
* servicios;
* repositorios;
* permisos seleccionados;
* planes y suscripciones;
* solicitudes de horas extra;
* endpoints web.

`pytest.ini` exige una cobertura global mínima del 80 %, excepto cuando se ejecutan pruebas focalizadas explícitamente con `--no-cov`.

Estado de validación:

* inspección estática del repositorio: realizada;
* pruebas focalizadas recientes: presentes en el historial, pero no ejecutadas durante esta revisión;
* suite backend completa posterior al último merge: pendiente;
* validación de migraciones en `db-test`: pendiente;
* typecheck web: pendiente;
* lint web: pendiente;
* build web: pendiente;
* validación manual integrada: pendiente.

## Estado del despliegue

### Backend

`.github/workflows/ci.yml`:

* se activa mediante push a `main` para cambios backend seleccionados;
* construye una imagen Docker;
* publica la imagen;
* despliega en Cloud Run.

El workflow actual no ejecuta pruebas antes del despliegue, aunque se denomina `CI - CD`.

### Frontend web

El frontend web se despliega de forma independiente en Vercel utilizando `apps/web` como directorio raíz.

El workflow backend no valida ni despliega automáticamente los cambios de `apps/web`.

## Riesgos activos

1. **Crítico — despliegue sin pruebas automáticas**

   El pipeline backend puede desplegar en producción sin ejecutar la suite de pruebas.

2. **Alto — historial Alembic no reproducible desde cero**

   La base de pruebas requiere temporalmente `create_all + stamp`. Debe diseñarse una baseline compatible con las bases existentes.

3. **Alto — endpoints públicos legacy**

   La auditoría identifica endpoints sin protección explícita. Deben tratarse gradualmente sin romper el contrato mobile.

4. **Medio — convivencia de `create_all` y Alembic**

   `Base.metadata.create_all` continúa activo durante el startup de desarrollo.

5. **Medio — documentación histórica de planes**

   Parte de la documentación describe como futuros elementos que ya están implementados.

6. **Medio — README desactualizado**

   `README.md` todavía describe el repositorio como un skeleton genérico y contiene comandos antiguos.

7. **Medio — validación del lint web**

   El script `npm run lint` utiliza `next lint`. Debe comprobarse su compatibilidad con la versión efectiva de Next.js instalada.

8. **Medio — frontend web fuera del pipeline backend**

   Los cambios de `apps/web` no activan las validaciones del workflow actual.

## Próximo punto de inicio

### Validación técnica inmediata

1. Ejecutar infraestructura aislada:

```bash
docker compose -f docker-compose.test.yml up -d --build
```

2. Inicializar la base de pruebas:

```bash
docker compose -f docker-compose.test.yml exec -T api-test \
  python run_tests.py bootstrap-db
```

3. Confirmar el estado de Alembic:

```bash
docker compose -f docker-compose.test.yml exec -T api-test \
  alembic heads

docker compose -f docker-compose.test.yml exec -T api-test \
  alembic current
```

4. Ejecutar la suite backend completa:

```bash
docker compose -f docker-compose.test.yml exec -T api-test \
  python run_tests.py all
```

5. Detener la infraestructura iniciada:

```bash
docker compose -f docker-compose.test.yml down
```

6. Validar el frontend web:

```bash
cd apps/web
npm run typecheck
npm run lint
npm run build
```

7. Registrar los resultados reales en este documento y actualizar `docs/board.md`.

### Prioridad posterior

Después de confirmar una línea base verde:

1. incorporar pruebas backend obligatorias antes del despliegue;
2. actualizar el README;
3. reconciliar la documentación histórica de planes;
4. continuar la siguiente iteración de horas extra entre backend y mobile;
5. diseñar por separado la baseline de Alembic.

## Validaciones de esta revisión

* Contenido del ZIP inspeccionado: sí.
* Ausencia de secretos evidentes en el ZIP: validada.
* Rama y sincronización con `origin/main`: validadas.
* Integración backend de horas extra: confirmada mediante historial Git.
* Integración de planes y suscripciones: confirmada mediante historial Git y código.
* Suite backend completa actual: no ejecutada.
* Estado real de Alembic en `db-test`: no ejecutado.
* Typecheck, lint y build web: no ejecutados.
* Despliegue actual en producción: no confirmado.
* Validación manual: no ejecutada.
