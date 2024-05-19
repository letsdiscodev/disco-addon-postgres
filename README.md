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



