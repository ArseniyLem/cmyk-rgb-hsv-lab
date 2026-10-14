import tkinter as tk
from tkinter import colorchooser, messagebox

# Цвет хранится внутри приложения в формате RGB (0..255).
# HSV: H в градусах (0..360), S и V в процентах (0..100).
# CMYK: все компоненты в процентах (0..100).


def rgb_to_hsv(r, g, b):
    """Преобразование RGB (0..255) в HSV (H: 0..360, S/V: 0..100)."""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(r, g, b), min(r, g, b)
    delta = mx - mn

    if delta == 0:
        h = 0.0
    elif mx == r:
        h = (60 * ((g - b) / delta)) % 360
    elif mx == g:
        h = 60 * ((b - r) / delta + 2)
    else:
        h = 60 * ((r - g) / delta + 4)

    s = 0.0 if mx == 0 else delta / mx
    v = mx
    return h, s * 100, v * 100


def hsv_to_rgb(h, s, v):
    """Преобразование HSV в RGB."""
    h = float(h) % 360
    s = max(0.0, min(100.0, float(s))) / 100.0
    v = max(0.0, min(100.0, float(v))) / 100.0

    c = v * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = v - c

    if h < 60:
        rp, gp, bp = c, x, 0
    elif h < 120:
        rp, gp, bp = x, c, 0
    elif h < 180:
        rp, gp, bp = 0, c, x
    elif h < 240:
        rp, gp, bp = 0, x, c
    elif h < 300:
        rp, gp, bp = x, 0, c
    else:
        rp, gp, bp = c, 0, x

    return tuple(round((component + m) * 255) for component in (rp, gp, bp))


def rgb_to_cmyk(r, g, b):
    """Преобразование RGB в CMYK, проценты."""
    rp, gp, bp = r / 255.0, g / 255.0, b / 255.0
    k = 1 - max(rp, gp, bp)

    if k >= 1:
        return 0.0, 0.0, 0.0, 100.0

    c = (1 - rp - k) / (1 - k)
    m = (1 - gp - k) / (1 - k)
    y = (1 - bp - k) / (1 - k)
    return c * 100, m * 100, y * 100, k * 100


def cmyk_to_rgb(c, m, y, k):
    """Преобразование CMYK в RGB."""
    c, m, y, k = [max(0.0, min(100.0, float(x))) / 100.0
                  for x in (c, m, y, k)]
    r = 255 * (1 - c) * (1 - k)
    g = 255 * (1 - m) * (1 - k)
    b = 255 * (1 - y) * (1 - k)
    return round(r), round(g), round(b)


