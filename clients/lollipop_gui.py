#!/usr/bin/env python3
"""Lollipop desktop GUI wrapper for vpn-ws-client.

Supports Linux/macOS/Windows as long as vpn-ws-client and TAP support are installed.
"""

from __future__ import annotations

import os
import signal
import sys
from pathlib import Path
from urllib.parse import quote

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
        self.server_ip.setPlaceholderText("203.0.113.10 or 2001:db8::10")
        self.port = QLineEdit("443")
        self.path = QLineEdit("vpn")
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.cert = QLineEdit()

        self.proto_ws = QRadioButton("ws")
        self.proto_wss = QRadioButton("wss")
        self.proto_wss.setChecked(True)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)

        browse = QPushButton("Browse cert")
        browse.clicked.connect(self.pick_cert)

        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(self.connect_vpn)
        disconnect_btn = QPushButton("Disconnect")
        disconnect_btn.clicked.connect(self.disconnect_vpn)

        form = QFormLayout()
        form.addRow("TAP name/device", self.tap)
        form.addRow("Server IP", self.server_ip)
        form.addRow("Port", self.port)
        form.addRow("Path", self.path)
        form.addRow("Username", self.username)
        form.addRow("Password", self.password)

        proto_row = QHBoxLayout()
        proto_row.addWidget(self.proto_ws)
        proto_row.addWidget(self.proto_wss)
        proto_wrap = QWidget()
        proto_wrap.setLayout(proto_row)
        form.addRow("Protocol", proto_wrap)

        cert_row = QHBoxLayout()
        cert_row.addWidget(self.cert)
        cert_row.addWidget(browse)
        cert_wrap = QWidget()
        cert_wrap.setLayout(cert_row)
        form.addRow("Client cert (--crt)", cert_wrap)

        controls = QHBoxLayout()
        controls.addWidget(connect_btn)
        controls.addWidget(disconnect_btn)

        group = QGroupBox("Connection")
        group.setLayout(form)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Lollipop GUI for vpn-ws-client"))
        layout.addWidget(group)
        layout.addLayout(controls)
        layout.addWidget(QLabel("Logs"))
        layout.addWidget(self.output)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def pick_cert(self) -> None:
        chosen, _ = QFileDialog.getOpenFileName(self, "Select client certificate", str(Path.home()))
        if chosen:
            self.cert.setText(chosen)

    def log(self, msg: str) -> None:
        self.output.appendPlainText(msg)

    def build_url(self) -> str:
        ip = self.server_ip.text().strip()
        if not ip:
            raise ValueError("Server IP is required")

        host = f"[{ip}]" if ":" in ip and not ip.startswith("[") else ip
        scheme = "wss" if self.proto_wss.isChecked() else "ws"
        user = quote(self.username.text().strip(), safe="")
        pwd = quote(self.password.text(), safe="")
        auth = f"{user}:{pwd}@" if user else ""
        path = self.path.text().strip().lstrip("/")
        return f"{scheme}://{auth}{host}:{self.port.text().strip()}/{path}"

    def connect_vpn(self) -> None:
        if self.process and self.process.state() != QProcess.NotRunning:
            QMessageBox.warning(self, "Lollipop", "Already connected")
            return

        try:
            url = self.build_url()
        except ValueError as exc:
            QMessageBox.critical(self, "Lollipop", str(exc))
            return

        args = []
        cert = self.cert.text().strip()
        if cert:
            args.extend(["--crt", cert])

        args.extend([self.tap.text().strip(), url])

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(
            lambda: self.log(bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace"))
        )
        self.process.readyReadStandardError.connect(
            lambda: self.log(bytes(self.process.readAllStandardError()).decode("utf-8", errors="replace"))
        )
        self.process.finished.connect(lambda *_: self.log("[Lollipop] Disconnected"))

        self.log(f"[Lollipop] Starting vpn-ws-client {' '.join(args)}")
        self.process.start("vpn-ws-client", args)
        if not self.process.waitForStarted(5000):
            QMessageBox.critical(self, "Lollipop", "Failed to start vpn-ws-client")
            self.log("[Lollipop] Failed to start vpn-ws-client")

    def disconnect_vpn(self) -> None:
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
    win.resize(840, 600)
    win.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
