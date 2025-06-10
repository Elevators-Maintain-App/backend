crear migracion:
docker exec -it fastapi_app alembic revision --autogenerate -m “agregar campo de logo”
14:19
Run migracion:
 docker exec -it fastapi_app alembic upgrade head