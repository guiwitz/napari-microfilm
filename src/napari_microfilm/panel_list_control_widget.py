from qtpy.QtWidgets import QFrame, QHBoxLayout, QPushButton


class PanelElementListControlWidget(QFrame):
    """Controls for a PanelItemListWidget"""

    def __init__(self, napari_panel, parent=None):
        super().__init__(parent=parent)
        self.napari_panel = napari_panel

        layout = QHBoxLayout()
        self.captureButton = PanelElementCaptureButton(self.napari_panel)
        self.deleteButton = PanelElementDeleteButton(self.napari_panel)
        layout.addWidget(self.captureButton)
        layout.addWidget(self.deleteButton)

        self.setLayout(layout)


class PanelElementCaptureButton(QPushButton):
    def __init__(self, napari_panel):
        super().__init__()

        self.napari_panel = napari_panel
        self.setToolTip("Capture key-frame")
        self.setText("Capture")

class PanelElementDeleteButton(QPushButton):
    def __init__(self, napari_panel):
        super().__init__()

        self.napari_panel = napari_panel
        self.setToolTip("Delete selected key-frame")
        self.setText("Delete")

        self.setEnabled(bool(self.napari_panel.key_frames))