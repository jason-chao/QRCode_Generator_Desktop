"""QR Code Generator — Tkinter desktop application."""

import configparser
import io
import os
import sys
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

import qrcode
from PIL import Image, ImageTk

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# _BASE_DIR  — directory of the exe / script (user-editable files live here)
# _RES_DIR   — directory where bundled read-only assets are extracted
#              (sys._MEIPASS in a onefile build, same as _BASE_DIR otherwise)
if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
    _RES_DIR  = sys._MEIPASS
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    _RES_DIR  = _BASE_DIR
CONFIG_FILE = os.path.join(_BASE_DIR, "config.ini")

NAMED_COLOURS = [
    "black", "white", "red", "green", "blue", "yellow",
    "cyan", "magenta", "orange", "purple", "gray", "transparent",
]

ERROR_CORRECTION_OPTIONS = {
    "L  –  7%": qrcode.constants.ERROR_CORRECT_L,
    "M  – 15%": qrcode.constants.ERROR_CORRECT_M,
    "Q  – 25%": qrcode.constants.ERROR_CORRECT_Q,
    "H  – 30%": qrcode.constants.ERROR_CORRECT_H,
}

BOX_SIZES = [str(n) for n in range(1, 21)]

SAVE_FILETYPES = [
    ("PNG image",   "*.png"),
    ("JPEG image",  "*.jpg"),
    ("BMP image",   "*.bmp"),
    ("GIF image",   "*.gif"),
    ("TIFF image",  "*.tiff"),
    ("WebP image",  "*.webp"),
    ("ICO image",   "*.ico"),
    ("All files",   "*.*"),
]


def load_config() -> dict:
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_FILE)
    d = cfg["defaults"] if "defaults" in cfg else {}
    return {
        "url":              d.get("url",              "https://github.com/jason-chao/QRCode_Generator_Desktop"),
        "foreground":       d.get("foreground",       "black"),
        "background":       d.get("background",       "white"),
        "error_correction": d.get("error_correction", "M"),
        "box_size":         d.get("box_size",         "10"),
        "border":           d.get("border",           "4"),
    }


def ec_label_for(level_char: str) -> str:
    """Return the dropdown label matching the single-char level string."""
    mapping = {"L": "L  –  7%", "M": "M  – 15%", "Q": "Q  – 25%", "H": "H  – 30%"}
    return mapping.get(level_char.upper(), "M  – 15%")


def is_valid_hex(value: str) -> bool:
    v = value.strip()
    if v.startswith("#"):
        v = v[1:]
    return len(v) in (3, 6) and all(c in "0123456789abcdefABCDEF" for c in v)


def normalise_colour(value: str) -> str | None:
    """Return a colour string Pillow accepts, or None for 'transparent'."""
    v = value.strip().lower()
    if v == "transparent":
        return None
    if v in NAMED_COLOURS:
        return v
    if is_valid_hex(value.strip()):
        return value.strip() if value.strip().startswith("#") else "#" + value.strip()
    return None  # treat unknown as transparent


def generate_qr_image(url: str, fg: str, bg: str | None,
                       ec_level, box_size: int, border: int) -> Image.Image:
    qr = qrcode.QRCode(
        error_correction=ec_level,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)

    if bg is None:
        # back_color="transparent" is the library's own trigger for RGBA mode;
        # passing (0, 0, 0, 0) instead hits the RGB branch and loses the alpha.
        img = qr.make_image(fill_color=fg, back_color="transparent").convert("RGBA")
    else:
        img = qr.make_image(fill_color=fg, back_color=bg).convert("RGBA")

    return img


# ---------------------------------------------------------------------------
# Colour picker widget
# ---------------------------------------------------------------------------

