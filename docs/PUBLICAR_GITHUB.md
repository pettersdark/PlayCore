# Publicación después de probar el instalador

El usuario ha probado el paquete 1.0 y ha autorizado publicarlo en el repositorio
**público `pettersdark/PlayCore`**, usando exclusivamente la cuenta personal.
Usar exclusivamente la cuenta personal indicada, sin recurrir a otras conexiones.

Material local preparado:

- Código fuente y pruebas del proyecto.
- `RELEASE_NOTES.md`, para la descripción de la Release 1.0.0.
- Constructor `scripts/build_release.py`, que genera el fichero gráfico `.run` y SHA-256.
- Paquetes en `entrega/`, excluidos del control de versiones.

Procedimiento de publicación:

1. Subir el código fuente, sin `.venv`, `entrega`, credenciales ni datos locales.
2. Crear el tag y la Release `v1.0.0` usando las notas revisadas.
3. Adjuntar `PlayCore-1.0.0-Bazzite-x86_64.run` y su `.sha256` como assets.
4. Actualizar README con el enlace real a esa descarga. No usar un repositorio ficticio.
5. Comprobar la descarga desde la Release y su suma antes de anunciarla.

Para el usuario final: descargar el `.run` desde la Release, permitir su ejecución
en las propiedades del fichero si el navegador elimina ese permiso, abrirlo con
doble clic y pulsar Instalar PlayCore. No es necesario abrir una terminal.

No hay una automatización que publique al hacer push. Los binarios se suben como
assets de la Release, no como blobs del repositorio. Las notas y las instrucciones
de instalación están en español e inglés. Los artefactos se verifican con SHA-256.
