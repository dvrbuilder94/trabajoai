# TrabajoAI — JobHunter AI

**Product requirements:** [PRD v1.0](docs/PRD.md) — product scope, acceptance criteria, security and milestones. This document is the source of truth for implementation.

MVP de búsqueda y revisión de empleos, sin Lovable. **No postula automáticamente**.

## Ver la aplicación

- Web: https://dvrbuilder94.github.io/trabajoai/
- **Modo demostración:** https://dvrbuilder94.github.io/trabajoai/?demo=1 (3 vacantes ficticias identificadas como tales).
- Si la URL devuelve 404, ve a **Settings → Pages → Build and deployment → Source: GitHub Actions**. El workflow `Publish TrabajoAI dashboard` prepara el despliegue.
- Los datos reales se cargarán tras una ejecución exitosa del workflow `Collect public job listings` en **Actions**. Las fuentes se configuran en `data/sources.json`.
- GitHub Pages muestra contenido público. **No subir CV ni datos personales al sitio estático**; el CV maestro se guarda en una tabla interna de Supabase.

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
