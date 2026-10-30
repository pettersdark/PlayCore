from dataclasses import dataclass


@dataclass(frozen=True)
class SystemInfo:
    distribution: str
    pretty_name: str
    version: str
    hostname: str
    kernel: str
    desktop: str
    session: str

    @property
    def supported(self) -> bool:
        return self.distribution in {"steamos", "bazzite"}


@dataclass(frozen=True)
class Finding:
    name: str
    status: str
    evidence: str = ""


@dataclass(frozen=True)
class Snapshot:
    system: SystemInfo
    applications: tuple[Finding, ...]
    proton: tuple[Finding, ...]
    decky: tuple[Finding, ...]
    themes: tuple[Finding, ...]
    profiles: tuple[str, ...]
    warnings: tuple[str, ...]
    free_bytes: int
    username: str = ""
    password_status: str = "Desconocido"
