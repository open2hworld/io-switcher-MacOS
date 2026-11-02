"""
I/O Switcher GUI for macOS
"""

import asyncio
import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

# Ensure switcher_core can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import switcher_core

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SWITCHER_BIN = os.path.join(CURRENT_DIR, "switcher")


class SwitchApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("I/O 스위처 로컬 (macOS)")
        self.root.geometry("540x440")
        self.root.resizable(False, False)

        # Apply macOS native look
        self.style = ttk.Style()
        try:
            self.style.theme_use("aqua")
        except Exception:
            pass

        # Load config
        self.config = switcher_core.load_config()
        self.address_var = tk.StringVar(value=self.config.get("address", ""))
        self.type_var = tk.IntVar(value=self.config.get("type", 1))
        self.invert_var = tk.BooleanVar(value=bool(self.config.get("invert", False)))

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        container = ttk.Frame(self.root, padding="16 16 16 16")
        container.pack(fill=tk.BOTH, expand=True)

        # 1. Device Address Section
        addr_frame = ttk.LabelFrame(container, text=" 스위처 기기 설정 ", padding="10 10 10 10")
        addr_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(addr_frame, text="기기 주소 (UUID/MAC):").grid(row=0, column=0, sticky="w", pady=(0, 4))
        
        entry_row = ttk.Frame(addr_frame)
        entry_row.grid(row=1, column=0, columnspan=3, sticky="ew")
        
        self.address_entry = ttk.Entry(entry_row, textvariable=self.address_var, width=38)
        self.address_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        self.save_btn = ttk.Button(entry_row, text="저장", width=6, command=self.save_config)
        self.save_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.find_btn = ttk.Button(entry_row, text="기기 찾기", width=8, command=self.find_devices)
        self.find_btn.pack(side=tk.LEFT)

        # Options
        opt_frame = ttk.Frame(addr_frame)
        opt_frame.grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))

        self.type_check = ttk.Checkbutton(
            opt_frame,
            text="2구 스위처 (체크 시 2번 스위치 활성화)",
            variable=self.type_var,
            onvalue=2,
            offvalue=1,
            command=self.on_type_change
        )
        self.type_check.pack(anchor="w")

        self.invert_check = ttk.Checkbutton(
            opt_frame,
            text="ON / OFF 반대로 작동",
            variable=self.invert_var,
            command=self.save_config
        )
        self.invert_check.pack(anchor="w", pady=(4, 0))

        # 2. Switch Control Buttons Section
        ctrl_frame = ttk.LabelFrame(container, text=" 스위치 조작 ", padding="12 12 12 12")
        ctrl_frame.pack(fill=tk.X, pady=(0, 10))

        # Switch 1
        s1_row = ttk.Frame(ctrl_frame)
        s1_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(s1_row, text="스위치 1:", width=8).pack(side=tk.LEFT)
        self.s1_on = ttk.Button(s1_row, text="1번 ON", width=12, command=lambda: self.on_action(1, "on"))
        self.s1_on.pack(side=tk.LEFT, padx=(0, 6))
        self.s1_off = ttk.Button(s1_row, text="1번 OFF", width=12, command=lambda: self.on_action(1, "off"))
        self.s1_off.pack(side=tk.LEFT, padx=(0, 6))
        self.s1_toggle = ttk.Button(s1_row, text="토글", width=8, command=lambda: self.on_action(1, "toggle"))
        self.s1_toggle.pack(side=tk.LEFT)

        # Switch 2 (Shown conditionally)
        self.s2_row = ttk.Frame(ctrl_frame)
        self.s2_row.pack(fill=tk.X)
        ttk.Label(self.s2_row, text="스위치 2:", width=8).pack(side=tk.LEFT)
        self.s2_on = ttk.Button(self.s2_row, text="2번 ON", width=12, command=lambda: self.on_action(2, "on"))
        self.s2_on.pack(side=tk.LEFT, padx=(0, 6))
        self.s2_off = ttk.Button(self.s2_row, text="2번 OFF", width=12, command=lambda: self.on_action(2, "off"))
        self.s2_off.pack(side=tk.LEFT, padx=(0, 6))
        self.s2_toggle = ttk.Button(self.s2_row, text="토글", width=8, command=lambda: self.on_action(2, "toggle"))
        self.s2_toggle.pack(side=tk.LEFT)

        if self.type_var.get() == 1:
            self.s2_row.pack_forget()

        # 3. macOS Shortcuts Helper Section
        sc_frame = ttk.LabelFrame(container, text=" macOS 단축어(Shortcuts) 연동 ", padding="10 10 10 10")
        sc_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            sc_frame,
            text="단축어 앱의 '셸 스크립트 실행' 액션에 넣을 명령어를 복사하세요:",
            font=("", 11)
        ).pack(anchor="w", pady=(0, 6))

        sc_btn_row = ttk.Frame(sc_frame)
        sc_btn_row.pack(fill=tk.X)

        ttk.Button(sc_btn_row, text="1번 ON 복사", command=lambda: self.copy_shortcut_cmd("on 1")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(sc_btn_row, text="1번 OFF 복사", command=lambda: self.copy_shortcut_cmd("off 1")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(sc_btn_row, text="1번 토글 복사", command=lambda: self.copy_shortcut_cmd("toggle 1")).pack(side=tk.LEFT)

        # Status Bar
        self.status_var = tk.StringVar(value="준비 완료")
        status_bar = ttk.Label(container, textvariable=self.status_var, foreground="#0066cc", anchor="w")
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(6, 0))

    def on_type_change(self):
        if self.type_var.get() == 2:
            self.s2_row.pack(fill=tk.X)
        else:
            self.s2_row.pack_forget()
        self.save_config()

    def save_config(self):
        self.config["address"] = self.address_var.get().strip()
        self.config["type"] = self.type_var.get()
        self.config["invert"] = bool(self.invert_var.get())
        switcher_core.save_config(self.config)
        self.status_var.set("설정이 저장되었습니다.")

    def copy_shortcut_cmd(self, subcmd: str):
        cmd = f'"{SWITCHER_BIN}" {subcmd}'
        self.root.clipboard_clear()
        self.root.clipboard_append(cmd)
        self.status_var.set(f"클립보드에 복사됨: {cmd}")

    def _set_controls_state(self, state: str):
        self.s1_on.config(state=state)
        self.s1_off.config(state=state)
        self.s1_toggle.config(state=state)
        self.s2_on.config(state=state)
        self.s2_off.config(state=state)
        self.s2_toggle.config(state=state)
        self.find_btn.config(state=state)
        self.save_btn.config(state=state)

    def on_action(self, switch_num: int, action: str):
        addr = self.address_var.get().strip()
        if not addr:
            messagebox.showwarning("주소 누락", "스위처 기기 주소(UUID)를 입력하거나 [기기 찾기]로 검색하세요.")
            return

        self._set_controls_state(tk.DISABLED)
        self.status_var.set(f"스위치 {switch_num} {action.upper()} 명령 전송 중...")

        def run_thread():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                # Resolve toggle if needed
                actual_action = action
                if action == "toggle":
                    last = self.config.get("last_state", {}).get(str(switch_num), "off")
                    actual_action = "off" if last == "on" else "on"

                loop.run_until_complete(
                    switcher_core.send_command(
                        action=actual_action,
                        switch_num=switch_num,
                        address=addr,
                        device_type=self.type_var.get(),
                        invert=bool(self.invert_var.get()),
                    )
                )
                loop.close()
                self.root.after(0, lambda: self._on_action_success(switch_num, actual_action))
            except Exception as e:
                self.root.after(0, lambda: self._on_action_fail(str(e)))

        t = threading.Thread(target=run_thread, daemon=True)
        t.start()

    def _on_action_success(self, switch_num: int, action: str):
        self._set_controls_state(tk.NORMAL)
        self.status_var.set(f"스위치 {switch_num} {action.upper()} 성공!")

    def _on_action_fail(self, err_msg: str):
        self._set_controls_state(tk.NORMAL)
        self.status_var.set("명령 전송 실패")
        messagebox.showerror("통신 실패", f"스위처 연결 실패:\n{err_msg}")

    def find_devices(self):
        win = tk.Toplevel(self.root)
        win.title("I/O 스위처 기기 찾기")
        win.geometry("520x320")
        win.transient(self.root)
        win.grab_set()

        lbl = ttk.Label(win, text="주변 I/O 스위처(SWITCHER_M)를 검색 중입니다... (약 5초)", padding="10 10 10 10")
        lbl.pack(anchor="w")

        tree_frame = ttk.Frame(win, padding="10 0 10 10")
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "address")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        tree.heading("name", text="기기 이름")
        tree.heading("address", text="기기 주소 (UUID)")
        tree.column("name", width=140)
        tree.column("address", width=340)
        tree.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(win, padding="10 5 10 10")
        btn_frame.pack(fill=tk.X)

        select_btn = ttk.Button(btn_frame, text="선택한 기기 사용", state=tk.DISABLED)
        select_btn.pack(side=tk.RIGHT, padx=(4, 0))

        close_btn = ttk.Button(btn_frame, text="닫기", command=win.destroy)
        close_btn.pack(side=tk.RIGHT)

        def on_tree_select(event):
            selected = tree.selection()
            if selected:
                select_btn.config(state=tk.NORMAL)
            else:
                select_btn.config(state=tk.DISABLED)

        tree.bind("<<TreeviewSelect>>", on_tree_select)

        def apply_selected():
            selected = tree.selection()
            if selected:
                item = tree.item(selected[0])
                addr = item["values"][1]
                self.address_var.set(addr)
                self.save_config()
                self.status_var.set(f"기기 주소 설정됨: {addr}")
                win.destroy()

        select_btn.config(command=apply_selected)

        def run_scan():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                devices = loop.run_until_complete(switcher_core.scan_for_switchers(timeout=5.0))
            except Exception as e:
                devices = []
            loop.close()

            def update_ui():
                if not win.winfo_exists():
                    return
                lbl.config(text=f"검색 완료: {len(devices)}개의 기기를 발견했습니다.")
                for d in devices:
                    tree.insert("", tk.END, values=(d.name or "SWITCHER_M", d.address))
                if not devices:
                    lbl.config(text="발견된 스위처 기기가 없습니다. 기기 전원을 확인하세요.")

            self.root.after(0, update_ui)

        threading.Thread(target=run_scan, daemon=True).start()

    def on_close(self):
        self.save_config()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = SwitchApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
