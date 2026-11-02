# I/O 스위처 로컬 (macOS 버전)

단종된 I/O 스위처(SWITCHER_M)를 공식 서버 인증 없이 macOS에서 블루투스(BLE)로 직접 제어하고, **macOS 단축어(Apple Shortcuts), 키보드 단축키(Global Hotkey), Siri 음성 제어**와 연동할 수 있도록 제작된 프로그램입니다.

---

## 📋 목차
1. [주요 특징 및 문제 해결 내역](#-주요-특징-및-문제-해결-내역)
2. [사전 요구사항 및 설치](#-사전-요구사항-및-설치)
3. [CLI 명령어 사용법](#-cli-명령어-사용법)
4. [macOS GUI 프로그램](#-macos-gui-프로그램)
5. [macOS 단축어(Apple Shortcuts) 등록 가이드](#-macos-단축어apple-shortcuts-등록-가이드)
6. [패킷 진단 도구](#-패킷-진단-도구)
7. [프로젝트 파일 구성](#-프로젝트-파일-구성)

---

## 🛠️ 주요 특징 및 문제 해결 내역

* **macOS CoreBluetooth(UUID) 완벽 지원**
  * Windows/Linux와 달리 macOS는 블루투스 보안 정책으로 기기의 실제 MAC 주소를 가리고 고유 UUID(`XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX`)를 부여합니다. 이를 완벽하게 스캔·인식·저장하도록 구현했습니다.
* **스위처 모터 동작 타이밍 문제 해결 (조기 연결 해제 방지)**
  * 기존 오픈소스 코드는 블루투스 쓰기 직후 즉시 연결을 끊어(`disconnect`), 모터가 돌기 전에 기기 펌웨어가 동작을 취소해버리는 문제가 있었습니다.
  * 명령 패킷 전송 후 **모터가 버튼을 누르고 복귀할 때까지 2초간 연결을 유지(Hold)**하도록 수정하여 정상 작동하도록 개선했습니다.
* **GATT Write Request (`response=True`) 적용**
  * 패킷 누락 방지를 위해 하드웨어 응답을 대기하는 안정적인 방식으로 전송합니다.
* **토글(Toggle) 기능 지원**
  * 로컬 상태 캐싱을 통해 단 하나의 단축어나 단축키로 켜기/끄기를 번갈아 실행할 수 있습니다.

---

## 📦 사전 요구사항 및 설치

### 1. 시스템 패키지 (Homebrew)
macOS 및 Python 3.12 환경에서 GUI(Tkinter)와 BLE 통신을 위해 다음 패키지가 설치되어 있어야 합니다:
```bash
# Python 3.12 및 Tkinter 패키지 설치
brew install python@3.12
brew install python-tk@3.12
```

### 2. Python 라이브러리 (`requirements.txt`)
프로젝트는 독립된 가상환경(`.venv`)에서 실행되며 다음 패키지를 사용합니다:
- `bleak==2.1.1` (macOS CoreBluetooth 비동기 BLE 라이브러리)
- `bleak_retry_connector==4.4.4` (연결 재시도 핸들러)
- `PySwitcherIO==0.0.7` (스위처 프로토콜 참조)

### 3. 원클릭 환경 설정
아래 스크립트를 실행하면 Python 3.12 기반 가상환경 생성 및 패키지 설치, 실행 권한 설정이 한 번에 완료됩니다:
```bash
./setup_macos.sh
```

---

## 💻 CLI 명령어 사용법

단축어 및 터미널에서 실행할 때는 프로젝트 내 [`switcher`](file:///Users/e_hyunus/build_room/io-switcher-local/switcher) 스크립트를 사용합니다. (가상환경을 자동으로 감지하여 실행합니다)

### 1. 스위처 기기 검색 및 자동 등록
주변의 `SWITCHER_M` 기기를 스캔하여 기본 기기 주소로 자동 저장합니다:
```bash
./switcher scan --save
```

### 2. 스위치 켜기 / 끄기 / 토글
```bash
# 1번 스위치 켜기
./switcher on

# 1번 스위치 끄기
./switcher off

# 상태 토글 (켜져 있으면 끄고, 꺼져 있으면 켬)
./switcher toggle
```

### 3. 2구 스위처 조작
```bash
# 2번 스위치 켜기 / 끄기
./switcher on 2
./switcher off 2

# 2번 스위치 토글
./switcher toggle 2
```

### 4. 설정 조회 및 변경
설정 파일은 macOS 표준 경로(`~/Library/Application Support/IO-Switcher-Local/config.json`)에 저장됩니다:
```bash
# 현재 설정 확인 (기기 주소, 1구/2구 여부, 반전 여부 등)
./switcher config

# 2구 스위처로 변경
./switcher config --type 2

# 1구 스위처로 변경
./switcher config --type 1

# 스위처가 거꾸로 부착된 경우 ON/OFF 반전 설정
./switcher config --invert on
./switcher config --invert off
```

---

## 🖥️ macOS GUI 프로그램

그래픽 인터페이스를 통해 기기를 검색하고, 스위치를 테스트하거나 단축어용 전체 경로 명령어를 원클릭으로 복사할 수 있습니다.

```bash
./run_gui
```

* **스위처 기기 설정**: [기기 찾기] 버튼으로 주변 스위처를 검색하고 더블클릭으로 주소 등록
* **스위치 조작**: 1번/2번 ON, OFF, 토글 버튼 제공
* **단축어 연동 도우미**: 클릭 시 단축어 앱에 바로 붙여넣을 수 있는 전체 경로 명령어(`"/Users/.../switcher" on 1` 등) 자동 복사

---

## 📱 macOS 단축어(Apple Shortcuts) 등록 가이드

macOS 단축어 앱에 등록하면 **Siri("Siri야, 불 켜줘")**, **키보드 단축키(Global Hotkey)**, **메뉴 막대**에서 원클릭으로 조작할 수 있습니다.

### 기존 단축어("불 켜줘", "불 꺼줘")에 연결하기
1. macOS에서 **단축어** 앱을 실행합니다.
2. 기존에 등록되어 있는 **"불 켜줘"** 단축어를 더블 클릭해 편집창을 엽니다.
3. 오른쪽 동작 라이브러리 검색창에서 **"셸 스크립트 실행"** (Run Shell Script)을 검색하여 추가합니다.
4. 스크립트 입력란에 아래 명령어를 입력합니다:
   ```bash
   /Users/e_hyunus/build_room/io-switcher-local/switcher on
   ```
5. 동일하게 **"불 꺼줘"** 단축어 편집창에는 아래를 입력합니다:
   ```bash
   /Users/e_hyunus/build_room/io-switcher-local/switcher off
   ```
6. 이제 **Siri에게 "불 켜줘" / "불 꺼줘"**라고 말하면 바로 작동합니다.

---

### 키보드 단축키(Global Hotkey)로 토글 단축어 만들기
1. 단축어 앱 우측 상단 **[+]** 버튼을 눌러 새 단축어를 생성합니다.
2. 단축어 이름을 **"방 불 토글"** 로 지정합니다.
3. 오른쪽에서 **"셸 스크립트 실행"** 동작을 추가하고 다음을 입력합니다:
   ```bash
   /Users/e_hyunus/build_room/io-switcher-local/switcher toggle
   ```
4. 오른쪽 사이드바에서 **단축어 세부사항(ⓘ 아이콘)** 을 클릭합니다:
   - ✅ **키보드 단축키 추가**: 원하는 키(예: `F1` 또는 `Cmd + Shift + L` 등) 지정
   - ✅ **빠른 동작으로 사용** 체크
   - ✅ **메뉴 막대에 고정** 체크 (화면 상단 메뉴바에서 마우스로 클릭 가능)

---

## 🔍 패킷 진단 도구

하드웨어 이상 유무나 신호별 반응을 독립적으로 테스트할 수 있는 진단 스크립트입니다:

```bash
# 진단 도구 테스트 목록 확인
./diagnose.py

# 개별 패킷 직접 전송 테스트 (연결 후 2.5초 대기)
./diagnose.py 0   # 1번 ON (0x00)
./diagnose.py 1   # 1번 OFF (0x01)
./diagnose.py 2   # 2번 ON 후보 A (0x02)
./diagnose.py 3   # 2번 OFF (0x03)
./diagnose.py 4   # 2번 ON 후보 B (0x05)
```

---

## 📁 프로젝트 파일 구성

| 파일명 | 설명 |
|---|---|
| [`switcher`](file:///Users/e_hyunus/build_room/io-switcher-local/switcher) | **단축어(Shortcuts) 및 터미널용 실행 래퍼 셸 스크립트** |
| [`cli.py`](file:///Users/e_hyunus/build_room/io-switcher-local/cli.py) | 스위치 ON/OFF/토글, 스캔, 설정 관리 CLI |
| [`switcher_core.py`](file:///Users/e_hyunus/build_room/io-switcher-local/switcher_core.py) | Bleak 기반 macOS BLE 통신 및 타이밍 제어 코어 모듈 |
| [`gui_macos.py`](file:///Users/e_hyunus/build_room/io-switcher-local/gui_macos.py) | macOS 네이티브 스타일 Tkinter GUI 프로그램 |
| [`run_gui`](file:///Users/e_hyunus/build_room/io-switcher-local/run_gui) | GUI 실행 런처 스크립트 |
| [`diagnose.py`](file:///Users/e_hyunus/build_room/io-switcher-local/diagnose.py) | BLE 패킷 및 딜레이 진단 도구 |
| [`setup_macos.sh`](file:///Users/e_hyunus/build_room/io-switcher-local/setup_macos.sh) | 가상환경 생성 및 의존성 원클릭 설치 스크립트 |
| [`requirements.txt`](file:///Users/e_hyunus/build_room/io-switcher-local/requirements.txt) | Python 필수 라이브러리 목록 |
| [`README.md`](file:///Users/e_hyunus/build_room/io-switcher-local/README.md) | 프로젝트 매뉴얼 및 단축어 연동 가이드 |
