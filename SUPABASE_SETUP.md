# Supabase — pasos finales (bucket + usuario)

Las tablas ya las tienes. Falta el **bucket** y un **usuario Auth** (las tablas apuntan a `auth.users`).

## 1. Crear bucket `cv-files`

1. Entra a tu proyecto en [supabase.com/dashboard](https://supabase.com/dashboard)
2. Menú izquierdo → **Storage**
3. **New bucket**
4. Configura:
   - **Name:** `cv-files`
   - **Public bucket:** **OFF** (privado)
   - File size limit: `5` MB (o el default)
   - Allowed MIME: opcional (`application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`)
5. **Create bucket**

Con `SERVICE_ROLE` el backend puede subir/leer sin policies públicas. No hagas el bucket público.

## 2. Crear usuario (obligatorio por ahora)

Las tablas tienen `user_id → auth.users`. Necesitas un usuario real:

1. **Authentication** → **Users** → **Add user**
2. **Create new user**
3. Email + password (los que uses tú)
4. Desactiva “Auto Confirm User” solo si ya desactivaste confirm email; si no, marca **Confirm user**
5. Abre el usuario creado y **copia el UUID** (ej. `a1b2c3d4-...`)

## 3. Pegar en `.env` (local, no en el chat)

```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
AGENT_USER_ID=pega-aqui-el-uuid-del-usuario
```

Opcional (si no quieres copiar el UUID a mano): el backend puede crear/buscar el usuario con:

```env
AGENT_BOOTSTRAP_EMAIL=tu@email.com
AGENT_BOOTSTRAP_PASSWORD=una-clave-segura
```

## 4. Comprobar

- Table Editor: debes ver `candidate_profiles`, `master_documents`, etc.
- Storage: bucket `cv-files`
- `.env` con las 4 variables (URL, anon, service_role, `AGENT_USER_ID`)

Luego reinicia el servidor. Al subir un CV debería guardarse y **sobrevivir al reinicio**.
