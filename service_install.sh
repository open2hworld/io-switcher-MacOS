#!/usr/bin/env bash
# Install I/O Switcher HTTP Service as a macOS LaunchAgent (Runs on User Login)

PLIST_NAME="com.e_hyunus.ioswitcher.plist"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME"
PROJECT_DIR="/Users/e_hyunus/build_room/io-switcher-MacOS"
LOG_DIR="$HOME/Library/Logs/IO-Switcher-Local"

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"

cat <<EOF > "$PLIST_PATH"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.e_hyunus.ioswitcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PROJECT_DIR/run_server.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/server.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/server_error.log</string>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
</dict>
</plist>
EOF

# Unload previous instance if any, then load
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo "✅ I/O 스위처 백그라운드 서비스가 등록되었습니다!"
echo "   - 상태: Mac 로그인 시 자동 시작"
echo "   - 포트: 8765 (http://100.64.0.4:8765)"
echo "   - 로그: $LOG_DIR/server.log"
echo ""
echo "서비스 중지 및 삭제 명령: ./service_uninstall.sh"
