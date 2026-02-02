
# Ratl Runner - Mobile Test Automation

This repository contains **mobile UI automation test flows** using YAML-based syntax to run tests on **real Android devices or emulators**.

Ratl Runner provides a simple, code-free approach to mobile testing with an intuitive visual interface.

---

## 🚀 What is Ratl Runner?

Ratl Runner is a mobile UI testing tool that:

* Uses **YAML files** for test cases
* Works on **real devices & emulators**
* Automatically waits for UI to be ready
* Supports **APK-based testing**
* Requires **zero test code** (no Java/Kotlin)
* Provides a **visual inspector** for creating tests

---

## 📋 Prerequisites

Before running tests, ensure the following are installed:

* macOS / Linux / Windows (WSL recommended)
* Java 8+
* Android SDK
* ADB configured
* Android phone with **USB debugging enabled** OR Android Emulator

Verify device connection:

```bash
adb devices
```

---

## 📁 Project Structure

```text
test-flows/
│
├── flows/               # YAML test flows
│   └── login.yaml
│
├── apk/                 # Android APK files
│   └── app-debug.apk
│
├── run.sh               # One-click test runner
│
└── README.md
```

---

## 🧪 Writing a Test (YAML)

Example test file:

### `flows/login.yaml`

```yaml
appId: com.example.myapp
---
- installApp: apk/app-debug.apk

- launchApp:
    clearState: true

- assertVisible: "Login"

- tapOn:
    id: "email_input"

- inputText: "testuser@gmail.com"

- tapOn:
    id: "password_input"

- inputText: "Test@123"

- tapOn: "Login"

- assertVisible: "Home"
```

---

## ▶️ Running Tests

### Using Ratl Studio (Recommended)

1. Start the application:
```bash
./start.sh
```

2. Open browser to `http://localhost:5173`
3. Select your test flow
4. Click "▶ Run Locally"

### Using Command Line

Run a single test:
```bash
maestro test flows/login.yaml
```

Run all tests:
```bash
maestro test flows/
```

---

## 🤖 One-Click Run Script

### `run.sh`

```bash
#!/bin/bash

echo "🔍 Checking connected devices"
adb devices

echo "🚀 Running Tests"
maestro test flows/
```

Make executable:

```bash
chmod +x run.sh
```

Run tests:

```bash
./run.sh
```

---

## 📸 Screenshots & Debugging

Take screenshots inside tests:

```yaml
- takeScreenshot: home_screen
```

Use the visual inspector in Ratl Studio to:
- View UI hierarchy
- Click elements to generate commands
- See element attributes in real-time

---

## 🔀 Conditional Flows

```yaml
- runFlow:
    when:
      visible: "Allow"
    file: allow_permission.yaml
```

---

## 📱 Supported Platforms

* ✅ Android (APK)
* 🚧 iOS (IPA – limited support)

---

## 🧩 CI/CD Integration

Ratl Runner works well with:

* GitHub Actions
* GitLab CI
* Jenkins

Example:

```bash
maestro test flows/
```

---

## 📚 Useful Commands

```bash
# Run all tests
maestro test flows/

# Interactive inspector
maestro studio

# Check setup
maestro doctor
```

---

## 📌 Best Practices

* Keep flows small & reusable
* Use clear assertions
* Avoid hard waits
* Run tests on real devices
* Use the visual inspector to identify reliable selectors

---

## 📄 License

MIT License

---

## 🙌 Maintained By

Ratl.ai Team

Happy Testing 🚀
