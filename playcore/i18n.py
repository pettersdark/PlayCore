"""Traducción de presentación; los identificadores y datos originales no cambian."""
import re
from string import Formatter

from PySide6.QtCore import QObject, QSettings, Signal
from PySide6.QtWidgets import QWidget, QLabel as NativeLabel, QListWidget

from .translations import ENGLISH

SOURCE_ROLE = 0x0100 + 73


def _compile_templates():
    templates = []
    for source, target in ENGLISH.items():
        if '{0}' not in source:
            continue
        parts, fields = [], []
        for literal, field, _, _ in Formatter().parse(source):
            parts.append(re.escape(literal))
            if field is not None:
                parts.append('(.+?)')
                fields.append(int(field))
        templates.append((len(source), re.compile(''.join(parts)), fields, source, target))
    return sorted(templates, key=lambda entry: entry[0], reverse=True)


TEMPLATES = _compile_templates()


def translate(text, language='es', depth=0):
    """Traduce mensajes completos, conservando rutas, versiones y salida externa."""
    if language != 'en' or not text or depth > 4:
        return text
    if text in ENGLISH:
        return ENGLISH[text]
    for _, pattern, fields, source, target in TEMPLATES:
        match = pattern.fullmatch(text)
        if match:
            values = [''] * (max(fields) + 1)
            nested = {
                'Usuario: {0} · Contraseña: {1}': {1},
                'Error: {0}': {0},
                'No se pudo completar la detección: {0}': {0},
                'No se puede leer {0}: {1}': {1},
                'No se pudo interpretar {0}: {1}': {1},
                'Flatpak {0}: {1}': {1},
                'No se pudo iniciar la instalación: {0}': {0},
                'No se completó la instalación: {0}': {0},
                'No se pudo iniciar el instalador: {0}': {0},
                'Instalar {0}': {0},
                'Instalar {0} · {1}': {1},
                '{0} detectado': {0},
                'Instalación de {0} completada.': {0},
                'No se completó la instalación de {0}.': {0},
                'Instalación solicitada: {0}': {0},
            }.get(source, set())
            for field, value in zip(fields, match.groups()):
                values[field] = translate(value, language, depth + 1) if field in nested else value
            return target.format(*values)
    if '\n' in text:
        return '\n'.join(translate(line, language, depth + 1) for line in text.split('\n'))
    prefix = re.fullmatch(r'(\d+\. |[•-] )(.*)', text)
    if prefix:
        return prefix[1] + translate(prefix[2], language, depth + 1)
    return text


class Localizer(QObject):
    changed = Signal(str)

    def __init__(self, settings=None, language=None, parent=None):
        super().__init__(parent)
        self.settings = settings if settings is not None else QSettings('PlayCore', 'PlayCore')
        saved = language if language is not None else self.settings.value('ui/language', 'es')
        self.language = saved if saved in ('es', 'en') else 'es'

    def text(self, source):
        return translate(source, self.language)

    def set_language(self, language):
        if language not in ('es', 'en') or language == self.language:
            return
        self.language = language
        self.settings.setValue('ui/language', language)
        self.settings.sync()
        self.changed.emit(language)

    def apply(self, root):
        """Actualiza widgets existentes, sin reconstruir la ventana ni sus tareas."""
        for widget in [root, *root.findChildren(QWidget)]:
            if hasattr(widget, 'retranslate'):
                widget.retranslate(self)
            elif isinstance(widget, NativeLabel):
                # QFormLayout crea internamente los rótulos de sus filas.
                if not hasattr(widget, '_translation_source'):
                    widget._translation_source = widget.text()
                widget.setText(self.text(widget._translation_source))
            if isinstance(widget, QListWidget):
                for index in range(widget.count()):
                    item = widget.item(index)
                    source = item.data(SOURCE_ROLE)
                    if source is None:
                        source = item.text()
                        item.setData(SOURCE_ROLE, source)
                    item.setText(self.text(source))
