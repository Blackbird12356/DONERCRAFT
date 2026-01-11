import random
import tkinter as tk
from tkinter import filedialog, messagebox

# --- MP3 через pygame ---
try:
    import pygame
    PYGAME_OK = True
except Exception:
    PYGAME_OK = False

# --------- Настройки ---------
SYMBOLS = ["🍒", "🍋", "🍉", "🍇", "⭐", "🔔"]

ANIMATION_TICKS = 14
TICK_MS = 70

# Цвета (неон-стиль)
BG = "#0b1020"
PANEL = "#121a33"
ACCENT = "#00e5ff"
ACCENT2 = "#a78bfa"
TEXT = "#e8eefc"
MUTED = "#a7b0c7"
GOOD = "#22c55e"
BAD = "#ef4444"
GOLD = "#fbbf24"

# --------- Звуки (фолбэк: beep/bell) ---------
try:
    import winsound  # Windows
except Exception:
    winsound = None

def beep(root: tk.Tk, freq=880, dur=80):
    if winsound:
        try:
            winsound.Beep(int(freq), int(dur))
            return
        except Exception:
            pass
    try:
        root.bell()
    except Exception:
        pass

def sound_click(root):     beep(root, 900, 40)
def sound_tick(root):      beep(root, 700, 35)
def sound_win(root):
    for f in (660, 880, 990):
        beep(root, f, 80)
def sound_jackpot(root):
    for f in (784, 988, 1175, 1568, 1976):
        beep(root, f, 90)

# --------- Логика наград (жетоны + очки) ---------
def reward(result):
    a, b, c = result
    # (очки, жетон_бонус, сообщение, тип)
    if a == b == c == "🍒":
        return 50, 10, "ДЖЕКПОТ: 🍒🍒🍒! (+50 очков, +10 жетонов)", "jackpot"
    if a == b == c:
        return 20, 4, f"Три одинаковых: {a}{b}{c}! (+20 очков, +4 жетона)", "triple"
    if a == b or b == c or a == c:
        return 5, 1, "Пара совпала! (+5 очков, +1 жетон)", "pair"
    return 0, 0, "Мимо.", "miss"

