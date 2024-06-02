# Postgresql Addon for Disco

## Regenerate requirements.txt

We edit `requirements.in` to list the dependencies.
```bash
docker build -t letsdiscodev/addon-postgres .
docker run \
    --volume .:/code \
    --workdir /code \
    letsdiscodev/addon-postgres \
    uv pip compile requirements.in -o requirements.txt
```

## Generating an Alembic revision

```
docker build -t letsdiscodev/addon-postgres .
docker run -it --volume ./data:/addon/data --volume .:/code letsdiscodev/addon-postgres bash
rm /addon/data/db.sqlite3
alembic upgrade head
alembic revision --autogenerate -m "1.0.0"
```
