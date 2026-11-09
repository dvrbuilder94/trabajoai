# TrabajoAI — despliegue y prueba del primer flujo

Este documento contiene solo la configuración que no podemos ejecutar desde la integración actual de GitHub. **Nunca pegues claves secretas en el chat, el repositorio, un issue o el código del navegador**.

## 1. Activar web visual
1. [GitHub Pages settings](https://github.com/dvrbuilder94/trabajoai/settings/pages)
2. En **Build and deployment → Source**, seleccionar **GitHub Actions**.
3. [Actions](https://github.com/dvrbuilder94/trabajoai/actions) → **Publish TrabajoAI dashboard** → **Run workflow** si no aparece ejecutado.
4. Comprobar https://dvrbuilder94.github.io/trabajoai/?demo=1 (demo) y https://dvrbuilder94.github.io/trabajoai/ (datos de Supabase).

**No afirmar un despliegue exitoso sin abrir la URL y verificarlo.** El modo demo contiene vacantes ficticias para probar la interfaz.

## 2. Login por enlace de correo
1. [Supabase Auth URL Configuration](https://supabase.com/dashboard/project/lpbqzagdforlafvavgkx/auth/url-configuration)
2. Configurar Site URL = `https://dvrbuilder94.github.io/trabajoai/` y añadir la misma URL a Redirect URLs.
3. [Auth Providers](https://supabase.com/dashboard/project/lpbqzagdforlafvavgkx/auth/providers) → confirmar que **Email** está habilitado.
4. Abrir la app, pulsar **Iniciar sesión**, enviar enlace al correo que usarás en la plataforma, abrir el enlace recibido.
5. Verificar que el botón indique cuenta autenticada y que **aprobar/descartar** persista al recargar y en otra sesión.
6. Cerrar sesión: sin usuario, la UI usa almacenamiento local de demo, no estado remoto.

No hay cuentas creadas por defecto; no crear usuarios ficticios en la base de producción. Si Supabase bloquea el correo por límites del servicio gratuito, configurar SMTP antes de un uso intensivo.

## 3. Sincronizar vacantes automáticamente

El workflow `Collect public job listings` puede producir `data/jobs.json` aunque no tenga conexión a Supabase. Para habilitar sincronización de DB:

1. Abrir [GitHub Actions secrets](https://github.com/dvrbuilder94/trabajoai/settings/secrets/actions).
2. Crear un secreto `SUPABASE_URL` con valor `https://lpbqzagdforlafvavgkx.supabase.co`.
3. Crear un secreto `SUPABASE_SERVICE_ROLE_KEY` con una **clave secreta de backend de Supabase** obtenida en el panel de API keys. Usarla exclusivamente en GitHub Actions; nunca en páginas HTML/JS ni commits.
4. Abrir [Actions](https://github.com/dvrbuilder94/trabajoai/actions) y ejecutar `Collect public job listings`.
5. Verificar número de filas en `public.job_listings` y registro de ejecución. Si alguna fuente falla, comprobar logs y slugs de ATS.

La clave pública `sb_publishable_...` que usa el navegador **no** permite acceso a CV protegido si RLS está bien configurado.

## 4. Seguridad de datos personales

El CV actual está importado a `internal.cv_imports`, fuera del esquema API público; sigue pendiente revisar RLS de staging. **No mostrar ni mover el CV al frontend** hasta que se complete Auth, políticas, propiedad del registro y pruebas de acceso de otro usuario.

Revisar [RLS](https://supabase.com/docs/guides/database/postgres/row-level-security). La recomendación de Supabase para bloquear accesos sin políticas es:

```sql
ALTER TABLE internal.cv_imports ENABLE ROW LEVEL SECURITY;
```

Requiere aprobación consciente del modelo de acceso, porque bloqueará consultas por API hasta crear políticas; no ejecutar a ciegas. Mientras tanto, el esquema `internal` tiene `REVOKE` para roles públicos.

## 5. Criterios mínimos de aceptación
- [ ] Web Pages carga con HTTP 200.
- [ ] Demo funciona incluso si la conexión de datos falla.
- [ ] Carga ofertas públicas desde AIJOBS sin mostrar CV.
- [ ] Login por enlace funciona.
- [ ] Aprobación persistente al recargar y desde segundo navegador.
- [ ] Roles anónimos no acceden al CV ni decisiones personales.
- [ ] Workflow de recolección ejecuta con éxito y actualiza datos.
- [ ] Documentar los resultados de las pruebas con fecha, no confundir código subido con funcionalidad verificada.
