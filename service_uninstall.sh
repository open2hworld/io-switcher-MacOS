#!/usr/bin/env bash
# Uninstall I/O Switcher HTTP Service

PLIST_NAME="com.e_hyunus.ioswitcher.plist"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME"

if [ -f "$PLIST_PATH" ]; then
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    rm -f "$PLIST_PATH"
    echo "✅ I/O 스위처 백그라운드 서비스가 중지 및 삭제되었습니다."
else
    echo "등록된 서비스가 없습니다."
fi