# --------- UI ---------
class FruitMatchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Фруктовый матч (жетоны, без денег)")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        # Состояние игры
        self.score = 0
        self.spins = 0
        self.jackpots = 0
        self.is_spinning = False

        self.balance = 0
        self.spin_cost = 1

        # Пользовательский звук прокрутки (MP3)
        self.spin_sound_path = None
        self.spin_sound_enabled = True
        self.spin_sound_volume = 0.6

        if PYGAME_OK:
            try:
                pygame.mixer.init()
            except Exception:
                # если mixer не завёлся, отключаем mp3-функции
                messagebox.showwarning("Звук", "Pygame установлен, но аудио не инициализировалось. MP3 будет недоступен.")
                self._disable_mp3()

        # Экраны
        self.start_frame = tk.Frame(root, bg=BG)
        self.game_frame = tk.Frame(root, bg=BG)

        self._build_start_screen()
        self._build_game_screen()

        self.show_start()

        # закрытие окна — гарантированно останавливаем звук
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _disable_mp3(self):
        global PYGAME_OK
        PYGAME_OK = False
        self.spin_sound_path = None

    def on_close(self):
        self.stop_spin_sound()
        self.root.destroy()

    # ----- Экран переключения -----
    def show_start(self):
        self.stop_spin_sound()
        self.game_frame.pack_forget()
        self.start_frame.pack(padx=16, pady=16)

    def show_game(self):
        self.start_frame.pack_forget()
        self.game_frame.pack(padx=16, pady=16)

    # ----- MP3 управление -----
    def load_spin_sound(self):
        sound_click(self.root)

        if not PYGAME_OK:
            messagebox.showinfo(
                "MP3 звук",
                "Чтобы выбрать MP3, установи pygame:\npython -m pip install pygame"
            )
            return

        path = filedialog.askopenfilename(
            title="Выбери MP3 для прокрутки",
            filetypes=[("Audio files", "*.mp3 *.wav *.ogg"), ("All files", "*.*")]
        )
        if not path:
            return

        self.spin_sound_path = path
        self.spin_sound_label.config(text=f"Звук: {path.split('/')[-1].split('\\\\')[-1]}")
        self._set_message("Звук прокрутки выбран.", "good")

    def start_spin_sound(self):
        # Включаем цикл на время прокрутки
        if not (PYGAME_OK and self.spin_sound_enabled and self.spin_sound_path):
            return
        try:
            pygame.mixer.music.load(self.spin_sound_path)
            pygame.mixer.music.set_volume(float(self.spin_sound_volume))
            pygame.mixer.music.play(loops=-1)
        except Exception:
            self._set_message("Не удалось проиграть выбранный файл. Попробуй другой (mp3/wav/ogg).", "bad")
            self.spin_sound_path = None
            self.spin_sound_label.config(text="Звук: (не выбран)")

    def stop_spin_sound(self):
        if not PYGAME_OK:
            return
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except Exception:
            pass

    # ----- Стартовый экран -----
    def _build_start_screen(self):
        f = self.start_frame

        tk.Label(f, text="Фруктовый матч", bg=BG, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10))

        tk.Label(
            f,
            text="Задай жетоны и цену спина. Цель — выбить 🍒🍒🍒.",
            bg=BG, fg=MUTED, font=("Segoe UI", 10)
        ).grid(row=1, column=0, columnspan=2, pady=(0, 14))

        panel = tk.Frame(f, bg=PANEL, highlightthickness=1, highlightbackground="#1f2a55")
        panel.grid(row=2, column=0, columnspan=2, sticky="ew")

        tk.Label(panel, text="Стартовые жетоны:", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))
        self.start_tokens_var = tk.StringVar(value="50")
        tk.Entry(panel, textvariable=self.start_tokens_var, width=12,
                 font=("Segoe UI", 11), bg="#0f1630", fg=TEXT, insertbackground=TEXT,
                 relief="flat").grid(row=0, column=1, sticky="w", padx=12, pady=(12, 6))

        tk.Label(panel, text="Цена 1 спина (жетоны):", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 11)).grid(row=1, column=0, sticky="w", padx=12, pady=(6, 12))
        self.cost_var = tk.StringVar(value="2")
        tk.Entry(panel, textvariable=self.cost_var, width=12,
                 font=("Segoe UI", 11), bg="#0f1630", fg=TEXT, insertbackground=TEXT,
                 relief="flat").grid(row=1, column=1, sticky="w", padx=12, pady=(6, 12))

        self.start_msg = tk.Label(f, text="", bg=BG, fg=BAD, font=("Segoe UI", 10, "bold"))
        self.start_msg.grid(row=3, column=0, columnspan=2, pady=(10, 0))

        btn_row = tk.Frame(f, bg=BG)
        btn_row.grid(row=4, column=0, columnspan=2, pady=(12, 0))

        tk.Button(btn_row, text="Начать", command=self.start_game,
                  bg=ACCENT, fg="#001018", activebackground="#7df4ff",
                  activeforeground="#001018", relief="flat",
                  font=("Segoe UI", 11, "bold"), padx=16, pady=8).grid(row=0, column=0, padx=6)

        tk.Button(btn_row, text="Выход", command=self.on_close,
                  bg="#1b244a", fg=TEXT, activebackground="#24305f",
                  activeforeground=TEXT, relief="flat",
                  font=("Segoe UI", 11), padx=16, pady=8).grid(row=0, column=1, padx=6)

    def start_game(self):
        sound_click(self.root)
        try:
            tokens = int(self.start_tokens_var.get().strip())
            cost = int(self.cost_var.get().strip())
        except Exception:
            self.start_msg.config(text="Введи целые числа.")
            return

        if tokens <= 0:
            self.start_msg.config(text="Стартовые жетоны должны быть > 0.")
            return
        if cost <= 0:
            self.start_msg.config(text="Цена спина должна быть > 0.")
            return

        self.balance = tokens
        self.spin_cost = cost

        self.score = 0
        self.spins = 0
        self.jackpots = 0
        self.is_spinning = False

        self._set_reels(["❔", "❔", "❔"])
        self._set_message("Нажми «Крутить».")
        self._update_stats()

        self.start_msg.config(text="")
        self.show_game()

    # ----- Игровой экран -----
    def _build_game_screen(self):
        f = self.game_frame

        header = tk.Frame(f, bg=BG)
        header.grid(row=0, column=0, columnspan=3, sticky="ew")

        tk.Label(header, text="Фруктовый матч", bg=BG, fg=TEXT,
                 font=("Segoe UI", 16, "bold")).grid(row=0, column=0, sticky="w")

        tk.Label(header, text="Цель: 🍒🍒🍒", bg=BG, fg=GOLD,
                 font=("Segoe UI", 12, "bold")).grid(row=0, column=1, padx=10)

        tk.Button(header, text="↩ Настройки", command=self.back_to_start,
                  bg="#1b244a", fg=TEXT, activebackground="#24305f",
                  activeforeground=TEXT, relief="flat",
                  font=("Segoe UI", 10), padx=10, pady=6).grid(row=0, column=2, sticky="e")

        # Статы
        stat_panel = tk.Frame(f, bg=PANEL, highlightthickness=1, highlightbackground="#1f2a55")
        stat_panel.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(10, 10))

        self.stats_lbl = tk.Label(stat_panel, text="", bg=PANEL, fg=TEXT, font=("Segoe UI", 10))
        self.stats_lbl.pack(padx=12, pady=10)

        # Барабаны
        reels = tk.Frame(f, bg=BG)
        reels.grid(row=2, column=0, columnspan=3, pady=(0, 10))

        self.reel_labels = []
        for i in range(3):
            box = tk.Frame(reels, bg=PANEL, highlightthickness=2, highlightbackground=ACCENT2)
            box.grid(row=0, column=i, padx=8)
            lbl = tk.Label(box, text="❔", bg=PANEL, fg=TEXT, width=3,
                           font=("Segoe UI Emoji", 40))
            lbl.pack(padx=14, pady=14)
            self.reel_labels.append(lbl)

        # Сообщение
        self.msg_lbl = tk.Label(f, text="", bg=BG, fg=TEXT, font=("Segoe UI", 11, "bold"))
        self.msg_lbl.grid(row=3, column=0, columnspan=3, pady=(6, 10))

        # Панель звука
        sound_panel = tk.Frame(f, bg=PANEL, highlightthickness=1, highlightbackground="#1f2a55")
        sound_panel.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        self.spin_sound_label = tk.Label(sound_panel, text="Звук: (не выбран)", bg=PANEL, fg=MUTED, font=("Segoe UI", 10))
        self.spin_sound_label.grid(row=0, column=0, padx=12, pady=10, sticky="w")

        tk.Button(sound_panel, text="Выбрать звук (MP3)", command=self.load_spin_sound,
                  bg=ACCENT2, fg="#10061f", activebackground="#c4b5fd",
                  activeforeground="#10061f", relief="flat",
                  font=("Segoe UI", 10, "bold"), padx=12, pady=6).grid(row=0, column=1, padx=8, pady=10)

        self.sound_on_var = tk.IntVar(value=1)
        tk.Checkbutton(sound_panel, text="Включить MP3 при прокрутке", variable=self.sound_on_var,
                       command=self.toggle_spin_sound,
                       bg=PANEL, fg=TEXT, selectcolor="#0f1630",
                       activebackground=PANEL, activeforeground=TEXT,
                       font=("Segoe UI", 10)).grid(row=1, column=0, columnspan=2, padx=12, pady=(0, 10), sticky="w")

        # Громкость
        tk.Label(sound_panel, text="Громкость:", bg=PANEL, fg=TEXT, font=("Segoe UI", 10)).grid(
            row=2, column=0, padx=12, pady=(0, 10), sticky="w"
        )
        self.vol = tk.Scale(sound_panel, from_=0, to=100, orient="horizontal",
                            command=self.set_volume,
                            bg=PANEL, fg=TEXT, troughcolor="#0f1630",
                            highlightthickness=0, length=220)
        self.vol.set(int(self.spin_sound_volume * 100))
        self.vol.grid(row=2, column=1, padx=8, pady=(0, 10), sticky="w")

        # Кнопки игры
        btns = tk.Frame(f, bg=BG)
        btns.grid(row=5, column=0, columnspan=3)

        self.spin_btn = tk.Button(btns, text="Крутить", command=self.spin,
                                  bg=ACCENT, fg="#001018", activebackground="#7df4ff",
                                  activeforeground="#001018", relief="flat",
                                  font=("Segoe UI", 11, "bold"), padx=16, pady=8)
        self.spin_btn.grid(row=0, column=0, padx=6)

        self.reset_btn = tk.Button(btns, text="Сброс", command=self.reset_game,
                                   bg="#1b244a", fg=TEXT, activebackground="#24305f",
                                   activeforeground=TEXT, relief="flat",
                                   font=("Segoe UI", 11), padx=16, pady=8)
        self.reset_btn.grid(row=0, column=1, padx=6)

        self.add_btn = tk.Button(btns, text="+10 жетонов", command=self.add_tokens,
                                 bg=ACCENT2, fg="#10061f", activebackground="#c4b5fd",
                                 activeforeground="#10061f", relief="flat",
                                 font=("Segoe UI", 11, "bold"), padx=16, pady=8)
        self.add_btn.grid(row=0, column=2, padx=6)

    def toggle_spin_sound(self):
        self.spin_sound_enabled = bool(self.sound_on_var.get())
        if not self.spin_sound_enabled:
            self.stop_spin_sound()

    def set_volume(self, value):
        try:
            self.spin_sound_volume = max(0.0, min(1.0, float(value) / 100.0))
            if PYGAME_OK:
                pygame.mixer.music.set_volume(float(self.spin_sound_volume))
        except Exception:
            pass

    def back_to_start(self):
        if self.is_spinning:
            return
        sound_click(self.root)
        self.show_start()

    def _set_reels(self, symbols):
        for lbl, s in zip(self.reel_labels, symbols):
            lbl.config(text=s)

    def _set_message(self, text, kind="normal"):
        color = TEXT
        if kind == "good":
            color = GOOD
        elif kind == "bad":
            color = BAD
        elif kind == "gold":
            color = GOLD
        self.msg_lbl.config(text=text, fg=color)

    def _update_stats(self):
        self.stats_lbl.config(
            text=(
                f"Жетоны: {self.balance}   |   Цена спина: {self.spin_cost}   |   "
                f"Очки: {self.score}   |   Прокруток: {self.spins}   |   Джекпотов 🍒🍒🍒: {self.jackpots}"
            )
        )

    def reset_game(self):
        if self.is_spinning:
            return
        sound_click(self.root)
        self.score = 0
        self.spins = 0
        self.jackpots = 0
        self._set_reels(["❔", "❔", "❔"])
        self._set_message("Сброшено. Цель прежняя: 🍒🍒🍒.")
        self._update_stats()

    def add_tokens(self):
        if self.is_spinning:
            return
        sound_click(self.root)
        self.balance += 10
        self._set_message("+10 жетонов добавлено.", "good")
        self._update_stats()

    def spin(self):
        if self.is_spinning:
            return
        sound_click(self.root)

        if self.balance < self.spin_cost:
            self._set_message("Не хватает жетонов на спин. Нажми “+10 жетонов” или вернись в настройки.", "bad")
            return

        self.balance -= self.spin_cost
        self.spins += 1

        self.is_spinning = True
        self.spin_btn.config(state="disabled")
        self.reset_btn.config(state="disabled")
        self.add_btn.config(state="disabled")

        self._set_message("Крутим…")
        self._update_stats()

        # старт пользовательского звука (цикл)
        self.start_spin_sound()

        self._anim_step(0)

    def _anim_step(self, tick):
        self._set_reels([random.choice(SYMBOLS) for _ in range(3)])

        # Если mp3 не выбран/выключен — оставляем старый "тик"
        if not (PYGAME_OK and self.spin_sound_enabled and self.spin_sound_path):
            sound_tick(self.root)

        if tick < ANIMATION_TICKS:
            self.root.after(TICK_MS, lambda: self._anim_step(tick + 1))
            return

        # Финал
        self.stop_spin_sound()

        result = [random.choice(SYMBOLS) for _ in range(3)]
        self._set_reels(result)

        points, token_bonus, msg, kind = reward(result)
        self.score += points
        self.balance += token_bonus

        if kind == "jackpot":
            self.jackpots += 1
            sound_jackpot(self.root)
            self._set_message(msg, "gold")
        elif kind in ("triple", "pair"):
            sound_win(self.root)
            self._set_message(msg, "good")
        else:
            self._set_message(msg)

        self._update_stats()

        self.is_spinning = False
        self.spin_btn.config(state="normal")
        self.reset_btn.config(state="normal")
        self.add_btn.config(state="normal")


def main():
    root = tk.Tk()
    FruitMatchApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
