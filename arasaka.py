#!/usr/bin/env python3
"""
ARASAKA RESCUE SOFTWARE v1.0
Análisis forense, diagnóstico y recuperación de discos.
Requiere: PyQt6, psutil, smartmontools (smartctl)
Ejecutar con sudo para acceso completo a SMART y dispositivos.
"""

import sys
import os
import json
import subprocess
import shutil
import threading
import time
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QTextEdit, QSplitter, QFrame, QScrollArea, QGridLayout,
    QMessageBox, QFileDialog, QGroupBox, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QPropertyAnimation,
    QEasingCurve, QRect
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QPixmap, QPainter, QPen, QBrush,
    QLinearGradient, QIcon, QFontDatabase
)

# ─────────────────────────────────────────────
#  PALETA ARASAKA
# ─────────────────────────────────────────────
C_BG       = "#050505"
C_BG2      = "#0D0D0D"
C_BG3      = "#141414"
C_RED      = "#CC0000"
C_RED_B    = "#FF2222"
C_RED_DIM  = "#550000"
C_GRAY     = "#1A1A1A"
C_GRAY2    = "#252525"
C_GRAY3    = "#333333"
C_TEXT     = "#EAEAEA"
C_TEXT2    = "#AAAAAA"
C_TEXT3    = "#555555"
C_GREEN    = "#00CC55"
C_AMBER    = "#FF8800"
C_ORANGE   = "#FF4400"

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {C_BG};
    color: {C_TEXT};
    font-family: 'Rajdhani', 'Liberation Sans', 'DejaVu Sans', sans-serif;
    font-size: 13px;
}}
QScrollArea {{ border: none; background: {C_BG}; }}
QScrollBar:vertical {{
    background: {C_BG};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {C_RED_DIM};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QListWidget {{
    background: {C_BG2};
    border: none;
    outline: none;
}}
QListWidget::item {{
    padding: 10px 14px;
    border-left: 2px solid transparent;
    color: {C_TEXT2};
}}
QListWidget::item:hover {{
    background: rgba(200,0,0,0.07);
    border-left: 2px solid {C_RED_DIM};
    color: {C_TEXT};
}}
QListWidget::item:selected {{
    background: rgba(200,0,0,0.12);
    border-left: 2px solid {C_RED};
    color: {C_RED_B};
}}
QTableWidget {{
    background: {C_BG2};
    border: 1px solid {C_GRAY2};
    gridline-color: rgba(255,255,255,0.04);
    color: {C_TEXT};
    selection-background-color: rgba(200,0,0,0.15);
}}
QTableWidget::item {{ padding: 6px 10px; }}
QHeaderView::section {{
    background: {C_BG3};
    color: {C_TEXT3};
    padding: 6px 10px;
    border: none;
    border-bottom: 1px solid {C_GRAY2};
    font-size: 10px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QProgressBar {{
    background: {C_BG3};
    border: 1px solid {C_GRAY2};
    border-radius: 2px;
    text-align: center;
    color: {C_TEXT2};
    height: 18px;
    font-size: 10px;
}}
QProgressBar::chunk {{
    background: {C_RED};
    border-radius: 1px;
}}
QPushButton {{
    background: {C_BG3};
    border: 1px solid {C_GRAY3};
    color: {C_TEXT2};
    padding: 8px 16px;
    border-radius: 1px;
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QPushButton:hover {{
    background: rgba(200,0,0,0.1);
    border: 1px solid {C_RED};
    color: {C_RED_B};
}}
QPushButton:pressed {{ background: rgba(200,0,0,0.2); }}
QPushButton:disabled {{ color: {C_TEXT3}; border-color: {C_GRAY2}; }}
QTextEdit {{
    background: {C_BG3};
    border: 1px solid {C_GRAY2};
    color: {C_GREEN};
    font-family: 'Courier New', monospace;
    font-size: 11px;
    padding: 8px;
}}
QGroupBox {{
    border: 1px solid {C_GRAY2};
    border-top: 1px solid {C_RED_DIM};
    margin-top: 8px;
    padding-top: 12px;
    font-size: 10px;
    letter-spacing: 2px;
    color: {C_TEXT3};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: {C_RED};
}}
QSplitter::handle {{ background: {C_GRAY2}; width: 1px; }}
QLabel {{ color: {C_TEXT}; }}
"""

# ─────────────────────────────────────────────
#  UTILIDADES DE SISTEMA
# ─────────────────────────────────────────────

def run_cmd(cmd, timeout=15):
    """Ejecuta un comando y retorna (stdout, stderr, returncode)."""
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1
    except FileNotFoundError:
        return "", f"Comando no encontrado: {cmd[0]}", -1
    except Exception as e:
        return "", str(e), -1


def bytes_to_human(b):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def get_disks():
    """Lista todos los discos usando lsblk."""
    out, _, rc = run_cmd([
        "lsblk", "-J", "-b", "-o",
        "NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL,VENDOR,SERIAL,ROTA,RM,RO,TRAN"
    ])
    if rc != 0:
        return []

    try:
        data = json.loads(out)
    except Exception:
        return []

    disks = []
    for dev in data.get("blockdevices", []):
        if dev.get("type") == "disk":
            disks.append(dev)
    return disks


def get_smart_data(dev_path):
    """Obtiene datos SMART con smartctl."""
    out, err, rc = run_cmd(
        ["smartctl", "-a", "-j", f"/dev/{dev_path}"],
        timeout=20
    )
    if not out:
        return None
    try:
        return json.loads(out)
    except Exception:
        return None


def get_disk_usage(mountpoint):
    """Retorna (total, used, free) en bytes para un punto de montaje."""
    try:
        s = os.statvfs(mountpoint)
        total = s.f_frsize * s.f_blocks
        free = s.f_frsize * s.f_bavail
        used = total - free
        return total, used, free
    except Exception:
        return 0, 0, 0


def get_io_stats(dev_name):
    """Lee /proc/diskstats para el dispositivo."""
    try:
        import psutil
        io = psutil.disk_io_counters(perdisk=True)
        if dev_name in io:
            d = io[dev_name]
            return {
                "read_bytes":  d.read_bytes,
                "write_bytes": d.write_bytes,
                "read_count":  d.read_count,
                "write_count": d.write_count,
            }
    except Exception:
        pass
    return None


def detect_disk_type(dev):
    """Determina el tipo de disco."""
    tran = (dev.get("tran") or "").lower()
    rota = dev.get("rota")
    rm   = dev.get("rm")

    if tran == "nvme":
        return "SSD NVMe"
    if rm:
        return "USB / Externo"
    if rota is False or rota == 0:
        return "SSD SATA"
    if rota is True or rota == 1:
        return "HDD"
    return "Desconocido"


# ─────────────────────────────────────────────
#  WIDGET DE TARJETA
# ─────────────────────────────────────────────

class Card(QFrame):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(f"""
            Card {{
                background: {C_BG2};
                border: 1px solid {C_GRAY2};
                border-top: 1px solid {C_RED_DIM};
            }}
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        if title:
            hdr = QWidget()
            hdr.setFixedHeight(38)
            hdr.setStyleSheet(f"background:{C_BG3}; border-bottom:1px solid {C_GRAY2};")
            hl = QHBoxLayout(hdr)
            hl.setContentsMargins(14, 0, 14, 0)
            lbl = QLabel(f"▸  {title.upper()}")
            lbl.setStyleSheet(f"color:{C_TEXT3}; font-size:10px; letter-spacing:2px;")
            hl.addWidget(lbl)
            self._layout.addWidget(hdr)

        self._body = QWidget()
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(14, 12, 14, 12)
        self._body_layout.setSpacing(8)
        self._layout.addWidget(self._body)

    def body(self):
        return self._body_layout


class InfoRow(QWidget):
    """Etiqueta + Valor en una fila."""
    def __init__(self, label, value, value_color=C_TEXT, parent=None):
        super().__init__(parent)
        hl = QHBoxLayout(self)
        hl.setContentsMargins(0, 2, 0, 2)
        lbl = QLabel(label.upper())
        lbl.setStyleSheet(f"color:{C_TEXT3}; font-size:10px; letter-spacing:1px;")
        lbl.setFixedWidth(160)
        val = QLabel(str(value))
        val.setStyleSheet(f"color:{value_color}; font-size:13px; font-weight:bold;")
        val.setWordWrap(True)
        hl.addWidget(lbl)
        hl.addWidget(val, 1)
        self.val_label = val

    def set_value(self, v, color=None):
        self.val_label.setText(str(v))
        if color:
            self.val_label.setStyleSheet(
                f"color:{color}; font-size:13px; font-weight:bold;"
            )


def badge(text, color=C_GREEN, bg=None):
    lbl = QLabel(text)
    bg = bg or color.replace("#", "rgba(").rstrip(")") + ",0.15)"
    lbl.setStyleSheet(f"""
        color:{color};
        background:{bg};
        border:1px solid {color};
        padding:1px 8px;
        font-size:10px;
        font-family:monospace;
        letter-spacing:1px;
        border-radius:1px;
    """)
    lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    return lbl


# ─────────────────────────────────────────────
#  PANEL PRINCIPAL DE DISCO
# ─────────────────────────────────────────────

class DiskPanel(QWidget):
    """Panel completo para un disco detectado."""

    def __init__(self, dev, parent=None):
        super().__init__(parent)
        self.dev = dev
        self.dev_name = dev["name"]
        self.dev_path = f"/dev/{self.dev_name}"
        self.smart = None
        self._prev_io = None
        self._prev_io_time = None

        # Carga datos SMART en hilo
        self._smart_thread = threading.Thread(
            target=self._load_smart, daemon=True
        )
        self._smart_thread.start()

        self._build_ui()

        # Timer actualización
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_live)
        self.timer.start(3000)

    def _load_smart(self):
        self.smart = get_smart_data(self.dev_name)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setSpacing(12)
        vbox.setContentsMargins(0, 0, 0, 0)

        # ── HEADER ──────────────────────────────
        hdr = QWidget()
        hdr.setStyleSheet(f"background:{C_BG2}; border:1px solid {C_GRAY2}; border-top:1px solid {C_RED};")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 16, 16, 16)

        # Icono
        ico = QLabel("💾")
        ico.setStyleSheet(f"""
            font-size:32px;
            background:{C_RED_DIM};
            padding:10px 14px;
            border:1px solid {C_RED};
        """)
        hl.addWidget(ico)
        hl.addSpacing(12)

        # Info izquierda
        info_left = QVBoxLayout()
        dev_lbl = QLabel(f"/dev/{self.dev_name}")
        dev_lbl.setStyleSheet(f"color:{C_RED_B}; font-size:20px; font-weight:bold; letter-spacing:2px;")

        model = (self.dev.get("model") or "").strip() or "Dispositivo de bloque"
        vendor = (self.dev.get("vendor") or "").strip()
        model_lbl = QLabel(f"{vendor} {model}".strip())
        model_lbl.setStyleSheet(f"color:{C_TEXT}; font-size:13px;")

        dtype = detect_disk_type(self.dev)
        size_raw = int(self.dev.get("size") or 0)
        size_str = bytes_to_human(size_raw)
        sub_lbl = QLabel(f"{dtype}  ·  {size_str}")
        sub_lbl.setStyleSheet(f"color:{C_TEXT2}; font-size:11px;")

        info_left.addWidget(dev_lbl)
        info_left.addWidget(model_lbl)
        info_left.addWidget(sub_lbl)
        hl.addLayout(info_left, 1)

        # Badge estado (actualizado tras cargar SMART)
        self.health_badge = badge("ANALIZANDO...", C_AMBER)
        hl.addWidget(self.health_badge, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        vbox.addWidget(hdr)

        # ── GRILLA INFO ──────────────────────────
        info_card = Card("Información general")
        grid = QGridLayout()
        grid.setSpacing(6)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        mps = self.dev.get("mountpoints") or []
        mountpoint = (mps[0] if mps and mps[0] else None)
        fstype = (self.dev.get("fstype") or "—")
        serial = "—"

        rows = [
            ("Tipo",            detect_disk_type(self.dev)),
            ("Tamaño",          bytes_to_human(size_raw)),
            ("Sistema archivos",fstype),
            ("Punto montaje",   mountpoint or "Sin montar"),
            ("Nº Serie",        serial),
            ("Interfaz",        (self.dev.get("tran") or "").upper() or "—"),
        ]
        for i, (k, v) in enumerate(rows):
            col = (i % 2) * 2
            row = i // 2
            lbl_k = QLabel(k.upper())
            lbl_k.setStyleSheet(f"color:{C_TEXT3}; font-size:10px; letter-spacing:1px;")
            lbl_v = QLabel(str(v))
            lbl_v.setStyleSheet(f"color:{C_TEXT}; font-size:13px; font-weight:bold;")
            lbl_v.setWordWrap(True)
            grid.addWidget(lbl_k, row * 2, col)
            grid.addWidget(lbl_v, row * 2 + 1, col)
            if col == 0:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.VLine)
                sep.setStyleSheet(f"color:{C_GRAY2};")
                grid.addWidget(sep, row * 2, 1, 2, 1)

        info_card.body().addLayout(grid)

        # Barra de uso (si montado)
        if mountpoint:
            total, used, free = get_disk_usage(mountpoint)
            if total > 0:
                pct = int(used / total * 100)
                bar_label = QLabel("ESPACIO UTILIZADO")
                bar_label.setStyleSheet(f"color:{C_TEXT3}; font-size:10px; letter-spacing:1px; margin-top:8px;")
                info_card.body().addWidget(bar_label)
                bar = QProgressBar()
                bar.setRange(0, 100)
                bar.setValue(pct)
                bar.setFormat(f"  {bytes_to_human(used)} / {bytes_to_human(total)}   ({pct}%)")
                bar_color = C_GREEN if pct < 70 else (C_AMBER if pct < 85 else C_RED)
                bar.setStyleSheet(f"""
                    QProgressBar {{ height:22px; }}
                    QProgressBar::chunk {{ background: {bar_color}; }}
                """)
                info_card.body().addWidget(bar)
                free_lbl = QLabel(f"Libre: {bytes_to_human(free)}")
                free_lbl.setStyleSheet(f"color:{C_TEXT2}; font-size:11px;")
                info_card.body().addWidget(free_lbl)

        vbox.addWidget(info_card)

        # ── MÉTRICAS EN TIEMPO REAL ─────────────
        metrics_card = Card("Métricas de E/S en tiempo real")
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(8)

        self.metric_boxes = {}
        metrics = [
            ("read_speed",  "Velocidad lectura", "—",    "MB/s", C_GREEN),
            ("write_speed", "Velocidad escritura","—",   "MB/s", C_RED_B),
            ("read_ops",    "Lecturas",           "—",   "ops",  C_TEXT2),
            ("write_ops",   "Escrituras",         "—",   "ops",  C_TEXT2),
        ]
        for i, (key, name, val, unit, color) in enumerate(metrics):
            box = QWidget()
            box.setStyleSheet(f"""
                background:{C_BG3};
                border:1px solid {C_GRAY2};
                border-bottom:2px solid {color};
            """)
            bl = QVBoxLayout(box)
            bl.setContentsMargins(12, 10, 12, 10)
            nm = QLabel(name.upper())
            nm.setStyleSheet(f"color:{C_TEXT3}; font-size:9px; letter-spacing:1px;")
            vl = QLabel(val)
            vl.setStyleSheet(f"color:{color}; font-size:22px; font-weight:bold; font-family:monospace;")
            ul = QLabel(unit)
            ul.setStyleSheet(f"color:{C_TEXT3}; font-size:10px;")
            bl.addWidget(nm)
            bl.addWidget(vl)
            bl.addWidget(ul)
            self.metric_boxes[key] = vl
            metrics_grid.addWidget(box, 0, i)

        metrics_card.body().addLayout(metrics_grid)
        vbox.addWidget(metrics_card)

        # ── SMART ────────────────────────────────
        self.smart_card = Card("Análisis SMART")
        self.smart_table = QTableWidget()
        self.smart_table.setColumnCount(7)
        self.smart_table.setHorizontalHeaderLabels([
            "Atributo", "ID", "Valor", "Peor", "Umbral", "RAW", "Estado"
        ])
        self.smart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.smart_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.smart_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.smart_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.smart_table.setAlternatingRowColors(True)
        self.smart_table.setStyleSheet(f"""
            QTableWidget {{ alternate-background-color: rgba(255,255,255,0.02); }}
        """)
        self.smart_table.setMinimumHeight(200)

        smart_loading = QLabel("Cargando datos SMART... (requiere sudo)")
        smart_loading.setStyleSheet(f"color:{C_AMBER}; font-size:11px; font-family:monospace; padding:8px;")
        self.smart_card.body().addWidget(smart_loading)
        self.smart_card.body().addWidget(self.smart_table)
        self.smart_loading_lbl = smart_loading
        vbox.addWidget(self.smart_card)

        # ── PARTICIONES ──────────────────────────
        part_card = Card("Particiones detectadas")
        part_table = QTableWidget()
        part_table.setColumnCount(5)
        part_table.setHorizontalHeaderLabels(
            ["Partición", "Tipo FS", "Tamaño", "Punto montaje", "Estado"]
        )
        part_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        part_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        part_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        part_table.setAlternatingRowColors(True)

        children = self.dev.get("children") or []
        if not children:
            # Disco sin tabla de particiones: el propio disco como partición
            children = [self.dev] if self.dev.get("fstype") else []

        part_table.setRowCount(max(len(children), 1))
        if children:
            for r, ch in enumerate(children):
                ch_mps = ch.get("mountpoints") or []
                ch_mp  = ch_mps[0] if ch_mps and ch_mps[0] else "—"
                ch_size = int(ch.get("size") or 0)
                status = "Montada" if ch_mp != "—" else "Sin montar"
                status_color = C_GREEN if ch_mp != "—" else C_TEXT3

                part_table.setItem(r, 0, QTableWidgetItem(f"/dev/{ch.get('name','')}"))
                part_table.setItem(r, 1, QTableWidgetItem(ch.get("fstype") or "—"))
                part_table.setItem(r, 2, QTableWidgetItem(bytes_to_human(ch_size)))
                part_table.setItem(r, 3, QTableWidgetItem(str(ch_mp)))
                status_item = QTableWidgetItem(status)
                status_item.setForeground(QColor(status_color))
                part_table.setItem(r, 4, status_item)
        else:
            part_table.setItem(0, 0, QTableWidgetItem("Sin particiones detectadas"))

        part_table.setMaximumHeight(150)
        part_card.body().addWidget(part_table)
        vbox.addWidget(part_card)

        # ── ACCIONES ─────────────────────────────
        act_card = Card("Acciones")
        act_layout = QHBoxLayout()
        act_layout.setSpacing(8)

        btn_smart = QPushButton("🔍  Recargar SMART")
        btn_smart.clicked.connect(self._reload_smart)
        btn_scan = QPushButton("📂  Scan con testdisk")
        btn_scan.clicked.connect(self._run_testdisk)
        btn_dd = QPushButton("💾  Imagen DD")
        btn_dd.clicked.connect(self._run_dd_image)
        btn_photorec = QPushButton("🗃  Recuperar con PhotoRec")
        btn_photorec.clicked.connect(self._run_photorec)

        for b in [btn_smart, btn_scan, btn_dd, btn_photorec]:
            act_layout.addWidget(b)

        act_card.body().addLayout(act_layout)

        # LOG TERMINAL
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(160)
        self.log.setPlaceholderText("— Log de operaciones —")
        act_card.body().addWidget(self.log)

        vbox.addWidget(act_card)
        vbox.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Timer para cargar SMART cuando esté listo
        self._smart_check = QTimer(self)
        self._smart_check.timeout.connect(self._check_smart_loaded)
        self._smart_check.start(1000)

    def _check_smart_loaded(self):
        if not self._smart_thread.is_alive():
            self._smart_check.stop()
            self._populate_smart()

    def _populate_smart(self):
        if not self.smart:
            self.smart_loading_lbl.setText(
                "⚠ Sin datos SMART (ejecuta con sudo, o el disco no lo soporta)"
            )
            self.smart_loading_lbl.setStyleSheet(f"color:{C_ORANGE}; font-size:11px; padding:8px;")
            # Intentar datos básicos de temperatura
            self._update_health_badge_no_smart()
            return

        self.smart_loading_lbl.hide()

        # Salud general
        status = self.smart.get("smart_status", {})
        passed = status.get("passed", None)
        if passed is True:
            self.health_badge.setText("SALUDABLE")
            self.health_badge.setStyleSheet(
                f"color:{C_GREEN}; background:rgba(0,200,80,0.1); border:1px solid {C_GREEN}; padding:1px 8px; font-size:10px; border-radius:1px;"
            )
        elif passed is False:
            self.health_badge.setText("FALLO DETECTADO")
            self.health_badge.setStyleSheet(
                f"color:{C_RED_B}; background:rgba(200,0,0,0.15); border:1px solid {C_RED}; padding:1px 8px; font-size:10px; border-radius:1px;"
            )
        else:
            self.health_badge.setText("SIN DATOS SMART")
            self.health_badge.setStyleSheet(
                f"color:{C_AMBER}; background:rgba(255,136,0,0.1); border:1px solid {C_AMBER}; padding:1px 8px; font-size:10px; border-radius:1px;"
            )

        # Temperatura
        temp_obj = self.smart.get("temperature", {})
        temp = temp_obj.get("current", None)
        if temp:
            self.log_msg(f"Temperatura: {temp}°C")

        # Atributos SMART
        attrs = self.smart.get("ata_smart_attributes", {}).get("table", [])
        if not attrs:
            # NVMe: diferentes campos
            nvme = self.smart.get("nvme_smart_health_information_log", {})
            self._populate_smart_nvme(nvme)
            return

        self.smart_table.setRowCount(len(attrs))
        for r, attr in enumerate(attrs):
            name   = attr.get("name", "").replace("_", " ").title()
            id_hex = f"{attr.get('id', 0):02X}h"
            val    = str(attr.get("value", "—"))
            worst  = str(attr.get("worst", "—"))
            thresh = str(attr.get("thresh", "—"))
            raw    = str(attr.get("raw", {}).get("value", "—"))
            failed = attr.get("when_failed", "") or ""

            if failed and failed not in ("", "-", "NEVER"):
                state, sc = "FALLO", C_RED_B
            elif attr.get("value", 999) <= attr.get("thresh", 0) + 5:
                state, sc = "ATENCIÓN", C_AMBER
            else:
                state, sc = "OK", C_GREEN

            self.smart_table.setItem(r, 0, QTableWidgetItem(name))
            self.smart_table.setItem(r, 1, QTableWidgetItem(id_hex))
            self.smart_table.setItem(r, 2, QTableWidgetItem(val))
            self.smart_table.setItem(r, 3, QTableWidgetItem(worst))
            self.smart_table.setItem(r, 4, QTableWidgetItem(thresh))
            self.smart_table.setItem(r, 5, QTableWidgetItem(raw))
            si = QTableWidgetItem(state)
            si.setForeground(QColor(sc))
            self.smart_table.setItem(r, 6, si)

    def _populate_smart_nvme(self, nvme):
        """Para discos NVMe que tienen otro esquema de atributos."""
        if not nvme:
            self.smart_table.setRowCount(1)
            self.smart_table.setItem(0, 0, QTableWidgetItem("NVMe: sin atributos ATA clásicos"))
            return

        rows = [
            ("Temperatura", "—", "—", "—", "—",
             f"{nvme.get('temperature',0)}°C",
             "OK" if nvme.get("temperature", 99) < 60 else "ATENCIÓN"),
            ("% Vida restante", "—", "—", "—", "—",
             f"{nvme.get('percentage_used', 0)}% usado",
             "OK" if nvme.get("percentage_used", 100) < 80 else "ATENCIÓN"),
            ("Horas encendido", "—", "—", "—", "—",
             f"{nvme.get('power_on_hours', 0)} h", "OK"),
            ("Ciclos encendido", "—", "—", "—", "—",
             str(nvme.get("power_cycles", 0)), "OK"),
            ("Errores críticos", "—", "—", "—", "—",
             str(nvme.get("critical_warning", 0)),
             "OK" if nvme.get("critical_warning", 0) == 0 else "FALLO"),
            ("Errores de media", "—", "—", "—", "—",
             str(nvme.get("media_errors", 0)),
             "OK" if nvme.get("media_errors", 0) == 0 else "ATENCIÓN"),
            ("Advertencias críticas", "—", "—", "—", "—",
             str(nvme.get("unsafe_shutdowns", 0)), "OK"),
        ]
        self.smart_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                if c == 6:
                    color = C_GREEN if val == "OK" else (C_AMBER if val == "ATENCIÓN" else C_RED_B)
                    item.setForeground(QColor(color))
                self.smart_table.setItem(r, c, item)

    def _update_health_badge_no_smart(self):
        self.health_badge.setText("SIN SMART")
        self.health_badge.setStyleSheet(
            f"color:{C_TEXT3}; background:{C_GRAY}; border:1px solid {C_GRAY3}; padding:1px 8px; font-size:10px; border-radius:1px;"
        )

    def _refresh_live(self):
        """Actualiza métricas de E/S en tiempo real."""
        io = get_io_stats(self.dev_name)
        now = time.time()

        if io and self._prev_io and self._prev_io_time:
            dt = now - self._prev_io_time
            if dt > 0:
                rb = (io["read_bytes"]  - self._prev_io["read_bytes"])  / dt
                wb = (io["write_bytes"] - self._prev_io["write_bytes"]) / dt
                rc = (io["read_count"]  - self._prev_io["read_count"])  / dt
                wc = (io["write_count"] - self._prev_io["write_count"]) / dt

                self.metric_boxes["read_speed"].setText(f"{rb/1024/1024:.1f}")
                self.metric_boxes["write_speed"].setText(f"{wb/1024/1024:.1f}")
                self.metric_boxes["read_ops"].setText(f"{int(rc):,}")
                self.metric_boxes["write_ops"].setText(f"{int(wc):,}")

        self._prev_io = io
        self._prev_io_time = now

    def _reload_smart(self):
        self.log_msg("Recargando SMART...")
        self.smart_loading_lbl.show()
        self.smart_loading_lbl.setText("Recargando datos SMART...")
        self._smart_thread = threading.Thread(
            target=self._load_smart, daemon=True
        )
        self._smart_thread.start()
        self._smart_check.start(1000)

    def _run_testdisk(self):
        self.log_msg(f"Abriendo testdisk en terminal para {self.dev_path}...")
        terminals = ["x-terminal-emulator", "gnome-terminal", "xterm", "konsole"]
        for term in terminals:
            if shutil.which(term):
                cmd = [term, "-e", f"sudo testdisk {self.dev_path}"]
                try:
                    subprocess.Popen(cmd)
                    return
                except Exception:
                    pass
        self.log_msg("No se encontró emulador de terminal. Ejecuta manualmente: sudo testdisk " + self.dev_path)

    def _run_photorec(self):
        self.log_msg(f"Abriendo photorec en terminal para {self.dev_path}...")
        terminals = ["x-terminal-emulator", "gnome-terminal", "xterm", "konsole"]
        for term in terminals:
            if shutil.which(term):
                cmd = [term, "-e", f"sudo photorec {self.dev_path}"]
                try:
                    subprocess.Popen(cmd)
                    return
                except Exception:
                    pass
        self.log_msg("No se encontró emulador de terminal. Ejecuta manualmente: sudo photorec " + self.dev_path)

    def _run_dd_image(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar imagen DD", f"/tmp/{self.dev_name}.img",
            "Imagen de disco (*.img *.raw);;Todos los archivos (*)"
        )
        if not path:
            return
        reply = QMessageBox.question(
            self,
            "Confirmar imagen DD",
            f"Se creará una imagen de:\n  {self.dev_path}\nEn:\n  {path}\n\n"
            "¡Esta operación es de sólo lectura, no modifica el disco original!\n\n¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.log_msg(f"Iniciando ddrescue: {self.dev_path} → {path}")
        thread = threading.Thread(
            target=self._do_dd, args=(path,), daemon=True
        )
        thread.start()

    def _do_dd(self, dest):
        if shutil.which("ddrescue"):
            cmd = ["sudo", "ddrescue", "-d", "-r3",
                   self.dev_path, dest, dest + ".log"]
            tool = "ddrescue"
        else:
            cmd = ["sudo", "dd", f"if={self.dev_path}",
                   f"of={dest}", "bs=4M", "status=progress"]
            tool = "dd"

        self.log_msg(f"Usando {tool}...")
        out, err, rc = run_cmd(cmd, timeout=3600)
        if rc == 0:
            self.log_msg(f"✓ Imagen completada: {dest}")
        else:
            self.log_msg(f"✗ Error ({rc}): {err[:200]}")

    def log_msg(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"<span style='color:{C_TEXT3}'>[{ts}]</span> {msg}")


# ─────────────────────────────────────────────
#  WORKER DE DETECCIÓN
# ─────────────────────────────────────────────

class DetectionWorker(QThread):
    done = pyqtSignal(list)

    def run(self):
        disks = get_disks()
        self.done.emit(disks)


# ─────────────────────────────────────────────
#  VENTANA PRINCIPAL
# ─────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARASAKA RESCUE SOFTWARE  v1.0")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)

        self._disk_panels = {}
        self._build_ui()
        self._detect_disks()

        # Redetección periódica
        self._scan_timer = QTimer(self)
        self._scan_timer.timeout.connect(self._detect_disks)
        self._scan_timer.start(15000)

        # Reloj
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)
        self._tick_clock()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_vbox = QVBoxLayout(central)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)

        # ── TOPBAR ────────────────────────────────
        topbar = QWidget()
        topbar.setFixedHeight(54)
        topbar.setStyleSheet(f"""
            background:{C_BG2};
            border-bottom: 1px solid {C_RED_DIM};
        """)
        tl = QHBoxLayout(topbar)
        tl.setContentsMargins(16, 0, 16, 0)

        logo = QLabel("⬡  ARASAKA RESCUE SOFTWARE")
        logo.setStyleSheet(f"""
            color:{C_TEXT};
            font-size:15px;
            font-weight:bold;
            letter-spacing:3px;
        """)
        tl.addWidget(logo)
        tl.addStretch()

        self.disk_count_lbl = QLabel("Detectando...")
        self.disk_count_lbl.setStyleSheet(f"color:{C_TEXT3}; font-family:monospace; font-size:11px;")
        tl.addWidget(self.disk_count_lbl)
        tl.addSpacing(20)

        self.status_dot = QLabel("●  ACTIVO")
        self.status_dot.setStyleSheet(f"color:{C_GREEN}; font-size:10px; letter-spacing:2px; font-family:monospace;")
        tl.addWidget(self.status_dot)
        tl.addSpacing(20)

        self.clock_lbl = QLabel("00:00:00")
        self.clock_lbl.setStyleSheet(f"color:{C_TEXT2}; font-family:monospace; font-size:12px;")
        tl.addWidget(self.clock_lbl)

        main_vbox.addWidget(topbar)

        # ── SPLITTER PRINCIPAL ───────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"QSplitter::handle {{ background:{C_GRAY2}; }}")

        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(210)
        sidebar.setStyleSheet(f"background:{C_BG2}; border-right:1px solid {C_GRAY2};")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 8, 0, 8)
        sb_layout.setSpacing(0)

        sb_title = QLabel("UNIDADES DETECTADAS")
        sb_title.setStyleSheet(f"color:{C_RED_DIM}; font-size:9px; letter-spacing:2px; padding:8px 14px 4px;")
        sb_layout.addWidget(sb_title)

        self.disk_list = QListWidget()
        self.disk_list.setStyleSheet(f"""
            QListWidget {{ background:{C_BG2}; border:none; }}
            QListWidget::item {{ padding:12px 14px; font-size:12px; }}
        """)
        self.disk_list.currentRowChanged.connect(self._on_disk_selected)
        sb_layout.addWidget(self.disk_list)

        refresh_btn = QPushButton("⟳  Re-escanear")
        refresh_btn.clicked.connect(self._detect_disks)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                margin: 8px;
                background:{C_BG3};
                border:1px solid {C_GRAY3};
                color:{C_TEXT3};
                font-size:10px;
                letter-spacing:1px;
                padding:8px;
            }}
            QPushButton:hover {{ border-color:{C_RED}; color:{C_RED_B}; }}
        """)
        sb_layout.addWidget(refresh_btn)

        # Panel principal
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background:{C_BG};")

        # Pantalla bienvenida
        welcome = QWidget()
        wl = QVBoxLayout(welcome)
        wl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wl.setSpacing(12)
        big = QLabel("⬡")
        big.setStyleSheet(f"color:{C_RED_DIM}; font-size:72px;")
        big.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wl.addWidget(big)
        wl1 = QLabel("ARASAKA RESCUE SOFTWARE")
        wl1.setStyleSheet(f"color:{C_TEXT2}; font-size:18px; letter-spacing:4px;")
        wl1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wl.addWidget(wl1)
        wl2 = QLabel("Selecciona un disco en el panel izquierdo")
        wl2.setStyleSheet(f"color:{C_TEXT3}; font-size:12px;")
        wl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wl.addWidget(wl2)
        self.stack.addWidget(welcome)
        self._welcome_idx = 0

        splitter.addWidget(sidebar)
        splitter.addWidget(self.stack)
        splitter.setSizes([210, 1070])

        main_vbox.addWidget(splitter)

        # ── STATUS BAR ───────────────────────────
        self.statusBar().setStyleSheet(f"""
            QStatusBar {{
                background:{C_BG2};
                color:{C_TEXT3};
                font-size:10px;
                font-family:monospace;
                border-top:1px solid {C_GRAY2};
            }}
        """)
        self.statusBar().showMessage(
            "Iniciado  |  Solo lectura activado  |  Para SMART completo ejecuta con: sudo python3 arasaka.py"
        )

    def _detect_disks(self):
        self.disk_count_lbl.setText("Escaneando...")
        worker = DetectionWorker(self)
        worker.done.connect(self._on_disks_found)
        worker.start()
        self._worker = worker

    def _on_disks_found(self, disks):
        if not disks:
            self.disk_count_lbl.setText("Sin discos detectados")
            return

        self.disk_count_lbl.setText(f"{len(disks)} unidad(es) detectada(s)")
        current_names = {self.disk_list.item(i).data(Qt.ItemDataRole.UserRole)
                         for i in range(self.disk_list.count())}
        new_names = {d["name"] for d in disks}

        for dev in disks:
            if dev["name"] not in current_names:
                self._add_disk(dev)

        # Eliminar discos que ya no están
        for name in current_names - new_names:
            for i in range(self.disk_list.count()):
                if self.disk_list.item(i).data(Qt.ItemDataRole.UserRole) == name:
                    self.disk_list.takeItem(i)
                    break

        if self.disk_list.count() > 0 and self.disk_list.currentRow() < 0:
            self.disk_list.setCurrentRow(0)

    def _add_disk(self, dev):
        size_raw = int(dev.get("size") or 0)
        dtype = detect_disk_type(dev)
        model = (dev.get("model") or "").strip()
        label = f"/dev/{dev['name']}\n{dtype}  ·  {bytes_to_human(size_raw)}"
        if model:
            label += f"\n{model[:28]}"

        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, dev["name"])

        # Icono por tipo
        icons = {
            "SSD NVMe":    "⚡",
            "SSD SATA":    "🔷",
            "HDD":         "💽",
            "USB / Externo":"🔌",
        }
        icon_chr = icons.get(dtype, "💾")
        item.setText(f"{icon_chr}  /dev/{dev['name']}\n"
                     f"   {dtype}  ·  {bytes_to_human(size_raw)}")

        self.disk_list.addItem(item)

        panel = DiskPanel(dev)
        idx = self.stack.addWidget(panel)
        self._disk_panels[dev["name"]] = idx

    def _on_disk_selected(self, row):
        if row < 0:
            return
        item = self.disk_list.item(row)
        if item:
            name = item.data(Qt.ItemDataRole.UserRole)
            idx = self._disk_panels.get(name, self._welcome_idx)
            self.stack.setCurrentIndex(idx)

    def _tick_clock(self):
        self.clock_lbl.setText(datetime.now().strftime("%H:%M:%S"))


# ─────────────────────────────────────────────
#  ENTRADA PRINCIPAL
# ─────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ARASAKA Rescue Software")
    app.setStyleSheet(STYLESHEET)

    # Intentar cargar fuente personalizada si está disponible
    QFontDatabase.addApplicationFont("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
