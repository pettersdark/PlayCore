# PlayCore 1.1.0 · Proton y perfiles FSR/OptiScaler / Proton and FSR/OptiScaler profiles

## Español

Esta versión mejora la instalación de Proton y añade el envío automático de las configuraciones FSR/OptiScaler a Decky Launch Options desde PlayCore.

- **Proton-CachyOS y Proton-GE en modo Latest:** nombres fijos en Steam y metadatos para que ProtonPlus reconozca la instalación y gestione sus actualizaciones.
- Se mantiene la opción de instalar una versión estable independiente y elegir el Steam de destino, nativo o Flatpak.
- **Instalar perfiles FSR/OptiScaler:** un botón envía a Steam los perfiles **OptiScaler**, **FSR 4 Upgrade** y **OptiScaler + FSR 4**, sin copiar scripts manualmente.
- Decky muestra su diálogo para revisar y confirmar la importación. Los perfiles quedan sin activación global y se elige uno por juego; el combinado sustituye a los individuales.
- Comprobación del plugin y del diálogo visible en Steam; los errores o solicitudes pendientes se indican sin afirmar una importación completada.
- El instalador incluye Qt WebSockets, necesario para comunicarse con Steam.

**Instalación:** descarga `PlayCore-1.1.0-Bazzite-x86_64.run`, habilita su ejecución si hace falta y ábrelo con doble clic. Pulsa **Instalar PlayCore** y después **Abrir PlayCore**. Esta versión se instala manualmente.

Para los perfiles, abre Steam/Big Picture con Decky y Launch Options cargados. Se necesita un Proton-CachyOS compatible con la función, el juego y el hardware. El botón prepara opciones de lanzamiento; no instala OptiScaler dentro de los juegos. Revisa y confirma el diálogo de Decky.

### Capturas

Capturas de la interfaz real con datos de demostración, sin datos personales.

![Proton Latest en PlayCore 1.1.0](https://raw.githubusercontent.com/pettersdark/PlayCore/v1.1.0/docs/images/v1.1/proton.png)

![Botón de importación de perfiles FSR/OptiScaler](https://raw.githubusercontent.com/pettersdark/PlayCore/v1.1.0/docs/images/v1.1/decky.png)

## English

This release improves Proton installation and adds automatic delivery of FSR/OptiScaler configurations to Decky Launch Options from PlayCore.

- **Proton-CachyOS and Proton-GE Latest mode:** stable names in Steam and metadata so ProtonPlus can recognize the installation and manage updates.
- Independent stable-version installation and native/Flatpak Steam destination selection remain available.
- **Install FSR/OptiScaler profiles:** one button sends the **OptiScaler**, **FSR 4 Upgrade**, and **OptiScaler + FSR 4** profiles to Steam, without manually copying scripts.
- Review and confirm Decky's import dialog. Global activation stays disabled; select one profile per game. The combined profile replaces the individual options.
- Plugin and visible-dialog checks report errors or pending confirmation without claiming a completed import.
- The installer bundles Qt WebSockets for the local connection to Steam.

**Installation:** download `PlayCore-1.1.0-Bazzite-x86_64.run`, enable executable permission if needed, and double-click it. Click **Instalar PlayCore**, then **Abrir PlayCore**. This version requires manual installation.

For the profiles, open Steam/Big Picture with Decky and Launch Options loaded. A compatible Proton-CachyOS build, game, and hardware are required. This action prepares launch options; it does not install OptiScaler into games. Review and confirm Decky's dialog.

The screenshots above show the actual UI with demonstration data. The application UI is in Spanish.

**Requirements / Requisitos:** Linux x86_64, SteamOS/Bazzite, KDE Plasma, Python 3.11+ with venv and safe tarfile filters, glibc 2.34+. Qt dependencies are bundled. Internet is required to download gaming components.