class ColorApp:
    def __init__(self, root):
        self.root = root
        root.title("Цветовые модели: CMYK — RGB — HSV")
        root.resizable(False, False)

        self.rgb_vars = [tk.StringVar(value=x) for x in ("255", "0", "0")]
        self.cmyk_vars = [tk.StringVar(value=x) for x in ("0", "100", "100", "0")]
        self.hsv_vars = [tk.StringVar(value=x) for x in ("0", "100", "100")]
        self.hex_var = tk.StringVar(value="#FF0000")
        self.status_var = tk.StringVar(value="Выберите цвет или измените компонент.")

        self._updating = False
        self._after_id = None
        self._build_ui()
        self.update_from_rgb((255, 0, 0))

    def _build_ui(self):
        main = tk.Frame(self.root, padx=14, pady=12)
        main.pack()

        self.preview = tk.Label(
            main, text="Предпросмотр цвета", bg="#ff0000", fg="white",
            width=46, height=4, relief="sunken", font=("Arial", 12, "bold")
        )
        self.preview.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 8))

        tk.Label(main, text="HEX:").grid(row=1, column=0, sticky="e")
        tk.Entry(main, textvariable=self.hex_var, width=12).grid(
            row=1, column=1, sticky="w", padx=4
        )
        tk.Button(main, text="Применить HEX", command=self.apply_hex).grid(
            row=1, column=2, sticky="ew", padx=4
        )
        tk.Button(main, text="Выбрать из палитры…", command=self.choose_color).grid(
            row=2, column=0, columnspan=3, sticky="ew", pady=(6, 10)
        )

        self.entries = {}
        self.scales = {}
        sections = [
            ("RGB (0–255)", ["R", "G", "B"], self.rgb_vars,
             [255, 255, 255], 3),
            ("CMYK (0–100%)", ["C", "M", "Y", "K"], self.cmyk_vars,
             [100, 100, 100, 100], 4),
            ("HSV (H: 0–360°, S/V: 0–100%)", ["H", "S", "V"], self.hsv_vars,
             [360, 100, 100], 3),
        ]

        for col, (title, labels, variables, maxima, _) in enumerate(sections):
            frame = tk.LabelFrame(main, text=title, padx=8, pady=6)
            frame.grid(row=3, column=col, padx=4, sticky="n")
            for row, (label, var, maximum) in enumerate(zip(labels, variables, maxima)):
                tk.Label(frame, text=label, width=3, anchor="w").grid(
                    row=row * 2, column=0, sticky="w"
                )
                entry = tk.Entry(frame, textvariable=var, width=7)
                entry.grid(row=row * 2, column=1, padx=(0, 4), pady=2)
                entry.bind("<Return>", lambda event, c=col: self.apply_entry(c))
                entry.bind("<FocusOut>", lambda event, c=col: self.apply_entry(c))
                self.entries[(col, label)] = entry

                scale = tk.Scale(
                    frame, from_=0, to=maximum, orient="horizontal",
                    length=145, resolution=1 if maximum in (255, 360) else 0.1,
                    showvalue=True, command=lambda value, c=col, l=label:
                    self.on_scale(c, l, value)
                )
                scale.grid(row=row * 2 + 1, column=0, columnspan=2, sticky="ew")
                self.scales[(col, label)] = scale

        tk.Label(main, textvariable=self.status_var, anchor="w").grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=(10, 0)
        )
        tk.Label(
            main,
            text="Изменяйте поля или ползунки. Значения остальных моделей обновятся автоматически.",
            wraplength=620, justify="left", fg="#444"
        ).grid(row=5, column=0, columnspan=3, sticky="w", pady=(5, 0))

    @staticmethod
    def clamp(value, low, high):
        return max(low, min(high, value))

    def read_values(self, variables, labels, maximums):
        values = []
        for var, label, maximum in zip(variables, labels, maximums):
            raw = var.get().strip().replace(",", ".")
            value = float(raw)
            if not (0 <= value <= maximum):
                raise ValueError(f"{label}: введите значение от 0 до {maximum}.")
            values.append(value)
        return values

    def apply_entry(self, column):
        if self._updating:
            return
        try:
            if column == 0:
                values = self.read_values(self.rgb_vars, ["R", "G", "B"], [255, 255, 255])
                rgb = tuple(round(v) for v in values)
            elif column == 1:
                values = self.read_values(
                    self.cmyk_vars, ["C", "M", "Y", "K"], [100, 100, 100, 100]
                )
                rgb = cmyk_to_rgb(*values)
            else:
                values = self.read_values(self.hsv_vars, ["H", "S", "V"], [360, 100, 100])
                rgb = hsv_to_rgb(*values)
            self.update_from_rgb(rgb)
        except ValueError as error:
            messagebox.showerror("Некорректное значение", str(error))
            self.update_from_rgb(self.current_rgb)

    def on_scale(self, column, label, value):
        if self._updating:
            return
        var_map = [self.rgb_vars, self.cmyk_vars, self.hsv_vars][column]
        labels_map = [["R", "G", "B"], ["C", "M", "Y", "K"], ["H", "S", "V"]][column]
        var_map[labels_map.index(label)].set(value)
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
        self._after_id = self.root.after(100, lambda: self.apply_entry(column))

    def update_from_rgb(self, rgb):
        self.current_rgb = tuple(self.clamp(int(v), 0, 255) for v in rgb)
        r, g, b = self.current_rgb
        cmyk = rgb_to_cmyk(r, g, b)
        hsv = rgb_to_hsv(r, g, b)

        self._updating = True
        try:
            for var, value in zip(self.rgb_vars, self.current_rgb):
                var.set(str(value))
            for var, value in zip(self.cmyk_vars, cmyk):
                var.set(f"{value:.1f}")
            for var, value in zip(self.hsv_vars, hsv):
                var.set(f"{value:.1f}")

            values_by_column = [
                self.current_rgb,
                cmyk,
                hsv,
            ]
            labels_by_column = [
                ["R", "G", "B"],
                ["C", "M", "Y", "K"],
                ["H", "S", "V"],
            ]
            for col, (labels, values) in enumerate(zip(labels_by_column, values_by_column)):
                for label, value in zip(labels, values):
                    self.scales[(col, label)].set(value)

            hex_color = "#{:02X}{:02X}{:02X}".format(r, g, b)
            self.hex_var.set(hex_color)
            # Выбираем контрастный цвет текста для читаемости.
            brightness = (299 * r + 587 * g + 114 * b) / 1000
            foreground = "black" if brightness > 145 else "white"
            self.preview.configure(bg=hex_color, fg=foreground,
                                   text=f"{hex_color}    RGB({r}, {g}, {b})")
            self.status_var.set("Цвет успешно пересчитан во всех трёх моделях.")
        finally:
            self._updating = False

    def choose_color(self):
        chosen = colorchooser.askcolor(color=self.hex_var.get(), title="Выберите цвет")
        if chosen and chosen[0]:
            self.update_from_rgb(tuple(round(v) for v in chosen[0]))

    def apply_hex(self):
        value = self.hex_var.get().strip()
        if value.startswith("#"):
            value = value[1:]
        if len(value) == 3:
            value = "".join(ch * 2 for ch in value)
        try:
            if len(value) != 6:
                raise ValueError
            rgb = tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            messagebox.showerror(
                "Некорректный HEX",
                "Введите цвет в формате #RRGGBB, например #2E86C1."
            )
            return
        self.update_from_rgb(rgb)


if __name__ == "__main__":
    root = tk.Tk()
    app = ColorApp(root)
    root.mainloop()
