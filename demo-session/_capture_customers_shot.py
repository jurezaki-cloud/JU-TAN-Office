"""Temporary demo-session screenshot helper. Not application source.

Launches JU-TAN Office against demo-session only, opens Stranke,
captures a candidate PNG via PrintWindow, then exits.
Never points at data/ju_tan.db.
"""
from __future__ import annotations

import ctypes
import os
import sys
import time
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = Path(__file__).resolve().parent
PROD_DB = ROOT / "data" / "ju_tan.db"
OUT = Path(r"C:\Users\jurez\ju-tan-web\screenshot-candidates\office-customers-candidate.png")
TARGET_W, TARGET_H = 1896, 1001

os.environ["JU_TAN_DATA_DIR"] = str(DEMO)
os.environ["JU_TAN_DATABASE"] = str(DEMO / "ju_tan.db")

for m in list(sys.modules):
    if m.startswith("app.") or m in {"config", "app"}:
        del sys.modules[m]

sys.path.insert(0, str(ROOT))

from app.core.constants import DATA_DIR, DATABASE_PATH  # noqa: E402

if "demo-session" not in str(DATA_DIR.resolve()) or DATABASE_PATH.resolve() != (DEMO / "ju_tan.db").resolve():
    print("STOP: not isolated demo-session")
    sys.exit(2)
if DATABASE_PATH.resolve() == PROD_DB.resolve():
    print("STOP: production database selected")
    sys.exit(2)

prod_before = (PROD_DB.stat().st_mtime_ns, PROD_DB.stat().st_size)
print("PROD_BEFORE", prod_before)
print("DATA_DIR", DATA_DIR.resolve())
print("DATABASE_PATH", DATABASE_PATH.resolve())


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


def capture_hwnd(hwnd: int):
    """Capture full top-level window including DWM frame (no desktop/taskbar)."""
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    # Physical outer rect
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise RuntimeError("GetWindowRect failed")
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    if width <= 0 or height <= 0:
        raise RuntimeError(f"bad window size {width}x{height}")

    hwnd_dc = user32.GetWindowDC(hwnd)
    if not hwnd_dc:
        raise RuntimeError("GetWindowDC failed")
    mem_dc = gdi32.CreateCompatibleDC(hwnd_dc)
    bmp = gdi32.CreateCompatibleBitmap(hwnd_dc, width, height)
    old = gdi32.SelectObject(mem_dc, bmp)

    # PW_RENDERFULLCONTENT = 2
    ok = user32.PrintWindow(hwnd, mem_dc, 2)
    if not ok:
        # Fallback BitBlt from window DC
        gdi32.BitBlt(mem_dc, 0, 0, width, height, hwnd_dc, 0, 0, 0x00CC0020)

    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = width
    bmi.bmiHeader.biHeight = -height  # top-down
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0

    buf_size = width * height * 4
    buf = (ctypes.c_ubyte * buf_size)()
    gdi32.GetDIBits(mem_dc, bmp, 0, height, buf, ctypes.byref(bmi), 0)

    gdi32.SelectObject(mem_dc, old)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem_dc)
    user32.ReleaseDC(hwnd, hwnd_dc)

    from PySide6.QtGui import QImage, QPixmap

    image = QImage(bytes(buf), width, height, width * 4, QImage.Format.Format_ARGB32)
    return QPixmap.fromImage(image.copy()), width, height


