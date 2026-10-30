# Perfiles FSR/OptiScaler

En **Decky → Instalar perfiles FSR/OptiScaler**, PlayCore comprueba el manifiesto
local de Launch Options y envía una solicitud de importación a Steam. El botón se habilita
cuando se detecta el plugin y vuelve a comprobar su presencia al pulsarlo.
Detectado no significa que esté cargado en Steam. No se instala ni activa OptiScaler
con esta acción: se preparan opciones de lanzamiento.

Requieren una **versión compatible de Proton-CachyOS**, seleccionada en las propiedades
de compatibilidad del juego. La versión, el juego y el hardware deben admitir estas
funciones; detectar Proton-CachyOS no garantiza que funcionen.

| Valor | ID estable | On command |
| --- | --- | --- |
| OptiScaler | `playcore-optiscaler` | `PROTON_USE_OPTISCALER=1 %command%` |
| FSR 4 Upgrade | `playcore-fsr4` | `PROTON_FSR4_UPGRADE=1 %command%` |
| OptiScaler + FSR 4 | `playcore-optiscaler-fsr4` | `PROTON_USE_OPTISCALER=1 PROTON_FSR4_UPGRADE=1 %command%` |

Las tres entradas llevan `enableGlobally=false`, `off=""`, `fallbackValue=false`,
`group="PlayCore"` y `valueId="playcore-fsr-optiscaler"`. Cada entrada tiene
su propio `name`: **OptiScaler**, **FSR 4 Upgrade** y **OptiScaler + FSR 4**,
también usado en `valueName`. El Value ID compartido forma un selector exclusivo: el combinado
sustituye a los individuales. No se importa un cuarto perfil ni se elige uno por defecto.

## Importación con confirmación en Steam

El procedimiento habitual es:

1. Abre Steam/Big Picture con Decky y Launch Options cargados.
2. En PlayCore pulsa **Instalar perfiles FSR/OptiScaler**.
3. Vuelve a Steam y acepta el diálogo de Decky: **I understand**, revisa los tres
   valores con **Enable globally** apagado y confirma **Add to Decky Launch Options**.
4. Comprueba el resultado en **Manage Launch Options** como se explica abajo.

