#!/usr/bin/env python3
"""
Lightweight HTTP Server for I/O Switcher (Tailscale & iPhone Shortcuts)
"""

import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import switcher_core

PORT = 8765
_LOGGER = logging.getLogger("switcher_server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class SwitcherHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Paths: /on, /off, /toggle, /status, /on/2, /off/2
        path = self.path.strip("/").split("/")
        cmd = path[0].lower() if path else ""
        switch_num = int(path[1]) if len(path) > 1 and path[1].isdigit() else 1

        if cmd in ("on", "off", "toggle"):
            action = cmd
            cfg = switcher_core.load_config()
            if action == "toggle":
                last = cfg.get("last_state", {}).get(str(switch_num), "off")
                action = "off" if last == "on" else "on"

            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    switcher_core.send_command(
                        action=action,
                        switch_num=switch_num,
                    )
                )
                loop.close()
                self._send_json(200, {"success": True, "message": f"Switch {switch_num} {action.upper()} OK"})
            except Exception as e:
                self._send_json(500, {"success": False, "error": str(e)})

        elif cmd == "status":
            cfg = switcher_core.load_config()
            self._send_json(200, {"success": True, "config": cfg})
        else:
            self._send_json(404, {"error": "Invalid endpoint. Use /on, /off, /toggle, or /status"})

    def _send_json(self, code: int, data: dict):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        # Override to use logger
        _LOGGER.info("%s - - [%s] %s", self.client_address[0], self.log_date_time_string(), format % args)


def run():
    server = HTTPServer(("0.0.0.0", PORT), SwitcherHTTPHandler)
    _LOGGER.info("I/O Switcher HTTP Server listening on port %d...", PORT)
    _LOGGER.info("Endpoints: /on, /off, /toggle, /status")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        _LOGGER.info("Server stopped.")
        server.server_close()


if __name__ == "__main__":
    run()
