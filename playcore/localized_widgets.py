"""Widgets Qt nativos que conservan el texto fuente para cambiar de idioma en vivo."""
from PySide6 import QtWidgets as QtW
from .i18n import SOURCE_ROLE


class TextSource:
    def _remember(self, field, source, setter):
        if not hasattr(self, '_sources'):
            self._sources = {}
        self._sources[field] = source
        setter(self._translated(source, field))

    def _translated(self, source, field='text'):
        localizer = getattr(self, '_localizer', None)
        if field == 'plain' and self.property('verbatim'):
            return source
        return localizer.text(source) if localizer is not None else source

    def setText(self, text):
        self._remember('text', text, super().setText)

    def setTitle(self, text):
        self._remember('title', text, super().setTitle)

    def setWindowTitle(self, text):
        self._remember('windowTitle', text, super().setWindowTitle)

    def setToolTip(self, text):
        self._remember('toolTip', text, super().setToolTip)

    def setAccessibleName(self, text):
        self._remember('accessibleName', text, super().setAccessibleName)

    def setPlainText(self, text):
        limit = getattr(self, 'maximumBlockCount', lambda: 0)()
        if limit:
            text = '\n'.join(text.split('\n')[-limit:])
        self._remember('plain', text, super().setPlainText)

    def sourcePlainText(self):
        return getattr(self, '_sources', {}).get('plain', self.toPlainText())

    def appendPlainText(self, text):
        source = self.sourcePlainText()
        self.setPlainText(source + ('\n' if source else '') + text)

    def retranslate(self, localizer):
        self._localizer = localizer
        if not hasattr(self, '_sources'):
            self._sources = {}
        for field, getter, setter in (
                ('text', 'text', 'setText'), ('title', 'title', 'setTitle'),
                ('windowTitle', 'windowTitle', 'setWindowTitle'),
                ('toolTip', 'toolTip', 'setToolTip'),
                ('accessibleName', 'accessibleName', 'setAccessibleName'),
                ('plain', 'toPlainText', 'setPlainText')):
            if not hasattr(self, getter):
                continue
            source = self._sources.setdefault(field, getattr(self, getter)())
            rendered = self._translated(source, field)
            if rendered == getattr(self, getter)():
                continue
            if field == 'plain':
                bar = self.verticalScrollBar()
                position, at_end = bar.value(), bar.value() == bar.maximum()
                getattr(super(), setter)(rendered)
                bar.setValue(bar.maximum() if at_end else position)
            else:
                getattr(super(), setter)(rendered)


class QLabel(TextSource, QtW.QLabel):
    pass


class QPushButton(TextSource, QtW.QPushButton):
    pass


class QToolButton(TextSource, QtW.QToolButton):
    pass


class QGroupBox(TextSource, QtW.QGroupBox):
    pass


class QTextBrowser(TextSource, QtW.QTextBrowser):
    pass


class QPlainTextEdit(TextSource, QtW.QPlainTextEdit):
    pass


class QDialog(TextSource, QtW.QDialog):
    pass


class QComboBox(TextSource, QtW.QComboBox):
    def addItem(self, *args):
        text_index = 0 if isinstance(args[0], str) else 1
        source = args[text_index]
        translated = list(args)
        translated[text_index] = self._translated(source)
        super().addItem(*translated)
        self.setItemData(self.count() - 1, source, SOURCE_ROLE)

    def addItems(self, texts):
        for text in texts:
            self.addItem(text)

    def retranslate(self, localizer):
        super().retranslate(localizer)
        blocked = self.blockSignals(True)
        try:
            for index in range(self.count()):
                source = self.itemData(index, SOURCE_ROLE)
                if source is None:
                    source = self.itemText(index)
                    self.setItemData(index, source, SOURCE_ROLE)
                self.setItemText(index, localizer.text(source))
        finally:
            self.blockSignals(blocked)


class QTableWidget(TextSource, QtW.QTableWidget):
    def _translate_item(self, item):
        if item is None:
            return
        if not hasattr(item, '_source_text'):
            item._source_text = item.text()
            item._source_tooltip = item.toolTip()
        item.setText(self._translated(item._source_text))
        item.setToolTip(self._translated(item._source_tooltip))

    def setItem(self, row, column, item):
        self._translate_item(item)
        super().setItem(row, column, item)

    def retranslate(self, localizer):
        super().retranslate(localizer)
        for column in range(self.columnCount()):
            self._translate_item(self.horizontalHeaderItem(column))
            for row in range(self.rowCount()):
                self._translate_item(self.item(row, column))


class QStatusBar(TextSource, QtW.QStatusBar):
    def showMessage(self, message, timeout=0):
        self._message_source = message
        super().showMessage(self._translated(message), timeout)

    def clearMessage(self):
        self._message_source = ''
        super().clearMessage()

    def retranslate(self, localizer):
        super().retranslate(localizer)
        if self.currentMessage():
            super().showMessage(localizer.text(getattr(self, '_message_source', self.currentMessage())))


class QMessageBox(QtW.QMessageBox):
    @staticmethod
    def question(parent, title, message, buttons=QtW.QMessageBox.StandardButton.Yes | QtW.QMessageBox.StandardButton.No,
                 defaultButton=QtW.QMessageBox.StandardButton.No):
        localizer = parent.localizer
        dialog = QtW.QMessageBox(QtW.QMessageBox.Icon.Question, localizer.text(title),
                                localizer.text(message), buttons, parent)
        dialog.setDefaultButton(defaultButton)
        for button, source in ((QtW.QMessageBox.StandardButton.Yes, 'Sí'),
                               (QtW.QMessageBox.StandardButton.No, 'No')):
            if dialog.button(button) is not None:
                dialog.button(button).setText(localizer.text(source))
        return dialog.exec()

    @staticmethod
    def warning(parent, title, message):
        localizer = parent.localizer
        return QtW.QMessageBox.warning(parent, localizer.text(title), localizer.text(message))