class ColourSelector(tk.Frame):
    """Combo + hex entry + colour-picker button."""

    def __init__(self, parent, default: str, allow_transparent: bool = False, **kw):
        super().__init__(parent, **kw)
        self._allow_transparent = allow_transparent

        colours = NAMED_COLOURS if allow_transparent else [c for c in NAMED_COLOURS if c != "transparent"]

        self._combo_var = tk.StringVar()
        self._hex_var = tk.StringVar()

        self._combo = ttk.Combobox(
            self, textvariable=self._combo_var,
            values=colours, state="readonly", width=13,
        )
        self._combo.grid(row=0, column=0, padx=(0, 4))
        self._combo.bind("<<ComboboxSelected>>", self._on_combo)

        self._hex_entry = ttk.Entry(self, textvariable=self._hex_var, width=9)
        self._hex_entry.grid(row=0, column=1, padx=(0, 4))
        self._hex_entry.bind("<FocusOut>", self._on_hex)
        self._hex_entry.bind("<Return>",   self._on_hex)

        self._swatch = tk.Label(self, width=2, relief="sunken")
        self._swatch.grid(row=0, column=2, padx=(0, 4))
        self._swatch.bind("<Button-1>", self._open_picker)
        self._default_bg = self._swatch.cget("bg")

        self._pick_btn = ttk.Button(self, text="Pick…", width=5, command=self._open_picker)
        self._pick_btn.grid(row=0, column=3)

        self.set(default)

    # ------------------------------------------------------------------
    def set(self, value: str):
        v = value.strip().lower()
        colours = NAMED_COLOURS if self._allow_transparent else [c for c in NAMED_COLOURS if c != "transparent"]
        if v in colours:
            self._combo_var.set(v)
            self._hex_var.set("")
        else:
            self._combo_var.set("")
            self._hex_var.set(value.strip())
        self._update_swatch()

    def get(self) -> str:
        hex_val = self._hex_var.get().strip()
        if hex_val:
            return hex_val
        return self._combo_var.get() or "black"

    # ------------------------------------------------------------------
    def _on_combo(self, _event=None):
        self._hex_var.set("")
        self._update_swatch()

    def _on_hex(self, _event=None):
        val = self._hex_var.get().strip()
        if val:
            self._combo_var.set("")
        self._update_swatch()

    def _open_picker(self, _event=None):
        current = self.get()
        if current.lower() == "transparent":
            current = "#ffffff"
        try:
            result = colorchooser.askcolor(color=current, title="Choose colour")
        except Exception:
            return
        if result and result[1]:
            self._hex_var.set(result[1])
            self._combo_var.set("")
            self._update_swatch()

    def _update_swatch(self):
        val = self.get()
        if val.lower() == "transparent":
            self._swatch.configure(bg=self._default_bg)
            return
        colour = normalise_colour(val)
        if colour:
            try:
                self._swatch.configure(bg=colour)
            except tk.TclError:
                pass


# ---------------------------------------------------------------------------
# Main application window
# ---------------------------------------------------------------------------

class QRCodeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Good QR Code Generator")
        self.resizable(True, True)
        self._qr_image: Image.Image | None = None
        self._tk_image: ImageTk.PhotoImage | None = None
        self._app_icon: ImageTk.PhotoImage | None = None

        self._set_window_icon()
        cfg = load_config()
        self._build_ui(cfg)
        self._centre_window()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self, cfg: dict):
        pad = {"padx": 8, "pady": 4}

        # ── Controls frame ─────────────────────────────────────────────
        ctrl = ttk.LabelFrame(self, text="Settings", padding=10)
        ctrl.grid(row=0, column=0, sticky="nsew", **pad)
        self.columnconfigure(0, weight=1)

        row = 0

        # URL
        ttk.Label(ctrl, text="URL:").grid(row=row, column=0, sticky="e", **pad)
        self._url_var = tk.StringVar(value=cfg["url"])
        ttk.Entry(ctrl, textvariable=self._url_var, width=45).grid(
            row=row, column=1, columnspan=3, sticky="ew", **pad)
        ctrl.columnconfigure(1, weight=1)
        row += 1

        # Foreground colour
        ttk.Label(ctrl, text="Foreground:").grid(row=row, column=0, sticky="e", **pad)
        self._fg_selector = ColourSelector(ctrl, default=cfg["foreground"], allow_transparent=False)
        self._fg_selector.grid(row=row, column=1, columnspan=3, sticky="w", **pad)
        row += 1

        # Background colour
        ttk.Label(ctrl, text="Background:").grid(row=row, column=0, sticky="e", **pad)
        self._bg_selector = ColourSelector(ctrl, default=cfg["background"], allow_transparent=True)
        self._bg_selector.grid(row=row, column=1, columnspan=3, sticky="w", **pad)
        row += 1

        # Error correction
        ttk.Label(ctrl, text="Error correction:").grid(row=row, column=0, sticky="e", **pad)
        self._ec_var = tk.StringVar(value=ec_label_for(cfg["error_correction"]))
        ttk.Combobox(
            ctrl, textvariable=self._ec_var,
            values=list(ERROR_CORRECTION_OPTIONS.keys()),
            state="readonly", width=14,
        ).grid(row=row, column=1, sticky="w", **pad)
        row += 1

        # Box size
        ttk.Label(ctrl, text="Box size (px):").grid(row=row, column=0, sticky="e", **pad)
        self._box_var = tk.StringVar(value=cfg["box_size"])
        ttk.Combobox(
            ctrl, textvariable=self._box_var,
            values=BOX_SIZES, state="readonly", width=6,
        ).grid(row=row, column=1, sticky="w", **pad)
        row += 1

        # Border
        ttk.Label(ctrl, text="Border (boxes):").grid(row=row, column=0, sticky="e", **pad)
        self._border_var = tk.StringVar(value=cfg["border"])
        vcmd = (self.register(self._validate_int), "%P")
        ttk.Spinbox(
            ctrl, textvariable=self._border_var,
            from_=0, to=20, width=6,
            validate="key", validatecommand=vcmd,
        ).grid(row=row, column=1, sticky="w", **pad)
        row += 1

        # Generate button
        ttk.Button(
            ctrl, text="Generate QR Code", command=self._on_generate,
        ).grid(row=row, column=0, columnspan=4, pady=(12, 4))

        # ── Preview frame ──────────────────────────────────────────────
        prev = ttk.LabelFrame(self, text="Preview", padding=10)
        prev.grid(row=1, column=0, sticky="nsew", **pad)
        self.rowconfigure(1, weight=1)

        self._preview_label = ttk.Label(prev, text="No QR code generated yet.")
        self._preview_label.pack(expand=True)

        # Action buttons (hidden until an image is ready)
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, pady=(0, 10))

        self._save_btn = ttk.Button(
            btn_frame, text="Save image…", command=self._on_save, state="disabled",
        )
        self._save_btn.grid(row=0, column=0, padx=4)

        self._copy_btn = ttk.Button(
            btn_frame, text="Copy image", command=self._on_copy, state="disabled",
        )
        self._copy_btn.grid(row=0, column=1, padx=4)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_int(value: str) -> bool:
        return value == "" or value.isdigit()

    def _set_window_icon(self):
        try:
            if sys.platform == "win32":
                # iconbitmap gives consistent title-bar, taskbar, and alt-tab icons on Windows
                ico_path = os.path.join(_RES_DIR, "assets", "icon.ico")
                if os.path.isfile(ico_path):
                    self.iconbitmap(ico_path)
            else:
                png_path = os.path.join(_RES_DIR, "assets", "icon.png")
                if os.path.isfile(png_path):
                    img = Image.open(png_path)
                    self._app_icon = ImageTk.PhotoImage(img)
                    self.iconphoto(True, self._app_icon)
        except Exception:
            pass

    def _centre_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_generate(self):
        url = self._url_var.get().strip()
        if not url:
            messagebox.showwarning("Missing URL", "Please enter a URL to encode.")
            return

        fg_raw = self._fg_selector.get()
        bg_raw = self._bg_selector.get()

        fg = normalise_colour(fg_raw)
        if fg is None:
            messagebox.showerror(
                "Invalid foreground colour",
                f"'{fg_raw}' is not a recognised colour. Use a name or #RRGGBB hex code.",
            )
            return

        bg = normalise_colour(bg_raw)
        # bg == None means transparent — that's fine

        ec_label = self._ec_var.get()
        ec_level = ERROR_CORRECTION_OPTIONS.get(ec_label, qrcode.constants.ERROR_CORRECT_M)

        try:
            box_size = int(self._box_var.get())
        except ValueError:
            box_size = 10

        try:
            border = int(self._border_var.get() or "4")
        except ValueError:
            border = 4

        try:
            img = generate_qr_image(url, fg, bg, ec_level, box_size, border)
        except Exception as exc:
            messagebox.showerror("Generation error", str(exc))
            return

        self._qr_image = img
        self._show_preview(img)
        self._save_btn.configure(state="normal")
        self._copy_btn.configure(state="normal")

    def _show_preview(self, img: Image.Image):
        # Scale to fit inside a 300×300 box while keeping aspect ratio
        max_dim = 300
        w, h = img.size
        scale = min(max_dim / w, max_dim / h, 1.0)
        disp = img.resize((int(w * scale), int(h * scale)), Image.NEAREST)

        # Composite onto a checkerboard to show transparency
        checker = self._make_checker(disp.size)
        checker.paste(disp, mask=disp.split()[3] if disp.mode == "RGBA" else None)

        self._tk_image = ImageTk.PhotoImage(checker)
        self._preview_label.configure(image=self._tk_image, text="")

    @staticmethod
    def _make_checker(size: tuple[int, int], tile: int = 8) -> Image.Image:
        """Light/dark grey checkerboard background for transparent previews."""
        img = Image.new("RGB", size, (204, 204, 204))
        for y in range(0, size[1], tile):
            for x in range(0, size[0], tile):
                if (x // tile + y // tile) % 2 == 0:
                    for py in range(y, min(y + tile, size[1])):
                        for px in range(x, min(x + tile, size[0])):
                            img.putpixel((px, py), (255, 255, 255))
        return img

    def _on_save(self):
        if self._qr_image is None:
            return

        path = filedialog.asksaveasfilename(
            title="Save QR code",
            defaultextension=".png",
            filetypes=SAVE_FILETYPES,
        )
        if not path:
            return

        ext = os.path.splitext(path)[1].lower()
        img = self._qr_image

        try:
            if ext in (".jpg", ".jpeg"):
                # JPEG does not support alpha; composite onto white
                bg = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    bg.paste(img, mask=img.split()[3])
                else:
                    bg.paste(img)
                bg.save(path, quality=95)
            elif ext == ".ico":
                img.save(path, format="ICO", sizes=[(256, 256)])
            else:
                img.save(path)
            messagebox.showinfo("Saved", f"QR code saved to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Save error", str(exc))

    def _on_copy(self):
        if self._qr_image is None:
            return

        try:
            self._copy_image_to_clipboard(self._qr_image)
            messagebox.showinfo("Copied", "QR code copied to clipboard.")
        except Exception as exc:
            messagebox.showerror("Copy error", f"Failed to copy image to clipboard:\n{exc}")

    @staticmethod
    def _copy_image_to_clipboard(img: Image.Image):
        if sys.platform == "win32":
            import ctypes
            import ctypes.wintypes
            import struct

            img_rgba = img.convert("RGBA")
            width, height = img_rgba.size

            # --- CF_DIBV5 (format 17): 32-bit BGRA with alpha masks ---
            # Windows DIB pixels are stored in BGRA byte order.
            r, g, b, a = img_rgba.split()
            pixel_data = Image.merge("RGBA", (b, g, r, a)).tobytes()

            BI_BITFIELDS  = 3
            LCS_sRGB      = 0x73524742
            LCS_GM_IMAGES = 4

            dibv5_header = struct.pack(
                "<IiiHHIIiiIIIIIII36sIIIIIII",
                124,              # bV5Size
                width,            # bV5Width
                -height,          # bV5Height  (negative = top-down)
                1,                # bV5Planes
                32,               # bV5BitCount
                BI_BITFIELDS,     # bV5Compression
                len(pixel_data),  # bV5SizeImage
                0, 0,             # bV5X/YPelsPerMeter
                0, 0,             # bV5ClrUsed / bV5ClrImportant
                0x00FF0000,       # bV5RedMask
                0x0000FF00,       # bV5GreenMask
                0x000000FF,       # bV5BlueMask
                0xFF000000,       # bV5AlphaMask
                LCS_sRGB,         # bV5CSType
                b"\x00" * 36,     # bV5Endpoints (CIEXYZTRIPLE, unused)
                0, 0, 0,          # bV5GammaRed/Green/Blue
                LCS_GM_IMAGES,    # bV5Intent
                0, 0, 0,          # bV5ProfileData/Size/Reserved
            )
            dibv5_data = dibv5_header + pixel_data

            # --- CF_DIB (format 8): RGB with white background (universal fallback) ---
            flat = Image.new("RGB", img_rgba.size, (255, 255, 255))
            flat.paste(img_rgba, mask=img_rgba.split()[3])
            dib_buf = io.BytesIO()
            flat.save(dib_buf, format="BMP")
            dib_data = dib_buf.getvalue()[14:]  # strip 14-byte BITMAPFILEHEADER

            # --- "PNG" registered format: raw PNG bytes (Chrome, GIMP, Inkscape…) ---
            png_buf = io.BytesIO()
            img_rgba.save(png_buf, format="PNG")
            png_data = png_buf.getvalue()

            CF_DIB    = 8
            CF_DIBV5  = 17
            GMEM_MOVEABLE = 0x0002

            kernel32 = ctypes.windll.kernel32
            user32   = ctypes.windll.user32

            # Explicit types are required on 64-bit Windows; without them ctypes
            # truncates 64-bit HANDLE/LPVOID returns to 32 bits, causing GlobalLock
            # to receive a corrupt handle and return NULL.
            kernel32.GlobalAlloc.restype   = ctypes.c_void_p
            kernel32.GlobalAlloc.argtypes  = [ctypes.wintypes.UINT, ctypes.c_size_t]
            kernel32.GlobalLock.restype    = ctypes.c_void_p
            kernel32.GlobalLock.argtypes   = [ctypes.c_void_p]
            kernel32.GlobalUnlock.restype  = ctypes.wintypes.BOOL
            kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalFree.restype    = ctypes.c_void_p
            kernel32.GlobalFree.argtypes   = [ctypes.c_void_p]

            user32.OpenClipboard.restype             = ctypes.wintypes.BOOL
            user32.OpenClipboard.argtypes            = [ctypes.wintypes.HWND]
            user32.EmptyClipboard.restype            = ctypes.wintypes.BOOL
            user32.EmptyClipboard.argtypes           = []
            user32.SetClipboardData.restype          = ctypes.c_void_p
            user32.SetClipboardData.argtypes         = [ctypes.wintypes.UINT, ctypes.c_void_p]
            user32.CloseClipboard.restype            = ctypes.wintypes.BOOL
            user32.CloseClipboard.argtypes           = []
            user32.RegisterClipboardFormatW.restype  = ctypes.wintypes.UINT
            user32.RegisterClipboardFormatW.argtypes = [ctypes.wintypes.LPCWSTR]

            CF_PNG = user32.RegisterClipboardFormatW("PNG")

            def _alloc(data: bytes) -> int:
                h = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
                if not h:
                    raise Exception("GlobalAlloc failed")
                ptr = kernel32.GlobalLock(h)
                if not ptr:
                    kernel32.GlobalFree(h)
                    raise Exception("GlobalLock failed")
                try:
                    ctypes.memmove(ptr, data, len(data))
                finally:
                    kernel32.GlobalUnlock(h)
                return h

            h_dibv5 = _alloc(dibv5_data)
            h_dib   = _alloc(dib_data)
            h_png   = _alloc(png_data)

            if not user32.OpenClipboard(0):
                for h in (h_dibv5, h_dib, h_png):
                    kernel32.GlobalFree(h)
                raise Exception("Failed to open clipboard.")

            try:
                user32.EmptyClipboard()
                # After a successful SetClipboardData the OS owns the handle;
                # only free it if the call itself fails.
                if not user32.SetClipboardData(CF_DIBV5, h_dibv5):
                    kernel32.GlobalFree(h_dibv5)
                if not user32.SetClipboardData(CF_DIB, h_dib):
                    kernel32.GlobalFree(h_dib)
                if CF_PNG and not user32.SetClipboardData(CF_PNG, h_png):
                    kernel32.GlobalFree(h_png)
            finally:
                user32.CloseClipboard()
                
        elif sys.platform == "darwin":
            import subprocess
            import tempfile
            
            fd, path = tempfile.mkstemp(suffix=".png")
            try:
                os.close(fd)
                img.save(path, format="PNG")
                script = f'set the clipboard to (read (POSIX file "{path}") as TIFF picture)'
                subprocess.run(["osascript", "-e", script], check=True)
            finally:
                try:
                    os.unlink(path)
                except OSError:
                    pass
                    
        else:  # Linux and others
            import subprocess
            
            output = io.BytesIO()
            img.save(output, format="PNG")
            data = output.getvalue()
            
            wayland_display = os.environ.get("WAYLAND_DISPLAY")
            
            if wayland_display:
                try:
                    subprocess.run(["wl-copy", "-t", "image/png"], input=data, check=True)
                except FileNotFoundError:
                    raise Exception("wl-copy is not installed. Please install wl-clipboard.")
                except subprocess.CalledProcessError as e:
                    raise Exception(f"wl-copy failed: {e}")
            else:
                try:
                    subprocess.run(["xclip", "-selection", "clipboard", "-t", "image/png", "-i"], input=data, check=True)
                except FileNotFoundError:
                    raise Exception("xclip is not installed. Please install xclip.")
                except subprocess.CalledProcessError as e:
                    raise Exception(f"xclip failed: {e}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    # On Windows, prevent the console window from showing when packaged
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except Exception:
            pass

    app = QRCodeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
