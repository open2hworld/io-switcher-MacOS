"""
I/O Switcher Core Library for macOS
Direct BLE control for I/O Switcher (SWITCHER_M) devices.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Optional, List, Dict, Any
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice

_LOGGER = logging.getLogger("io_switcher")

CHAR_UUID = "000015ba-0000-1000-8000-00805f9b34fb"
SERVICE_UUID = "0000150b-0000-1000-8000-00805f9b34fb"

# 1구: ON=0x00, OFF=0x01
# 2구: ON=0x05 (일부 0x02), OFF=0x03
COMMAND_KEYS = {
    1: {"on": b"\x00", "off": b"\x01"},
    2: {"on": b"\x05", "off": b"\x03"},
}


def get_config_dir() -> str:
    """Return platform config directory."""
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    elif sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    path = os.path.join(base, "IO-Switcher-Local")
    os.makedirs(path, exist_ok=True)
    return path


def get_config_path() -> str:
    legacy_path = os.path.expanduser("~/.config/IO-Switcher-Local/config.json")
    if sys.platform == "darwin" and os.path.exists(legacy_path):
        return legacy_path
    return os.path.join(get_config_dir(), "config.json")


def load_config() -> Dict[str, Any]:
    cfg_path = get_config_path()
    default_cfg = {
        "address": "",
        "type": 1,
        "invert": False,
        "last_state": {"1": "off", "2": "off"}
    }
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "mac" in data and not data.get("address"):
                    data["address"] = data["mac"]
                default_cfg.update(data)
        except Exception as e:
            _LOGGER.warning("Failed to read config: %s", e)
    return default_cfg


def save_config(config: Dict[str, Any]) -> None:
    cfg_path = get_config_path()
    try:
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        _LOGGER.error("Failed to write config: %s", e)


async def scan_for_switchers(timeout: float = 5.0) -> List[BLEDevice]:
    """Scan for devices matching SWITCHER_M."""
    devices = await BleakScanner.discover(timeout=timeout)
    results = []
    for d in devices:
        name = d.name or ""
        if "SWITCHER_M" in name:
            results.append(d)
    return results


async def find_device(address: Optional[str] = None, timeout: float = 5.0) -> Optional[BLEDevice]:
    """Find switcher by address or scan for SWITCHER_M."""
    if address:
        dev = await BleakScanner.find_device_by_address(address, timeout=timeout)
        if dev:
            return dev

    switchers = await scan_for_switchers(timeout=timeout)
    if address:
        for s in switchers:
            if s.address.lower() == address.lower():
                return s
    elif switchers:
        return switchers[0]

    return None


async def send_command(
    action: str,
    switch_num: int = 1,
    address: Optional[str] = None,
    device_type: int = 1,
    invert: bool = False,
    retries: int = 3,
    retry_delay: float = 1.0,
    post_delay: float = 2.0,
) -> bool:
    """
    Send ON/OFF command to I/O Switcher.
    
    action: 'on' or 'off'
    switch_num: 1 or 2
    address: BLE Address / UUID
    device_type: 1 (1구) or 2 (2구)
    invert: if True, flip on and off
    post_delay: seconds to keep connection alive for motor movement
    """
    config = load_config()
    target_address = address or config.get("address")
    target_type = device_type or config.get("type", 1)
    effective_invert = invert if invert is not None else config.get("invert", False)

    if not target_address:
        _LOGGER.info("스위처 주소가 미설정되어 주변 장치를 자동 검색합니다...")
        found = await find_device(timeout=4.0)
        if found:
            target_address = found.address
            _LOGGER.info("스위처 발견됨: %s", target_address)
            config["address"] = target_address
            save_config(config)
        else:
            raise RuntimeError("스위처 주소가 설정되지 않았고 주변에서 SWITCHER_M 기기를 찾을 수 없습니다.")

    if switch_num not in (1, 2):
        raise ValueError("스위치 번호는 1 또는 2여야 합니다.")

    if switch_num == 2 and target_type == 1:
        raise ValueError("현재 1구 스위처로 설정되어 있어 스위치 2를 조작할 수 없습니다.")

    # Apply inversion if configured
    actual_action = action.lower()
    if effective_invert:
        actual_action = "off" if actual_action == "on" else "on"

    key = COMMAND_KEYS.get(switch_num, {}).get(actual_action)
    if key is None:
        raise ValueError(f"유효하지 않은 동작입니다: {action}")

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            _LOGGER.debug("시도 %d/%d: %s 연결 중...", attempt, retries, target_address)
            device = await BleakScanner.find_device_by_address(target_address, timeout=5.0)
            if not device:
                raise RuntimeError(f"장치({target_address})를 찾을 수 없습니다.")

            async with BleakClient(device, timeout=10.0) as client:
                if not client.is_connected:
                    raise RuntimeError("BLE 연결에 실패했습니다.")

                # Short delay to ensure GATT connection stabilization
                await asyncio.sleep(0.3)

                _LOGGER.info(
                    "스위치 %d %s 명령 전송 중 (key=0x%s, char=%s)...",
                    switch_num,
                    actual_action.upper(),
                    key.hex(),
                    CHAR_UUID
                )

                # Try write with response first; fallback to write without response
                try:
                    await client.write_gatt_char(CHAR_UUID, key, response=True)
                except Exception as we:
                    _LOGGER.debug("Write with response 실패 (%s), response=False 로 재시도...", we)
                    await client.write_gatt_char(CHAR_UUID, key, response=False)

                # IMPORTANT: Keep connection alive while physical motor executes!
                # If we disconnect immediately, the embedded MCU aborts motor movement.
                _LOGGER.debug("모터 동작 대기 중 (%.1f초)...", post_delay)
                await asyncio.sleep(post_delay)

                _LOGGER.info("스위치 %d %s 명령 실행 완료!", switch_num, action.upper())

                # Update last known state in config
                last_state = config.get("last_state", {})
                last_state[str(switch_num)] = action.lower()
                config["last_state"] = last_state
                save_config(config)
                return True

        except Exception as e:
            last_error = e
            _LOGGER.warning("시도 %d 실패: %s", attempt, e)
            if attempt < retries:
                await asyncio.sleep(retry_delay)

    _LOGGER.error("최대 재시도 횟수 초과. 명령 전송 실패: %s", last_error)
    raise RuntimeError(f"스위처 통신 실패: {last_error}")
