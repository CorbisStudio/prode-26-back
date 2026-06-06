# API — Prode Mundial 2026 (prode-back)

Documentación de todos los endpoints del backend: qué hacen, qué payload reciben y qué devuelven.

- **Base URL (local):** `http://localhost:8000`
- **Prefijo común:** todos los endpoints cuelgan de `/api/`
- **Formato:** JSON (`Content-Type: application/json`)
- **Autenticación:** JWT (Bearer). En los endpoints protegidos hay que mandar el header:
  ```
  Authorization: Bearer <access_token>
  ```
- **Respuestas de error comunes:**
  - `401 Unauthorized` — falta el token o está vencido.
  - `400 Bad Request` — payload inválido.
  - `403 Forbidden` — sin permiso sobre el recurso.
  - `404 Not Found` — recurso inexistente.

---

## Índice

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| POST | `/api/token/` | No | Login (devuelve access + refresh + user) |
| POST | `/api/token/refresh/` | No | Renovar el access token |
| POST | `/api/token/verify/` | No | Validar un token |
| GET | `/api/profile/` | Sí | Datos del usuario autenticado |
| GET | `/api/matches/` | Sí | Lista de partidos (con filtros) |
| GET | `/api/matches/{id}/` | Sí | Detalle de un partido |
| GET | `/api/predictions/` | Sí | Mis pronósticos |
| POST | `/api/predictions/` | Sí | Crear/editar mi pronóstico (upsert) |
| GET | `/api/ranking/` | Sí | Ranking global |
| GET | `/api/leagues/` | Sí | Mis ligas |
| POST | `/api/leagues/` | Sí | Crear una liga |
| POST | `/api/leagues/join/` | Sí | Unirse a una liga por código |
| GET | `/api/leagues/{id}/ranking/` | Sí | Ranking de una liga |
| GET | `/api/swagger/` · `/api/redoc/` | No | Documentación interactiva |

---

## Autenticación

### POST `/api/token/` — Login
Inicia sesión. Acepta **usuario o email** + contraseña. Devuelve el par de tokens JWT y los datos del usuario.

**Payload**
```json
{
  "username": "pdalmasso",
  "password": "prode1234"
}
```

