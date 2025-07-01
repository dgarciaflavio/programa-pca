# ui/ui_components.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QListWidgetItem,
    QDialogButtonBox, QPushButton
)
from PySide6.QtCore import Qt

class MultiSelectDialog(QDialog):
    """
    Uma janela de diálogo que permite ao usuário selecionar múltiplos itens
    de uma lista usando checkboxes.
    """
    def __init__(self, items, titulo="Selecione os Itens", parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumSize(400, 300)

        # Layout principal
        layout = QVBoxLayout(self)

        # Lista com checkboxes
        self.list_widget = QListWidget()
        for item in items:
            list_item = QListWidgetItem(item)
            list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
            list_item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(list_item)
        
        layout.addWidget(self.list_widget)

        # Botões OK e Cancelar
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)

        self.selected_items = []

    def accept(self):
        """
        Coleta os itens selecionados quando o usuário clica em OK.
        """
        self.selected_items = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                self.selected_items.append(item.text())
        super().accept()

    @staticmethod
    def get_selection(parent, items, titulo):
        """
        Método estático para criar, exibir o diálogo e retornar a seleção.
        """
        dialog = MultiSelectDialog(items, titulo, parent)
        result = dialog.exec()
        if result == QDialog.Accepted:
            return dialog.selected_items
        return None # Retorna None se o usuário cancelar