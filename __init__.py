"""
bracket-matcher --- autocomplete [], (), {}, "", '', “”, ‘’, «», ‹›, and ``.
"""
__author__ = "Marco Laspe"
__pluginname__ = "Bracket Matcher"
__copyright__ = "Copyright 2017"
__credits__ = [
    "Marco Laspe",
    "Andrei Kopats",
    "Filipe Azevedo",
    "Bryan A. Jones"]
__license__ = "GPL3"
__version__ = "0.0.1"
__maintainer__ = "Marco Laspe"
__email__ = "marco@rockiger.com"
__status__ = "Beta"

# DONE autocomplete defaults
# TODO custom autocompletes
# TODO custom autocompletes per file-types


from PyQt5.QtCore import QObject, QEvent, Qt
from PyQt5.QtGui import QTextCursor

from enki.core.core import core

# DONE Settings page
# DONE adhere to settings page
# DONE write closing parens
# DONE wrap parens around selected text
# DONE overwrite closing parens
# DONE delete closing char if backspace is pressed and opening charis deleted
# DONE generalize for all pairing characters
# Done Cleanup

openers = ("[", "(", "{", '"', "'", "“", "‘", "«", "‹", "`", "<")
closers = ("]", ")", "}", '"', "'", "”", "’", "»", "›", "`", ">")


class Plugin(QObject):
    """Plugin interface implementation
    """

    def __init__(self):
        QObject.__init__(self)
        core.workspace().currentDocumentChanged.connect(
            self._onCurrentDocumentChanged)

        document = core.workspace().currentDocument()
        if document:
            document.qutepart.installEventFilter(self)

    def terminate(self):
        """clean up"""
        pass

    def _onCurrentDocumentChanged(self, oldDocument, newDocument):
        try:
            oldDocument.qutepart.removeEventFilter(self)
        except AttributeError:
            pass
        try:
            newDocument.qutepart.installEventFilter(self)
        except AttributeError:
            pass

    def eventFilter(self, qutepart, event):
        """The eventFilter filters for three cases of the editor (qutepart) of
        the current document and takes according action:
        - an opening character is pressed => closing character is inserted and
          cursor in moved between both characters. If text is selected, it is
          enclosed by the characters; the cursor is outside the closing
          character.
        - a closing character is pressed => if the same closing character is
          already at the current text position, the character is omitted.
        - backspace is pressed to delete an opening character =>
          if the coresponding closing character is behind the cursor, it is
          also removed.
        """
        # function definitions
        def wrap(qutepart, event, textCursor):
            """wrap the selected text with the coresponding characters"""
            # it's important to get selectionStart and selectionEnd
            # before we change the textCursor, otherwise they will
            # change when we do operations like insertText
            selectionStart = textCursor.selectionStart()
            selectionEnd = textCursor.selectionEnd() + 1

            textCursor.setPosition(selectionStart)
            textCursor.insertText(opener)
            qutepart.setTextCursor(textCursor)
            textCursor.setPosition(selectionEnd)
            textCursor.insertText(closer)
            qutepart.setTextCursor(textCursor)

        def close(qutepart, textCursor):
            """close the inserted character with the coresponding character"""
            textCursor.insertText(opener + closer)
            textCursor.movePosition(QTextCursor.Left)
            qutepart.setTextCursor(textCursor)

        def getChar(qutepart, n):
            """return character n steps away or empty string if n is outside
            of text."""
            text = qutepart.toPlainText()
            textCursor = qutepart.textCursor()
            pos = textCursor.position() + n
            try:
                return text[pos]
            except IndexError as e:
                return ""

        def nextChar(qutepart):
            """return character right to cursor position"""
            return getChar(qutepart, 0)

        def prevChar(qutepart):
            """return character left to cursor position"""
            return getChar(qutepart, -1)
        # main part of event filter
        if (event.type() == QEvent.KeyPress and
                event.modifiers() == Qt.NoModifier):
            textCursor = qutepart.textCursor()
            # if opening character is inserted by the user, close it
            if event.text() in openers:
                index = openers.index(event.text())
                opener = openers[index]
                closer = closers[index]
                if textCursor.hasSelection():
                    wrap(qutepart, event, textCursor)
                else:
                    close(qutepart, textCursor)
                return True
            elif (event.text() in closers and
                  event.text() == nextChar(qutepart)):
                # move cursor right
                textCursor.movePosition(QTextCursor.Right)
                qutepart.setTextCursor(textCursor)
                return True
            elif event.key() == Qt.Key_Backspace:
                closer = nextChar(qutepart)
                opener = prevChar(qutepart)
                if (closer in closers and
                        opener == openers[closers.index(closer)]):
                    textCursor.deleteChar()
                    textCursor.deletePreviousChar()
                    qutepart.setTextCursor(textCursor)
                    return True
                else:
                    return False
        return False
