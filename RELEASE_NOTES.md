# PlayCore 1.0.0 — Español / English

## Español

Primera publicación pública, con el instalador probado satisfactoriamente por el usuario.

**Instalación sin terminal:** descarga `PlayCore-1.0.0-Bazzite-x86_64.run`, habilita
su ejecución desde Propiedades → Permisos si hace falta, ábrelo con doble clic y pulsa
Instalar PlayCore. Al terminar, pulsa Abrir PlayCore o búscalo en el menú de aplicaciones.

- Detección e instalación de Proton-GE junto a Proton-CachyOS, en Steam nativo o Flatpak.
- Mensaje final «Instalación de [componente] completada» que se conserva al actualizar el inventario.
- Panel de mensajes reducido y plegable mediante Mostrar/Ocultar mensajes.
- Instalador gráfico offline para Linux x86_64: un fichero `.run`, sin terminal.
- Instalación por usuario y acceso en el menú de aplicaciones, conservando las versiones anteriores.
- Mantiene Heroic, ProtonPlus, Decky Loader, los cuatro plugins, Machine Ready TV y sus 14 dependencias.
- Conserva la selección manual del perfil Machine Ready TV y los pasos de Nav Patch y Refresh.
- Permite establecer o cambiar la contraseña del usuario mediante passwd en Konsole, sin guardarla en PlayCore.

Descarga: `PlayCore-1.0.0-Bazzite-x86_64.run` y su `.sha256`.
Requiere Python 3.11+ con venv y filtros de tarfile, glibc 2.34+, KDE Plasma y Linux x86_64.
Las dependencias Qt están incluidas; descargar componentes desde PlayCore sí necesita Internet.

## English

First public release. The user has successfully tested the graphical installer.

**No-terminal installation:** download `PlayCore-1.0.0-Bazzite-x86_64.run`, allow
execution in Properties → Permissions if needed, double-click it and select
Instalar PlayCore (Install PlayCore). Then click Abrir PlayCore (Open PlayCore)
or use the application-menu launcher. The app UI is currently in Spanish.

- Detect and install Proton-GE and Proton-CachyOS for native or Flatpak Steam.
- Persistent installation-completed messages after inventory refresh.
- Smaller log panels with show/hide controls.
- A single offline graphical `.run` installer for Linux x86_64.
- Per-user installation and an application-menu launcher, retaining previous versions.
- Heroic, ProtonPlus, Decky Loader, SteamGridDB, HLTB, CSS Loader and Decky Launch Options.
- Machine Ready TV themes, profiles and 14 CSS dependencies; profile activation remains manual.
- Account password setup/change through Konsole and passwd; PlayCore never stores the password.

Requires Linux x86_64, KDE Plasma, Python 3.11+ with venv and safe tarfile filters,
glibc 2.34+ and about 1 GB free. Qt dependencies are bundled; Python is not.
Installing gaming components from the app requires Internet. The installer is offline.

68 automated tests and an offline graphical installation/launch check passed.
The full catalog is not guaranteed compatible with every Steam version or device.

[Español / English instructions](https://github.com/pettersdark/PlayCore#readme)
