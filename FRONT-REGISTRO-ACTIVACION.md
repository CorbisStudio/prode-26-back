# Front — Registro con activación por código

Guía para que el front implemente el **auto-registro de usuarios nuevos** contra
prode-back. El usuario se registra → recibe un **código de 6 dígitos** por mail → lo
ingresa en la app → queda logueado.

- **Base URL (prod):** `https://prode.vera-demo.site/api`
- **Base URL (local):** `http://localhost:8060/api`
- Auth: JWT Bearer (igual que el login actual).
- **Remitente del mail:** `Prode Mundial <prode.corbis@gmail.com>` (envío ya operativo en prod).
  El front debería avisar al usuario que revise **Spam/Promociones** la primera vez.

---

## Flujo completo

```
1. Usuario completa  Nombre + Correo + Contraseña      (pantalla "Registrarme")
2. Front  ──POST /api/register/──▶  backend crea el user is_active=False y manda el código
3. Front muestra  "Te enviamos un código a tu correo"   (pantalla "Ingresá el código")
4. Usuario copia el código de 6 dígitos del mail
5. Front  ──POST /api/activate/ { email, code }──▶  backend:
      • valida el código (no vencido, intentos disponibles, coincide)
      • is_active = True
      • suma al usuario al grupo EXTERNAL
      • devuelve  { access, refresh, user }   (queda logueado)
6. Front guarda los tokens y entra a la app
```

---

## Endpoints

### 1) Registro — `POST /api/register/`

Crea la cuenta (inactiva) y dispara el mail con el código.

**Request**
```json
{
  "first_name": "Manuel",
  "email": "manuel@corbisstudio.com",
  "password": "MiClaveSegura123"
}
```

**Responses**

| Código | Caso | Body |
|--------|------|------|
| `201` | Registro OK | `{ "detail": "Registro exitoso. Te enviamos un código a tu correo para activar la cuenta." }` |
| `200` | El email ya existía pero **sin activar** → se reenvía un código nuevo | `{ "detail": "Esa cuenta ya estaba registrada. Te reenviamos un código nuevo." }` |
| `400` | El email ya tiene una **cuenta activa** | `{ "detail": "Ya existe una cuenta activa con ese correo." }` |
| `400` | Validación de campos | `{ "email": ["..."] }` / `{ "password": ["..."] }` / `{ "first_name": ["..."] }` |

**Validaciones (las hace el backend, conviene replicarlas en el front):**
- `email`: formato válido y único. Se normaliza a minúsculas.
- `password`: reglas de Django → mínimo **8 caracteres**, no sólo numérica, ni muy común,
  ni muy parecida al email. Los mensajes vienen en `password: [...]`.
- `first_name`: requerido (máx. 150).

> **Reenviar código:** volver a llamar `POST /api/register/` con el mismo email. Si la
> cuenta sigue inactiva, devuelve `200` y manda un **código nuevo** (invalida el anterior).

---

### 2) Activación — `POST /api/activate/`

Valida el código y, si está OK, activa la cuenta y devuelve los tokens.

**Request**
```json
{ "email": "manuel@corbisstudio.com", "code": "695618" }
```
> `email`: el mismo del registro. `code`: 6 dígitos (string).

**Response `200`**
```json
{
  "access":  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 472,
    "username": "manuel@corbisstudio.com",
    "email": "manuel@corbisstudio.com",
    "first_name": "Manuel",
    "last_name": "",
    "is_staff": false,
    "profile_picture_url": null
  }
}
```

**Errores `400`** (todos con `{ "detail": "..." }`)

| Caso | `detail` |
|------|----------|
| Código incorrecto | `"Código incorrecto. Te quedan N intento(s)."` |
| Se agotaron los **5 intentos** | `"Demasiados intentos. Pedí un código nuevo desde la app."` |
| Código **vencido** (>15 min) | `"El código venció. Pedí uno nuevo desde la app."` |
| La cuenta **ya estaba activa** | `"La cuenta ya está activa. Iniciá sesión."` |
| Email o código sin match / inexistente | `"Correo o código incorrecto."` |
| Formato inválido (no son 6 dígitos) | `{ "code": ["..."] }` |

