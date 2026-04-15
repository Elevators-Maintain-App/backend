# AGENTS.md

## Proyecto
VertiOne Backend es una API FastAPI con SQLAlchemy async, PostgreSQL, Firebase Auth/Firestore y una arquitectura en capas con rutas, servicios, repositorios, modelos y schemas. El negocio principal gira alrededor de compañías, usuarios, proyectos, unidades, órdenes de trabajo, checklists, reportes y dashboards por rol.

## Objetivo de este archivo
Dar contexto operativo a agentes de código para corregir bugs y agregar funcionalidades sin romper contratos, permisos ni consistencia entre capas.

## Stack real del repo
- FastAPI
- SQLAlchemy 2 async + asyncpg
- PostgreSQL
- Pydantic v2
- Firebase Admin (Auth + Firestore)
- WeasyPrint + Jinja2 para reportes PDF
- Docker Compose para entorno local

## Comandos de trabajo
- Instalar dependencias: `pip install -r requirements.txt`
- Levantar local con Docker: `docker-compose up -d`
- Ejecutar API manualmente: `uvicorn app.main:app --reload`
- Docs Swagger: `http://localhost:8000/docs`

## Skills disponibles
- `.agent-skills/fastapi-domain-changes/SKILL.md`: cambios de dominio completos en FastAPI por capas.
- `.agent-skills/checklist-contract-sync/SKILL.md`: cambios sensibles en submit y sincronización de checklists.
- `.agent-skills/frontend-backend-contract-alignment/SKILL.md`: cambios que afectan contrato entre API y app móvil.

## Arquitectura observada
- `app/api/routes/*`: endpoints FastAPI
- `app/services/*`: lógica de negocio
- `app/db/repositories/*`: acceso a datos
- `app/db/models/*`: modelos SQLAlchemy
- `app/schemas/*`: contratos request/response
- `app/auth/firebase.py`: autenticación y usuario actual vía token Firebase
- `app/services/reportes/*` + `app/templates/*`: generación de PDF/HTML

## Reglas de arquitectura
1. No saltes capas sin motivo. Un endpoint no debería contener lógica de negocio compleja ni consultas SQL directas.
2. Si un cambio toca persistencia, evalúa impacto en modelo, schema, repositorio y servicio.
3. Si un cambio toca permisos, revisa también `app/auth/firebase.py`, casos por rol y filtros por compañía.
4. Mantén las respuestas alineadas con schemas Pydantic.
5. Prefiere centralizar reglas de negocio en `services`, no duplicarlas entre rutas.
6. Los repositorios deben seguir siendo la capa de acceso a datos, no una mezcla de reglas de negocio.

## Principios obligatorios
- Multiempresa: no devolver ni modificar datos fuera de la compañía del usuario, salvo superadmin.
- Roles: technician, supervisor, admin, superAdmin, client deben seguir comportamientos consistentes entre backend y app móvil.
- Errores descriptivos: usa mensajes claros y códigos HTTP correctos.
- Compatibilidad: no rompas campos esperados por mobile sin coordinar el contrato.

## Convenciones de cambio
- Si agregas campo a una entidad:
  - modelo
  - schema(s) request/response
  - repositorio
  - servicio
  - ruta
  - documentación funcional si cambia contrato
- Si agregas endpoint:
  - define schema de entrada/salida
  - agrega service dedicado o amplía uno existente
  - protege con dependencia de auth si aplica
  - respeta filtros por compañía/rol
- Si cambias filtros o paginación, evita romper listados móviles existentes.

## Seguridad y configuración
- No agregues secretos al repositorio.
- Mantén compatibilidad con variables de entorno actuales.
- Si tocas CORS o auth, evalúa impacto completo en mobile.
- Firestore se usa como fuente de metadatos de usuario autenticado; Postgres como fuente principal de datos operativos.

## Reglas para Firebase y usuarios
- El token recibido del mobile es de Firebase.
- `get_current_firebase_user` es una dependencia crítica; cualquier cambio debe preservar autenticación y resolución del usuario.
- No asumas que todo usuario Firebase tiene datos completos; maneja faltantes con errores claros.
- Si sincronizas datos entre Firebase y Postgres, mantén integridad y rollback razonable cuando sea posible.

## Reglas para órdenes y checklists
- Las órdenes están fuertemente condicionadas por rol, compañía y estado.
- Un cambio en checklists puede afectar mobile offline, reportes PDF y dashboards.
- No cambies nombres de campos del payload sin revisar frontend.
- Si agregas validaciones al submit del checklist, procura mensajes accionables y compatibilidad con reintentos del móvil.

## Checklist para cambios
1. Entender el caso de negocio y el rol afectado.
2. Ubicar endpoint, service, repo y schema impactados.
3. Revisar impacto en filtros por compañía y permisos.
4. Revisar impacto en mobile y reportes.
5. Implementar el cambio en la menor superficie posible.
6. Verificar respuesta final y errores.
7. Documentar follow-ups si queda deuda técnica.

## Qué evitar
- No reescribas el repo a otra arquitectura.
- No mezcles lógica de presentación o formateo móvil en servicios backend.
- No pongas consultas complejas repetidas en múltiples rutas.
- No uses respuestas ad hoc cuando ya existe un schema claro.

## Deuda técnica visible a tratar con cuidado
- `Base.metadata.create_all` en startup para development convive con Alembic; evita suponer una sola estrategia.
- Hay mezcla de servicios viejos y nuevos para órdenes/checklists; antes de editar, identifica cuál usa realmente la ruta.
- Existen varios módulos de dashboard y reportes que comparten entidades; cambios en órdenes repercuten en varias salidas.
- La configuración y manejo de errores puede mejorarse, pero hazlo de forma incremental.

## Entregables esperados de un agente
Cuando el cambio sea relevante, deja:
- bug o requerimiento atendido
- causa raíz
- archivos tocados
- impacto en contrato API
- riesgos o migraciones pendientes
