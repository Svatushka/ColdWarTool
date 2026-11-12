import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, simpledialog
import math
import json
import os
import re
import sys
from datetime import datetime
from PIL import Image, ImageTk, ImageGrab


# =====================================================================
# ЧАСТЬ 0: СИСТЕМНЫЕ ХЕЛПЕРЫ
# =====================================================================
def executable_dir():
    """Папка, где лежит .exe (или app.py в dev-режиме)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(relative):
    """Путь к ресурсу, вшитому в PyInstaller (onefile -> _MEIPASS)."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative)


APP_DATA_DIR = os.getenv('APPDATA') or os.path.expanduser('~')
APP_FOLDER = os.path.join(APP_DATA_DIR, "ColdWarTools")
os.makedirs(APP_FOLDER, exist_ok=True)
LOG_FILE = os.path.join(APP_FOLDER, "debug.log")


def debug_log(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")
    except Exception:
        pass
    try:
        print(msg)
    except Exception:
        pass


# =====================================================================
# ЧАСТЬ 0.1: ЦВЕТНЫЕ ЭМОДЗИ
# =====================================================================
_EMOJI_RANGES = (
    "\U0001F1E0-\U0001F1FF"
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002300-\U000023FF"
    "\U00002600-\U000026FF"
    "\U00002700-\U000027BF"
    "\U0001F000-\U0001F02F"
)


class EmojiManager:
    _instance = None
    EMOJI_PATTERN = re.compile(
        "(?:"
        "[" + _EMOJI_RANGES + "]"
        "[\uFE0F\uFE0E]?"
        "(?:\u200D[" + _EMOJI_RANGES + "][\uFE0F\uFE0E]?)*"
        ")"
    )

    def __init__(self):
        self._pil_cache = {}
        self._ctk_cache = {}
        self._photo_cache = {}
        self.font_path = self._find([
            r"C:\Windows\Fonts\seguiemj.ttf",
            r"C:\Windows\Fonts\SegoeUIEmoji.ttf",
            "/System/Library/Fonts/Apple Color Emoji.ttc",
            "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        ])
        self.symbol_font_path = self._find([
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\seguisym.ttf",
            r"C:\Windows\Fonts\arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ])

    @staticmethod
    def _find(paths):
        for p in paths:
            if os.path.exists(p):
                return p
        return None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def render(self, emoji, size=20):
        if not self.font_path:
            return None
        key = ("e", emoji, size)
        if key in self._pil_cache:
            return self._pil_cache[key]
        try:
            from PIL import ImageFont, ImageDraw
            font = ImageFont.truetype(self.font_path, size)
            canvas = size * 3
            img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            try:
                draw.text((0, 0), emoji, font=font, embedded_color=True)
            except TypeError:
                draw.text((0, 0), emoji, font=font)
            bbox = img.getbbox()
            if bbox:
                img = img.crop(bbox)
            self._pil_cache[key] = img
            return img
        except Exception as e:
            debug_log(f"[Emoji] '{emoji}': {e}")
            return None

    def render_symbol(self, char, size=20, color="#dcdcdc"):
        if not self.symbol_font_path:
            return None
        key = ("s", char, size, color)
        if key in self._pil_cache:
            return self._pil_cache[key]
        try:
            from PIL import ImageFont, ImageDraw
            font = ImageFont.truetype(self.symbol_font_path, size)
            bbox = font.getbbox(char)
            w, h = max(1, bbox[2] - bbox[0]), max(1, bbox[3] - bbox[1])
            img = Image.new("RGBA", (w + 4, h + 4), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((2 - bbox[0], 2 - bbox[1]), char, font=font, fill=color)
            self._pil_cache[key] = img
            return img
        except Exception as e:
            debug_log(f"[Symbol] '{char}': {e}")
            return None

    def ctk_image(self, emoji, size=20):
        key = ("ce", emoji, size)
        if key in self._ctk_cache:
            return self._ctk_cache[key]
        img = self.render(emoji, size)
        if img is None:
            return None
        ci = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        self._ctk_cache[key] = ci
        return ci

    def ctk_symbol(self, char, size=20, color="#dcdcdc"):
        key = ("cs", char, size, color)
        if key in self._ctk_cache:
            return self._ctk_cache[key]
        img = self.render_symbol(char, size, color)
        if img is None:
            return None
        ci = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        self._ctk_cache[key] = ci
        return ci

    def photo_image(self, emoji, size=14):
        key = ("p", emoji, size)
        if key in self._photo_cache:
            return self._photo_cache[key]
        img = self.render(emoji, size)
        if img is None:
            return None
        pi = ImageTk.PhotoImage(img)
        self._photo_cache[key] = pi
        return pi

    def split(self, text):
        result, pos = [], 0
        for m in self.EMOJI_PATTERN.finditer(text):
            if m.start() > pos:
                result.append(("text", text[pos:m.start()]))
            result.append(("emoji", m.group(0)))
            pos = m.end()
        if pos < len(text):
            result.append(("text", text[pos:]))
        return result


EMOJI = EmojiManager.get()


def apply_emoji_widget(widget, text, size=16):
    parts = EMOJI.split(text)
    if parts and parts[0][0] == "emoji":
        emoji, rest = parts[0][1], "".join(p[1] for p in parts[1:])
        img = EMOJI.ctk_image(emoji, size=size)
        if img is not None:
            widget.configure(image=img, text=rest, compound="left")
            return
    widget.configure(text=text)


def insert_rich_textbox(textbox, text, emoji_size=14):
    tb = textbox._textbox
    if not hasattr(textbox, '_emoji_refs'):
        textbox._emoji_refs = []
    for kind, part in EMOJI.split(text):
        if kind == "text":
            tb.insert("end", part)
        else:
            photo = EMOJI.photo_image(part, size=emoji_size)
            if photo is not None:
                textbox._emoji_refs.append(photo)
                tb.image_create("end", image=photo)
            else:
                tb.insert("end", part)


# =====================================================================
# ЧАСТЬ 1: КОНСТАНТЫ
# =====================================================================
COLOR_BG = "#121212"
COLOR_PANEL = "#1e1e1e"
COLOR_ACCENT = "#2d4a3e"
COLOR_ACCENT_HOVER = "#3c6353"
COLOR_RED = "#6b1d1d"
COLOR_RED_HOVER = "#8c2a2a"
COLOR_TEXT = "#dcdcdc"
COLOR_TEXT_MUTED = "#8a8a8a"
COLOR_GREEN = "#4ade80"

WEAPONS_BY_FACTION = {
    "NATO": {
        "Sniper Rifles": {"LW3 - Tundra": 580, "M82": 525, "Pelington 703": 478},
        "Tactical Rifles": {"AUG": 775, "M16": 725, "DMR 14": 700},
        "Assault Rifles": {"C58": 730, "FARA 83": 729, "EM2": 688, "Krig 6": 686, "QBZ-83": 671, "XM4": 657, "FFAR 1": 629},
        "LMGs": {"M60": 791, "Stoner 63": 714},
        "Shotguns": {"Hauer 77": 850, "Gallo SA12": 850, "Streetsweeper": 850},
        "SMGs": {"LC10": 410, "KSP 45": 265, "TEC-9": 258, "Milano 821": 225, "MAC 10": 200},
        "Handguns": {"Magnum": 313, "1911": 200},
    },
    "Warsaw Pact": {
        "Sniper Rifles": {"ZRG 20mm": 923, "Swiss K31": 684},
        "Tactical Rifles": {"Type 63": 625, "CARV.2": 605},
        "Assault Rifles": {"AK-47": 702, "Groza": 660},
        "LMGs": {"RPD": 684, "MG82": 603},
        "Shotguns": {"Hauer 77": 850, "Gallo SA12": 850},
        "SMGs": {"AK-74u": 383, "Bullfrog": 250},
        "Handguns": {"Magnum": 313},
    },
}

CATEGORIES = {
    "Sniper Rifles": {"ru": "Снайперские винтовки", "en": "Sniper Rifles"},
    "Tactical Rifles": {"ru": "Тактические винтовки", "en": "Tactical Rifles"},
    "Assault Rifles": {"ru": "Штурмовые винтовки", "en": "Assault Rifles"},
    "LMGs": {"ru": "Пулемёты", "en": "LMGs"},
    "Shotguns": {"ru": "Дробовики", "en": "Shotguns"},
    "SMGs": {"ru": "Пистолеты-пулемёты", "en": "SMGs"},
    "Handguns": {"ru": "Пистолеты", "en": "Handguns"},
    "NATO": {"ru": "НАТО", "en": "NATO"},
    "Warsaw Pact": {"ru": "Варшавский договор", "en": "Warsaw Pact"},
}

GRAVITY = 9.8

UI_TEXT = {
    "title": {"ru": "☢️ COLD WAR TOOLS", "en": "☢️ COLD WAR TOOLS"},
    "btn_lang": {"ru": "🌐 EN", "en": "🌐 RU"},
    "tab_calc": {"ru": "Баллистика", "en": "Ballistics"},
    "tab_map": {"ru": "Тактическая карта", "en": "Tactical Map"},

    "faction": {"ru": "ФРАКЦИЯ", "en": "FACTION"},
    "weapon": {"ru": "ВООРУЖЕНИЕ", "en": "WEAPONRY"},
    "velocity": {"ru": "Скорость пули:", "en": "Bullet velocity:"},
    "params": {"ru": "ПАРАМЕТРЫ ВЫСТРЕЛА", "en": "SHOT PARAMETERS"},
    "dist": {"ru": "Дистанция (м):", "en": "Distance (m):"},
    "target_spd": {"ru": "Скорость цели (м/с):", "en": "Target speed (m/s):"},
    "btn_calc": {"ru": "РАССЧИТАТЬ", "en": "CALCULATE"},
    "btn_reset": {"ru": "СБРОС", "en": "RESET"},
    "chart": {"ru": "ГРАФИК ПАДЕНИЯ", "en": "DROP CHART"},
    "results": {"ru": "ТЕЛЕМЕТРИЯ", "en": "TELEMETRY"},
    "axis_dist": {"ru": "Дистанция (м)", "en": "Distance (m)"},
    "axis_drop": {"ru": "Падение (см)", "en": "Drop (cm)"},
    "res_faction": {"ru": "Фракция:", "en": "Faction:"},
    "res_weapon": {"ru": "Оружие:", "en": "Weapon:"},
    "res_velocity": {"ru": "Скорость пули:", "en": "Bullet velocity:"},
    "res_distance": {"ru": "Дистанция:", "en": "Distance:"},
    "res_time": {"ru": "⏱ Время полёта:", "en": "⏱ Time of flight:"},
    "res_drop": {"ru": "📉 Падение пули:", "en": "📉 Bullet drop:"},
    "res_lead": {"ru": "🎯 Упреждение:", "en": "🎯 Lead required:"},
    "res_no_lead": {"ru": "🎯 Цель неподвижна", "en": "🎯 Target is stationary"},
    "unit_m": {"ru": "м", "en": "m"},
    "unit_cm": {"ru": "см", "en": "cm"},
    "unit_mps": {"ru": "м/с", "en": "m/s"},
    "unit_sec": {"ru": "с", "en": "s"},
    "err_dist": {"ru": "Дистанция > 0", "en": "Distance > 0"},
    "err_calc": {"ru": "Ошибка расчёта", "en": "Calculation error"},

    "map_title": {"ru": "ТАКТИЧЕСКАЯ КАРТА", "en": "TACTICAL MAP"},
    "map_select": {"ru": "Выбор карты", "en": "Select map"},
    "map_tool": {"ru": "ИНСТРУМЕНТ", "en": "TOOL"},
    "map_color": {"ru": "Цвет кисти", "en": "Brush color"},
    "map_size": {"ru": "Размер кисти", "en": "Brush size"},
    "map_undo": {"ru": "ОТМЕНИТЬ", "en": "UNDO"},
    "map_clear": {"ru": "ОЧИСТИТЬ", "en": "CLEAR"},
    "map_save": {"ru": "СОХРАНИТЬ КАРТУ", "en": "SAVE MAP"},
    "map_open_folder": {"ru": "📂 ОТКРЫТЬ ПАПКУ MAPS", "en": "📂 OPEN MAPS FOLDER"},
    "tool_pencil": {"ru": "✏️ Кисть", "en": "✏️ Pencil"},
    "tool_line": {"ru": "📏 Линия", "en": "📏 Line"},
    "tool_arrow": {"ru": "➡️ Стрелка", "en": "➡️ Arrow"},
    "tool_rect": {"ru": "▭ Прямоугольник", "en": "▭ Rectangle"},
    "tool_ellipse": {"ru": "◯ Эллипс", "en": "◯ Ellipse"},
    "tool_text": {"ru": "T Текст", "en": "T Text"},
    "dlg_text_title": {"ru": "Текст метки", "en": "Label text"},
    "dlg_text_prompt": {"ru": "Введите текст:", "en": "Enter text:"},
}


# =====================================================================
# ПУТИ К КАРТАМ
# =====================================================================
MAPS_DIR_USER = os.path.join(APP_FOLDER, "maps")
MAPS_DIR_EXE = os.path.join(executable_dir(), "maps")

MAPS_DIRS = [MAPS_DIR_EXE, MAPS_DIR_USER]
if hasattr(sys, '_MEIPASS'):
    MAPS_DIRS.append(os.path.join(sys._MEIPASS, "maps"))

MAPS_DIR = MAPS_DIR_USER

README_CONTENT = """COLD WAR TOOLS — ТАКТИЧЕСКИЕ КАРТЫ
==================================

Поместите PNG-файлы с ТОЧНЫМИ именами:

  morslingen.png     — Morslingen
  valley_view.png    — Valley View
  khokhlovka.png     — Khokhlovka
  vavidas.png        — Vavidas
"""


def ensure_maps_folder():
    for d in (MAPS_DIR_USER, MAPS_DIR_EXE):
        try:
            os.makedirs(d, exist_ok=True)
        except Exception as e:
            debug_log(f"[MAPS] cannot create {d}: {e}")
    readme = os.path.join(MAPS_DIR_USER, "README.txt")
    if not os.path.exists(readme):
        try:
            with open(readme, "w", encoding="utf-8") as f:
                f.write(README_CONTENT)
        except Exception:
            pass


def find_map_file(filename):
    for d in MAPS_DIRS:
        p = os.path.join(d, filename)
        if os.path.exists(p):
            return p
    return None


def open_maps_folder():
    os.makedirs(MAPS_DIR_USER, exist_ok=True)
    try:
        if sys.platform == "win32":
            os.startfile(MAPS_DIR_USER)
        elif sys.platform == "darwin":
            os.system(f'open "{MAPS_DIR_USER}"')
        else:
            os.system(f'xdg-open "{MAPS_DIR_USER}"')
    except Exception as e:
        debug_log(f"[MAPS] cannot open folder: {e}")


# =====================================================================
# ЧАСТЬ 2: ВКЛАДКА БАЛЛИСТИКИ
# =====================================================================
class BallisticsTab(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="transparent")
        self.main_app = main_app
        self.current_faction = list(WEAPONS_BY_FACTION.keys())[0]
        self.current_category = list(WEAPONS_BY_FACTION[self.current_faction].keys())[0]
        self.current_weapon = list(WEAPONS_BY_FACTION[self.current_faction][self.current_category].keys())[0]
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.build_ui()
        self.update_lang()
        self.after(100, self.draw_chart)

    def build_ui(self):
        self.left_frame = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=0, border_width=1, border_color="#333", width=320)
        self.left_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        self.left_frame.grid_propagate(False)

        self.faction_label = ctk.CTkLabel(self.left_frame, text="", font=("Consolas", 12, "bold"), text_color=COLOR_TEXT_MUTED, anchor="w")
        self.faction_label.pack(padx=15, pady=(15, 0), fill="x")
        self.faction_combo = ctk.CTkComboBox(self.left_frame, values=[], corner_radius=0, fg_color="#121212", border_color="#333", button_color="#333", command=self.on_faction_change)
        self.faction_combo.pack(padx=15, pady=(5, 15), fill="x")

        self.weapon_label = ctk.CTkLabel(self.left_frame, text="", font=("Consolas", 12, "bold"), text_color=COLOR_TEXT_MUTED, anchor="w")
        self.weapon_label.pack(padx=15, fill="x")
        self.category_combo = ctk.CTkComboBox(self.left_frame, values=[], corner_radius=0, fg_color="#121212", border_color="#333", button_color="#333", command=self.on_category_change)
        self.category_combo.pack(padx=15, pady=(5, 5), fill="x")
        self.weapon_combo = ctk.CTkComboBox(self.left_frame, values=[], corner_radius=0, fg_color="#121212", border_color="#333", button_color="#333", command=self.on_weapon_change)
        self.weapon_combo.pack(padx=15, pady=(0, 10), fill="x")

        self.velocity_prefix = ctk.CTkLabel(self.left_frame, text="", font=("Consolas", 12), text_color=COLOR_TEXT_MUTED, anchor="w")
        self.velocity_prefix.pack(padx=15, fill="x")
        self.velocity_val = ctk.CTkLabel(self.left_frame, text="---", font=("Consolas", 14, "bold"), text_color=COLOR_GREEN, anchor="w")
        self.velocity_val.pack(padx=15, pady=(0, 15), fill="x")

        self.params_label = ctk.CTkLabel(self.left_frame, text="", font=("Consolas", 12, "bold"), text_color=COLOR_TEXT_MUTED, anchor="w")
        self.params_label.pack(padx=15, fill="x")

        self.dist_label = ctk.CTkLabel(self.left_frame, text="", font=("Consolas", 12), anchor="w")
        self.dist_label.pack(padx=15, fill="x")
        self.distance_var = tk.StringVar(value="100")
        self.distance_entry = ctk.CTkEntry(self.left_frame, textvariable=self.distance_var, corner_radius=0, fg_color="#121212", border_color="#333")
        self.distance_entry.pack(padx=15, pady=(0, 10), fill="x")
        self.distance_entry.bind("<KeyRelease>", lambda e: self.draw_chart())

        self.target_spd_label = ctk.CTkLabel(self.left_frame, text="", font=("Consolas", 12), anchor="w")
        self.target_spd_label.pack(padx=15, fill="x")
        self.target_speed_var = tk.StringVar(value="0")
        self.target_entry = ctk.CTkEntry(self.left_frame, textvariable=self.target_speed_var, corner_radius=0, fg_color="#121212", border_color="#333")
        self.target_entry.pack(padx=15, pady=(0, 15), fill="x")

        self.calc_btn = ctk.CTkButton(self.left_frame, text="", fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, corner_radius=0, font=("Consolas", 12, "bold"), command=self.calculate)
        self.calc_btn.pack(padx=15, pady=(5, 5), fill="x")
        self.reset_btn = ctk.CTkButton(self.left_frame, text="", fg_color="#333", hover_color="#444", corner_radius=0, font=("Consolas", 12, "bold"), command=self.reset)
        self.reset_btn.pack(padx=15, pady=(0, 15), fill="x")

        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        self.chart_frame = ctk.CTkFrame(self.right_frame, fg_color=COLOR_PANEL, corner_radius=0, border_width=1, border_color="#333")
        self.chart_frame.pack(fill="both", expand=True, pady=(0, 10))
        self.chart_title = ctk.CTkLabel(self.chart_frame, text="", font=("Consolas", 12, "bold"), text_color=COLOR_TEXT_MUTED, anchor="w")
        self.chart_title.pack(padx=15, pady=(10, 0), fill="x")
        self.chart_canvas = tk.Canvas(self.chart_frame, bg="#121212", highlightthickness=0, bd=0)
        self.chart_canvas.pack(padx=10, pady=10, fill="both", expand=True)
        self.chart_canvas.bind("<Configure>", lambda e: self.draw_chart())

        self.results_frame = ctk.CTkFrame(self.right_frame, fg_color=COLOR_PANEL, corner_radius=0, border_width=1, border_color="#333", height=180)
        self.results_frame.pack(fill="x")
        self.results_frame.pack_propagate(False)
        self.results_title = ctk.CTkLabel(self.results_frame, text="", font=("Consolas", 12, "bold"), text_color=COLOR_TEXT_MUTED, anchor="w")
        self.results_title.pack(padx=15, pady=(10, 0), fill="x")
        self.result_text = ctk.CTkTextbox(self.results_frame, font=("Consolas", 13), fg_color="#121212", text_color=COLOR_TEXT, corner_radius=0)
        self.result_text.pack(padx=10, pady=10, fill="both", expand=True)
        self.result_text.configure(state="disabled")

    def update_lang(self):
        lang = self.main_app.lang
        t = lambda k: UI_TEXT[k][lang]
        self.faction_label.configure(text=t("faction"))
        self.weapon_label.configure(text=t("weapon"))
        self.params_label.configure(text=t("params"))
        self.dist_label.configure(text=t("dist"))
        self.target_spd_label.configure(text=t("target_spd"))
        self.velocity_prefix.configure(text=t("velocity"))
        self.calc_btn.configure(text=t("btn_calc"))
        self.reset_btn.configure(text=t("btn_reset"))
        self.chart_title.configure(text=t("chart"))
        self.results_title.configure(text=t("results"))
        self._refresh_combos()
        self.draw_chart()

    def _refresh_combos(self):
        lang = self.main_app.lang
        factions = [CATEGORIES[f][lang] for f in WEAPONS_BY_FACTION.keys()]
        self.faction_combo.configure(values=factions)
        self.faction_combo.set(CATEGORIES[self.current_faction][lang])
        cats = [CATEGORIES[c][lang] for c in WEAPONS_BY_FACTION[self.current_faction].keys()]
        self.category_combo.configure(values=cats)
        self.category_combo.set(CATEGORIES[self.current_category][lang])
        weapons = list(WEAPONS_BY_FACTION[self.current_faction][self.current_category].keys())
        self.weapon_combo.configure(values=weapons)
        self.weapon_combo.set(self.current_weapon)
        self.on_weapon_change()

    def on_faction_change(self, choice):
        lang = self.main_app.lang
        for f in WEAPONS_BY_FACTION.keys():
            if CATEGORIES[f][lang] == choice:
                self.current_faction = f
                break
        self.current_category = list(WEAPONS_BY_FACTION[self.current_faction].keys())[0]
        self._refresh_combos()

    def on_category_change(self, choice):
        lang = self.main_app.lang
        for c in WEAPONS_BY_FACTION[self.current_faction].keys():
            if CATEGORIES[c][lang] == choice:
                self.current_category = c
                break
        self.current_weapon = list(WEAPONS_BY_FACTION[self.current_faction][self.current_category].keys())[0]
        self._refresh_combos()

    def on_weapon_change(self, choice=None):
        self.current_weapon = self.weapon_combo.get()
        try:
            v = WEAPONS_BY_FACTION[self.current_faction][self.current_category][self.current_weapon]
            self.velocity_val.configure(text=f"{v} {UI_TEXT['unit_mps'][self.main_app.lang]}")
        except KeyError:
            self.velocity_val.configure(text="---")
        self.draw_chart()

    def draw_chart(self):
        canvas = self.chart_canvas
        canvas.delete("all")
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 50 or h < 50:
            return
        try:
            v = WEAPONS_BY_FACTION[self.current_faction][self.current_category][self.current_weapon]
        except (KeyError, TypeError):
            return
        try:
            dist = float(self.distance_var.get().replace(",", "."))
            if dist < 0:
                dist = 0
        except ValueError:
            dist = 0
        max_d = max(500, int(math.ceil(dist * 1.2 / 100.0)) * 100) if dist > 0 else 500
        max_drop = 0.5 * GRAVITY * (max_d / v) ** 2 * 100
        if max_drop <= 0:
            return
        pl, pr, pt, pb = 60, 15, 20, 35
        pw, ph = w - pl - pr, h - pt - pb
        for i in range(6):
            y = pt + ph * i / 5
            canvas.create_line(pl, y, pl + pw, y, fill="#333", dash=(2, 4))
            canvas.create_text(pl - 5, y, text=f"{max_drop * i / 5:.0f}", anchor="e", fill="#555", font=("Consolas", 9))
            x = pl + pw * i / 5
            canvas.create_text(x, pt + ph + 5, text=f"{max_d * i / 5:.0f}", anchor="n", fill="#555", font=("Consolas", 9))
        canvas.create_line(pl, pt, pl, pt + ph, fill="#444")
        canvas.create_line(pl, pt + ph, pl + pw, pt + ph, fill="#444")
        lang = self.main_app.lang
        canvas.create_text(pl + pw/2, h - 8, text=UI_TEXT["axis_dist"][lang], fill="#888", font=("Consolas", 9, "bold"))
        canvas.create_text(12, pt + ph/2, text=UI_TEXT["axis_drop"][lang], fill="#888", font=("Consolas", 9, "bold"), angle=90)
        pts = []
        for i in range(101):
            d = max_d * i / 100
            drop = 0.5 * GRAVITY * (d / v) ** 2 * 100
            pts.extend([pl + (d / max_d) * pw, pt + (drop / max_drop) * ph])
        canvas.create_line(*pts, fill=COLOR_GREEN, width=2)
        if 0 < dist <= max_d:
            cd = 0.5 * GRAVITY * (dist / v) ** 2 * 100
            cx, cy = pl + (dist / max_d) * pw, pt + (cd / max_drop) * ph
            canvas.create_line(cx, pt, cx, cy, fill=COLOR_RED, dash=(3, 3))
            canvas.create_line(pl, cy, cx, cy, fill=COLOR_RED, dash=(3, 3))
            canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill=COLOR_RED, outline="")
            lx, ax = (cx + 8, "w") if cx + 8 + 70 <= pl + pw else (cx - 8, "e")
            ly, ay = (cy + 8, "n") if cy < pt + 25 else (cy - 8, "s")
            canvas.create_text(lx, ly, text=f"{cd:.1f} {UI_TEXT['unit_cm'][lang]}", anchor=ay+ax, fill=COLOR_RED, font=("Consolas", 10, "bold"))

    def calculate(self):
        lang = self.main_app.lang
        t = lambda k: UI_TEXT[k][lang]
        try:
            v = WEAPONS_BY_FACTION[self.current_faction][self.current_category][self.current_weapon]
            try:
                dist = float(self.distance_var.get().replace(",", "."))
                if dist <= 0:
                    return self.show_error(t("err_dist"))
            except ValueError:
                return self.show_error("ERR: FORMAT")
            try:
                spd = float(self.target_speed_var.get().replace(",", "."))
                if spd < 0:
                    return self.show_error("ERR: NEGATIVE SPEED")
            except ValueError:
                return self.show_error("ERR: FORMAT")
            tof = dist / v
            drop = 0.5 * GRAVITY * tof ** 2
            lead = spd * tof
            lines = [
                f"{t('res_faction')} {CATEGORIES[self.current_faction][lang]}",
                f"{t('res_weapon')} {self.current_weapon}",
                f"{t('res_velocity')} {v} {t('unit_mps')}",
                f"{t('res_distance')} {dist:.1f} {t('unit_m')}",
                "----------------------------------------",
                f"{t('res_time')} {tof:.3f} {t('unit_sec')}",
                f"{t('res_drop')} {drop:.3f} {t('unit_m')} ({drop*100:.1f} {t('unit_cm')})",
            ]
            if spd > 0:
                lines.append(f"{t('res_lead')} {lead:.3f} {t('unit_m')} ({lead*100:.1f} {t('unit_cm')})")
            else:
                lines.append(t("res_no_lead"))
            self.set_result("\n".join(lines))
            self.draw_chart()
        except Exception as e:
            self.show_error(f"{t('err_calc')}: {e}")

    def reset(self):
        self.distance_var.set("100")
        self.target_speed_var.set("0")
        self.set_result("")
        self.draw_chart()

    def set_result(self, text):
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text._emoji_refs = []
        insert_rich_textbox(self.result_text, text, emoji_size=15)
        self.result_text.configure(state="disabled")

    def show_error(self, msg):
        self.set_result(f"[!] {msg}")


# =====================================================================
# ЧАСТЬ 3: ТАКТИЧЕСКАЯ КАРТА
# =====================================================================
class MapTab(ctk.CTkFrame):
    MAPS = {
        "Morslingen": {"file": "morslingen.png", "desc": "Городские руины"},
        "Valley View": {"file": "valley_view.png", "desc": "Пригород Аляски"},
        "Khokhlovka": {"file": "khokhlovka.png", "desc": "Деревня в СССР"},
        "Vavidas": {"file": "vavidas.png", "desc": "Побережье Кубы"},
    }
    TOOLS = ["pencil", "line", "arrow", "rect", "ellipse", "text"]
    TOOL_ICONS = {
        "pencil": ("emoji", "✏️"),
        "line": ("emoji", "📏"),
        "arrow": ("emoji", "➡️"),
        "rect": ("symbol", "▭"),
        "ellipse": ("symbol", "◯"),
        "text": ("symbol", "T"),
    }
    MIN_ZOOM = 0.1
    MAX_ZOOM = 8.0
    MAX_RENDER_PIXELS = 25_000_000

    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="transparent")
        self.main_app = main_app
        self.brush_color = COLOR_GREEN
        self.brush_size = 5
        self.current_tool = "pencil"
        self.strokes = []
        self.base_image = None
        self.current_map = list(self.MAPS.keys())[0]

        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._needs_fit = True
        self._cached_zoom = None
        self._cached_photo = None

        self.start_x = None
        self.start_y = None
        self.start_wx = None
        self.start_wy = None
        self.pencil_points = None

        self._pan_active = False
        self._pan_last_x = 0
        self._pan_last_y = 0

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.build_ui()
        self.update_lang()
        self.after(200, lambda: self.load_map_bg(self.current_map))
        self.bind('<Map>', lambda e: self.after(80, self.redraw_all))

    def build_ui(self):
        self.left_frame = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=0, border_width=1, border_color="#333", width=270)
        self.left_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        self.left_frame.grid_propagate(False)

        self.title_label = ctk.CTkLabel(self.left_frame, text="", font=("Consolas", 12, "bold"), text_color=COLOR_TEXT_MUTED, anchor="w")
        self.title_label.pack(padx=15, pady=(15, 8), fill="x")

        self.map_select_label = ctk.CTkLabel(self.left_frame, text="", font=("Consolas", 11), text_color=COLOR_TEXT_MUTED, anchor="w")
        self.map_select_label.pack(padx=15, fill="x")
        self.map_combo = ctk.CTkComboBox(self.left_frame, values=list(self.MAPS.keys()), corner_radius=0, fg_color="#121212", border_color="#333", button_color="#333", command=self.load_map_bg)
        self.map_combo.pack(padx=15, pady=(3, 10), fill="x")

        self.tool_label = ctk.CTkLabel(self.left_frame, text="", font=("Consolas", 11), text_color=COLOR_TEXT_MUTED, anchor="w")
        self.tool_label.pack(padx=15, fill="x")
        self.tool_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.tool_frame.pack(padx=15, pady=(3, 3), fill="x")
        self.tool_buttons = {}
        for i, tool in enumerate(self.TOOLS):
            kind, char = self.TOOL_ICONS[tool]
            icon_img = EMOJI.ctk_image(char, size=20) if kind == "emoji" else EMOJI.ctk_symbol(char, size=18, color=COLOR_TEXT)
            if icon_img is not None:
                btn = ctk.CTkButton(self.tool_frame, text="", image=icon_img, width=68, height=30,
                                    fg_color=COLOR_ACCENT if tool == self.current_tool else "#333",
                                    hover_color=COLOR_ACCENT_HOVER, corner_radius=0,
                                    command=lambda t=tool: self.set_tool(t))
            else:
                btn = ctk.CTkButton(self.tool_frame, text=char, width=68, height=30,
                                    fg_color=COLOR_ACCENT if tool == self.current_tool else "#333",
                                    hover_color=COLOR_ACCENT_HOVER, corner_radius=0,
                                    font=("Consolas", 13, "bold"), command=lambda t=tool: self.set_tool(t))
            btn.grid(row=i // 3, column=i % 3, padx=2, pady=2)
            self.tool_buttons[tool] = btn

        self.tool_name_label = ctk.CTkLabel(self.left_frame, text="", font=("Consolas", 10), text_color=COLOR_TEXT_MUTED, anchor="w")
        self.tool_name_label.pack(padx=15, pady=(0, 8), fill="x")

        self.color_label = ctk.CTkLabel(self.left_frame, text="", font=("Consolas", 12), anchor="w")
        self.color_label.pack(padx=15, fill="x")
        self.color_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.color_frame.pack(padx=15, pady=3, fill="x")
        for c in [COLOR_GREEN, "#ef4444", "#3b82f6", "#eab308", "#ffffff"]:
            btn = ctk.CTkButton(self.color_frame, text="", width=30, height=30, fg_color=c, hover_color=c,
                                corner_radius=0, command=lambda col=c: self.set_color(col))
            btn.pack(side="left", padx=2)

        self.size_label = ctk.CTkLabel(self.left_frame, text="", font=("Consolas", 12), anchor="w")
        self.size_label.pack(padx=15, pady=(10, 0), fill="x")
        self.size_slider = ctk.CTkSlider(self.left_frame, from_=1, to=20, number_of_steps=19, command=self.set_size)
        self.size_slider.set(self.brush_size)
        self.size_slider.pack(padx=15, pady=5, fill="x")

        self.zoom_label = ctk.CTkLabel(self.left_frame, text="ZOOM", font=("Consolas", 12), text_color=COLOR_TEXT_MUTED, anchor="w")
        self.zoom_label.pack(padx=15, pady=(8, 0), fill="x")
        self.zoom_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.zoom_frame.pack(padx=15, pady=3, fill="x")
        self.zoom_out_btn = ctk.CTkButton(self.zoom_frame, text="−", width=45, height=30, fg_color="#333", hover_color="#444",
                                          corner_radius=0, font=("Consolas", 14, "bold"),
                                          command=lambda: self.zoom_at_canvas_center(1 / 1.3))
        self.zoom_out_btn.pack(side="left", padx=(0, 3))
        self.zoom_val_label = ctk.CTkLabel(self.zoom_frame, text="100%", font=("Consolas", 11, "bold"), text_color=COLOR_GREEN)
        self.zoom_val_label.pack(side="left", fill="x", expand=True)
        self.zoom_in_btn = ctk.CTkButton(self.zoom_frame, text="+", width=45, height=30, fg_color="#333", hover_color="#444",
                                         corner_radius=0, font=("Consolas", 14, "bold"),
                                         command=lambda: self.zoom_at_canvas_center(1.3))
        self.zoom_in_btn.pack(side="right", padx=(3, 0))

        self.fit_btn = ctk.CTkButton(self.left_frame, text="FIT", fg_color="#333", hover_color="#444",
                                     corner_radius=0, font=("Consolas", 11, "bold"), command=self.fit_to_window_btn)
        self.fit_btn.pack(padx=15, pady=(3, 8), fill="x")

        self.undo_btn = ctk.CTkButton(self.left_frame, text="", fg_color="#333", hover_color="#444",
                                      corner_radius=0, font=("Consolas", 11, "bold"), command=self.undo)
        self.undo_btn.pack(padx=15, pady=(4, 4), fill="x")
        self.clear_btn = ctk.CTkButton(self.left_frame, text="", fg_color="#333", hover_color="#444",
                                       corner_radius=0, font=("Consolas", 12, "bold"), command=self.clear_canvas)
        self.clear_btn.pack(padx=15, pady=4, fill="x")
        self.save_btn = ctk.CTkButton(self.left_frame, text="", fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                                      corner_radius=0, font=("Consolas", 12, "bold"), command=self.save_map)
        self.save_btn.pack(padx=15, pady=(4, 4), fill="x")

        self.open_folder_btn = ctk.CTkButton(self.left_frame, text="", fg_color="#333", hover_color="#444",
                                             corner_radius=0, font=("Consolas", 11, "bold"), command=open_maps_folder)
        self.open_folder_btn.pack(padx=15, pady=(0, 15), fill="x")

        self.right_frame = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=0, border_width=1, border_color="#333")
        self.right_frame.grid(row=0, column=1, sticky="nsew")

        self.hint_label = ctk.CTkLabel(self.right_frame, text="", font=("Consolas", 10), text_color=COLOR_TEXT_MUTED)
        self.hint_label.pack(padx=10, pady=(5, 0), anchor="w")

        self.canvas = tk.Canvas(self.right_frame, bg="#1a1a1a", highlightthickness=0, bd=0, cursor="cross")
        self.canvas.pack(padx=10, pady=(3, 10), fill="both", expand=True)

        self.canvas.bind('<Button-1>', self.start_draw)
        self.canvas.bind('<B1-Motion>', self.draw)
        self.canvas.bind('<ButtonRelease-1>', self.reset_draw)
        self.canvas.bind('<Configure>', lambda e: self.redraw_all())

        self.canvas.bind('<Button-2>', self.start_pan)
        self.canvas.bind('<B2-Motion>', self.do_pan)
        self.canvas.bind('<ButtonRelease-2>', self.end_pan)
        self.canvas.bind('<Button-3>', self.start_pan)
        self.canvas.bind('<B3-Motion>', self.do_pan)
        self.canvas.bind('<ButtonRelease-3>', self.end_pan)

        self.canvas.bind('<MouseWheel>', self.on_mousewheel)
        self.canvas.bind('<Button-4>', self.on_mousewheel_linux)
        self.canvas.bind('<Button-5>', self.on_mousewheel_linux)

    def update_lang(self):
        lang = self.main_app.lang
        t = lambda k: UI_TEXT[k][lang]
        self.title_label.configure(text=t("map_title"))
        self.map_select_label.configure(text=t("map_select"))
        self.tool_label.configure(text=t("map_tool"))
        self.color_label.configure(text=t("map_color"))
        self.size_label.configure(text=t("map_size"))
        self.undo_btn.configure(text=t("map_undo"))
        self.clear_btn.configure(text=t("map_clear"))
        self.save_btn.configure(text=t("map_save"))
        apply_emoji_widget(self.open_folder_btn, t("map_open_folder"), size=14)
        self.tool_name_label.configure(text=t(f"tool_{self.current_tool}"))
        apply_emoji_widget(self.hint_label, "🖱 ЛКМ — рисовать  |  Колесо — зум  |  СКМ/ПКМ drag — двигать карту", size=12)
        self._update_zoom_label()

    def _update_zoom_label(self):
        if hasattr(self, 'zoom_val_label'):
            self.zoom_val_label.configure(text=f"{int(round(self.zoom * 100))}%")

    def world_to_screen(self, x, y):
        return (x * self.zoom + self.pan_x, y * self.zoom + self.pan_y)

    def screen_to_world(self, x, y):
        return ((x - self.pan_x) / self.zoom, (y - self.pan_y) / self.zoom)

    def _max_zoom(self):
        if not self.base_image:
            return self.MAX_ZOOM
        iw, ih = self.base_image.size
        return min(self.MAX_ZOOM, (self.MAX_RENDER_PIXELS / max(1, iw * ih)) ** 0.5)

    def zoom_at(self, sx, sy, factor):
        wx, wy = self.screen_to_world(sx, sy)
        new_zoom = max(self.MIN_ZOOM, min(self.zoom * factor, self._max_zoom()))
        if abs(new_zoom - self.zoom) < 1e-6:
            return
        self.zoom = new_zoom
        self.pan_x = sx - wx * self.zoom
        self.pan_y = sy - wy * self.zoom
        self._cached_zoom = None
        self.redraw_all()

    def zoom_at_canvas_center(self, factor):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w > 10 and h > 10:
            self.zoom_at(w / 2, h / 2, factor)

    def on_mousewheel(self, event):
        self.zoom_at(event.x, event.y, 1.15 if event.delta > 0 else 1 / 1.15)

    def on_mousewheel_linux(self, event):
        self.zoom_at(event.x, event.y, 1.15 if event.num == 4 else 1 / 1.15)

    def start_pan(self, event):
        self._pan_active = True
        self._pan_last_x = event.x
        self._pan_last_y = event.y
        self.canvas.configure(cursor="fleur")

    def do_pan(self, event):
        if not self._pan_active:
            return
        dx = event.x - self._pan_last_x
        dy = event.y - self._pan_last_y
        self.pan_x += dx
        self.pan_y += dy
        self._pan_last_x = event.x
        self._pan_last_y = event.y
        self.canvas.move("all", dx, dy)

    def end_pan(self, event):
        self._pan_active = False
        self.canvas.configure(cursor="cross")

    def fit_to_window_btn(self):
        self._needs_fit = True
        self._cached_zoom = None
        self.redraw_all()

    def fit_to_window(self):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 50 or h < 50:
            return False
        if not self.base_image:
            self.zoom = 1.0
            self.pan_x = self.pan_y = 0.0
            return True
        iw, ih = self.base_image.size
        if iw <= 0 or ih <= 0:
            return False
        self.zoom = max(self.MIN_ZOOM, min(min(w / iw, h / ih) * 0.95, self._max_zoom()))
        self.pan_x = (w - iw * self.zoom) / 2
        self.pan_y = (h - ih * self.zoom) / 2
        self._cached_zoom = None
        return True

    def _make_placeholder(self, name, size=(1600, 1200)):
        from PIL import ImageDraw, ImageFont
        img = Image.new("RGB", size, "#1a2028")
        draw = ImageDraw.Draw(img)
        for x in range(0, size[0], 100):
            draw.line([(x, 0), (x, size[1])], fill="#2a3540", width=2)
        for y in range(0, size[1], 100):
            draw.line([(0, y), (size[0], y)], fill="#2a3540", width=2)
        draw.rectangle([6, 6, size[0] - 6, size[1] - 6], outline="#4a6070", width=4)
        cx, cy = size[0] // 2, size[1] // 2
        expected = os.path.join(MAPS_DIR_USER, self.MAPS.get(name, {}).get("file", "?"))
        try:
            font_big = ImageFont.truetype("consola.ttf", 72)
            font_md = ImageFont.truetype("consola.ttf", 30)
            font_sm = ImageFont.truetype("consola.ttf", 22)
            draw.text((cx, cy - 140), name, fill="#a8c4dc", font=font_big, anchor="mm")
            draw.text((cx, cy - 40), "PLACEHOLDER — картинка не найдена", fill="#8aa8c0", font=font_md, anchor="mm")
            draw.text((cx, cy + 20), "Положите PNG сюда:", fill="#7a9cb0", font=font_sm, anchor="mm")
            draw.text((cx, cy + 60), expected, fill="#c8d8e4", font=font_sm, anchor="mm")
            draw.text((cx, cy + 120), "или нажмите кнопку «ОТКРЫТЬ ПАПКУ MAPS»", fill="#7a9cb0", font=font_sm, anchor="mm")
        except Exception as e:
            debug_log(f"[MAP] placeholder font error: {e}")
            draw.text((60, cy - 20), name, fill="#a8c4dc")
            draw.text((60, cy + 20), f"PLACEHOLDER. Expected: {expected}", fill="#8aa8c0")
        return img

    def load_map_bg(self, map_name=None):
        if map_name is None:
            map_name = self.map_combo.get()
        self.current_map = map_name
        self.strokes = []
        filename = self.MAPS.get(map_name, {}).get("file", "")
        path = find_map_file(filename) if filename else None
        debug_log(f"[MAP] loading '{map_name}' -> {path or 'NOT FOUND'}")
        self.base_image = None
        if path:
            try:
                self.base_image = Image.open(path).convert("RGB")
                debug_log(f"[MAP] OK {path} size={self.base_image.size}")
            except Exception as e:
                debug_log(f"[MAP] FAIL {path}: {e}")
        if self.base_image is None:
            try:
                self.base_image = self._make_placeholder(map_name)
                debug_log(f"[MAP] placeholder for '{map_name}'")
            except Exception as e:
                debug_log(f"[MAP] placeholder failed: {e}")
        self._cached_zoom = None
        self._cached_photo = None
        self._needs_fit = True
        self.redraw_all()

    def _get_bg_photo(self):
        if self._cached_zoom == self.zoom and self._cached_photo is not None:
            return self._cached_photo
        iw, ih = self.base_image.size
        new_w = max(1, int(iw * self.zoom))
        new_h = max(1, int(ih * self.zoom))
        max_dim = 12000
        if new_w > max_dim or new_h > max_dim:
            scale = max_dim / max(new_w, new_h)
            new_w, new_h = max(1, int(new_w * scale)), max(1, int(new_h * scale))
        resized = self.base_image.resize((new_w, new_h), Image.LANCZOS)
        self._cached_photo = ImageTk.PhotoImage(resized)
        self._cached_zoom = self.zoom
        return self._cached_photo

    def redraw_all(self, retry=0):
        if self.canvas.winfo_width() < 50 or self.canvas.winfo_height() < 50:
            if retry < 30:
                self.after(100, lambda: self.redraw_all(retry + 1))
            return
        if self._needs_fit:
            if self.fit_to_window():
                self._needs_fit = False
        self.canvas.delete("all")
        self.redraw_background()
        for shape in self.strokes:
            self.draw_shape(shape)
        self._update_zoom_label()

    def redraw_background(self):
        w = self.canvas.winfo_width() or 800
        h = self.canvas.winfo_height() or 600
        if w < 10 or h < 10:
            return
        self.canvas.create_rectangle(0, 0, w, h, fill="#161616", outline="", tags="bg")
        if not self.base_image:
            return
        try:
            photo = self._get_bg_photo()
            self.canvas.create_image(self.pan_x, self.pan_y, anchor="nw", image=photo, tags="bg")
        except Exception as e:
            debug_log(f"[MAP] draw bg error: {e}")
        self.canvas.tag_lower("bg")

    def draw_shape(self, shape, dashed=False):
        tool = shape["tool"]
        color = shape["color"]
        screen_size = max(1, shape["size"] * self.zoom)
        tags = ("preview",) if dashed else ()
        dash = (4, 4) if dashed else None

        if tool == "pencil":
            pts = shape["points"]
            if len(pts) < 2:
                return
            screen_pts = []
            for p in pts:
                sx, sy = self.world_to_screen(*p)
                screen_pts.extend([sx, sy])
            self.canvas.create_line(*screen_pts, fill=color, width=screen_size, capstyle=tk.ROUND, smooth=True, tags=tags)
        elif tool == "line":
            x1, y1 = self.world_to_screen(shape["x1"], shape["y1"])
            x2, y2 = self.world_to_screen(shape["x2"], shape["y2"])
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=screen_size, tags=tags)
        elif tool == "arrow":
            x1, y1 = self.world_to_screen(shape["x1"], shape["y1"])
            x2, y2 = self.world_to_screen(shape["x2"], shape["y2"])
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=screen_size, arrow=tk.LAST, arrowshape=(12, 15, 4), tags=tags)
        elif tool == "rect":
            x1, y1 = self.world_to_screen(shape["x1"], shape["y1"])
            x2, y2 = self.world_to_screen(shape["x2"], shape["y2"])
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=screen_size, fill="", dash=dash, tags=tags)
        elif tool == "ellipse":
            x1, y1 = self.world_to_screen(shape["x1"], shape["y1"])
            x2, y2 = self.world_to_screen(shape["x2"], shape["y2"])
            self.canvas.create_oval(x1, y1, x2, y2, outline=color, width=screen_size, fill="", dash=dash, tags=tags)
        elif tool == "text":
            sx, sy = self.world_to_screen(shape["x"], shape["y"])
            font_size = max(8, int(shape["size"] * self.zoom))
            self.canvas.create_text(sx, sy, text=shape["text"], fill=color, font=("Consolas", font_size, "bold"), anchor="nw", tags=tags)

    def set_tool(self, tool):
        self.current_tool = tool
        for t, btn in self.tool_buttons.items():
            btn.configure(fg_color=COLOR_ACCENT if t == tool else "#333")
        self.tool_name_label.configure(text=UI_TEXT[f"tool_{tool}"][self.main_app.lang])

    def set_color(self, color):
        self.brush_color = color

    def set_size(self, val):
        self.brush_size = int(val)

    def start_draw(self, event):
        if self.current_tool == "text":
            text = simpledialog.askstring(
                UI_TEXT["dlg_text_title"][self.main_app.lang],
                UI_TEXT["dlg_text_prompt"][self.main_app.lang],
                parent=self
            )
            if text:
                wx, wy = self.screen_to_world(event.x, event.y)
                shape = {"tool": "text", "x": wx, "y": wy, "text": text,
                         "color": self.brush_color, "size": max(10, self.brush_size + 10)}
                self.strokes.append(shape)
                self.draw_shape(shape)
            return
        self.start_x, self.start_y = event.x, event.y
        self.start_wx, self.start_wy = self.screen_to_world(event.x, event.y)
        if self.current_tool == "pencil":
            self.pencil_points = [(self.start_wx, self.start_wy)]

    def draw(self, event):
        if self.current_tool == "pencil":
            if self.pencil_points is None:
                return
            wx, wy = self.screen_to_world(event.x, event.y)
            self.pencil_points.append((wx, wy))
            if len(self.pencil_points) >= 2:
                x1, y1 = self.world_to_screen(*self.pencil_points[-2])
                x2, y2 = self.world_to_screen(*self.pencil_points[-1])
                self.canvas.create_line(x1, y1, x2, y2, fill=self.brush_color,
                                        width=max(1, self.brush_size * self.zoom),
                                        capstyle=tk.ROUND, smooth=True)
            return
        if self.start_x is None:
            return
        self.canvas.delete("preview")
        wx, wy = self.screen_to_world(event.x, event.y)
        self.draw_shape({"tool": self.current_tool, "x1": self.start_wx, "y1": self.start_wy,
                         "x2": wx, "y2": wy, "color": self.brush_color, "size": self.brush_size}, dashed=True)

    def reset_draw(self, event):
        if self.current_tool == "pencil":
            if self.pencil_points and len(self.pencil_points) > 1:
                self.strokes.append({"tool": "pencil", "points": self.pencil_points,
                                     "color": self.brush_color, "size": self.brush_size})
            self.pencil_points = None
            return
        if self.start_x is None:
            return
        self.canvas.delete("preview")
        if abs(event.x - self.start_x) > 3 or abs(event.y - self.start_y) > 3:
            wx, wy = self.screen_to_world(event.x, event.y)
            shape = {"tool": self.current_tool, "x1": self.start_wx, "y1": self.start_wy,
                     "x2": wx, "y2": wy, "color": self.brush_color, "size": self.brush_size}
            self.strokes.append(shape)
            self.draw_shape(shape)
        self.start_x = self.start_y = self.start_wx = self.start_wy = None

    def undo(self):
        if self.strokes:
            self.strokes.pop()
            self.redraw_all()

    def clear_canvas(self):
        self.strokes = []
        self.redraw_all()

    def save_map(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if not filepath:
            return
        try:
            self.update_idletasks()
            x, y = self.canvas.winfo_rootx(), self.canvas.winfo_rooty()
            x1 = x + self.canvas.winfo_width()
            y1 = y + self.canvas.winfo_height()
            ImageGrab.grab(bbox=(x, y, x1, y1)).save(filepath)
            debug_log(f"[MAP] saved to {filepath}")
        except Exception as e:
            debug_log(f"[MAP] save error: {e}")


# =====================================================================
# ЧАСТЬ 4: ГЛАВНОЕ ОКНО
# =====================================================================
class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.lang = "ru"
        self.title("Cold War Tools")
        self.geometry("1100x700")
        self.minsize(950, 600)
        self.configure(fg_color=COLOR_BG)

        # Иконка окна (заголовок + панель задач)
        self._set_window_icon()

        ensure_maps_folder()

        self.header_frame = ctk.CTkFrame(self, fg_color=COLOR_PANEL, corner_radius=0, height=50)
        self.header_frame.pack(fill="x", side="top")
        self.title_label = ctk.CTkLabel(self.header_frame, text="", font=("Consolas", 18, "bold"), text_color=COLOR_TEXT)
        self.title_label.pack(side="left", padx=20, pady=10)
        self.lang_btn = ctk.CTkButton(self.header_frame, text="", width=80, fg_color="#333", hover_color="#444",
                                      corner_radius=0, font=("Consolas", 14, "bold"), command=self.toggle_lang)
        self.lang_btn.pack(side="right", padx=20, pady=10)

        self.tabview = ctk.CTkTabview(self, fg_color=COLOR_BG,
                                      segmented_button_selected_color=COLOR_ACCENT,
                                      segmented_button_selected_hover_color=COLOR_ACCENT_HOVER,
                                      corner_radius=0)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)

        self.tabview.add("TAB_CALC")
        self.tabview.add("TAB_MAP")
        self.tab_names = {"calc": "TAB_CALC", "map": "TAB_MAP"}

        self.ballistics_tab = BallisticsTab(self.tabview.tab("TAB_CALC"), self)
        self.ballistics_tab.pack(fill="both", expand=True)
        self.map_tab = MapTab(self.tabview.tab("TAB_MAP"), self)
        self.map_tab.pack(fill="both", expand=True)

        self.update_lang()

    def _set_window_icon(self):
        """Устанавливает иконку окна из icon.ico (вшитого в .exe)."""
        ico = resource_path("icon.ico")
        if not os.path.exists(ico):
            debug_log(f"[ICON] not found: {ico}")
            return
        # iconbitmap — работает на Windows и в .exe
        try:
            self.iconbitmap(ico)
            debug_log(f"[ICON] window icon set from {ico}")
            return
        except Exception as e:
            debug_log(f"[ICON] iconbitmap failed: {e}")
        # fallback через iconphoto (PNG) — если вдруг .ico не принят
        try:
            png = resource_path("icon.png")
            if os.path.exists(png):
                from PIL import ImageTk as _ITk
                self._icon_photo = _ITk.PhotoImage(Image.open(png))
                self.iconphoto(True, self._icon_photo)
                debug_log(f"[ICON] window icon set from {png} (fallback)")
        except Exception as e:
            debug_log(f"[ICON] iconphoto fallback failed: {e}")

    def toggle_lang(self):
        self.lang = "en" if self.lang == "ru" else "ru"
        self.update_lang()

    def update_lang(self):
        t = lambda k: UI_TEXT[k][self.lang]
        apply_emoji_widget(self.title_label, t("title"), size=20)
        apply_emoji_widget(self.lang_btn, t("btn_lang"), size=16)
        for key, new_name in [("calc", t("tab_calc")), ("map", t("tab_map"))]:
            if self.tab_names[key] != new_name:
                self.tabview.rename(self.tab_names[key], new_name)
                self.tab_names[key] = new_name
        self.ballistics_tab.update_lang()
        self.map_tab.update_lang()


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()