No necesitas copiar código ni abrir Chrome. PlayCore usa la conexión de depuración
local de Steam ya habilitada en `127.0.0.1:8081`, localiza una ventana donde el plugin
declara su disponibilidad y emite el evento público mediante
[Runtime.evaluate de CDP](https://chromedevtools.github.io/devtools-protocol/tot/Runtime/#method-evaluate).
La conexión WebSocket usa Qt y solo admite destinos locales del mismo puerto.
No habilita la depuración, reinicia Steam, confirma diálogos ni cambia ajustes del
plugin. Una solicitud enviada se muestra como **pendiente de confirmación**, nunca
como importación completada. Un envío con resultado incierto no se reintenta automáticamente.

PlayCore comprueba además que el diálogo con los perfiles aparece en una ventana de
Steam. Launch Options puede seguir marcado como cargado en el contexto compartido
cuando Steam está en modo escritorio, aunque no muestre el diálogo. Si no se puede
localizar, PlayCore avisa: abre Big Picture y el panel de Launch Options, comprueba
que no haya una confirmación pendiente y vuelve a pulsar el botón. No hace falta
reiniciar el equipo. Localizar el diálogo tampoco confirma que se hayan guardado
los perfiles: hay que aceptarlos en Decky.

Si falta la conexión o el plugin no está cargado, la aplicación explica cómo volver
a intentarlo. **Ver procedimiento manual de importación…** conserva la alternativa
de consola descrita a continuación.

La [API oficial de integración](https://github.com/Wurielle/decky-launch-options#integration-with-third-party-plugins)
recibe un `CustomEvent` llamado `dlo-add-launch-options`, cuyo `detail` es la lista de
opciones. `window.hasDeckyLaunchOptions` permite comprobar la disponibilidad en esa
ventana. El [receptor](https://github.com/Wurielle/decky-launch-options/blob/dev/src/index.tsx)
y el [diálogo de importación](https://github.com/Wurielle/decky-launch-options/blob/dev/src/components/batch-add-launch-options.tsx)
se ejecutan dentro del frontend de Steam. Una aplicación PySide6 no comparte su
objeto `window`; emitirlo en Qt o en un navegador normal no llega a Decky.

Como alternativa, PlayCore ofrece un procedimiento manual que usa ese mismo evento,
sin escribir ajustes, bases de datos o archivos internos del plugin:

1. Instala Launch Options desde la sección Decky y carga Steam/Big Picture con Decky.
2. Pulsa **Ver procedimiento manual de importación…**. Lee la guía y el script y pulsa
   **Copiar script de importación**. Esto solo cambia el portapapeles: aún no hay importación.
3. Abre Chrome/Chromium → `chrome://inspect/#devices`. Configura `localhost:8081`
   en el mismo equipo o `IP_DEL_EQUIPO:8081` desde otro. Steam debe tener habilitada
   la depuración remota; consulta el apartado [Debugging del autor](https://github.com/Wurielle/decky-launch-options#debugging).
   Pulsa **Inspect** sobre la ventana de Steam que contiene Decky. Si no hay destino,
   no continúes hasta disponer de depuración remota. PlayCore no la habilita con esta acción.
4. En **Console**, comprueba `window.hasDeckyLaunchOptions === true`. Si devuelve
   `false` o `undefined`, carga el plugin o selecciona el contexto correcto. El script
   también comprueba esto y aborta si falta. No lo ejecutes en la consola de una web.
5. Revisa y ejecuta el script copiado. Si DevTools bloquea pegar código, sigue sus
   indicaciones de revisión. El evento solicita la importación y abre el diálogo
   del plugin; no equivale a una importación completada.
6. Pulsa **I understand**, comprueba los tres comandos y deja **Enable globally**
   apagado en todos. Confirma con **Add to Decky Launch Options**, o cancela.

Se necesita una versión del plugin con el evento oficial y soporte de selectores
por `valueId`. Si no aparece el diálogo o el selector, actualiza el plugin y vuelve
a intentarlo. No se ofrece escritura directa como alternativa.

## Comprobar el resultado y repetir

En **Decky → Launch Options → Manage Launch Options**, busca el grupo **PlayCore**.
Comprueba los nombres **OptiScaler**, **FSR 4 Upgrade** y **OptiScaler + FSR 4**
en la importación y los tres valores de la tabla en el selector compartido.
Al editar los valores, verifica los IDs estables, los comandos, **Off command** vacío,
el **Value ID** común, **Fallback Value** apagado y **Enable globally** apagado.

En la página del juego → ajustes → **Launch Options**, selecciona **None** para
desactivar o un solo valor del selector. No actives a la vez el combinado y los
individuales. El selector excluye esos tres valores; antes de usarlo desactiva otros
perfiles equivalentes y revisa variables previas en **Original launch options**.

Para reimportar, vuelve a usar la acción y conserva los IDs. La
[implementación oficial](https://github.com/Wurielle/decky-launch-options/blob/dev/src/settings/launch-option-actions.ts)
actualiza las entradas con el mismo ID en vez de añadir copias. No uses **Duplicate**
ni crees entradas manuales con IDs distintos. Si el usuario activó antes un valor
globalmente, el plugin puede conservarlo al reimportar: **desactívalo en Manage Launch
Options antes de repetir** y comprueba el estado después. PlayCore siempre envía
los tres valores globales a `false`; el usuario conserva el control del diálogo y
de los ajustes posteriores.

Las pruebas locales validan la solicitud y la interfaz Qt con carpetas temporales.
La confirmación y el resultado final deben comprobarse en Steam con el plugin cargado.
