# TrabajoAI — JobHunter AI

MVP de búsqueda y revisión de empleos, sin Lovable. **No postula automáticamente**.

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
