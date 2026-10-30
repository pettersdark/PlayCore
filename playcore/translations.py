"""Catálogo inglés de los textos propios de PlayCore; español es el idioma fuente."""
from .catalog import PROFILE_STEPS
from .launch_options import GUIDE, WARNING

# {0}, {1}, ... representan datos de ejecución, nunca identificadores traducidos.
_PAIRS = r'''
Sistema|||System
Aplicaciones|||Applications
Temas|||Themes
Mantenimiento|||Maintenance
Actualizaciones|||Updates
Idioma|||Language
Sí|||Yes
Componente|||Component
Estado local|||Local status
Evidencia|||Evidence
Distribución|||Distribution
Versión|||Version
Hostname|||Hostname
Kernel|||Kernel
Escritorio|||Desktop
Sesión|||Session
Detectado|||Detected
No detectado|||Not detected
Desconocido|||Unknown
Desconocido (passwd no disponible)|||Unknown (passwd unavailable)
Configurada|||Set
Sin contraseña|||No password
Cuenta bloqueada|||Account locked
No comprobado|||Not checked
Pendiente de detección|||Waiting for scan
No se ha iniciado ninguna instalación.|||No installation has been started.
Mostrar mensajes|||Show messages
Ocultar mensajes|||Hide messages
Mensajes de instalación|||Installation messages
Versión {0} · Instalación bajo demanda|||Version {0} · Install on demand
Buscar actualizaciones|||Check for updates
Actualizar detección|||Refresh inventory
Tu equipo de juego, de un vistazo. Consulta el sistema, las aplicaciones y los complementos locales.|||Your gaming system at a glance. View your system, applications, and installed add-ons.
Secciones de PlayCore|||PlayCore sections
Las instalaciones comienzan al pulsar Instalar. Los perfiles se aplican manualmente en CSS Loader; no se modifican las opciones de lanzamiento de los juegos.|||Installations start when you click Install. Apply theme profiles manually in CSS Loader; game launch options are not changed automatically.
Listo para detectar|||Ready to scan
Mantén PlayCore al día|||Keep PlayCore up to date
Versión instalada: {0}|||Installed version: {0}
Busca nuevas versiones estables en el repositorio oficial de GitHub. Tú decides cuándo instalarlas.|||Check the official GitHub repository for new stable releases. You decide when to install them.
Todavía no se han buscado actualizaciones.|||Updates have not been checked yet.
Descargar e instalar|||Download and install
Ver en GitHub|||View on GitHub
La descarga se comprueba con SHA-256. La aplicación se volverá a abrir al terminar. Se conservan tus componentes y la versión anterior.|||The download is verified with SHA-256. The app reopens when installation finishes. Your components and the previous version are preserved.
Esta copia se ejecuta desde el código fuente. Instala la nueva versión con el instalador para activar las actualizaciones desde la app.|||This copy is running from source. Install PlayCore with the installer to enable in-app updates.
Novedades de la versión|||Release notes
Aquí aparecerán las novedades cuando haya una actualización disponible.|||Release notes will appear here when an update is available.
Información del equipo|||System information
Detectando SteamOS o Bazzite…|||Detecting SteamOS or Bazzite…
Contraseña del usuario|||User password
Consultando el estado de la cuenta…|||Checking account status…
Para autorizar instalaciones de Decky necesitas la contraseña de tu usuario. Puedes establecerla o cambiarla con passwd en Konsole. PlayCore no recibe ni guarda tu contraseña. Los Flatpaks y Proton en tu carpeta de usuario no requieren permisos de administrador.|||You need your user password to authorize Decky installations. Set or change it with passwd in Konsole. PlayCore never receives or stores your password. Flatpak apps and Proton in your home folder do not require administrator privileges.
Establecer o cambiar contraseña…|||Set or change password…
En la terminal, sigue los mensajes de passwd. Al escribir la contraseña no aparecen caracteres. Si te pide la contraseña actual y nunca has definido una, prueba a dejarla vacía pulsando Intro.|||Follow the passwd prompts in the terminal. No characters appear as you type your password. If it asks for your current password and you have never set one, try leaving it blank by pressing Enter.
Heroic y ProtonPlus: consulta Flatpak de usuario y sistema, además de ejecutables disponibles en PATH.|||Heroic and ProtonPlus: checks user and system Flatpak installations, plus executables available in PATH.
Proton-CachyOS y Proton-GE: detecta herramientas instaladas en Steam nativo y Flatpak. La selección para cada juego se realiza en Steam.|||Proton-CachyOS and Proton-GE: detects tools installed in native and Flatpak Steam. Select a tool for each game in Steam.
Decky Loader y los cuatro plugins solicitados. Se leen los manifiestos locales de ~/homebrew/plugins; no se comprueba si el servicio está ejecutándose.|||Decky Loader and four plugins. Reads local manifests in ~/homebrew/plugins; it does not check whether the service is running.
Instalación Flatpak para tu usuario desde Flathub. Se descargarán la aplicación y sus dependencias.|||Install Flatpak apps from Flathub for your user account. The app and its dependencies will be downloaded.
Instala primero Decky Loader y después los plugins. Se descargan las versiones estables oficiales con SHA-256. Cada plugin nuevo pide permisos de administrador y reinicia Decky. No se sobrescriben componentes existentes.|||Install Decky Loader first, then the plugins. Official stable releases are downloaded and verified with SHA-256. Each new plugin requires administrator privileges and restarts Decky. Existing components are preserved.
Instalar Decky Loader ejecuta su instalador oficial: crea el servicio y habilita la depuración remota de Steam; en Bazzite también puede ajustar el contexto SELinux. Configura tu contraseña desde Sistema antes de autorizarlo.|||Installing Decky Loader runs its official installer: it creates the service and enables Steam remote debugging; on Bazzite it may also adjust the SELinux context. Set your password in System before authorizing it.
Instalar perfiles FSR/OptiScaler|||Install FSR/OptiScaler profiles
Ver procedimiento manual de importación…|||View manual import instructions…
Instala Proton-CachyOS SLR o Proton-GE. Latest mantiene un nombre fijo en Steam y los datos de instalación para que ProtonPlus lo reconozca y lo actualice. Reinicia Steam después de instalarlo y selecciónalo en Compatibilidad.|||Install Proton-CachyOS SLR or Proton-GE. Latest keeps a fixed name in Steam and installation metadata so ProtonPlus can recognize and update it. Restart Steam after installation and select it under Compatibility.
Modalidad de instalación de Proton|||Proton installation mode
Latest · para actualizar con ProtonPlus|||Latest · update with ProtonPlus
Versión independiente · última estable|||Separate version · latest stable
Instalación de Steam para Proton|||Steam installation for Proton
Machine Ready TV · Tema base y 14 dependencias CSS. Los manifiestos indican presencia local, no activación ni compatibilidad de versión.|||Machine Ready TV · Base theme and 14 CSS dependencies. Manifests indicate local presence, not activation or version compatibility.
Dependencias CSS|||CSS dependencies
Tema CSS seleccionado|||Selected CSS theme
Machine Ready TV instala los temas y perfiles del repositorio y las 14 dependencias. Conserva todas las carpetas existentes. También puedes instalar una dependencia concreta:|||Machine Ready TV installs the repository's themes, profiles, and 14 dependencies. All existing folders are preserved. You can also install an individual dependency:
Perfil local para consultar; no se aplica|||Local profile to view; does not apply it
Sin selección · elige el perfil manualmente en CSS Loader|||No selection · choose a profile manually in CSS Loader
No se ha elegido ningún perfil. PlayCore no cambia la selección de CSS Loader.|||No profile selected. PlayCore does not change the CSS Loader selection.
Configuración manual en CSS Loader|||Manual setup in CSS Loader
Fuente y descarga manual: {0}|||Source and manual download: {0}
Diagnóstico de solo lectura. Actualizar detección vuelve a consultar el inventario; no borra cachés, actualiza paquetes ni reinicia servicios.|||Read-only diagnostics. Refresh inventory scans again; it does not clear caches, update packages, or restart services.
Espacio libre: pendiente|||Free space: pending
Avisos de diagnóstico|||Diagnostic messages
Consultando las novedades…|||Checking release notes…
Buscando versiones estables en GitHub…|||Checking GitHub for stable releases…
PlayCore está al día. Tienes la versión {0}.|||PlayCore is up to date. You have version {0}.
No hay una versión estable más reciente disponible.|||No newer stable release is available.
Nueva versión disponible: {0} · {1} MiB|||New version available: {0} · {1} MiB
Actualizar a {0}|||Update to {0}
Nueva versión: {0}|||New version: {0}
Actualizar PlayCore|||Update PlayCore
¿Descargar e instalar PlayCore {0}?\n\nLa aplicación se volverá a abrir al terminar. Tus componentes instalados se conservan.|||Download and install PlayCore {0}?\n\nThe app will reopen when installation finishes. Your installed components will be preserved.
Descargando el instalador y comprobando su integridad…|||Downloading the installer and verifying its integrity…
No se pudo identificar la instalación actual.|||Could not identify the current installation.
Descarga verificada. Instalando PlayCore; se abrirá al terminar…|||Download verified. Installing PlayCore; it will reopen when finished…
No se pudo iniciar el instalador: {0}|||Could not start the installer: {0}
La actualización no se completó. Puedes seguir usando esta versión y volver a intentarlo.|||The update did not complete. You can keep using this version and try again.
No se han podido consultar las novedades. Puedes volver a buscar actualizaciones.|||Could not retrieve release notes. You can check for updates again.
Instalar {0}|||Install {0}
Conectando con Steam para solicitar la importación de perfiles…|||Connecting to Steam to request profile import…
Perfiles preparados · importación pendiente en Decky|||Profiles prepared · awaiting import in Decky
Script de importación para la consola de Steam|||Import script for the Steam console
Copiar script de importación|||Copy import script
Script copiado · ejecuta y confirma en Steam|||Script copied · run and confirm in Steam
Cerrar|||Close
Solicita la importación directamente en Steam; revisa y confirma en Decky.|||Requests import directly in Steam; review and confirm in Decky.
{0} detectado|||{0} detected
Instalar {0} · {1}|||Install {0} · {1}
última estable|||latest stable
Instalar lo que falta de Machine Ready TV y sus dependencias|||Install missing Machine Ready TV components and dependencies
Completa primero los requisitos: Decky / CSS Loader o Steam de destino|||Complete the prerequisites first: Decky / CSS Loader or a target Steam installation
Disponible en SteamOS y Bazzite; requiere conexión a Internet|||Available on SteamOS and Bazzite; requires an Internet connection
Instalación de {0} completada.|||Installation of {0} completed.
No se completó la instalación de {0}.|||Installation of {0} did not complete.
Error: {0}|||Error: {0}
Instalación solicitada: {0}|||Installation requested: {0}
Konsole abrirá passwd para tu usuario. Introduce allí la contraseña siguiendo sus mensajes; PlayCore no registra la conversación. Cierra Konsole al terminar y se actualizará el estado.|||Konsole will open passwd for your user account. Enter your password there, following its prompts; PlayCore does not log the conversation. Close Konsole when finished to refresh the status.
La terminal ha terminado. Revisa el estado de la contraseña; puedes volver a abrirla si no completaste el cambio.|||The terminal has finished. Check your password status; you can open it again if you did not complete the change.
No se pudo abrir o mantener Konsole: {0}|||Could not open or keep Konsole running: {0}
Perfil consultado: {0}. Para activarlo, selecciónalo manualmente en CSS Loader después de Nav Patch y Refresh.|||Profile being viewed: {0}. To activate it, select it manually in CSS Loader after Nav Patch and Refresh.
Leyendo inventario local…|||Reading local inventory…
No se pudo completar la detección: {0}|||Could not complete the scan: {0}
Sistema objetivo detectado: SteamOS / Bazzite.|||Target system detected: SteamOS / Bazzite.
Distribución fuera de los sistemas objetivo. El inventario sigue disponible; no se ejecutan cambios.|||This distribution is outside the target systems. Inventory remains available; no changes are made.
Usuario: {0} · Contraseña: {1}|||User: {0} · Password: {1}
Selecciona Steam de destino…|||Select target Steam installation…
Espacio libre en el volumen del usuario: {0} GiB|||Free space on the user volume: {0} GiB
Espacio libre: desconocido|||Free space: unknown
Detección completada sin errores de lectura.|||Scan completed without read errors.
No detectado significa que no se encontró en las rutas comprobadas.|||Not detected means it was not found in the checked locations.
Detección completada · {0} avisos|||Scan completed · {0} warnings
Espera a que termine la consulta o descarga de la actualización…|||Wait for the update check or download to finish…
Termina y cierra la terminal de contraseña antes de cerrar PlayCore.|||Finish and close the password terminal before closing PlayCore.
Espera a que termine la instalación antes de cerrar…|||Wait for the installation to finish before closing…
Espera a que termine la lectura antes de cerrar…|||Wait for the scan to finish before closing…
Sin notas de versión.|||No release notes.
La versión publicada no es una versión estable válida.|||The published version is not a valid stable release.
La descarga no pertenece a la versión oficial de PlayCore.|||The download does not belong to the official PlayCore release.
La nueva versión todavía no incluye el instalador y su SHA-256. Inténtalo más tarde.|||The new release does not include the installer and its SHA-256 yet. Try again later.
El tamaño del instalador no es válido.|||The installer size is invalid.
La respuesta de GitHub es demasiado grande.|||The GitHub response is too large.
Todavía no hay una versión pública disponible en GitHub.|||No public release is available on GitHub yet.
GitHub ha limitado las consultas. Vuelve a intentarlo más tarde.|||GitHub has rate-limited requests. Try again later.
No se pudo consultar GitHub (HTTP {0}).|||Could not query GitHub (HTTP {0}).
No se pudo conectar con GitHub. Comprueba tu conexión e inténtalo de nuevo.|||Could not connect to GitHub. Check your connection and try again.
El actualizador necesita Linux x86_64.|||The updater requires Linux x86_64.
El fichero SHA-256 no es válido.|||The SHA-256 file is invalid.
El SHA-256 publicado por GitHub no coincide con el fichero de comprobación.|||GitHub's SHA-256 digest does not match the checksum file.
La descarga debe utilizar HTTPS.|||The download must use HTTPS.
El instalador supera el tamaño esperado.|||The installer exceeds the expected size.
El instalador está incompleto o su SHA-256 no coincide. No se ha instalado nada.|||The installer is incomplete or its SHA-256 does not match. Nothing has been installed.
Se necesita Konsole y passwd para cambiar la contraseña desde PlayCore.|||Konsole and passwd are required to change your password from PlayCore.
No se puede leer {0}: {1}|||Cannot read {0}: {1}
No se pudo interpretar {0}: {1}|||Could not parse {0}: {1}
falta un nombre válido|||a valid name is missing
consulta fallida|||query failed
Espacio libre: {0}|||Free space: {0}
Sistema desconocido|||Unknown system
No se pudo obtener información de Flatpak|||Could not retrieve Flatpak information
Desconocido (falló consulta Flatpak)|||Unknown (Flatpak query failed)
Steam recibió la solicitud, pero no se ha podido confirmar que el diálogo de Decky esté visible. Abre Steam en modo Big Picture y el panel Decky → Launch Options. Si no hay un diálogo pendiente, vuelve a pulsar el botón en PlayCore. No se ha confirmado la importación; no necesitas reiniciar el equipo.|||Steam received the request, but the Decky dialog could not be confirmed as visible. Open Steam in Big Picture mode and the Decky → Launch Options panel. If there is no pending dialog, click the button in PlayCore again. Import has not been confirmed; you do not need to restart your computer.
Respuesta inesperada de Steam.|||Unexpected response from Steam.
Steam no confirmó la recepción. Comprueba el diálogo antes de repetir.|||Steam did not confirm receipt. Check the dialog before trying again.
Steam no pudo ejecutar la solicitud. Comprueba el diálogo antes de repetir.|||Steam could not execute the request. Check the dialog before trying again.
No se puede conectar con Steam. Abre Big Picture con Decky y la depuración remota habilitada, y vuelve a pulsar el botón.|||Could not connect to Steam. Open Big Picture with Decky and remote debugging enabled, then click the button again.
Steam no confirmó la solicitud. Comprueba el diálogo antes de repetir.|||Steam did not confirm the request. Check the dialog before trying again.
Diálogo de importación localizado en Steam. Revisa y confirma los tres perfiles en Decky; deja Enable globally apagado. Importación pendiente de tu confirmación.|||Import dialog found in Steam. Review and confirm the three profiles in Decky; leave Enable globally off. Import is awaiting your confirmation.
Launch Options está instalado pero no está cargado en una ventana accesible. Abre Big Picture y el panel de Decky → Launch Options, y vuelve a intentarlo.|||Launch Options is installed but is not loaded in an accessible window. Open Big Picture and the Decky → Launch Options panel, then try again.
Decky Launch Options no detectado. Instálalo desde Decky y actualiza la detección.|||Decky Launch Options was not detected. Install it from Decky and refresh the inventory.
La descarga supera el límite de tamaño.|||The download exceeds the size limit.
La descarga de Proton supera 1 GiB.|||The Proton download exceeds 1 GiB.
Descargando Proton: {0} MiB…|||Downloading Proton: {0} MiB…
El SHA-256 de Proton no coincide con la publicación oficial.|||The Proton SHA-256 does not match the official release.
Se esperaba una publicación estable.|||A stable release was expected.
La publicación apunta a un origen no permitido.|||The release points to a disallowed source.
La publicación no proporciona un SHA-256 válido.|||The release does not provide a valid SHA-256.
No se encuentra {0} en la publicación estable.|||Could not find {0} in the stable release.
La publicación no proporciona SHA-256. Usa la instalación desde Decky.|||The release does not provide SHA-256. Install it from Decky.
No se encuentra el ZIP compilado en la publicación estable.|||Could not find the compiled ZIP in the stable release.
PolicyKit (pkexec) no está disponible para solicitar permisos.|||PolicyKit (pkexec) is unavailable to request privileges.
Autoriza la instalación en la ventana del escritorio. Si no tienes contraseña, configúrala desde Sistema.|||Authorize installation in the desktop dialog. If you do not have a password, set one in System.
Instala primero Decky Loader y CSS Loader.|||Install Decky Loader and CSS Loader first.
Instala primero el plugin CSS Loader desde la sección Decky.|||Install the CSS Loader plugin from the Decky section first.
{0}: ya presente; se conserva.|||{0}: already present; preserved.
Consultando el tema {0} en DeckThemes…|||Looking up theme {0} on DeckThemes…
No se encuentra una única coincidencia oficial para {0}.|||Could not find a unique official match for {0}.
El tema {0} no está aprobado o no está disponible.|||Theme {0} is not approved or is unavailable.
{0}: archivos instalados; activación manual en CSS Loader.|||{0}: files installed; activate manually in CSS Loader.
Flatpak no está disponible en este equipo.|||Flatpak is unavailable on this computer.
Instalando {0} desde Flathub para tu usuario…|||Installing {0} from Flathub for your user account…
Necesitas Decky Loader instalado en ~/homebrew antes de instalar el plugin.|||Decky Loader must be installed in ~/homebrew before installing the plugin.
Consultando la versión estable de {0}…|||Checking the stable release of {0}…
{0} no está disponible en la tienda de Decky.|||{0} is unavailable in the Decky store.
La tienda no proporciona un SHA-256 válido.|||The store does not provide a valid SHA-256.
El origen del paquete no es el esperado.|||The package source is not the expected one.
Descargando el plugin y verificando SHA-256…|||Downloading the plugin and verifying SHA-256…
Decky Loader ya está instalado; se conserva.|||Decky Loader is already installed; preserved.
Descargando el instalador estable oficial de Decky Loader…|||Downloading the official stable Decky Loader installer…
No coincide el SHA-256 del instalador de Decky.|||The Decky installer SHA-256 does not match.
No se encuentra Steam. Abre Steam al menos una vez antes de instalar Proton.|||Steam was not found. Open Steam at least once before installing Proton.
Selecciona la instalación de Steam de destino.|||Select the target Steam installation.
El destino no es una instalación de Steam detectada.|||The target is not a detected Steam installation.
{0} Latest ya existe en {1}. Usa ProtonPlus para actualizarlo.|||{0} Latest already exists at {1}. Use ProtonPlus to update it.
Arquitectura no soportada por este instalador de Proton.|||This architecture is not supported by the Proton installer.
No se encuentra una única publicación de {0} para esta arquitectura.|||Could not find a unique release of {0} for this architecture.
Última versión estable de {0}: {1}|||Latest stable release of {0}: {1}
Necesitas espacio para la descarga y al menos 5 GiB para descomprimir Proton.|||You need space for the download and at least 5 GiB to extract Proton.
Extrayendo {0} en la instalación de Steam elegida…|||Extracting {0} into the selected Steam installation…
Instalado en {0}. Reinicia Steam y selecciona {1} manualmente en Compatibilidad.|||Installed at {0}. Restart Steam and manually select {1} under Compatibility.
Consultando una revisión fija del repositorio Machine Ready TV…|||Checking a pinned revision of the Machine Ready TV repository…
La revisión del repositorio no es válida.|||The repository revision is invalid.
Machine Ready TV: {0} carpetas añadidas y {1} existentes conservadas.|||Machine Ready TV: {0} folders added and {1} existing folders preserved.
Activa Nav Patch, pulsa Refresh y elige manualmente el perfil en CSS Loader.|||Enable Nav Patch, click Refresh, and choose a profile manually in CSS Loader.
Pulsa Refresh en CSS Loader; la activación es manual.|||Click Refresh in CSS Loader; activation is manual.
Este componente todavía requiere instalación manual.|||This component still requires manual installation.
No se autorizó la instalación. El plugin no se ha instalado.|||Installation was not authorized. The plugin has not been installed.
La instalación falló.|||Installation failed.
La suma SHA-256 del paquete no coincide con la publicación oficial.|||The package SHA-256 does not match the official release.
El paquete supera el tamaño permitido.|||The package exceeds the size limit.
El contenido descomprimido supera el límite permitido.|||The extracted contents exceed the size limit.
El ZIP contiene una ruta o tipo de archivo no permitido.|||The ZIP contains a disallowed path or file type.
Falta {0} en el plugin compilado.|||{0} is missing from the compiled plugin.
La identidad o los permisos del plugin no son los esperados.|||The plugin identity or permissions are not as expected.
El paquete necesita un método de instalación diferente. Usa Decky.|||The package needs a different installation method. Use Decky.
{0} ya existe. Usa Decky para actualizarlo.|||{0} already exists. Use Decky to update it.
El plugin se instaló desde otra aplicación. Actualiza el inventario.|||The plugin was installed by another application. Refresh the inventory.
El ZIP de temas supera el límite permitido.|||The theme ZIP exceeds the size limit.
El ZIP contiene rutas, enlaces o tipos de archivo no permitidos.|||The ZIP contains disallowed paths, links, or file types.
No se encuentra un único tema {0} en el ZIP.|||Could not find a unique {0} theme in the ZIP.
El ZIP contiene carpetas ajenas al tema solicitado.|||The ZIP contains folders unrelated to the requested theme.
El paquete de Machine Ready TV no tiene la estructura esperada.|||The Machine Ready TV package does not have the expected structure.
Falta el tema base Machine Ready.|||The Machine Ready base theme is missing.
El paquete contiene nombres de tema o perfil duplicados.|||The package contains duplicate theme or profile names.
Manifiesto Proton Latest no válido.|||Invalid Proton Latest manifest.
Manifiesto Proton Latest incompleto.|||Incomplete Proton Latest manifest.
Se esperaba una única herramienta Proton con display_name.|||A single Proton tool with display_name was expected.
El archivo Proton supera el límite permitido.|||The Proton archive exceeds the size limit.
El archivo Proton contiene una ruta no permitida.|||The Proton archive contains a disallowed path.
El archivo Proton contiene un tipo de archivo no permitido.|||The Proton archive contains a disallowed file type.
El archivo Proton contiene un enlace absoluto.|||The Proton archive contains an absolute link.
Un enlace de Proton sale de su carpeta.|||A Proton link points outside its folder.
El archivo no contiene una única herramienta {0}.|||The archive does not contain a single {0} tool.
Faltan los archivos de una herramienta de compatibilidad Steam.|||Steam compatibility tool files are missing.
Esta versión de {0} ya está instalada.|||This version of {0} is already installed.
Instalar PlayCore {0}|||Install PlayCore {0}
Actualizar PlayCore {0}|||Update PlayCore {0}
Instala PlayCore para SteamOS o Bazzite en tu cuenta de usuario.|||Install PlayCore for SteamOS or Bazzite in your user account.
Incluye sus bibliotecas Qt. No necesita conexión ni permisos de administrador para instalar PlayCore.|||Qt libraries are included. Installing PlayCore requires neither an Internet connection nor administrator privileges.
Al terminar tendrás un acceso en el menú de aplicaciones. Los componentes de juego se instalan después, desde PlayCore.|||A launcher will be added to the application menu. Gaming components can be installed later from PlayCore.
Destino: {0}|||Destination: {0}
Todo listo. Pulsa Instalar PlayCore para comenzar.|||Ready. Click Install PlayCore to begin.
Abrir PlayCore|||Open PlayCore
Instalar PlayCore|||Install PlayCore
Actualizando PlayCore. La aplicación se volverá a abrir al terminar.|||Updating PlayCore. The app will reopen when finished.
Instalando PlayCore. Espera a que termine…|||Installing PlayCore. Please wait…
El proceso terminó sin crear el lanzador de PlayCore.|||The process finished without creating the PlayCore launcher.
Instalación de PlayCore {0} completada. Ya puedes abrir la aplicación.|||PlayCore {0} installation completed. You can now open the app.
Instalado|||Installed
No se completó la instalación. Abre los mensajes para consultar el motivo.|||Installation did not complete. Open the messages to see why.
Reintentar instalación|||Retry installation
No se pudo iniciar la instalación: {0}|||Could not start installation: {0}
La instalación terminó, pero no se pudo abrir la aplicación.|||Installation finished, but the app could not be opened.
Comprobando la integridad del paquete…|||Verifying package integrity…
Copiando PlayCore y creando su entorno privado…|||Copying PlayCore and creating its private environment…
Instalando las bibliotecas Qt incluidas, sin conexión…|||Installing bundled Qt libraries offline…
Comprobando que Qt y PlayCore se pueden importar…|||Checking that Qt and PlayCore can be imported…
Acceso al menú: {0}|||Application menu entry: {0}
Lanzador: {0}|||Launcher: {0}
Instalación completada. Abre PlayCore desde el menú de aplicaciones.|||Installation completed. Open PlayCore from the application menu.
También puedes ejecutar:|||You can also run:
Ya puedes retirar el USB o borrar la carpeta del instalador.|||You can now remove the USB drive or delete the installer folder.
No se completó la instalación: {0}|||Installation did not complete: {0}
El manifiesto contiene una ruta no permitida.|||The manifest contains a disallowed path.
Archivo dañado o modificado: {0}. Vuelve a copiar el paquete completo.|||Damaged or modified file: {0}. Copy the complete package again.
El paquete contiene archivos ausentes o inesperados.|||The package contains missing or unexpected files.
Abre el instalador como usuario normal, sin sudo.|||Open the installer as a regular user, without sudo.
Se necesita Python 3.11 o posterior en el sistema de destino.|||Python 3.11 or later is required on the target system.
Este paquete es para Linux x86_64 (Bazzite/SteamOS de 64 bits).|||This package is for Linux x86_64 (64-bit Bazzite/SteamOS).
Se necesita glibc 2.34 o posterior para las bibliotecas Qt incluidas.|||The bundled Qt libraries require glibc 2.34 or later.
Esta revisión de Python no incluye los filtros seguros de tarfile. Actualiza Python desde tu distribución.|||This Python revision does not include safe tarfile filters. Update Python through your distribution.
Ya existe un acceso ajeno a este instalador: {0}|||A shortcut not managed by this installer already exists: {0}
Se esperaba un único wheel de pip incluido.|||A single bundled pip wheel was expected.
'''

