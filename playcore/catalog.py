"""Catálogo declarativo. No contiene comandos de instalación."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Application:
    name: str
    flatpak_id: str
    executables: tuple[str, ...]


APPLICATIONS = (
    Application("Heroic", "com.heroicgameslauncher.hgl", ("heroic",)),
    Application("ProtonPlus", "com.vysp3r.ProtonPlus", ("protonplus",)),
)

PLUGINS = {
    "SteamGridDB": ("SteamGridDB",),
    "HLTB": ("HLTB for Deck", "HLTB", "hltb-for-deck"),
    "CSS Loader": ("CSS Loader", "SDH-CssLoader"),
    "Decky Launch Options": ("Launch Options", "Decky Launch Options", "decky-launch-options"),
}

CSS_DEPENDENCIES = (
    "Animated PSP Waves Background",
    "Avatar Customization Suite",
    "Better Blur",
    "Centered Game Text",
    "Clean Library Capsule",
    "Focus Highlight Color",
    "Game Cover Shine Animation Color",
    "Main Menu Hide Tabs",
    "No Friend Playing Icon",
    "No Hero Gradient",
    "No Home Tabs",
    "QAM Hide Tabs",
    "Top Bar Padding",
    "Volume Tweaker",
)

# Identidades de la tienda oficial; se conservan los nombres de la guía del autor.
CSS_ALIASES = {
    "Main Menu Hide Tabs": ("Main Menu Hide Tabs", "Main Menu Hide Tabs (hide the Store)"),
    "No Home Tabs": ("No Home Tabs", "no_home_tabs"),
}
CSS_THEME_IDS = dict(zip(CSS_DEPENDENCIES, (
    "f068122c-0556-412e-8bc9-77939964d8ed", "1f9f487c-d6ab-43d0-9e51-a953f9438d9c",
    "6ad1eed7-99a9-47e2-8184-f5d826e42d54", "eb3f538b-173d-43b5-a83b-dddce528243f",
    "60dcd4b3-ec7c-453a-a565-44385bffc1ff", "6a92019b-ee46-4e3d-b085-d26a045a1660",
    "a55d59e2-17ff-41f2-a672-45864169d394", "72c0a8a8-5099-43c7-a551-5d0c8461dafe",
    "88363437-0fc3-44f7-9ae4-0ced63893aca", "a55ecfab-a99d-43d5-8612-03ea0bf45ea0",
    "1f13929d-cb5b-4ab9-985f-a69504e055fe", "fa803fc3-a391-4cec-9721-7b6c33b13b74",
    "1b4164ab-24e2-4de4-8fac-3e8a05b939af", "afb5f41d-34aa-40c2-9cbc-3d941846b990",
)))

MACHINE_READY_URL = "https://github.com/leoooorocha/Machine-Ready-TV"
PROFILE_STEPS = (
    "Instala Decky Loader y CSS Loader desde Decky; después instala Machine Ready TV y sus 14 dependencias desde Temas.",
    "PlayCore copia los temas y las carpetas .profile a ~/homebrew/themes, conservando los existentes; no activa ningún perfil.",
    "En Gaming Mode, abre CSS Loader → Settings (engranaje) → Enable Nav Patch y actívalo.",
    "Vuelve a CSS Loader en el QAM, baja hasta el final y pulsa Refresh.",
    "Selecciona y aplica manualmente el perfil Machine Ready que prefieras desde CSS Loader.",
)
