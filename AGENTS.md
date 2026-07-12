# AGENTS.md — VertiOne Backend + Web

## 1. Alcance y prioridad

Este repositorio contiene dos aplicaciones desplegables:

- `app/`: API FastAPI.
- `apps/web/`: frontend Next.js.

Estas instrucciones aplican a todo el repositorio. Antes de trabajar, lee este archivo y únicamente los documentos de `docs/` relacionados con la tarea. Las instrucciones más específicas del dominio prevalecen sobre las generales cuando no las contradigan.

No asumas que un documento histórico representa el estado actual: confirma contratos, comandos y comportamiento en el código y las pruebas.

## 2. Principios obligatorios

1. Implementa el cambio mínimo completo y coherente con la arquitectura existente.
2. No reescribas el repositorio ni introduzcas capas, dependencias o patrones sin una necesidad demostrable.
3. Conserva compatibilidad con web y mobile. Todo cambio de contrato debe identificarse y documentarse.
4. El backend es la autoridad de autenticación, autorización, reglas de negocio y aislamiento multiempresa. Los guards de frontend son solo UX.
5. No accedas a producción ni ejecutes pruebas, seeds o migraciones contra bases remotas.
6. No hagas commit, merge, rebase, push, deploy ni cambios destructivos sin autorización explícita.
7. Preserva cambios locales o trabajo ajeno. No reviertas archivos que no pertenecen al alcance.
8. No expongas secretos, tokens, credenciales, datos personales ni URLs de conexión en código, logs o reportes.

## 3. Stack y arquitectura real

### Backend

- FastAPI, Pydantic v2.
- SQLAlchemy 2 async + asyncpg.
- PostgreSQL y Alembic.
- Firebase Admin: autenticación y metadatos de usuario en Firestore.
- Jinja2 + WeasyPrint para reportes.
- Arquitectura en capas existente:
  - `app/api/routes/`: endpoints y dependencias HTTP.
  - `app/services/`: casos de uso y reglas de negocio.
  - `app/db/repositories/`: acceso a datos.
  - `app/db/models/`: modelos SQLAlchemy.
  - `app/schemas/`: contratos Pydantic.
  - `app/auth/firebase.py`: autenticación y resolución de usuario.

El repositorio contiene servicios legacy y servicios más recientes. Antes de editar, sigue desde la ruta registrada en `app/main.py` hasta la implementación realmente usada; no deduzcas el flujo por el nombre del archivo.

### Frontend web

- Next.js App Router, React 19 y TypeScript.
- Tailwind CSS y componentes compatibles con shadcn/ui.
- Firebase Auth.
- Axios, React Query, Zod y React Hook Form.
- Código en `apps/web/src/`.

Las reglas específicas están en:

- `docs/web-architecture.md`
- `docs/web-development-rules.md`
- `docs/web-design-system.md`
- `docs/web-deploy-vercel.md`

## 4. Documentos que se leen según el cambio

No leas toda la carpeta `docs/` por defecto.

| Cambio | Documentos iniciales |
| --- | --- |
| Estado del proyecto | `docs/project-status.md`, `docs/board.md` |
| Backend general | `docs/backend-audit.md`, `docs/backend-risk-register.md` solo si el área lo requiere |
| Contrato con mobile | `docs/backend-mobile-contract.md` |
| Pruebas/backend DB | `docs/testing-database-isolation.md` |
| Seguridad de endpoints | `docs/public-endpoints-security-audit.md` |
| Web | los cuatro documentos web indicados arriba |
| Planes y suscripciones | documentos `plans-*` y guía backend relacionada |
| Horas extra | `docs/overtime-requests-architecture.md` |
| Checklists | `docs/checklists.md` y skill específica |

Skills locales disponibles:

- `.agent-skills/fastapi-domain-changes/SKILL.md`
- `.agent-skills/checklist-contract-sync/SKILL.md`
- `.agent-skills/frontend-backend-contract-alignment/SKILL.md`