ENGLISH = {}
for _line in _PAIRS.strip().splitlines():
    _source, _target = _line.split('|||')
    ENGLISH[_source.replace('\\n', '\n')] = _target.replace('\\n', '\n')

ENGLISH[WARNING] = (
    'Requires a compatible Proton-CachyOS version selected for the game. '
    'The presence of Proton does not guarantee game or hardware compatibility. '
    'Do not turn on Enable globally. Choose one profile per game; the combined '
    'profile replaces the individual options.'
)
ENGLISH.update(zip(PROFILE_STEPS, (
    'Install Decky Loader and CSS Loader from Decky, then install Machine Ready TV and its 14 dependencies from Themes.',
    'PlayCore copies themes and .profile folders to ~/homebrew/themes, preserving existing ones; it does not activate any profile.',
    'In Gaming Mode, open CSS Loader → Settings (gear) → Enable Nav Patch and turn it on.',
    'Return to CSS Loader in the QAM, scroll to the bottom, and click Refresh.',
    'Manually select and apply your preferred Machine Ready profile in CSS Loader.',
)))
ENGLISH[GUIDE] = '''PlayCore prepares the request; nothing has been imported yet.
1. Open Steam/Big Picture with Decky and Launch Options loaded.
2. In Chrome/Chromium open chrome://inspect/#devices, configure localhost:8081
   (or DEVICE_IP:8081 from another computer), and click Inspect for the Steam window
   containing Decky. Steam remote debugging must be enabled.
3. In Console check window.hasDeckyLaunchOptions === true. If it is not true,
   select the correct window/context or load the plugin. Do not use a web page's
   console or a Qt window: they do not share Steam's window.
4. Copy the script with the button and run it in that console. Review the code
   before pasting; if the browser blocks pasting, follow its review procedure.
5. Decky will ask for I understand and then Add to Decky Launch Options. Check the
   three commands and leave Enable globally off for all of them; you can cancel.
6. In Decky → Launch Options → Manage Launch Options, find the PlayCore group and
   OptiScaler, FSR 4 Upgrade, and OptiScaler + FSR 4. Check their IDs, On command,
   empty Off command, shared Value ID, and Enable globally off. No default value.
7. In a game's options, select None to disable, or choose one value in the selector.
   First remove/disable equivalent profiles or variables in Original launch options;
   the selector only excludes the three values imported by PlayCore.
To repeat, use the same script and keep the IDs: the plugin updates those entries.
Do not use Duplicate or create manual copies. The plugin may retain a previous
activation: turn it off in Manage Launch Options BEFORE importing again.
Without remote debugging or a version supporting this event and selectors, update
 the plugin or leave import pending. No internal files are modified.
Source: https://github.com/Wurielle/decky-launch-options#integration-with-third-party-plugins
'''

