# 🚀 Ratl Runner

**Ratl Runner** is a modern, visual mobile test automation platform that makes creating and running mobile UI tests simple and intuitive.

![Ratl Studio](https://img.shields.io/badge/Ratl-Studio-blue)
![Platform](https://img.shields.io/badge/Platform-Android-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

- 🎯 **Visual Inspector** - Click on your device screen to generate test commands
- 📝 **YAML-Based Tests** - Simple, readable test syntax
- 🔄 **Live Device Mirroring** - See your device screen in real-time
- 🎨 **Modern UI** - Beautiful, intuitive interface inspired by VS Code
- ⚡ **Fast Execution** - Run tests directly on connected devices
- 📊 **Real-time Feedback** - See test results as they execute
- 🔍 **Element Inspector** - Explore UI hierarchy and element attributes
- 💾 **File Management** - Create, edit, and organize test flows

---

## 🏗️ Architecture

```
ratl-runner/
├── backend/           # FastAPI server
│   ├── main.py       # API endpoints
│   └── runner.py     # Test execution engine
├── frontend/         # React + Vite UI
│   └── src/
│       ├── App.jsx   # Main application
│       └── index.css # Styling
├── test-flows/       # YAML test files
│   └── flows/
└── start.sh          # Startup script
```

---

## 🚀 Quick Start

### Prerequisites

- **macOS** / Linux / Windows (WSL)
- **Python 3.8+**
- **Node.js 16+**
- **Android SDK** with ADB
- **Android device** with USB debugging enabled OR Android emulator

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd rattl-runner/rattl-runner
```

2. **Install backend dependencies**
```bash
cd backend
pip3 install -r requirements.txt
cd ..
```

3. **Install frontend dependencies**
```bash
cd frontend
npm install
cd ..
```

4. **Connect your Android device**
```bash
adb devices
# Should show your device as "device"
```

5. **Start the application**
```bash
./start.sh
```

6. **Open your browser**
```
http://localhost:5173
```

---

## 📱 Usage

### Creating a Test

1. **Connect your device** - Ensure it shows as "CONNECTED" in the header
2. **Click "New Test"** - Enter test name and app package ID
3. **Use the Inspector** - Click "Inspector On" to enable element selection
4. **Click on screen elements** - Commands are automatically generated
5. **Run your test** - Click "▶ Run Locally"

### Test Example

```yaml
appId: com.example.app
---
- launchApp:
    clearState: true

- tapOn: "Login"

- tapOn:
    id: "email_input"

- inputText: "user@example.com"

- tapOn:
    id: "password_input"

- inputText: "password123"

- tapOn: "Submit"

- assertVisible: "Welcome"
```

---

## 🎮 Inspector Commands

The Inspector panel provides quick access to common commands:

### 👉 Tap & Click
- Tap Element
- Double Tap
- Long Press

### 🖐️ Swipe & Gestures
- Swipe Up/Down/Left/Right

### 📜 Scroll
- Scroll Down/Up
- Scroll to Element

### ⌨️ Input & Text
- Tap and Type
- Input Text
- Erase Text
- Press Keys

### 👁️ Assertions
- Assert Visible
- Assert Not Visible

### ⏱️ Wait & Timing
- Wait for Visible
- Wait for Not Visible
- Wait (delay)

### 🧭 Navigation
- Go Back
- Hide Keyboard
- Open Link

---

## 🔧 API Endpoints

The backend provides the following REST API:

- `GET /devices` - List connected devices
- `GET /packages` - List installed packages
- `GET /screenshot` - Get device screenshot
- `GET /hierarchy` - Get UI element hierarchy
- `POST /run` - Execute test flow
- `POST /run-step` - Execute single step
- `GET /files` - List test files
- `POST /files` - Create file/folder
- `GET /file?path=...` - Read file content
- `PUT /file` - Update file content
- `DELETE /file?path=...` - Delete file

---

## 🛠️ Development

### Backend (FastAPI)

```bash
cd backend
python3 main.py
# Server runs on http://localhost:8000
```

### Frontend (React + Vite)

```bash
cd frontend
npm run dev
# UI runs on http://localhost:5173
```

---

## 📚 Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **ADB** - Android Debug Bridge for device communication
- **PyYAML** - YAML parsing

### Frontend
- **React** - UI framework
- **Vite** - Build tool
- **Vanilla CSS** - Styling

---

## 🎨 Design Philosophy

Ratl Runner is designed with the following principles:

1. **Visual First** - See your device, click to create tests
2. **Zero Code** - No programming knowledge required
3. **Fast Feedback** - Instant visual feedback on test execution
4. **Modern UX** - Clean, intuitive interface
5. **Developer Friendly** - YAML is readable and version-control friendly

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🙌 Credits

Built with ❤️ by the Ratl.ai Team

---

## 📞 Support

For issues and questions:
- Create an issue in the repository
- Check the documentation in `/test-flows/README.md`

---

**Happy Testing! 🚀**
