#!/usr/bin/env python3
"""Lollipop desktop GUI (Linux/macOS/Windows).

Single GUI for both transports:
- wss (true TAP VPN tunnel via lollipop-client)
- https2 (experimental payload tunnel)
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from pathlib import Path

from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)


class LollipopWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Lollipop")
        self.process: QProcess | None = None

        self.tap = QLineEdit("vpn-ws0" if os.name != "nt" else "lollipop")
        self.server_ip = QLineEdit()
        self.server_ip.setPlaceholderText("127.0.0.1 / 203.0.113.10 / 2001:db8::10")
        self.port = QLineEdit("443")
        self.path = QLineEdit("cucumber")
        self.username = QLineEdit("cucumber")
        self.password = QLineEdit("potato")
        self.password.setEchoMode(QLineEdit.Password)
        self.cert = QLineEdit()
        self.headers_json = QLineEdit(str(Path("config/browser_headers.example.json")))
        self.message = QLineEdit()
        self.message.setPlaceholderText("HTTPS2 payload to send")

        self.proto_wss = QRadioButton("wss (true VPN)")
        self.proto_h2 = QRadioButton("https2 (payload)")
        self.proto_wss.setChecked(True)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)

        browse_cert = QPushButton("Browse cert")
        browse_cert.clicked.connect(self.pick_cert)
        browse_headers = QPushButton("Browse headers JSON")
        browse_headers.clicked.connect(self.pick_headers_json)

        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(self.connect_transport)
        disconnect_btn = QPushButton("Disconnect")
        disconnect_btn.clicked.connect(self.disconnect_transport)
        send_btn = QPushButton("Send HTTPS2 payload")
        send_btn.clicked.connect(self.send_h2_payload)

        form = QFormLayout()
        form.addRow("TAP name/device", self.tap)
        form.addRow("Server IP", self.server_ip)
        form.addRow("Port", self.port)
        form.addRow("Path", self.path)
        form.addRow("Username", self.username)
        form.addRow("Password", self.password)

        proto_row = QHBoxLayout()
        proto_row.addWidget(self.proto_wss)
        proto_row.addWidget(self.proto_h2)
        proto_wrap = QWidget()
        proto_wrap.setLayout(proto_row)
        form.addRow("Protocol", proto_wrap)

        cert_row = QHBoxLayout()
        cert_row.addWidget(self.cert)
        cert_row.addWidget(browse_cert)
        cert_wrap = QWidget()
        cert_wrap.setLayout(cert_row)
        form.addRow("CA/client cert", cert_wrap)

        hdr_row = QHBoxLayout()
        hdr_row.addWidget(self.headers_json)
        hdr_row.addWidget(browse_headers)
        hdr_wrap = QWidget()
        hdr_wrap.setLayout(hdr_row)
        form.addRow("Headers JSON", hdr_wrap)

        form.addRow("HTTPS2 payload", self.message)

        controls = QHBoxLayout()
        controls.addWidget(connect_btn)
        controls.addWidget(disconnect_btn)
        controls.addWidget(send_btn)

        group = QGroupBox("Lollipop connection")
        group.setLayout(form)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("All controls are in GUI. Connect/Disconnect is safe and reversible."))
        layout.addWidget(group)
        layout.addLayout(controls)
        layout.addWidget(QLabel("Logs"))
        layout.addWidget(self.output)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def pick_cert(self) -> None:
        chosen, _ = QFileDialog.getOpenFileName(self, "Select certificate", str(Path.home()))
        if chosen:
            self.cert.setText(chosen)

    def pick_headers_json(self) -> None:
        chosen, _ = QFileDialog.getOpenFileName(self, "Select headers JSON", str(Path.home()), "JSON (*.json)")
        if chosen:
            self.headers_json.setText(chosen)

    def log(self, msg: str) -> None:
        self.output.appendPlainText(msg)

    def host_fmt(self) -> str:
        ip = self.server_ip.text().strip()
        if not ip:
            raise ValueError("Server IP is required")
        return f"[{ip}]" if ":" in ip and not ip.startswith("[") else ip

    def build_wss_url(self) -> str:
        host = self.host_fmt()
        path = self.path.text().strip().lstrip("/")
        return f"wss://{host}:{self.port.text().strip()}/{path}"

    def build_h2_base(self) -> str:
        host = self.host_fmt()
        path = self.path.text().strip().lstrip("/")
        return f"https://{host}:{self.port.text().strip()}/{path}"

    def validate_headers_json(self) -> str:
        path = self.headers_json.text().strip()
        if not path:
            return ""
        p = Path(path)
        if not p.exists():
            raise ValueError("Headers JSON path does not exist")
        try:
            loaded = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise ValueError("Headers JSON must be an object")
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Invalid headers JSON: {exc}") from exc
        return path

    def connect_transport(self) -> None:
        if self.process and self.process.state() != QProcess.NotRunning:
            QMessageBox.warning(self, "Lollipop", "Already connected")
            return

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(
            lambda: self.log(bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace"))
        )
        self.process.readyReadStandardError.connect(
            lambda: self.log(bytes(self.process.readAllStandardError()).decode("utf-8", errors="replace"))
        )
        self.process.finished.connect(lambda *_: self.log("[Lollipop] Disconnected"))

        user = self.username.text().strip()
        password = self.password.text()

        try:
            hdr_path = self.validate_headers_json()
            if self.proto_h2.isChecked():
                base = self.build_h2_base()
                args = [
                    str(Path(__file__).with_name("https2_payload_poll.py")),
                    "--base",
                    base,
                    "--client-id",
                    user or "client1",
                ]
                if self.cert.text().strip():
                    args.extend(["--cafile", self.cert.text().strip()])
                if hdr_path:
                    args.extend(["--headers-json", hdr_path])
                self.log(f"[Lollipop] Starting HTTPS2 loop: python3 {' '.join(args)}")
                self.process.start("python3", args)
            else:
                url = self.build_wss_url()
                args = ["--user", user, "--password", password]
                cert = self.cert.text().strip()
                if cert:
                    args.extend(["--crt", cert])
                if hdr_path:
                    args.extend(["--headers-json", hdr_path])
                args.extend([self.tap.text().strip(), url])
                self.log(f"[Lollipop] Starting lollipop-client {' '.join(args)}")
                self.process.start("lollipop-client", args)

            if not self.process.waitForStarted(5000):
                QMessageBox.critical(self, "Lollipop", "Failed to start process")
                self.log("[Lollipop] Failed to start")
        except ValueError as exc:
            QMessageBox.critical(self, "Lollipop", str(exc))

    def send_h2_payload(self) -> None:
        if not self.proto_h2.isChecked():
            QMessageBox.information(self, "Lollipop", "Switch protocol to https2 first")
            return
        msg = self.message.text().strip()
        if not msg:
            return

        try:
            base = self.build_h2_base()
            hdr_path = self.validate_headers_json()
        except ValueError as exc:
            QMessageBox.critical(self, "Lollipop", str(exc))
            return

        cmd = [
            "python3",
            str(Path(__file__).with_name("https2_payload_cli.py")),
            "--base",
            base,
            "--client-id",
            self.username.text().strip() or "client1",
            "--send",
            msg,
        ]
        cert = self.cert.text().strip()
        if cert:
            cmd.extend(["--cafile", cert])
        if hdr_path:
            cmd.extend(["--headers-json", hdr_path])

        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            self.log(out.strip())
        except subprocess.CalledProcessError as exc:
            self.log(exc.output)

    def disconnect_transport(self) -> None:
        if not self.process or self.process.state() == QProcess.NotRunning:
            return
        self.log("[Lollipop] Disconnect requested")
        if os.name == "nt":
            self.process.kill()
        else:
            pid = self.process.processId()
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            self.process.kill()


def main() -> int:
    app = QApplication(sys.argv)
    win = LollipopWindow()
    win.resize(1040, 720)
    win.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
