# Backlog de VertiOne Backend + Web

Las prioridades deben revisarse después de validar `main` y ejecutar la línea base. Estimación relativa: `S`, `M`, `L`; dividir todo ítem `L` antes de implementarlo.

## Alta prioridad

- [ ] `DEVOPS-001` | `M` | Ejecutar pruebas backend antes del despliegue automático.
  - Valor: evita desplegar regresiones conocidas a producción.
  - Criterio: el job de deploy depende de un job de test exitoso y el workflow también valida pull requests.

- [ ] `DB-001` | `L` | Crear una baseline Alembic reproducible para bases vacías.
  - Valor: elimina la dependencia temporal de `create_all + stamp` en pruebas.
  - Riesgo: requiere validar compatibilidad con bases existentes; debe dividirse en análisis, baseline y transición.

- [ ] `SEC-001` | `L` | Tratar endpoints públicos legacy según auditoría.
  - Valor: reduce exposición de datos y operaciones.
  - Restricción: proteger por fases sin romper mobile; dividir por dominio.

## Prioridad media

- [ ] `DOC-001` | `S` | Actualizar `README.md` con identidad, comandos y despliegues reales.
- [ ] `DOC-002` | `S` | Marcar roadmaps de planes como implementados, parciales o históricos.
- [ ] `WEB-001` | `S` | Validar y corregir el comando `npm run lint` para la versión efectiva de Next.js.
- [ ] `DEVOPS-002` | `M` | Agregar validaciones de web al pipeline o a un workflow independiente.
- [ ] `ARCH-001` | `M` | Retirar gradualmente `create_all` del startup de desarrollo cuando Alembic sea reproducible.
- [ ] `TEST-001` | `M` | Ampliar cobertura de permisos y aislamiento multiempresa en endpoints de mayor riesgo.

## Por confirmar

- [ ] `PLAN-001` | `S` | Confirmar estado final de slices de planes en backend y web.

## Reglas de mantenimiento

- Toda deuda nueva debe incluir valor, riesgo y criterio de cierre.
- Una tarea pasa a `docs/board.md` al entrar en preparación o ejecución.
- No mantener aquí tareas ya terminadas; conservar su evidencia en estado, historial Git o documento de dominio.
