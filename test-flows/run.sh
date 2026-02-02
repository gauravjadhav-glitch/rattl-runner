
#!/bin/bash

echo "🔍 Checking connected devices"
adb devices

echo "🚀 Running Ratl Tests"
maestro test flows/
