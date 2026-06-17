# Reconstruir la base local — `rebuild_local_db.sh`

Script que arma la base de **prode-back** desde cero, trayendo los usuarios de PAC
y los datos del Mundial, y deja un backup. Útil para regenerar el entorno local
(o repoblar) de forma reproducible.

## Qué hace (4 pasos)

| Paso | Comando | Qué hace |
|------|---------|----------|
| 1 | `manage.py flush --noinput` | **Borra todos los datos** de la base (mantiene el esquema/migraciones) |
| 2 | `manage.py import_from_pac` | Importa **usuarios + grupos + fotos** desde la base de PAC |
| 3 | `manage.py import_worldcup` | Carga **equipos y partidos** del Mundial desde football-data.org |
| 4 | `pg_dump` | Genera un **backup** `.sql` en `backup/prode_<timestamp>.sql` |

Al final imprime un resumen (usuarios, fotos, equipos, partidos).

## Cómo se usa

```bash
# con el stack local levantado (docker compose up) y la base de PAC accesible
bash scripts/rebuild_local_db.sh
```

## El comando `import_from_pac` (el corazón del script)

Se conecta **directo a la base de PAC** (postgres) y copia a prode-back:

- `auth_group` → `Group` (preserva el `id`)
- `auth_user` → `User` (preserva el `id` **y el hash de la contraseña** → las credenciales son las mismas que en PAC)
- `employees_employee.frank_profile_picture_url` → `UserProfile.profile_picture_url`

> Nota: **no** se importan las membresías usuario↔grupo (los grupos se crean vacíos).

Detalles:
- Es **idempotente** (`update_or_create`): se puede correr varias veces sin duplicar.
- Reajusta las **secuencias** de `id` al final (porque inserta ids explícitos).
- A los usuarios sin foto les crea igual el `UserProfile` (vacío).

### Parámetros de conexión a PAC
Con defaults para el entorno docker local (PAC en `host.docker.internal:5432`):

| Flag | Env var | Default |
|------|---------|---------|
| `--pac-host` | `PAC_DB_HOST` | `host.docker.internal` |
| `--pac-port` | `PAC_DB_PORT` | `5432` |
| `--pac-db` | `PAC_DB_NAME` | `pac` |
| `--pac-user` | `PAC_DB_USER` | `postgres` |
| `--pac-password` | `PAC_DB_PASSWORD` | `pac_1234` |

```bash
# ejemplo apuntando a otra PAC
docker compose exec web python manage.py import_from_pac --pac-host 10.0.0.5 --pac-db pac_prod
```

## Backups

- Se guardan en `backup/` con timestamp: `prode_YYYYMMDD-HHMMSS.sql`.
- **No se versionan** (`backup/*.sql` está en `.gitignore`) porque contienen
  hashes de contraseñas y emails.

### Restaurar un backup
```bash
# borra y recarga la base local desde un dump
docker compose exec -T db psql -U postgres -c "DROP DATABASE IF EXISTS prode;"
docker compose exec -T db psql -U postgres -c "CREATE DATABASE prode;"
cat backup/prode_<timestamp>.sql | docker compose exec -T db psql -U postgres prode
```

## Requisitos
- Stack local levantado: `docker compose up -d`
- Base de PAC corriendo y accesible (contenedor `pacapp-db` en `localhost:5432`)
- Token de football-data en el `.env` (`FOOTBALL_DATA_TOKEN`) para el paso 3
