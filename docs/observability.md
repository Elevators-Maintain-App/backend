# Observability Logs

La observabilidad inicial registra una linea por request HTTP desde middleware, sin cambiar rutas, payloads, autenticacion ni logica de negocio.

## Formato

El logger `app.observability` emite JSON compacto con estos campos:

| Campo | Descripcion |
| --- | --- |
| `event` | Siempre `http_request`. |
| `request_id` | Valor recibido en `X-Request-ID` o UUID generado por el backend. Tambien se devuelve en la respuesta como `X-Request-ID`. |
| `method` | Metodo HTTP. |
| `path` | Path normalizado de FastAPI cuando esta disponible; si no, path real sin query string. |
| `status_code` | Codigo HTTP final de la respuesta. |
| `duration_ms` | Duracion del request en milisegundos. |
| `user_role` | Rol si alguna capa anterior lo dejo disponible en `request.state`; si no, `null`. El middleware no fuerza auth ni decodifica tokens. |
| `company_id_hash` | Hash truncado de `company_id` si esta disponible en `request.state`; si no, `null`. |
| `x_app_version` | Header `X-App-Version` si mobile lo envia. |
| `x_app_platform` | Header `X-App-Platform` si mobile lo envia. |

Ejemplo:

```json
{"company_id_hash":null,"duration_ms":12.41,"event":"http_request","method":"GET","path":"/api/ordenes-trabajo/{orden_id}","request_id":"6f52a64f-27de-4ad1-8bb4-b4a769e29b2b","status_code":200,"user_role":null,"x_app_platform":"ios","x_app_version":"1.2.3"}
```

## Datos excluidos

No se registran tokens, emails, nombres, payloads, firmas, fotos, URLs sensibles, query strings ni datos personales. `company_id` solo se registra como hash truncado cuando ya esta disponible sin ejecutar autenticacion adicional.

## Uso durante limpieza

- Agrupar por `method`, `path`, `status_code`, `x_app_version` y `x_app_platform` para confirmar uso mobile.
- Buscar endpoints publicos operativos con uso real antes de cambiar auth.
- Usar `request_id` para correlacionar errores entre mobile, API y logs de infraestructura.
- Mantener este registro como medicion de compatibilidad antes de deprecar endpoints legacy.
