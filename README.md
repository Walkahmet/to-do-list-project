# Desktop To-Do List Widget

A lightweight, customizable, transparent To-Do list widget for Windows desktops built with Python and PyQt6. It acts as an interactive wallpaper widget that you can seamlessly integrate into your daily workflow.

## ✨ Features
- **Transparent Desktop Widget:** Sits natively on your wallpaper without interfering with your mouse clicks.
- **Edit Mode:** Toggle edit mode via the system tray to add, delete, move, and check off tasks.
- **Customizable Backgrounds:** Choose from default images, set your own custom images, or make it completely transparent.
- **Customizable Fonts:** Change the font family, style, size, and color of your tasks.
- **Auto-Start:** Optionally run the application automatically when Windows starts.

## 🚀 Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd TodoListProject
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

## 📦 Building Executable (.exe)

You can build a standalone executable using PyInstaller. Make sure you are in the project directory:

```bash
pyinstaller --noconsole --onefile --name "DesktopTodoList" --add-data "images;images" --add-data "logo;logo" app.py
```
The compiled `.exe` will be located in the `dist` folder.
