#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=== I/O Switcher macOS 환경 설정 시작 ==="

# Check Python 3.10+
PYTHON_BIN=""
for py in python3.12 python3.11 python3.10 /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11 /opt/homebrew/bin/python3; do
    if command -v "$py" >/dev/null 2>&1; then
        VER=$("$py" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        MAJOR=$(echo "$VER" | cut -d. -f1)
        MINOR=$(echo "$VER" | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
            PYTHON_BIN="$py"
            echo " 호환되는 파이썬 감지: $PYTHON_BIN (Python $VER)"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "❌ Python 3.10 이상이 필요합니다. Homebrew로 설치해주세요: brew install python@3.12"
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo " 가상환경 생성 중 (.venv)..."
    "$PYTHON_BIN" -m venv .venv
fi

echo " 필수 패키지 설치 중..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

chmod +x switcher run_gui cli.py gui_macos.py

echo "=== 설정 완료! ==="
echo "CLI 사용: ./switcher --help"
echo "GUI 실행: ./run_gui"