Úsalas solo cuando el cambio coincida con su alcance.

## 5. Inicio obligatorio de cada tarea

1. Confirma rama y ejecuta `git status --short`.
2. Identifica cambios locales y no sobrescribas trabajo existente.
3. Si se autorizó acceso remoto, ejecuta `git fetch` y compara con `main`; no hagas pull, merge o rebase automáticamente.
4. Lee `docs/project-status.md` y la tarjeta aplicable de `docs/board.md`.
5. Inspecciona de forma selectiva rutas, servicios, repositorios, modelos, schemas, componentes y pruebas relacionados.
6. Expresa alcance, riesgos y supuestos. Consulta antes de continuar si una duda cambia datos, seguridad, contrato o UX de forma material.
7. Determina explícitamente si se requiere migración antes de modificar persistencia.

Si se trabaja desde un ZIP, registra que el análisis corresponde al snapshot entregado y que no fue posible verificar rama, estado local ni diferencias remotas.

## 6. Reglas del backend

### Capas y dominio

- Las rutas coordinan HTTP; no contienen consultas SQL ni lógica de negocio compleja.
- Los servicios contienen reglas de negocio y orquestación.
- Los repositorios encapsulan acceso a datos.
- Los schemas definen requests y responses; no devuelvas ORM crudo si existe contrato de salida.
- Al agregar un campo, revisa modelo, migración, schema, repositorio, servicio, ruta, pruebas y consumidores.
- Usa errores esperables con códigos HTTP correctos y mensajes accionables; no conviertas casos de negocio en 500.

### Multiempresa, roles y Firebase

- Ningún usuario puede leer o modificar datos de otra compañía salvo una operación explícita de `superAdmin`.
- Roles compatibles: `technician`/`tecnico`, `supervisor`, `admin`, `superAdmin`/`super_admin`, `client`/`cliente` según el contrato existente.
- Los endpoints protegidos requieren token Firebase y autorización efectiva en backend.
- Firestore aporta metadatos del usuario autenticado; PostgreSQL es la fuente principal de datos operativos.
- Maneja usuarios Firebase o documentos Firestore incompletos con errores claros.
- No uses Firebase real en pruebas automatizadas; emplea mocks/fakes existentes.

### Contratos

- No renombres ni elimines campos consumidos por mobile o web sin transición coordinada.
- Revisa nullabilidad, enums, fechas, paginación, filtros, errores y reintentos.
- Checklists pueden afectar sincronización offline, evidencias, reportes y dashboards.
- Nuevas pantallas web usan `/api/web/*` por defecto o endpoints core protegidos y aprobados.

## 7. Migraciones y base de datos

Antes de implementar, responde: `Migración requerida: sí/no` y justifica.

Si se requiere:

1. Revisa el grafo actual con Alembic; no asumas una única cabeza.
2. Crea una migración nueva. No edites migraciones aplicadas en entornos compartidos.
3. Revisa manualmente operaciones, constraints, índices, defaults, nullabilidad, pérdida de datos y downgrade.
4. Prueba solo en `db-test` usando `docker-compose.test.yml`.
5. No ejecutes migraciones de producción sin autorización y plan de rollback.

La cadena histórica no puede reconstruir todavía una base vacía. En tests se usa temporalmente `create_all + stamp`, exclusivamente en la base efímera `db-test`. Consulta `docs/testing-database-isolation.md`.

## 8. Pruebas backend seguras

No instales ni uses un entorno virtual local para ejecutar pruebas. Usa Docker Compose aislado.

Inicio:

```bash
docker compose -f docker-compose.test.yml up -d --build
docker compose -f docker-compose.test.yml exec -T api-test python run_tests.py bootstrap-db
```

Primero ejecuta pruebas focalizadas, normalmente sin cobertura para iterar:

```bash
docker compose -f docker-compose.test.yml exec -T api-test \
  python -m pytest <ruta-de-prueba> -q --tb=short --no-cov
```

