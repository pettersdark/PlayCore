# PlayCore 1.3.0 · Español / English

## Español

- Selector **Español / English** arriba a la derecha, con el estilo nativo de Qt.
- Cambio inmediato, sin reiniciar ni perder la sección, inventario, selecciones o tareas en curso.
- Traducción de secciones, botones, estados, mensajes, errores, ayudas y diálogos propios de PlayCore.
- Preferencia guardada para las siguientes aperturas y compartida con el instalador gráfico.
- Nombres de componentes, rutas, comandos y notas originales de GitHub preservados.

Desde **1.2.0**, instala la 1.3.0 con **Actualizaciones**.
Desde 1.0.0 o 1.1.0, descarga e instala manualmente `PlayCore-1.3.0-Bazzite-x86_64.run`.

![Interfaz en español](https://raw.githubusercontent.com/pettersdark/PlayCore/v1.3.0/docs/images/v1.3/es/proton.png)

## English

- **Español / English** selector in the top-right corner, using the existing native Qt style.
- Instant switching without restarting or losing the open section, inventory, selections, or running tasks.
- Translated sections, buttons, status labels, messages, errors, instructions, and PlayCore dialogs.
- Language preference saved for subsequent launches and shared with the graphical installer.
- Component names, paths, commands, and original GitHub release notes preserved.

On **1.2.0**, use **Actualizaciones / Updates** to install 1.3.0.
On 1.0.0 or 1.1.0, download and install `PlayCore-1.3.0-Bazzite-x86_64.run` manually.

![English interface](https://raw.githubusercontent.com/pettersdark/PlayCore/v1.3.0/docs/images/v1.3/en/proton.png)

---

# PlayCore 1.2.0 · Actualizador integrado / In-app updater

## Español

Esta versión añade la actualización de PlayCore desde la propia aplicación e incluye las mejoras de Proton y los perfiles FSR/OptiScaler de la 1.1.0.

- Nueva sección **Actualizaciones**: versión instalada, búsqueda de versiones estables de GitHub y novedades de cada publicación.
- Comprobación en segundo plano al abrir la app y aviso de una nueva versión en la cabecera.
- Botón para **descargar e instalar**, con confirmación antes de comenzar.
- Verificación del tamaño y SHA-256 del instalador antes de ejecutarlo; también se contrasta el digest de GitHub cuando está disponible.
- Instalación por usuario y reapertura de la versión nueva. La ventana anterior se cierra después de abrir la nueva.
- Conserva los componentes, configuraciones y versiones anteriores de PlayCore. Si falla la actualización, puedes continuar usando la versión actual y reintentar.

**Importante:** si tienes 1.0.0 o 1.1.0, descarga e instala **1.2.0 manualmente una vez**. Desde esta versión podrás actualizar a **1.3.0 y posteriores desde la app**, cuando se publiquen. La descarga e instalación requieren que confirmes la actualización.

Descarga `PlayCore-1.2.0-Bazzite-x86_64.run`, ábrelo y pulsa **Instalar PlayCore**. Las copias ejecutadas desde el código fuente pueden consultar novedades; la actualización desde la app requiere una copia instalada con el instalador.

### Captura

Interfaz real con datos de demostración. La **1.3.0 mostrada es un ejemplo simulado y no está publicada**.

![Actualizador de PlayCore 1.2.0 con una futura versión simulada](https://raw.githubusercontent.com/pettersdark/PlayCore/v1.2.0/docs/images/v1.2/actualizaciones.png)

## English

This release adds in-app PlayCore updates and includes the Proton improvements and FSR/OptiScaler profiles introduced in 1.1.0.

- New **Actualizaciones / Updates** section showing the installed version, stable GitHub releases, and release notes.
- Background checks at startup and a new-version indicator in the header.
- **Download and install** action with confirmation before starting.
- Installer size and SHA-256 verification before execution, including GitHub's asset digest when available.
- Per-user installation and automatic reopening of the new version. The previous window closes after the new version launches.
- Existing components, settings, and previous PlayCore versions are preserved. Failed updates leave the current app available for retry.

**Important:** users on 1.0.0 or 1.1.0 must **download and install 1.2.0 manually once**. After that, **1.3.0 and later can be installed from the app** when published. Download and installation still require your confirmation.

Download and open `PlayCore-1.2.0-Bazzite-x86_64.run`, then click **Instalar PlayCore**. Source checkouts can check releases; in-app installation requires a copy installed with the graphical installer.

The screenshot above shows the actual UI with demonstration data. **The displayed 1.3.0 release is a simulated example and has not been published.** The application UI is in Spanish.

**Requirements / Requisitos:** Linux x86_64, SteamOS/Bazzite, KDE Plasma, Python 3.11+ with venv and safe tarfile filters, glibc 2.34+. Qt dependencies are bundled. Checking and downloading updates requires Internet.

---

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
