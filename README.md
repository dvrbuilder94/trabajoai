# TrabajoAI — JobHunter AI

**Product requirements:** [PRD v1.0](docs/PRD.md) — product scope, acceptance criteria, security and milestones. This document is the source of truth for implementation.

MVP de búsqueda y revisión de empleos, sin Lovable. **No postula automáticamente**.

## Ver la aplicación

- Web: https://dvrbuilder94.github.io/trabajoai/
- **Modo demostración:** https://dvrbuilder94.github.io/trabajoai/?demo=1 (3 vacantes ficticias identificadas como tales).
- Si la URL devuelve 404, ve a **Settings → Pages → Build and deployment → Source: GitHub Actions**. El workflow `Publish TrabajoAI dashboard` prepara el despliegue.
- Los datos reales se cargarán tras una ejecución exitosa del workflow `Collect public job listings` en **Actions**. Las fuentes se configuran en `data/sources.json`.
- GitHub Pages muestra contenido público. **No subir CV ni datos personales al sitio estático**; el CV maestro se guarda en una tabla interna de Supabase.

## Supabase sync (optional setup for fully automated persistence)

The app currently uses **Supabase AIJOBS** for public job listings. Three initial candidate listings were manually imported on 2026-11-08, each flagged **unverified for Chile eligibility and application status**. The collector also writes public `data/jobs.json`.

For automated GitHub Actions → Supabase sync, configure two **GitHub Actions repository secrets** under **Settings → Secrets and variables → Actions**:

1. `SUPABASE_URL` = `https://lpbqzagdforlafvavgkx.supabase.co`
2. `SUPABASE_SERVICE_ROLE_KEY` = your Supabase **secret/service_role** key, obtained from the Supabase dashboard. Do **not** paste it into GitHub files, chat, browser code, screenshots, or issues. The GitHub Actions workflow passes it only to a server-side Python process.

Until these are configured, the sync script intentionally skips DB writes and the generated public JSON remains a fallback. There is no user login yet: decisions are currently browser-local and are not submitted applications.

## Cómo funciona
- Dashboard estático en `index.html`.
- `scripts/collect.py` obtiene publicaciones de APIs públicas Greenhouse/Lever configuradas en `data/sources.json`.
- `data/jobs.json` contiene vacantes cargadas; inicialmente está vacío.
- El workflow de GitHub Actions puede actualizar las vacantes diariamente.
- Aprobar una vacante en la interfaz **no** envía una postulación; el estado se conserva solo en el navegador.

## Privacidad
**Este repositorio es público.** No subir CV, documentos personales, credenciales, correo ni respuestas de postulación. GitHub Pages también será visible públicamente si se habilita. La plataforma privada con autenticación y generación de CV es una etapa posterior.

## Probar localmente
```bash
python scripts/collect.py
python -m http.server 8000
```
Abrir http://localhost:8000

## Limitaciones
El ranking es heurístico, no verifica elegibilidad legal de trabajo, remoto desde Chile, sponsor migratorio, salarios ni fechas de apertura. Las fuentes pueden fallar o cambiar. Las postulaciones requieren tu aprobación explícita y una futura integración compatible.
