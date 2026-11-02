#!/usr/bin/env python3
"""
I/O Switcher CLI for macOS & Apple Shortcuts
"""

import argparse
import asyncio
import logging
import sys
import os

# Add parent directory to sys.path so it works when run from anywhere
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import switcher_core


def setup_logger(verbose: bool, quiet: bool):
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )


async def cmd_scan(args):
    print(" 주변 I/O 스위처(SWITCHER_M)를 검색 중입니다... (약 5초 소요)")
    devices = await switcher_core.scan_for_switchers(timeout=5.0)
    if not devices:
        print("❌ 발견된 I/O 스위처가 없습니다. 스위처의 전원이 켜져 있고 블루투스 범위 내에 있는지 확인하세요.")
        return 1

    print(f"\n 총 {len(devices)}대의 스위처를 발견했습니다:")
    cfg = switcher_core.load_config()
    current_addr = cfg.get("address", "").lower()

    for i, dev in enumerate(devices, 1):
        is_current = " [현재 설정됨]" if dev.address.lower() == current_addr else ""
        print(f"  {i}. {dev.name or '이름 없음'} ({dev.address}){is_current}")

    if args.save:
        target = devices[0].address
        cfg["address"] = target
        switcher_core.save_config(cfg)
        print(f"\n 첫 번째 기기({target})를 기본 주소로 저장했습니다.")
    else:
        print("\n 팁: 이 기기를 기본 주소로 저장하려면 다음 명령을 실행하세요:")
        print(f"     switcher config --address \"{devices[0].address}\"")
        print(f"     또는 자동으로 첫 번째 기기를 저장하려면: switcher scan --save")
    return 0


async def cmd_action(args):
    action = args.action.lower()
    switch_num = args.switch
    cfg = switcher_core.load_config()

    if action == "toggle":
        last_state = cfg.get("last_state", {}).get(str(switch_num), "off")
        action = "off" if last_state == "on" else "on"
        if not args.quiet:
            print(f"🔄 토글 모드: 현재 상태({last_state}) -> '{action.upper()}' 실행")

    try:
        await switcher_core.send_command(
            action=action,
            switch_num=switch_num,
            address=args.address,
            device_type=args.type,
            invert=args.invert,
            retries=args.retries,
        )
        if not args.quiet:
            print(f" 스위치 {switch_num} {action.upper()} 완료")
        return 0
    except Exception as e:
        print(f"❌ 오류 발생: {e}", file=sys.stderr)
        return 1


def cmd_config(args):
    cfg = switcher_core.load_config()
    updated = False

    if args.address is not None:
        cfg["address"] = args.address.strip()
        updated = True
    if args.type is not None:
        if args.type not in (1, 2):
            print("❌ --type은 1 또는 2여야 합니다.", file=sys.stderr)
            return 1
        cfg["type"] = args.type
        updated = True
    if args.invert is not None:
        cfg["invert"] = args.invert.lower() in ("true", "1", "yes", "on")
        updated = True

    if updated:
        switcher_core.save_config(cfg)
        print(" 설정이 저장되었습니다.")

    print("\n[현재 I/O 스위처 설정]")
    print(f"  설정 파일 경로 : {switcher_core.get_config_path()}")
    print(f"  기기 주소(UUID): {cfg.get('address') or '(미설정)'}")
    print(f"  스위처 타입     : {cfg.get('type', 1)}구 스위처")
    print(f"  ON/OFF 반전     : {'활성화 (반대로 동작)' if cfg.get('invert') else '비활성화 (정상)'}")
    print(f"  최근 기록된 상태: {cfg.get('last_state', {})}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="I/O Switcher macOS CLI (Apple Shortcuts 지원)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 1번 스위치 켜기 / 끄기
  switcher on
  switcher off

  # 2구 스위처의 2번 스위치 켜기 / 끄기
  switcher on 2
  switcher off 2

  # 스위치 상태 토글 (켜져있으면 끄고, 꺼져있으면 켬)
  switcher toggle 1

  # 주변 스위처 검색 및 첫 번째 기기 자동 등록
  switcher scan --save

  # 현재 설정 확인
  switcher config
        """
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="상세 디버그 로그 출력")
    parser.add_argument("-q", "--quiet", action="store_true", help="출력 끄기 (단축어 백그라운드 실행용)")

    subparsers = parser.add_subparsers(dest="subcommand", help="실행할 명령")

    # on / off / toggle commands
    for act in ["on", "off", "toggle"]:
        p = subparsers.add_parser(act, help=f"스위치 {act.upper()} 동작 수행")
        p.add_argument("switch", type=int, nargs="?", default=1, choices=[1, 2], help="스위치 번호 (1 또는 2, 기본값: 1)")
        p.add_argument("-a", "--address", help="대상 스위처 BLE UUID/MAC 주소 (생략 시 config 사용)")
        p.add_argument("-t", "--type", type=int, choices=[1, 2], help="1구(1) 또는 2구(2)")
        p.add_argument("--invert", action="store_true", default=None, help="ON/OFF 반대로 작동")
        p.add_argument("-r", "--retries", type=int, default=3, help="실패 시 재시도 횟수 (기본 3회)")

    # scan command
    p_scan = subparsers.add_parser("scan", help="주변 SWITCHER_M 검색")
    p_scan.add_argument("--save", action="store_true", help="검색된 첫 번째 기기를 config에 자동 저장")

    # config command
    p_cfg = subparsers.add_parser("config", help="설정 조회 및 수정")
    p_cfg.add_argument("-a", "--address", help="스위처 BLE 주소(UUID) 설정")
    p_cfg.add_argument("-t", "--type", type=int, choices=[1, 2], help="스위처 타입 설정 (1구=1, 2구=2)")
    p_cfg.add_argument("--invert", choices=["true", "false", "on", "off"], help="ON/OFF 반전 여부 설정")

    args = parser.parse_args()
    setup_logger(args.verbose, args.quiet)

    if not args.subcommand:
        parser.print_help()
        sys.exit(0)

    if args.subcommand in ["on", "off", "toggle"]:
        args.action = args.subcommand
        code = asyncio.run(cmd_action(args))
        sys.exit(code)
    elif args.subcommand == "scan":
        code = asyncio.run(cmd_scan(args))
        sys.exit(code)
    elif args.subcommand == "config":
        code = cmd_config(args)
        sys.exit(code)


if __name__ == "__main__":
    main()
