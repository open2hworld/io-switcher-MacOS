#!/usr/bin/env python3
"""
I/O Switcher Packet & Delay Diagnosis Tool
"""

import asyncio
import sys
from bleak import BleakScanner, BleakClient

ADDRESS = "EBE20A0D-7C73-17E8-2631-4981F5896FA2"
CHAR_BA = "000015ba-0000-1000-8000-00805f9b34fb"
CHAR_BB = "000015bb-0000-1000-8000-00805f9b34fb"

# Packet candidate list: (Description, Characteristic UUID, Byte payload)
TESTS = [
    # 15ba tests
    ("15ba - 0x00 (1번 ON / 1구 ON)", CHAR_BA, b"\x00"),
    ("15ba - 0x01 (1번 OFF / 1구 OFF)", CHAR_BA, b"\x01"),
    ("15ba - 0x02 (2번 ON 후보 A)", CHAR_BA, b"\x02"),
    ("15ba - 0x03 (2번 OFF)", CHAR_BA, b"\x03"),
    ("15ba - 0x05 (2번 ON 후보 B)", CHAR_BA, b"\x05"),
    # 15bb tests
    ("15bb - 0x00 (15bb 테스트 0)", CHAR_BB, b"\x00"),
    ("15bb - 0x01 (15bb 테스트 1)", CHAR_BB, b"\x01"),
    ("15bb - 0x02 (15bb 테스트 2)", CHAR_BB, b"\x02"),
]


async def run_single_test(char_uuid: str, payload: bytes, desc: str):
    print(f"\n==========================================")
    print(f"▶ 테스트 실행: {desc}")
    print(f"  대상 특성: {char_uuid}")
    print(f"  보낼 바이트: 0x{payload.hex()}")
    print(f"  연결 시도 중...")

    dev = await BleakScanner.find_device_by_address(ADDRESS, timeout=5.0)
    if not dev:
        print("❌ 스위처 장치를 찾을 수 없습니다.")
        return False

    async with BleakClient(dev, timeout=10.0) as client:
        print("  연결 성공! 안정화를 위해 0.5초 대기...")
        await asyncio.sleep(0.5)

        # Try with response
        try:
            print(f"  Write with response 전송 중...")
            await client.write_gatt_char(char_uuid, payload, response=True)
            print("  Write with response 성공!")
        except Exception as e:
            print(f"  Write with response 실패 ({e}), response=False 로 재시도...")
            await client.write_gatt_char(char_uuid, payload, response=False)
            print("  Write without response 성공!")

        print("  모터 구동을 위해 2.5초간 연결 유지 중...")
        await asyncio.sleep(2.5)
        print("  완료 (연결 해제)")
    return True


async def main():
    if len(sys.argv) > 1:
        # Run specific index
        idx = int(sys.argv[1])
        desc, char_uuid, payload = TESTS[idx]
        await run_single_test(char_uuid, payload, desc)
    else:
        print("=== I/O 스위처 패킷 진단 도구 ===")
        print("테스트 목록:")
        for i, (desc, _, _) in enumerate(TESTS):
            print(f"  [{i}] {desc}")
        print("\n사용법: python3 diagnose.py [번호]")
        print("예: ./diagnose.py 0  (1번 ON 테스트)")


if __name__ == "__main__":
    asyncio.run(main())
