import sys
import os
import shutil
import subprocess
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QComboBox, 
                             QSpinBox, QCheckBox, QTabWidget, QLineEdit,
                             QMessageBox, QDoubleSpinBox, QDialog, QDialogButtonBox)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QKeySequence
import time

# Check for required libraries
missing_libs = []
try:
    import pyautogui
except ImportError:
    missing_libs.append("pyautogui")

try:
    import keyboard
except ImportError:
    missing_libs.append("keyboard")

class SettingsDialog(QDialog):
    def __init__(self, parent=None, ignore_tos=False):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        self.ignore_tos_checkbox = QCheckBox("Ignore ToS Violation Warnings")
        self.ignore_tos_checkbox.setChecked(ignore_tos)
        layout.addWidget(self.ignore_tos_checkbox)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

class ClickerThread(QThread):
    finished = pyqtSignal()
    countdown = pyqtSignal(int)
    
    def __init__(self, interval, time_unit, stop_key):
        super().__init__()
        self.interval = interval
        self.time_unit = time_unit
        self.stop_key = stop_key.lower() if stop_key else 'q'
        self.running = True
        
    def run(self):
        # Countdown from 5 to 1
        for i in range(5, 0, -1):
            if not self.running:
                self.finished.emit()
                return
            self.countdown.emit(i)
            time.sleep(1)
        
        # Convert interval to seconds
        if self.time_unit == "Milliseconds":
            wait_time = self.interval / 1000
        elif self.time_unit == "Seconds":
            wait_time = self.interval
        else:  # Minutes
            wait_time = self.interval * 60
        
        # Signal that countdown is done
        self.countdown.emit(0)
            
        while self.running:
            if keyboard.is_pressed(self.stop_key):
                self.running = False
                self.finished.emit()
                break
            pyautogui.click()
            time.sleep(wait_time)
    
    def stop(self):
        self.running = False
        self.finished.emit()

class TyperThread(QThread):
    finished = pyqtSignal()
    
    def __init__(self, interval, time_unit, text_to_type, duration):
        super().__init__()
        self.interval = interval
        self.time_unit = time_unit
        self.text_to_type = text_to_type
        self.duration = duration
        self.running = True
        
    def run(self):
        # Convert interval to seconds
        if self.time_unit == "Second":
            wait_time = self.interval
        else:  # Minute
            wait_time = self.interval * 60
        
        start_time = time.time()
        
        while self.running:
            # Check duration if set
            if self.duration > 0:
                if time.time() - start_time >= self.duration:
                    self.running = False
                    self.finished.emit()
                    break
                    
            pyautogui.typewrite(self.text_to_type, interval=0.05)
            time.sleep(wait_time)
    
    def stop(self):
        self.running = False
        self.finished.emit()

class HotkeyListener(QThread):
    hotkey_pressed = pyqtSignal()
    
    def __init__(self, hotkey):
        super().__init__()
        self.hotkey = hotkey.lower() if hotkey else None
        self.running = True
        
    def run(self):
        if not self.hotkey:
            return
        while self.running:
            if keyboard.is_pressed(self.hotkey):
                self.hotkey_pressed.emit()
                time.sleep(0.5)  # Debounce
            time.sleep(0.1)
    
    def stop(self):
        self.running = False

class AutoClickerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Clicker & Typer - Malware Free!")
        self.setGeometry(100, 100, 650, 600)
        
        self.dark_mode = False
        self.ignore_tos_warnings = False
        self.clicker_thread = None
        self.typer_thread = None
        self.hotkey_listener = None
        
        self.config_file = os.path.join(os.path.expanduser("~"), ".autoclicker_config.json")
        self.load_settings()
        
        # Show ToS warning on first launch
        if not self.ignore_tos_warnings:
            self.show_tos_warning()
        
        self.init_ui()
        
    def show_tos_warning(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Terms of Service Warning")
        msg.setText("⚠️ IMPORTANT LEGAL NOTICE ⚠️")
        msg.setInformativeText(
            "Using auto clickers and auto typers may violate the Terms of Service of many:\n\n"
            "• Online games\n"
            "• Applications\n"
            "• Websites\n"
            "• Services\n\n"
            "Violations may result in:\n"
            "• Account bans\n"
            "• Loss of progress/data\n"
            "• Legal action in some cases\n\n"
            "USE AT YOUR OWN RISK. You are solely responsible for any consequences.\n\n"
            "By clicking 'I Understand', you acknowledge you have read and accept these risks. In settings, you cna forever turn this off!"
        )
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.button(QMessageBox.Ok).setText("I Understand")
        msg.button(QMessageBox.Cancel).setText("Exit")
        
        result = msg.exec_()
        if result != QMessageBox.Ok:
            sys.exit(0)
        
    def load_settings(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    settings = json.load(f)
                    self.dark_mode = settings.get('dark_mode', False)
                    self.ignore_tos_warnings = settings.get('ignore_tos_warnings', False)
        except:
            pass
    
    def save_settings(self):
        try:
            settings = {
                'dark_mode': self.dark_mode,
                'ignore_tos_warnings': self.ignore_tos_warnings
            }
            with open(self.config_file, 'w') as f:
                json.dump(settings, f)
        except:
            pass
        
    def init_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Settings button at top
        settings_btn_layout = QHBoxLayout()
        settings_btn_layout.addStretch()
        self.settings_btn = QPushButton("⚙ Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        settings_btn_layout.addWidget(self.settings_btn)
        main_layout.addLayout(settings_btn_layout)
        
        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create Auto Clicker Tab
        self.clicker_tab = QWidget()
        self.create_clicker_tab()
        self.tabs.addTab(self.clicker_tab, "Auto Clicker")
        
        # Create Auto Typer Tab
        self.typer_tab = QWidget()
        self.create_typer_tab()
        self.tabs.addTab(self.typer_tab, "Auto Typer")
        
        # Apply dark mode if saved
        if self.dark_mode:
            self.dark_mode_checkbox.setChecked(True)
            self.apply_dark_mode()
        
    def create_clicker_tab(self):
        layout = QVBoxLayout(self.clicker_tab)
        
        # Title
        title = QLabel("Auto Clicker - Malware Free")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Source code link
        link_layout = QHBoxLayout()
        link_label = QLabel('See Source Code <a href="https://github.com/mitan7/Auto-Clicker-/upload/main" style="color: #4287f5;">HERE</a>')
        link_label.setOpenExternalLinks(True)
        link_layout.addWidget(link_label)
        link_layout.addStretch()
        layout.addLayout(link_layout)
        
        layout.addSpacing(20)
        
        # Clicks per interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Clicks per:"))
        self.click_interval = QSpinBox()
        self.click_interval.setRange(1, 10000)
        self.click_interval.setValue(100)
        interval_layout.addWidget(self.click_interval)
        
        self.time_unit = QComboBox()
        self.time_unit.addItems(["Milliseconds", "Seconds", "Minutes"])
        interval_layout.addWidget(self.time_unit)
        interval_layout.addStretch()
        layout.addLayout(interval_layout)
        
        # Auto turn on button
        turn_on_layout = QHBoxLayout()
        turn_on_layout.addWidget(QLabel("Button to auto turn on:"))
        self.turn_on_key = QLineEdit()
        self.turn_on_key.setMaxLength(1)
        self.turn_on_key.setPlaceholderText("Press a key...")
        self.turn_on_key.setMaximumWidth(50)
        self.turn_on_key.textChanged.connect(self.validate_hotkey)
        turn_on_layout.addWidget(self.turn_on_key)
        turn_on_layout.addStretch()
        layout.addLayout(turn_on_layout)
        
        # Emergency STOP button
        stop_layout = QHBoxLayout()
        stop_layout.addWidget(QLabel("Emergency STOP button:"))
        self.stop_key = QLineEdit()
        self.stop_key.setMaxLength(1)
        self.stop_key.setPlaceholderText("Press a key...")
        self.stop_key.setMaximumWidth(50)
        self.stop_key.setText("q")
        stop_layout.addWidget(self.stop_key)
        important_label = QLabel("(THIS IS IMPORTANT!!!)")
        important_label.setStyleSheet("color: red; font-weight: bold;")
        stop_layout.addWidget(important_label)
        stop_layout.addStretch()
        layout.addLayout(stop_layout)
        
        # Add to Startup Folder
        startup_layout = QVBoxLayout()
        startup_folder = os.path.join(
            os.environ.get('APPDATA', 'C:\\Users\\[User]\\AppData\\Roaming'),
            r'Microsoft\Windows\Start Menu\Programs\Startup'
        )
        self.startup_checkbox = QCheckBox(f"Add to Startup Folder at {startup_folder}?")
        self.startup_checkbox.stateChanged.connect(self.handle_startup)
        startup_layout.addWidget(self.startup_checkbox)
        layout.addLayout(startup_layout)
        
        layout.addSpacing(20)
        
        # Turn On/Off button
        toggle_layout = QHBoxLayout()
        toggle_layout.addWidget(QLabel("Turn On or Off:"))
        self.clicker_toggle = QPushButton("OFF")
        self.clicker_toggle.setCheckable(True)
        self.clicker_toggle.setMinimumWidth(100)
        self.clicker_toggle.setStyleSheet("""
            QPushButton {
                background-color: #cc0000;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:checked {
                background-color: #00cc00;
            }
        """)
        self.clicker_toggle.clicked.connect(self.toggle_clicker)
        toggle_layout.addWidget(self.clicker_toggle)
        toggle_layout.addStretch()
        layout.addLayout(toggle_layout)
        
        layout.addSpacing(20)
        
        # Dark mode checkbox
        self.dark_mode_checkbox = QCheckBox("Dark mode")
        self.dark_mode_checkbox.stateChanged.connect(self.toggle_dark_mode)
        layout.addWidget(self.dark_mode_checkbox)
        
        layout.addStretch()
        
    def create_typer_tab(self):
        layout = QVBoxLayout(self.typer_tab)
        
        # Warning - BIGGER
        warning = QLabel("⚠️ WARNING ⚠️\n\nHIGH CHANCE THIS TRIGGERS YOUR ANTI-VIRUS AND FLAGS THIS AS \"jokeware\",\nONLY RUN IF YOU THINK OTHERWISE!")
        warning.setStyleSheet("color: red; font-weight: bold; font-size: 16px; padding: 10px; border: 2px solid red; border-radius: 5px;")
        warning.setWordWrap(True)
        warning.setAlignment(Qt.AlignCenter)
        layout.addWidget(warning)
        
        layout.addSpacing(20)
        
        # Type per interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Type per:"))
        self.type_interval = QDoubleSpinBox()
        self.type_interval.setRange(0.1, 10000)
        self.type_interval.setValue(1.0)
        interval_layout.addWidget(self.type_interval)
        
        self.type_time_unit = QComboBox()
        self.type_time_unit.addItems(["Second", "Minute"])
        interval_layout.addWidget(self.type_time_unit)
        interval_layout.addStretch()
        layout.addLayout(interval_layout)
        
        # Duration (optional)
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("For (seconds; optional):"))
        self.type_duration = QSpinBox()
        self.type_duration.setRange(0, 3600)
        self.type_duration.setValue(0)
        self.type_duration.setSpecialValueText("Unlimited")
        duration_layout.addWidget(self.type_duration)
        duration_layout.addStretch()
        layout.addLayout(duration_layout)
        
        # Text to type
        text_layout = QVBoxLayout()
        text_layout.addWidget(QLabel("What to type:"))
        self.text_to_type = QLineEdit()
        self.text_to_type.setPlaceholderText("Enter text to type...")
        text_layout.addWidget(self.text_to_type)
        layout.addLayout(text_layout)
        
        layout.addSpacing(20)
        
        # Turn On/Off button
        toggle_layout = QHBoxLayout()
        toggle_layout.addWidget(QLabel("Turn On or Off:"))
        self.typer_toggle = QPushButton("OFF")
        self.typer_toggle.setCheckable(True)
        self.typer_toggle.setMinimumWidth(100)
        self.typer_toggle.setStyleSheet("""
            QPushButton {
                background-color: #cc0000;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:checked {
                background-color: #00cc00;
            }
        """)
        self.typer_toggle.clicked.connect(self.toggle_typer)
        toggle_layout.addWidget(self.typer_toggle)
        toggle_layout.addStretch()
        layout.addLayout(toggle_layout)
        
        layout.addStretch()
    
    def validate_hotkey(self, text):
        if not text:
            return
        
        major_keys = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                      'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                      ' ']
        special_keys = ['ctrl', 'shift', 'tab']
        
        key_lower = text.lower()
        
        if key_lower in major_keys or key_lower in special_keys:
            reply = QMessageBox.question(
                self,
                "Confirm Hotkey",
                f"Are you SURE you want to use '{text}' as your hotkey?\n\n"
                f"This is a commonly used key and may interfere with normal typing/usage.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                self.turn_on_key.clear()
    
    def open_settings(self):
        dialog = SettingsDialog(self, self.ignore_tos_warnings)
        if dialog.exec_() == QDialog.Accepted:
            self.ignore_tos_warnings = dialog.ignore_tos_checkbox.isChecked()
            self.save_settings()
        
    def toggle_clicker(self):
        if self.clicker_toggle.isChecked():
            # Start hotkey listener if key is set
            hotkey = self.turn_on_key.text()
            if hotkey and not self.hotkey_listener:
                self.hotkey_listener = HotkeyListener(hotkey)
                self.hotkey_listener.hotkey_pressed.connect(self.start_clicker)
                self.hotkey_listener.start()
            
            self.start_clicker()
        else:
            self.clicker_toggle.setText("OFF")
            if self.clicker_thread:
                self.clicker_thread.stop()
                self.clicker_thread.wait()
            if self.hotkey_listener:
                self.hotkey_listener.stop()
                self.hotkey_listener.wait()
                self.hotkey_listener = None
    
    def start_clicker(self):
        if self.clicker_thread and self.clicker_thread.isRunning():
            return
            
        stop_key = self.stop_key.text() if self.stop_key.text() else "q"
        self.clicker_thread = ClickerThread(
            self.click_interval.value(),
            self.time_unit.currentText(),
            stop_key
        )
        self.clicker_thread.countdown.connect(self.update_clicker_countdown)
        self.clicker_thread.finished.connect(self.on_clicker_finished)
        self.clicker_thread.start()
    
    def update_clicker_countdown(self, count):
        if count > 0:
            self.clicker_toggle.setText(f"Starting in {count}")
        else:
            self.clicker_toggle.setText("ON")
    
    def on_clicker_finished(self):
        self.clicker_toggle.setChecked(False)
        self.clicker_toggle.setText("OFF")
                
    def toggle_typer(self):
        if self.typer_toggle.isChecked():
            if not self.text_to_type.text():
                QMessageBox.warning(self, "Error", "Please enter text to type!")
                self.typer_toggle.setChecked(False)
                return
                
            self.typer_toggle.setText("ON")
            self.typer_thread = TyperThread(
                self.type_interval.value(),
                self.type_time_unit.currentText(),
                self.text_to_type.text(),
                self.type_duration.value()
            )
            self.typer_thread.finished.connect(self.on_typer_finished)
            self.typer_thread.start()
        else:
            self.typer_toggle.setText("OFF")
            if self.typer_thread:
                self.typer_thread.stop()
                self.typer_thread.wait()
    
    def on_typer_finished(self):
        self.typer_toggle.setChecked(False)
        self.typer_toggle.setText("OFF")
                
    def handle_startup(self, state):
        if state == Qt.Checked:
            reply = QMessageBox.question(
                self,
                "Confirm Startup",
                "Are you SURE you want to add this to your Startup Folder?\nIt will run every time you turn your device on.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    # Use user-specific startup folder
                    startup_folder = os.path.join(
                        os.environ['APPDATA'],
                        r'Microsoft\Windows\Start Menu\Programs\Startup'
                    )
                    
                    if not os.path.exists(startup_folder):
                        os.makedirs(startup_folder)
                    
                    script_path = os.path.abspath(sys.argv[0])
                    startup_path = os.path.join(startup_folder, os.path.basename(script_path))
                    
                    # Note: This will only work if running as .exe
                    if script_path.endswith('.py'):
                        QMessageBox.information(
                            self,
                            "Info",
                            "Startup feature only works with compiled .exe files."
                        )
                        self.startup_checkbox.setChecked(False)
                    else:
                        shutil.copy(script_path, startup_path)
                        QMessageBox.information(self, "Success", "Added to startup!")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add to startup: {e}")
                    self.startup_checkbox.setChecked(False)
            else:
                self.startup_checkbox.setChecked(False)
                
    def toggle_dark_mode(self, state):
        if state == Qt.Checked:
            self.dark_mode = True
            self.apply_dark_mode()
        else:
            self.dark_mode = False
            self.apply_light_mode()
        self.save_settings()
            
    def apply_dark_mode(self):
        dark_stylesheet = """
            QMainWindow, QWidget, QTabWidget::pane {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 8px 16px;
                border: 1px solid #555555;
            }
            QTabBar::tab:selected {
                background-color: #2b2b2b;
                border-bottom: 2px solid #4287f5;
            }
            QLabel {
                color: #ffffff;
                background-color: transparent;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 5px;
            }
            QCheckBox {
                color: #ffffff;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #555555;
                border-radius: 3px;
                background-color: #3c3c3c;
            }
            QCheckBox::indicator:checked {
                background-color: #4287f5;
                border-color: #4287f5;
            }
            QPushButton#settings_btn {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QMessageBox {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #ffffff;
            }
            QMessageBox QPushButton {
                background-color: #4287f5;
                color: #ffffff;
                padding: 5px 15px;
                border-radius: 3px;
                min-width: 60px;
            }
            QMessageBox QPushButton:hover {
                background-color: #5a9fff;
            }
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QDialog QLabel {
                color: #ffffff;
            }
            QDialog QPushButton {
                background-color: #4287f5;
                color: #ffffff;
                padding: 5px 15px;
                border-radius: 3px;
            }
        """
        self.setStyleSheet(dark_stylesheet)
        self.settings_btn.setObjectName("settings_btn")
        
    def apply_light_mode(self):
        self.setStyleSheet("")
    
    def closeEvent(self, event):
        # Stop all threads before closing
        if self.clicker_thread:
            self.clicker_thread.stop()
            self.clicker_thread.wait()
        if self.typer_thread:
            self.typer_thread.stop()
            self.typer_thread.wait()
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener.wait()
        event.accept()

def check_and_install_dependencies():
    if not missing_libs:
        return True
    
    app = QApplication(sys.argv)
    
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("Missing Dependencies")
    msg.setText("Required libraries are not installed!")
    msg.setInformativeText(
        f"The following libraries are missing:\n{', '.join(missing_libs)}\n\n"
        "Would you like to install them now?"
    )
    
    yes_btn = msg.addButton("Yes", QMessageBox.YesRole)
    no_btn = msg.addButton("No", QMessageBox.NoRole)
    installed_btn = msg.addButton("I have them installed", QMessageBox.AcceptRole)
    
    msg.exec_()
    clicked = msg.clickedButton()
    
    if clicked == no_btn:
        sys.exit(0)
    elif clicked == installed_btn:
        return True
    elif clicked == yes_btn:
        # Show warning about CMD window
        warning = QMessageBox()
        warning.setIcon(QMessageBox.Information)
        warning.setWindowTitle("Installation Notice")
        warning.setText("A CMD window will pop up to install dependencies, please don't freak out.")
        warning.setInformativeText(
            "IMPORTANT:\n"
            "• DO NOT close the CMD window\n"
            "• Wait for installation to complete\n"
            "• The application will start automatically when done"
        )
        warning.exec_()
        
        try:
            for lib in missing_libs:
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
            
            QMessageBox.information(None, "Success", "Dependencies installed successfully!\nPlease restart the application.")
            sys.exit(0)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to install dependencies:\n{e}")
            sys.exit(1)
    
    return False

if __name__ == "__main__":
    if check_and_install_dependencies():
        # Try to enable multi-monitor support
        try:
            import pyautogui
            # PyAutoGUI automatically supports multi-monitor setups
            # Get all monitors info
            screen_width, screen_height = pyautogui.size()
        except:
            pass
        
        app = QApplication(sys.argv)
        window = AutoClickerGUI()
        window.show()
        sys.exit(app.exec_())