Después ejecuta las pruebas del módulo. Antes de cerrar un slice backend, solicita o ejecuta la suite completa según el alcance:

```bash
docker compose -f docker-compose.test.yml exec -T api-test python run_tests.py all
```

Al finalizar:

```bash
docker compose -f docker-compose.test.yml down
```

No uses `down -v` por defecto. No detengas servicios que ya estaban activos antes de la tarea.

Si una prueba falla, distingue entre fallo causado por el cambio y fallo preexistente. No modifiques una prueba válida solo para obtener verde.

## 9. Reglas del frontend web

- Trabaja desde `apps/web` y usa `npm` porque existe `package-lock.json`.
- Reutiliza los componentes y tokens existentes antes de crear variantes nuevas.
- Componentes genéricos viven en las carpetas definidas por `docs/web-development-rules.md`; UI específica permanece cerca de su dominio.
- Servicios HTTP en `src/services`, server state con React Query, formularios con Zod + React Hook Form.
- Incluye estados de carga, vacío, error, éxito y permisos cuando apliquen.
- Mantén accesibilidad básica, navegación por teclado y comportamiento responsive.
- No modifiques backend desde un slice exclusivamente frontend.
- No uses endpoints públicos legacy.

Validación mínima de cierre:

```bash
cd apps/web
npm run typecheck
npm run lint
npm run build
```

Si `lint` falla por incompatibilidad del comando configurado con la versión instalada de Next.js, repórtalo; no lo omitas ni cambies configuración fuera de alcance.

No dejes `npm run dev` u otros watchers activos al terminar.

## 10. Documentación viva

Actualiza únicamente las fuentes afectadas:

- `docs/project-status.md`: estado verificable y siguiente punto de inicio.
- `docs/backlog.md`: trabajo futuro identificado y priorizado.
- `docs/board.md`: movimiento de tareas entre estados.
- documento de arquitectura/contrato del dominio modificado.
- `README.md` o `AGENTS.md` solo si cambian instalación, comandos o reglas duraderas.

No mantengas roadmaps completados como si fueran pendientes. Marca su estado o muévelos a referencia histórica cuando corresponda.

## 11. Git, integración y despliegue

- Antes de entregar, revisa `git diff`, `git diff --check` y `git status --short`.
- No incluyas `.env`, cuentas de servicio, dumps, builds, caches ni archivos generados.
- El workflow actual despliega el backend al hacer push a `main`; no presupongas que ejecuta pruebas.
- El frontend web se despliega por separado en Vercel desde `apps/web`.
- Commit, merge, push y deploy requieren autorización explícita y validación manual previa.

## 12. Limpieza obligatoria

Registra qué procesos o contenedores iniciaste y detén solo esos al finalizar. Esto incluye Docker Compose de pruebas, servidores de desarrollo y watchers. No elimines volúmenes, imágenes o caches salvo instrucción explícita.

## 13. Definición de terminado

Un slice está terminado cuando:

- cumple criterios de aceptación;
- respeta arquitectura, roles y aislamiento por compañía;
- migración fue evaluada y probada en test si aplica;
- pruebas focalizadas pasan y la validación de cierre fue ejecutada o queda explícitamente pendiente;
- web pasa typecheck, lint y build cuando aplica;
- contratos y documentación afectada están actualizados;
- no quedaron procesos iniciados por la tarea;
- diff no contiene secretos ni cambios accidentales;
- la validación manual está completada o descrita como pendiente.

## 14. Formato de entrega

```markdown
## Resultado
[Qué quedó implementado]

## Cambios
- [archivo/área]: [cambio]

## Migración
- Requerida: sí/no
- Estado y riesgos: ...

## Validaciones
- `[comando]`: OK | FALLÓ | NO EJECUTADO

## Documentación
- [archivos actualizados]

## Limpieza
- [procesos detenidos o ninguno iniciado]

## Pendientes y riesgos
- ...

## Validación manual recomendada
1. ...
```

No declares “todo correcto” si solo ejecutaste pruebas parciales.
