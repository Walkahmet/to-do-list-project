import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QListWidgetItem, QFileDialog, QLabel)
from PyQt6.QtGui import QIcon, QPixmap, QImageReader
from PyQt6.QtCore import QSize, Qt

class BackgroundDialog(QDialog):
    def __init__(self, current_bg, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Background")
        self.setFixedSize(500, 400)
        self.selected_bg = current_bg
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Transparent button
        self.btn_transparent = QPushButton("Transparent Background (Default)")
        self.btn_transparent.clicked.connect(self.select_transparent)
        layout.addWidget(self.btn_transparent)
        
        # Custom image button
        self.btn_custom = QPushButton("Select Custom Image...")
        self.btn_custom.clicked.connect(self.select_custom)
        layout.addWidget(self.btn_custom)
        
        layout.addWidget(QLabel("Or select from default images:"))
        
        # List widget for default images
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setIconSize(QSize(100, 100))
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setSpacing(10)
        self.list_widget.itemDoubleClicked.connect(self.item_selected)
        layout.addWidget(self.list_widget)
        
        self.load_default_images()
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.accept_selection)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def load_default_images(self):
        self.image_files = []
        images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
        if os.path.exists(images_dir):
            for filename in os.listdir(images_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.image_files.append(os.path.join(images_dir, filename))
                    
        # Start timer for async loading
        from PyQt6.QtCore import QTimer
        self.load_timer = QTimer(self)
        self.load_timer.timeout.connect(self.load_next_image)
        self.load_timer.start(10) # 10ms

    def load_next_image(self):
        if not self.image_files:
            self.load_timer.stop()
            return
            
        filepath = self.image_files.pop(0)
        filename = os.path.basename(filepath)
        
        item = QListWidgetItem(self.list_widget)
        item.setData(Qt.ItemDataRole.UserRole, filepath)
        
        # Use QImageReader for fast thumbnail loading
        reader = QImageReader(filepath)
        reader.setScaledSize(QSize(100, 100))
        img = reader.read()
        if not img.isNull():
            pixmap = QPixmap.fromImage(img)
            icon = QIcon(pixmap)
            item.setIcon(icon)
            item.setText(filename[:15] + "..")

    def select_transparent(self):
        self.selected_bg = "transparent"
        self.accept()
        
    def select_custom(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Background", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_path:
            self.selected_bg = file_path
            self.accept()

    def item_selected(self, item):
        self.selected_bg = item.data(Qt.ItemDataRole.UserRole)
        self.accept()
        
    def accept_selection(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            self.selected_bg = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.accept()
