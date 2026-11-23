# KAIROS Salud — web pública

## Cómo actualizar
1. Editá textos en `src/index.html` o `src/profesionales.html`, o los datos de contacto en el bloque `DATOS` de `build.py`.
2. Subí el cambio a GitHub (rama `main`). La publicación es automática (GitHub Actions).

## Versión de prueba vs. producción
- Mientras no haya dominio, el sitio se publica con `noindex` (Google no lo indexa).
- Cuando el dominio esté conectado: en `.github/workflows/deploy.yml` cambiar `python3 build.py` por `python3 build.py --produccion`.
- Cuando se apruebe la habilitación: en `build.py` poner `habilitacion_aprobada: True`.

## Qué NO va en este repositorio
- `portal-turnos.html` (portal interno). Va en un repositorio privado aparte.
- Datos de pacientes, contraseñas o tokens.
