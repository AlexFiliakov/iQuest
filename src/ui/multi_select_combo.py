"""Multi-select combo box widget for PyQt6."""

from PyQt6.QtWidgets import QComboBox, QStyledItemDelegate, QStyleOptionViewItem
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QKeyEvent

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class CheckableComboBox(QComboBox):
    """A combo box that allows multiple selections via checkboxes."""
    
    # Signal emitted when selection changes
    selectionChanged = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create model
        self.model = QStandardItemModel()
        self.setModel(self.model)
        
        # Make it editable so we can set custom text
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        
        # Install event filter to handle clicks
        self.view().viewport().installEventFilter(self)
        
        # Connect to handle item changes
        self.model.itemChanged.connect(self._on_item_changed)
        
        # Store placeholder text
        self._placeholder = "Select items..."
        self._update_text()
        
        # Enable keyboard navigation
        self.view().installEventFilter(self)
        
        # Set accessible name for screen readers
        self.setAccessibleName("Multi-select dropdown")
        self.setAccessibleDescription("Use arrow keys to navigate, Space to toggle selection, Ctrl+A to select all")
        
        # Set default tooltip
        self.setToolTip("Select multiple items (Space: toggle, Ctrl+A: all, Ctrl+D: none)")
    
    def addItem(self, text, data=None, checked=False):
        """Add an item to the combo box.
        
        Args:
            text: Display text for the item
            data: Optional data associated with the item
            checked: Whether the item should be initially checked
        """
        item = QStandardItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
        item.setData(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
        if data is not None:
            item.setData(data, Qt.ItemDataRole.UserRole)
        self.model.appendRow(item)
        self._update_text()
    
    def addItems(self, texts):
        """Add multiple items to the combo box.
        
        Args:
            texts: List of display texts for the items
        """
        for text in texts:
            self.addItem(text)
    
    def clear(self):
        """Clear all items from the combo box."""
        self.model.clear()
        self._update_text()
    
    def setPlaceholderText(self, text):
        """Set the placeholder text shown when no items are selected.
        
        Args:
            text: Placeholder text
        """
        self._placeholder = text
        self._update_text()
    
    def checkedItems(self):
        """Get list of checked items.
        
        Returns:
            List of tuples (text, data) for checked items
        """
        checked = []
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                text = item.text()
                data = item.data(Qt.ItemDataRole.UserRole)
                checked.append((text, data))
        return checked
    
    def checkedTexts(self):
        """Get list of checked item texts.
        
        Returns:
            List of texts for checked items
        """
        return [text for text, _ in self.checkedItems()]
    
    def setCheckedItems(self, texts):
        """Set which items are checked by their text.
        
        Args:
            texts: List of item texts to check
        """
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            if item.text() in texts:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
        self._update_text()
    
    def checkAll(self):
        """Check all items."""
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            item.setCheckState(Qt.CheckState.Checked)
        self._update_text()
    
    def uncheckAll(self):
        """Uncheck all items."""
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)
        self._update_text()
    
    def eventFilter(self, obj, event):
        """Handle events to prevent dropdown from closing on item click and add keyboard support."""
        if obj == self.view().viewport():
            if event.type() == QEvent.Type.MouseButtonRelease:
                # Keep dropdown open when clicking items
                return True
        
        if obj == self.view() and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            modifiers = event.modifiers()
            
            # Space key toggles current item
            if key == Qt.Key.Key_Space:
                index = self.view().currentIndex()
                if index.isValid():
                    item = self.model.itemFromIndex(index)
                    if item:
                        current_state = item.checkState()
                        new_state = Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked else Qt.CheckState.Checked
                        item.setCheckState(new_state)
                        return True
            
            # Ctrl+A selects all
            elif key == Qt.Key.Key_A and modifiers == Qt.KeyboardModifier.ControlModifier:
                self.checkAll()
                return True
            
            # Ctrl+D deselects all
            elif key == Qt.Key.Key_D and modifiers == Qt.KeyboardModifier.ControlModifier:
                self.uncheckAll()
                return True
            
            # Escape closes dropdown
            elif key == Qt.Key.Key_Escape:
                self.hidePopup()
                return True
            
            # Enter confirms selection and closes
            elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.hidePopup()
                return True
        
        return super().eventFilter(obj, event)
    
    def showPopup(self):
        """Override to set focus and provide keyboard hints."""
        super().showPopup()
        # Set focus to the view for keyboard navigation
        self.view().setFocus()
        
        # Log keyboard shortcuts for debugging
        logger.debug("Multi-select dropdown opened - Keyboard shortcuts: Space=toggle, Ctrl+A=select all, Ctrl+D=deselect all, Escape=close")
    
    def hidePopup(self):
        """Override to emit signal when popup is hidden."""
        super().hidePopup()
        # Emit signal with current selection
        self.selectionChanged.emit(self.checkedTexts())
    
    def _on_item_changed(self, item):
        """Handle item state changes."""
        self._update_text()
    
    def _update_text(self):
        """Update the display text based on checked items."""
        checked_texts = self.checkedTexts()
        
        if not checked_texts:
            self.lineEdit().setText(self._placeholder)
            self.lineEdit().setStyleSheet("color: #A69583;")  # Muted color for placeholder
        else:
            count = len(checked_texts)
            total = self.model.rowCount()
            
            if count == total and total > 0:
                display_text = "All selected"
            elif count <= 3:
                display_text = ", ".join(checked_texts)
            else:
                display_text = f"{count} items selected"
            
            self.lineEdit().setText(display_text)
            self.lineEdit().setStyleSheet("")  # Reset to default color
    
    def wheelEvent(self, event):
        """Disable wheel scrolling to prevent accidental changes."""
        event.ignore()