**Reglas del código:**
- **6 dígitos numéricos**, vence a los **15 minutos**.
- Máximo **5 intentos**; pasado eso hay que pedir uno nuevo (re-`POST /register/`).
- Por seguridad, una cuenta ya activa **nunca** devuelve tokens sin código → mandá al login.

---

### 3) Login (ya existe) — `POST /api/token/`
```json
{ "email": "manuel@corbisstudio.com", "password": "MiClaveSegura123" }
```
Devuelve el mismo shape que activación: `{ access, refresh, user }`.

### 4) Refresh — `POST /api/token/refresh/`
```json
{ "refresh": "<refresh_token>" }   →   { "access": "<nuevo_access>" }
```

### 5) Perfil — `GET /api/profile/`  (header `Authorization: Bearer <access>`)
Devuelve el objeto `user` del usuario logueado.

---

## Manejo de tokens

- **Guardar** `access` y `refresh` tras la activación / login.
- Mandar en cada request protegido: `Authorization: Bearer <access>`.
- **Lifetimes:** `access` = 6 hs · `refresh` = 1 día. Al expirar el access, usar
  `/api/token/refresh/`.
- El `access` trae un claim **`groups`** con los grupos del usuario. Para un registrado
  por este flujo incluirá `"EXTERNAL"`:
  ```json
  { "user_id": "472", "groups": ["EXTERNAL"], "exp": ..., "token_type": "access" }
  ```

---

## Ejemplo de integración (fetch / TS)

```ts
const API = 'https://prode.vera-demo.site/api';

// 1) Registro
async function register(first_name: string, email: string, password: string) {
  const res = await fetch(`${API}/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ first_name, email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw data;          // { detail } o { email:[...] } / { password:[...] }
  return data;                       // { detail: "Registro exitoso..." }  (201)
}

// 2) Activación con el código
async function activate(email: string, code: string) {
  const res = await fetch(`${API}/activate/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, code }),
  });
  const data = await res.json();
  if (!res.ok) throw data;          // { detail: "Código incorrecto. Te quedan N..." }
  // data = { access, refresh, user }
  localStorage.setItem('access', data.access);
  localStorage.setItem('refresh', data.refresh);
  return data;
}

// 3) Reenviar código  → es el mismo register (cae en 200 si la cuenta sigue inactiva)
const resendCode = (first_name: string, email: string, password: string) =>
  register(first_name, email, password);

// 4) Request autenticado
async function getProfile() {
  const res = await fetch(`${API}/profile/`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access')}` },
  });
  return res.json();
}
```

> El reenvío necesita reusar la `password` del registro; si no la tenés en estado, pedila
> de nuevo en la pantalla de reenvío.

---

## Pantallas a construir en el front

1. **Registrarme** — formulario `Nombre / Correo / Contraseña` → `POST /api/register/`.
   - 201 → ir a la pantalla "Ingresá el código".
   - 400 → mostrar el error (`detail` o el del campo).

2. **Ingresá el código** — input de **6 dígitos** (un solo campo o 6 casillas) + el email
   en estado (del paso anterior).
   - Botón "Activar" → `POST /api/activate/ { email, code }`.
   - 200 → guardar tokens + entrar a la app.
   - 400 → mostrar el `detail` (incorrecto / vencido / demasiados intentos / ya activa).
   - Botón **"Reenviar código"** → `POST /api/register/` con el mismo email (cae en `200`).
   - Opcional: contador de 15 min y deshabilitar "Activar" al vencer.

---

## Notas

- El registrado entra al sistema en el grupo **EXTERNAL** y como participante del ranking.
- El `username` se setea igual al email.
- CORS ya permite cualquier origen en el back, así que el front lo consume sin fricción.
- **Mail:** el envío en prod ya está operativo (remitente `prode.corbis@gmail.com`). El mail
  llega con el código en una caja destacada; puede caer en Spam/Promociones la 1ª vez.
- **Mensajes al usuario:** mostrá siempre el `detail` que devuelve el back (está en español
  y listo para UI). Para los errores de validación de campos, el error viene por campo
  (`email` / `password` / `first_name` / `code`).
