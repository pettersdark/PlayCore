# Third-party components / Componentes de terceros

PlayCore is a separate project and is not an official Valve, Bazzite, KDE, Decky,
Heroic, ProtonPlus or Proton distribution. Product names belong to their respective projects.

PlayCore es un proyecto independiente; no es una distribución oficial de Valve,
Bazzite, KDE, Decky, Heroic, ProtonPlus ni Proton. Los nombres pertenecen a sus respectivos proyectos.

The graphical installer bundles unmodified PyPI wheels for:

| Component | Version | Source |
| --- | --- | --- |
| PySide6 Essentials / Qt for Python | 6.12.0 | https://pypi.org/project/PySide6-Essentials/6.12.0/ |
| PySide6 Addons / Qt WebSockets | 6.12.0 | https://pypi.org/project/PySide6-Addons/6.12.0/ |
| shiboken6 | 6.12.0 | https://pypi.org/project/shiboken6/6.12.0/ |
| pip (offline bootstrap only) | 26.1.2 | https://pypi.org/project/pip/26.1.2/ |

Their bundled license and copyright notices remain inside the wheels and installed
packages. Third-party components retain their own licenses. Qt libraries are separate
shared libraries; their distribution here does not change their license terms.

El instalador incluye esos wheels sin modificar y conserva sus avisos y licencias.
Los componentes de terceros mantienen sus propias licencias. Las bibliotecas Qt
se distribuyen como bibliotecas compartidas separadas.

Other applications, plugins, Proton builds and themes are downloaded on demand
from their upstream services, not bundled as PlayCore-owned code:

- [Heroic](https://github.com/Heroic-Games-Launcher/HeroicGamesLauncher)
- [ProtonPlus](https://github.com/Vysp3r/ProtonPlus)
- [Proton-CachyOS](https://github.com/CachyOS/proton-cachyos)
- [Proton-GE](https://github.com/GloriousEggroll/proton-ge-custom)
- [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader)
- [Decky plugin catalog](https://plugins.deckbrew.xyz/plugins)
- [CSS Loader](https://github.com/DeckThemes/SDH-CssLoader)
- [Decky Launch Options](https://github.com/Wurielle/decky-launch-options)
- [Machine Ready TV](https://github.com/leoooorocha/Machine-Ready-TV)

Las aplicaciones, plugins, versiones de Proton y temas se descargan bajo demanda
desde sus fuentes; PlayCore no cambia sus licencias ni se atribuye su autoría.