def main() -> int:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QGuiApplication, QColor, QPixmap, QPixmapCache
    from PySide6.QtWidgets import QApplication, QSplashScreen, QAbstractItemView
    from PySide6.QtCore import qInstallMessageHandler

    from app.core.logger import install_excepthook
    from app.theme import theme_manager
    from app.windows.main_window import MainWindow, _qt_message

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    install_excepthook()
    qInstallMessageHandler(_qt_message)
    app = QApplication(sys.argv)
    QPixmapCache.setCacheLimit(20 * 1024)

    splash_pix = QPixmap(420, 200)
    splash_pix.fill(QColor("#0F172A"))
    splash = QSplashScreen(splash_pix)
    splash.showMessage(
        "JU-TAN Office Enterprise",
        Qt.AlignBottom | Qt.AlignCenter,
        QColor("#F8FAFC"),
    )
    splash.show()
    app.processEvents()
    theme_manager.apply(app)

    from app.core.update import apply_schema_upgrade
    apply_schema_upgrade()
    from app.core.db_guard import ensure_runtime
    from app.core.recovery import mark_running

    mark_running()
    ensure_runtime()

    from app.modules.settings.settings_controller import SettingsController
    from app.core.session import session

    extras = SettingsController().load_extras()
    session.remember_user = bool(extras.get("remember_user", True))
    session.login(
        extras.get("administrator") or "Administrator",
        extras.get("role") or "Administrator",
    )

    window = MainWindow()
    window.setWindowTitle("JU-TAN Office Enterprise")
    window.show()
    splash.finish(window)
    app.processEvents()

    window.change_page(2)
    app.processEvents()

    dpr = float(window.devicePixelRatioF())
    screen = window.screen() or QGuiApplication.primaryScreen()
    avail = screen.availableGeometry()
    print("DPR", dpr, "AVAIL_LOGICAL", avail.width(), avail.height())

    # Target outer physical size == approved marketing shots.
    target_logical_w = int(round(TARGET_W / dpr))
    target_logical_h = int(round(TARGET_H / dpr))

    # Place fully on-screen (avoid negative Y from restored geometry).
    x = avail.x() + 12
    y = avail.y() + 12
    # setGeometry sets client area; approximate chrome then refine via WinAPI.
    window.setGeometry(x, y, target_logical_w - 16, target_logical_h - 40)
    app.processEvents()
    time.sleep(0.15)
    app.processEvents()

    hwnd = int(window.winId())
    user32 = ctypes.windll.user32
    # Adjust outer size precisely with SetWindowPos (physical pixels on Per-Monitor v2).
    SWP_NOZORDER = 0x0004
    SWP_NOACTIVATE = 0x0010
    # Convert logical top-left to physical for SetWindowPos? On Win10+ with DPI awareness,
    # Qt winId windows typically expect physical for Get/SetWindowRect.
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    phys_x, phys_y = rect.left, max(0, rect.top)
    user32.SetWindowPos(hwnd, 0, phys_x, phys_y, TARGET_W, TARGET_H, SWP_NOZORDER | SWP_NOACTIVATE)
    app.processEvents()
    time.sleep(0.2)
    app.processEvents()

    current = window.customers.ensure()
    app.processEvents()
    # Clear search to avoid match highlights
    if hasattr(current, "search") and current.search is not None:
        current.search.blockSignals(True)
        current.search.clear()
        current.search.blockSignals(False)
        current.refresh()
        app.processEvents()

    table = current.table
    model = current.model
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.clearSelection()
    if model.rowCount() > 0:
        # Prefer Alpina Digital for a stable hero row if present
        target_row = 0
        for r in range(model.rowCount()):
            if str(model.customers[r][1]).startswith("Alpina"):
                target_row = r
                break
        idx = model.index(target_row, 1)
        table.selectRow(target_row)
        table.setCurrentIndex(idx)
        current.show_details(idx)
        app.processEvents()

    # Kill carets / text selection artifacts
    table.setFocus(Qt.OtherFocusReason)
    window.activateWindow()
    app.processEvents()

    deadline = time.time() + 1.2
    while time.time() < deadline:
        app.processEvents()
        time.sleep(0.05)

    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    print(
        "WIN_RECT",
        rect.left,
        rect.top,
        rect.right - rect.left,
        rect.bottom - rect.top,
    )

    pix, raw_w, raw_h = capture_hwnd(hwnd)
    print("RAW_SIZE", raw_w, raw_h)

    if pix.width() != TARGET_W or pix.height() != TARGET_H:
        print("RESCALE", pix.width(), pix.height(), "->", TARGET_W, TARGET_H)
        pix = pix.scaled(
            TARGET_W,
            TARGET_H,
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation,
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    ok = pix.save(str(OUT), "PNG")
    print("SAVED", ok, OUT, pix.width(), pix.height())

    prod_after = (PROD_DB.stat().st_mtime_ns, PROD_DB.stat().st_size)
    print("PROD_AFTER", prod_after)
    if prod_after != prod_before:
        print("STOP: production database changed")
        window.close()
        app.quit()
        return 3

    print("REAL_DATABASE_TOUCHED NO")
    QTimer.singleShot(50, app.quit)
    app.exec()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