ENGLISH.update({
    'Demostración': 'Demonstration',
    'Este ayudante debe iniciarse desde PlayCore mediante PolicyKit.': 'This helper must be started from PlayCore through PolicyKit.',
    'Se esperaba el componente, el paquete y su SHA-256.': 'The component, package, and its SHA-256 were expected.',
    'Abre PlayCore como usuario normal.': 'Open PlayCore as a regular user.',
    'Componente no permitido.': 'Disallowed component.',
    'Decky ya está instalado. No se reemplaza desde este instalador.': 'Decky is already installed. This installer does not replace it.',
    'No coincide el SHA-256 del instalador oficial de Decky.': 'The official Decky installer SHA-256 does not match.',
    'El instalador oficial de Decky terminó con errores. Revisa el registro.': 'The official Decky installer finished with errors. Check the log.',
    'Instalador oficial de Decky completado.': 'Official Decky installer completed.',
    'No se encuentra Decky en ~/homebrew. Instálalo primero.': 'Decky was not found in ~/homebrew. Install it first.',
    '{0} {1}: archivos instalados.': '{0} {1}: files installed.',
    'El plugin está copiado, pero no se pudo reiniciar Decky: {0}': 'The plugin has been copied, but Decky could not be restarted: {0}',
    'El plugin está copiado, pero Decky no está activo. Consulta su servicio.': 'The plugin has been copied, but Decky is not active. Check its service.',
    'Decky reiniciado. Comprueba {0} en el menú Decky de Gaming Mode.': 'Decky restarted. Check {0} in the Decky menu in Gaming Mode.',
})

ENGLISH.update({
    'Versión {0}': 'Version {0}',
    'Vista de demostración del actualizador': 'Updater demonstration',
    '{0}: paquete verificado.': '{0}: package verified.',
})

ENGLISH['Flatpak {0}: {1}'] = 'Flatpak {0}: {1}'
