import sys
import os
import winreg
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QCheckBox, QPushButton, 
                             QLineEdit, QScrollArea, QSystemTrayIcon, QMenu, 
                             QStyle, QSizePolicy, QSizeGrip, QComboBox)
from PyQt6.QtCore import Qt, QPoint, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QColor
import datetime

import data_manager
import config_manager
from background_dialog import BackgroundDialog

class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class TaskItemWidget(QWidget):
    def __init__(self, task_data, on_delete, on_status_change):
        super().__init__()
        self.task_data = task_data
        self.on_delete = on_delete
        self.on_status_change = on_status_change
        
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task_data.get("completed", False))
        self.checkbox.stateChanged.connect(self.status_changed)
        
        self.label = ClickableLabel(self.task_data.get("text", ""))
        self.label.setWordWrap(True)
        self.label.clicked.connect(self.start_editing)
        self.font_config = {"family": "Arial", "size": 14, "bold": True, "italic": False, "color": "#ffffff"}
        self.apply_font(self.font_config)
        
        self.edit_input = QLineEdit(self.task_data.get("text", ""))
        self.edit_input.hide()
        self.edit_input.setStyleSheet("padding: 5px; border-radius: 5px; color: black; background-color: white;")
        self.edit_input.returnPressed.connect(self.finish_editing)
        self.edit_input.editingFinished.connect(self.finish_editing)
            
        self.delete_btn = QPushButton("X")
        self.delete_btn.setStyleSheet("background-color: #ff4d4d; color: white; border: none; border-radius: 3px; padding: 2px 5px;")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.clicked.connect(lambda: self.on_delete(self))
        self.delete_btn.hide() # Hidden by default, shown in edit mode
        
        layout.addWidget(self.checkbox)
        layout.addWidget(self.label, 1) # stretch
        layout.addWidget(self.edit_input, 1)
        layout.addWidget(self.delete_btn)
        
        self.setLayout(layout)
        
    def apply_font(self, font_config):
        self.font_config = font_config
        family = font_config.get("family", "Arial")
        size = font_config.get("size", 14)
        bold = "bold" if font_config.get("bold", True) else "normal"
        italic = "italic" if font_config.get("italic", False) else "normal"
        color = font_config.get("color", "#ffffff")
        
        if self.task_data.get("completed", False):
            self.label.setStyleSheet(f"color: {color}; font-family: '{family}'; font-size: {size}px; font-weight: {bold}; font-style: italic; text-decoration: line-through;")
        else:
            self.label.setStyleSheet(f"color: {color}; font-family: '{family}'; font-size: {size}px; font-weight: {bold}; font-style: {italic};")

    def status_changed(self, state):
        completed = state == Qt.CheckState.Checked.value
        self.task_data["completed"] = completed
        self.apply_font(self.font_config)
        self.on_status_change()
        
    def start_editing(self):
        if getattr(self, 'edit_mode', False):
            self.label.hide()
            self.edit_input.setText(self.task_data.get("text", ""))
            self.edit_input.show()
            self.edit_input.setFocus()

    def finish_editing(self):
        if self.edit_input.isHidden():
            return
        new_text = self.edit_input.text().strip()
        if new_text:
            self.task_data["text"] = new_text
            self.label.setText(new_text)
            self.on_status_change()
        self.edit_input.hide()
        self.label.show()
        
    def set_edit_mode(self, enabled):
        self.edit_mode = enabled
        self.delete_btn.setVisible(enabled)
        if not enabled and not getattr(self, 'edit_input', None) is None and not self.edit_input.isHidden():
            self.finish_editing()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = config_manager.load_config()
        self.tasks_dict = data_manager.load_tasks()
        
        today_idx = datetime.datetime.today().weekday()
        self.current_day = data_manager.DEFAULT_DAYS[today_idx]
        
        self.edit_mode = False
        self.drag_pos = QPoint()
        
        self.init_ui()
        self.setup_tray_icon()
        self.update_window_mode()
        
    def init_ui(self):
        # Set window flags for desktop widget
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Apply geometry
        geom = self.config.get("geometry", {})
        self.setGeometry(geom.get("x", 100), geom.get("y", 100), geom.get("width", 300), geom.get("height", 400))
        
        # Central widget
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Day Label (Visible in normal mode)
        self.day_label = QLabel(self.current_day)
        self.day_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        self.day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.day_label)
        
        # Day Combo (Visible in edit mode)
        self.day_combo = QComboBox()
        self.day_combo.addItems(data_manager.DEFAULT_DAYS)
        self.day_combo.setCurrentText(self.current_day)
        self.day_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid #aaa;
                border-radius: 5px;
                padding: 5px;
                font-weight: bold;
                color: black;
            }
        """)
        self.day_combo.currentTextChanged.connect(self.on_day_changed)
        self.main_layout.addWidget(self.day_combo)
        self.day_combo.hide()
        
        # Scroll area for tasks
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        self.scroll_area.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.scroll_area.viewport().setStyleSheet("background-color: transparent;")
        
        self.scroll_widget = QWidget()
        self.scroll_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.scroll_widget.setStyleSheet("background-color: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_widget)
        
        self.main_layout.addWidget(self.scroll_area)
        
        # Input area (hidden in normal mode)
        self.input_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Add new task...")
        self.task_input.setStyleSheet("padding: 5px; border-radius: 5px;")
        self.task_input.returnPressed.connect(self.add_task)
        
        self.add_btn = QPushButton("Add")
        self.add_btn.setStyleSheet("background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 5px 10px;")
        self.add_btn.clicked.connect(self.add_task)
        
        self.input_layout.addWidget(self.task_input)
        self.input_layout.addWidget(self.add_btn)
        
        self.input_widget = QWidget()
        self.input_widget.setLayout(self.input_layout)
        self.main_layout.addWidget(self.input_widget)
        
        # Size grip for resizing
        self.size_grip = QSizeGrip(self)
        self.main_layout.addWidget(self.size_grip, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        
        self.task_widgets = []
        self.populate_tasks()

    def on_day_changed(self, text):
        self.current_day = text
        self.day_label.setText(text)
        self.populate_tasks()

    def populate_tasks(self):
        # Clear existing
        for w in self.task_widgets:
            self.scroll_layout.removeWidget(w)
            w.deleteLater()
        self.task_widgets.clear()
        
        current_tasks = self.tasks_dict.get(self.current_day, [])
        for task in current_tasks:
            self.create_task_widget(task)
            
    def create_task_widget(self, task):
        widget = TaskItemWidget(task, self.delete_task, self.save_data)
        widget.apply_font(self.config.get("font", {}))
        widget.set_edit_mode(self.edit_mode)
        self.scroll_layout.addWidget(widget)
        self.task_widgets.append(widget)

    def add_task(self):
        text = self.task_input.text().strip()
        if text:
            new_task = {"text": text, "completed": False}
            if self.current_day not in self.tasks_dict:
                self.tasks_dict[self.current_day] = []
            self.tasks_dict[self.current_day].append(new_task)
            self.create_task_widget(new_task)
            self.task_input.clear()
            self.save_data()

    def delete_task(self, widget):
        if widget.task_data in self.tasks_dict.get(self.current_day, []):
            self.tasks_dict[self.current_day].remove(widget.task_data)
        self.scroll_layout.removeWidget(widget)
        self.task_widgets.remove(widget)
        widget.deleteLater()
        self.save_data()
        
    def save_data(self):
        data_manager.save_tasks(self.tasks_dict)
        
    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        # Load custom logo if available
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo", "logo_transparent.png")
        if os.path.exists(logo_path):
            self.tray_icon.setIcon(QIcon(logo_path))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
            
        self.tray_icon.setToolTip("Desktop To-Do List")
        
        tray_menu = QMenu()
        
        self.edit_action = QAction("Enable Edit Mode", self)
        self.edit_action.triggered.connect(self.toggle_edit_mode)
        tray_menu.addAction(self.edit_action)
        
        self.bg_action = QAction("Change Background", self)
        self.bg_action.triggered.connect(self.open_background_dialog)
        tray_menu.addAction(self.bg_action)
        
        self.font_action = QAction("Change Font & Color", self)
        self.font_action.triggered.connect(self.open_font_dialog)
        tray_menu.addAction(self.font_action)
        
        self.startup_action = QAction("Run at Startup", self)
        self.startup_action.setCheckable(True)
        self.startup_action.setChecked(self.check_autostart())
        self.startup_action.triggered.connect(self.toggle_autostart)
        tray_menu.addAction(self.startup_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        if self.edit_mode:
            self.edit_action.setText("Disable Edit Mode")
        else:
            self.edit_action.setText("Enable Edit Mode")
            
        self.update_window_mode()

    def update_window_mode(self):
        self.hide() # Hide before changing flags
        
        if self.edit_mode:
            # Interactive, visible background
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
            self.day_label.hide()
            self.day_combo.show()
            self.input_widget.show()
            self.size_grip.show()
        else:
            # Click-through, transparent, on bottom
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnBottomHint | Qt.WindowType.WindowTransparentForInput)
            self.day_combo.hide()
            self.day_label.show()
            self.input_widget.hide()
            self.size_grip.hide()
            
        self.update_background()
            
        for w in self.task_widgets:
            w.set_edit_mode(self.edit_mode)
            
        self.show()

    def update_background(self):
        bg = self.config.get("background", "transparent")
        
        if bg == "transparent" or not os.path.exists(bg):
            if self.edit_mode:
                style = "#CentralWidget { background-color: rgba(0, 0, 0, 150); border-radius: 10px; border: 1px solid #555; }"
            else:
                style = "#CentralWidget { background-color: transparent; border: none; }"
        else:
            bg_fixed = bg.replace('\\', '/')
            # Keep style identical between modes to avoid reloading heavy images
            style = f"#CentralWidget {{ border-image: url('{bg_fixed}') 0 0 0 0 stretch stretch; }}"
            
        if not hasattr(self, 'current_style') or self.current_style != style:
            self.current_style = style
            self.central_widget.setStyleSheet(style)

    def open_background_dialog(self):
        dialog = BackgroundDialog(self.config.get("background", "transparent"), self)
        if dialog.exec():
            self.config["background"] = dialog.selected_bg
            config_manager.save_config(self.config)
            self.update_background()

    def open_font_dialog(self):
        from PyQt6.QtWidgets import QFontDialog, QColorDialog
        from PyQt6.QtGui import QFont, QColor
        
        font_cfg = self.config.get("font", {})
        
        current_font = QFont(font_cfg.get("family", "Arial"), font_cfg.get("size", 14))
        current_font.setBold(font_cfg.get("bold", True))
        current_font.setItalic(font_cfg.get("italic", False))
        
        font, ok = QFontDialog.getFont(current_font, self, "Select Font")
        if ok:
            color = QColorDialog.getColor(QColor(font_cfg.get("color", "#ffffff")), self, "Select Color")
            if color.isValid():
                self.config["font"] = {
                    "family": font.family(),
                    "size": font.pointSize(),
                    "bold": font.bold(),
                    "italic": font.italic(),
                    "color": color.name()
                }
                config_manager.save_config(self.config)
                for w in self.task_widgets:
                    w.apply_font(self.config["font"])

    def mousePressEvent(self, event):
        if self.edit_mode and event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.edit_mode and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.edit_mode:
            self.save_geometry()

    def save_geometry(self):
        geo = self.geometry()
        self.config["geometry"] = {
            "x": geo.x(),
            "y": geo.y(),
            "width": geo.width(),
            "height": geo.height()
        }
        config_manager.save_config(self.config)
        
    def moveEvent(self, event):
        super().moveEvent(event)
        if self.edit_mode:
            self.save_geometry()

    def quit_app(self):
        self.save_geometry()
        QApplication.quit()

    # --- Autostart logic using Windows Registry ---
    def get_reg_key(self):
        return r"Software\Microsoft\Windows\CurrentVersion\Run"
        
    def check_autostart(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.get_reg_key(), 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "DesktopTodoList")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False

    def toggle_autostart(self, checked):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.get_reg_key(), 0, winreg.KEY_SET_VALUE)
            if checked:
                # Add to startup
                app_path = os.path.abspath(sys.argv[0])
                if app_path.endswith('.py'):
                    # If running as script, run with pythonw to hide console
                    pythonw_path = sys.executable.replace('python.exe', 'pythonw.exe')
                    cmd = f'"{pythonw_path}" "{app_path}"'
                else:
                    # If running as compiled exe
                    cmd = f'"{app_path}"'
                winreg.SetValueEx(key, "DesktopTodoList", 0, winreg.REG_SZ, cmd)
            else:
                # Remove from startup
                winreg.DeleteValue(key, "DesktopTodoList")
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Error toggling autostart: {e}")
            self.startup_action.setChecked(not checked) # revert UI

if __name__ == "__main__":
    # Prevent scaling issues on high DPI displays
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        
    app = QApplication(sys.argv)
    
    # Required for tray icon on some systems, prevents app from closing if last window is closed
    app.setQuitOnLastWindowClosed(False)
    
    window = MainWindow()
    sys.exit(app.exec())