**Respuesta `200 OK`**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "pdalmasso",
    "email": "pablo@corbisstudio.com",
    "first_name": "Pablo",
    "last_name": "Dalmasso",
    "is_staff": true,
    "profile_picture_url": "http://projects.frankcollaboration.com/media/img/contacts/company/1/PDalmasso.png"
  }
}
```

**Error `401`** — credenciales inválidas:
```json
{ "detail": "No active account found with the given credentials" }
```

---

### POST `/api/token/refresh/` — Renovar access
Genera un nuevo `access` token a partir del `refresh`.

**Payload**
```json
{ "refresh": "eyJhbGciOiJIUzI1NiIs..." }
```

**Respuesta `200 OK`**
```json
{ "access": "eyJhbGciOiJIUzI1NiIs..." }
```

**Error `401`** — refresh vencido o inválido:
```json
{ "detail": "Token is invalid or expired", "code": "token_not_valid" }
```

---

### POST `/api/token/verify/` — Validar token
Verifica si un token es válido. No devuelve cuerpo.

**Payload**
```json
{ "token": "eyJhbGciOiJIUzI1NiIs..." }
```

**Respuesta `200 OK`** — `{}` (token válido)
**Error `401`** — token inválido.

---

### GET `/api/profile/` — Usuario autenticado
Devuelve los datos del usuario logueado (según el token enviado).

**Headers:** `Authorization: Bearer <access>`
**Payload:** —

**Respuesta `200 OK`**
```json
{
  "id": 1,
  "username": "pdalmasso",
  "email": "pablo@corbisstudio.com",
  "first_name": "Pablo",
  "last_name": "Dalmasso",
  "is_staff": true,
  "profile_picture_url": "http://projects.frankcollaboration.com/media/img/contacts/company/1/PDalmasso.png"
}
```

---

## Partidos

### GET `/api/matches/` — Lista de partidos
Devuelve el fixture del Mundial. Admite filtros opcionales por query param.

**Query params (opcionales)**

| Param | Ejemplo | Descripción |
|-------|---------|-------------|
| `group` | `Group A` | Filtra por grupo |
| `stage` | `GROUP_STAGE` | Filtra por fase (`GROUP_STAGE`, `LAST_32`, `LAST_16`, `QUARTER_FINALS`, `SEMI_FINALS`, `THIRD_PLACE`, `FINAL`) |
| `status` | `TIMED` | Filtra por estado (`TIMED`, `IN_PLAY`, `PAUSED`, `FINISHED`, etc.) |

Ej: `GET /api/matches/?status=TIMED&group=Group A`

**Respuesta `200 OK`**
```json
[
  {
    "id": 1,
    "stage": "GROUP_STAGE",
    "group": "Group A",
    "matchday": 1,
    "home_team": {
      "id": 5,
      "name": "Mexico",
      "code": "MEX",
      "group": "Group A",
      "flag_url": "https://crests.football-data.org/769.svg"
    },
    "away_team": {
      "id": 9,
      "name": "South Africa",
      "code": "RSA",
      "group": "Group A",
      "flag_url": "https://crests.football-data.org/9396.svg"
    },
    "utc_date": "2026-06-11T19:00:00Z",
    "status": "TIMED",
    "home_score": null,
    "away_score": null,
    "winner": null
  }
]
```
> En partidos finalizados, `status` = `"FINISHED"`, `home_score`/`away_score` traen el resultado y `winner` es `"HOME_TEAM" | "AWAY_TEAM" | "DRAW"`.

---

### GET `/api/matches/{id}/` — Detalle de un partido
Igual que un item de la lista anterior, para un solo partido.

**Respuesta `200 OK`** — un objeto `Match` (mismo shape que arriba).
**Error `404`** — partido inexistente.

---

## Pronósticos

### GET `/api/predictions/` — Mis pronósticos
Devuelve los pronósticos del usuario autenticado, con el detalle del partido y los puntos obtenidos.

**Respuesta `200 OK`**
```json
[
  {
    "id": 42,
    "match": 1,
    "match_detail": {
      "id": 1,
      "home_team": "Mexico",
      "away_team": "South Africa",
      "utc_date": "2026-06-11T19:00:00Z",
      "stage": "GROUP_STAGE",
      "group": "Group A",
      "status": "FINISHED",
      "home_score": 2,
      "away_score": 1
    },
    "home_score": 2,
    "away_score": 1,
    "points": 3,
    "is_scored": true,
    "is_exact": true
  }
]
```
> `points`, `is_scored` e `is_exact` son **read-only** (los calcula el backend al puntuar). Mientras el partido no se juega: `points: 0`, `is_scored: false`, `is_exact: false`.

---

### POST `/api/predictions/` — Crear / editar pronóstico (upsert)
Guarda mi pronóstico de marcador para un partido. Si ya existe uno para ese partido, lo actualiza.

**Payload**
```json
{
  "match": 1,
  "home_score": 2,
  "away_score": 1
}
```

**Respuesta**
- `201 Created` — si era un pronóstico nuevo.
- `200 OK` — si actualizó uno existente.

Devuelve el pronóstico (mismo shape que el GET).

**Error `400`** — el partido ya empezó (cierre por `utc_date`):
```json
{ "non_field_errors": ["El partido ya comenzó: no se puede cargar ni editar el pronóstico."] }
```

> **Regla de negocio:** se puede crear/editar hasta el momento exacto de inicio del partido (`utc_date`).

---

## Ranking

### GET `/api/ranking/` — Ranking global
Devuelve a todos los usuarios ordenados por puntos (desc) y, como desempate, por aciertos exactos.

**Respuesta `200 OK`**
```json
[
  {
    "position": 1,
    "user_id": 118,
    "username": "fromanutti",
    "full_name": "Florencia Romanutti",
    "profile_picture_url": "http://projects.frankcollaboration.com/media/img/contacts/company/1/FRomanutti.png",
    "total_points": 24,
    "exact_hits": 6
  }
]
```

---

## Ligas privadas

### GET `/api/leagues/` — Mis ligas
Devuelve las ligas donde el usuario es miembro.

**Respuesta `200 OK`**
```json
[
  {
    "id": 1,
    "name": "Liga de los Pibes",
    "join_code": "KFcEZkul",
    "owner": 1,
    "members_count": 15,
    "create_date": "2026-06-03T19:06:32.300218-03:00"
  }
]
```

---

### POST `/api/leagues/` — Crear liga
Crea una liga privada. El backend genera el `join_code` y agrega al creador como miembro/owner.

**Payload**
```json
{ "name": "Amigos del Prode" }
```

**Respuesta `201 Created`**
```json
{
  "id": 2,
  "name": "Amigos del Prode",
  "join_code": "1mGPLCzN",
  "owner": 1,
  "members_count": 1,
  "create_date": "2026-06-03T19:10:00-03:00"
}
```

---

### POST `/api/leagues/join/` — Unirse a una liga
Une al usuario autenticado a una liga usando su código.

**Payload**
```json
{ "join_code": "1mGPLCzN" }
```

**Respuesta `200 OK`** — la liga a la que se unió (mismo shape que arriba).

**Errores**
- `400` — falta el código: `{ "error": "join_code es requerido" }`
- `404` — código inexistente: `{ "error": "Liga no encontrada" }`

---

### GET `/api/leagues/{id}/ranking/` — Ranking de una liga
Devuelve el ranking filtrado a los miembros de esa liga (mismo shape que el ranking global).

**Respuesta `200 OK`**
```json
[
  {
    "position": 1,
    "user_id": 1,
    "username": "admin",
    "full_name": "Admin",
    "profile_picture_url": null,
    "total_points": 18,
    "exact_hits": 5
  }
]
```

**Error `403`** — el usuario no es miembro de la liga:
```json
{ "error": "No sos miembro de esta liga" }
```

---

## Documentación interactiva

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/swagger/` | Swagger UI (probar endpoints desde el navegador) |
| `GET /api/redoc/` | Redoc (documentación legible) |
| `GET /api/swagger.json` | Esquema OpenAPI en JSON |

---

## Notas

- El front consume todos estos endpoints a través de `src/lib/services.ts` (capa de servicios) — ahí está el mapa `ENDPOINTS` que refleja esta tabla.
- Los partidos se cargan con el comando `python manage.py import_worldcup` y los resultados se actualizan de noche vía Celery (`update_match_results`), que además dispara el puntaje de los pronósticos.
- Sistema de puntos (configurable en `settings.py`): **3** pts marcador exacto, **1** pt acertar resultado, por un **multiplicador de fase** (grupos ×1 … final ×5).
