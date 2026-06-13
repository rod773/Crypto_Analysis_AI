from fpdf import FPDF
import math

class ElliottWavePDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120)
            self.cell(0, 5, "Elliott Wave Theory - Complete Tutorial", align="C")
            self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def chapter_title(self, title):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(20, 60, 120)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(20, 60, 120)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def section_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(40, 80, 140)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, txt):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30)
        self.multi_cell(0, 5, txt)
        self.ln(2)

    def bullet(self, txt):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30)
        x = self.get_x()
        self.cell(6)
        self.set_font("Helvetica", "", 10)
        self.cell(4, 5, "-")
        self.multi_cell(0, 5, txt)
        self.ln(1)

    def draw_impulse_wave(self, x, y, w, h, label="Impulse Wave"):
        # Draw a 5-wave impulse pattern
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(20, 60, 120)
        self.cell(0, 5, label, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        wave_h = h * 0.7
        seg_w = w / 6
        colors = [(0, 180, 0), (200, 0, 0), (0, 180, 0), (200, 0, 0), (0, 180, 0)]
        labels_w = ["1", "2", "3", "4", "5"]

        pts = [(x, y + wave_h)]
        # Wave 1: up
        pts.append((x + seg_w, y + wave_h * 0.3))
        # Wave 2: down (retrace ~0.5)
        pts.append((x + 2 * seg_w, y + wave_h * 0.6))
        # Wave 3: strong up (longest)
        pts.append((x + 3 * seg_w, y + wave_h * 0.05))
        # Wave 4: down (shallow)
        pts.append((x + 4 * seg_w, y + wave_h * 0.4))
        # Wave 5: up (final)
        pts.append((x + 5 * seg_w, y + wave_h * 0.15))

        self.set_line_width(1.5)
        for i in range(len(pts) - 1):
            self.set_draw_color(*colors[i])
            idx = i + 1
            mid_x = (pts[i][0] + pts[i + 1][0]) / 2
            mid_y = (pts[i][1] + pts[i + 1][1]) / 2
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*colors[i])
            self.text(mid_x - 2, mid_y - 4, str(idx))

        # Extend annotation
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(80)
        self.text(x, y + wave_h + 4, "5-wave impulse (1-2-3-4-5)")

    def draw_corrective_wave(self, x, y, w, h, label="Corrective Wave (A-B-C)"):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(20, 60, 120)
        self.cell(0, 5, label, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        seg_w = w / 4
        wave_h = h * 0.7

        pts = [(x, y + wave_h * 0.1)]
        # A: down
        pts.append((x + seg_w, y + wave_h * 0.7))
        # B: up (retrace)
        pts.append((x + 2 * seg_w, y + wave_h * 0.3))
        # C: down (below A)
        pts.append((x + 3 * seg_w, y + wave_h * 0.9))

        colors = [(200, 0, 0), (0, 0, 200), (200, 0, 0)]
        self.set_line_width(1.5)
        for i in range(len(pts) - 1):
            self.set_draw_color(*colors[i])
            mid_x = (pts[i][0] + pts[i + 1][0]) / 2
            mid_y = (pts[i][1] + pts[i + 1][1]) / 2
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*colors[i])
            label_char = chr(65 + i)
            self.text(mid_x - 2, mid_y - 4, label_char)

        self.set_font("Helvetica", "I", 8)
        self.set_text_color(80)
        self.text(x, y + wave_h + 4, "3-wave corrective (A-B-C)")

    def draw_wave_degrees(self, x, y, w):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(20, 60, 120)
        self.cell(0, 5, "Wave Degrees (Fractal Nature)", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

        degrees = [
            ("Grand Supercycle", "Century", "Multi-century"),
            ("Supercycle", "40-70 years", "Long-term"),
            ("Cycle", "1-4 years", "Intermediate"),
            ("Primary", "Months", "Medium-term"),
            ("Intermediate", "Weeks-Months", "Short-term"),
            ("Minor", "Weeks", "Trading"),
            ("Minute", "Days", "Short-term trading"),
            ("Minuette", "Hours", "Intraday"),
            ("Subminuette", "Minutes", "Very short-term"),
        ]

        self.set_font("Helvetica", "B", 8)
        col_w = w / 3
        # header
        self.set_fill_color(20, 60, 120)
        self.set_text_color(255)
        self.cell(col_w, 6, "  Degree", border=1, align="C", fill=True)
        self.cell(col_w, 6, "  Duration", border=1, align="C", fill=True)
        self.cell(col_w, 6, "  Context", border=1, align="C", fill=True)
        self.ln()

        self.set_font("Helvetica", "", 8)
        self.set_text_color(30)
        for i, (deg, dur, ctx) in enumerate(degrees):
            if i % 2 == 0:
                self.set_fill_color(235, 240, 250)
            else:
                self.set_fill_color(255, 255, 255)
            self.cell(col_w, 5, f"  {deg}", border=1, fill=True)
            self.cell(col_w, 5, f"  {dur}", border=1, align="C", fill=True)
            self.cell(col_w, 5, f"  {ctx}", border=1, align="C", fill=True)
            self.ln()

    def draw_zigzag(self, x, y, w, h, label="Zigzag (5-3-5)"):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(20, 60, 120)
        self.cell(0, 5, label, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        seg_w = w / 6
        y0 = y + h * 0.5
        pts = [(x, y0)]
        pts.append((x + seg_w, y + h * 0.05))
        pts.append((x + 2 * seg_w, y0 + h * 0.3))
        pts.append((x + 3 * seg_w, y + h * 0.1))
        pts.append((x + 4 * seg_w, y0 + h * 0.35))
        pts.append((x + 5 * seg_w, y + h * 0.1))

        self.set_draw_color(200, 0, 0)
        self.set_line_width(1.5)
        for i in range(len(pts) - 1):
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])

        self.set_font("Helvetica", "I", 8)
        self.set_text_color(80)
        self.text(x, y + h * 0.4 + 4, "Sharp, steep correction (A: 5, B: 3, C: 5)")

    def draw_flat(self, x, y, w, h, label="Flat (3-3-5)"):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(20, 60, 120)
        self.cell(0, 5, label, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        seg_w = w / 4
        y0 = y + h * 0.35
        pts = [(x, y0)]
        pts.append((x + seg_w, y0 + h * 0.45))
        pts.append((x + 2 * seg_w, y0 - h * 0.05))
        pts.append((x + 3 * seg_w, y0 + h * 0.5))

        self.set_draw_color(0, 0, 200)
        self.set_line_width(1.5)
        for i in range(len(pts) - 1):
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])

        self.set_font("Helvetica", "I", 8)
        self.set_text_color(80)
        self.text(x, y + h * 0.55 + 4, "Sideways correction (A: 3, B: 3, C: 5)")

    def draw_triangle(self, x, y, w, h, label="Triangle (3-3-3-3-3)"):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(20, 60, 120)
        self.cell(0, 5, label, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        seg_w = w / 6
        y0 = y + h * 0.4
        pts = [(x, y0)]
        pts.append((x + seg_w, y0 + h * 0.3))
        pts.append((x + 2 * seg_w, y0 - h * 0.1))
        pts.append((x + 3 * seg_w, y0 + h * 0.2))
        pts.append((x + 4 * seg_w, y0 - h * 0.05))
        pts.append((x + 5 * seg_w, y0 + h * 0.15))

        self.set_draw_color(180, 120, 0)
        self.set_line_width(1.5)
        for i in range(len(pts) - 1):
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])

        self.set_font("Helvetica", "I", 8)
        self.set_text_color(80)
        self.text(x, y + h * 0.45 + 4, "Contracting/expanding sideways pattern")

    def draw_rule_of_alternation(self, x, y, w):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(20, 60, 120)
        self.cell(0, 5, "Rule of Alternation - Wave 2 vs Wave 4", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        seg_w = w / 5
        h_wave = 30
        y0 = y + 45

        pts = [(x, y0)]
        pts.append((x + seg_w, y0 - h_wave * 0.6))
        pts.append((x + 2 * seg_w, y0 - h_wave * 0.4))
        pts.append((x + 3 * seg_w, y0 - h_wave * 0.9))
        pts.append((x + 4 * seg_w, y0 - h_wave * 0.5))
        pts.append((x + 5 * seg_w, y0 - h_wave * 0.85))

        colors = [(0, 180, 0), (200, 0, 0), (0, 180, 0)]
        self.set_line_width(1.2)
        for i in range(len(pts) - 1):
            ci = 0 if i % 2 == 0 else 1
            self.set_draw_color(*colors[ci])
            mid_x = (pts[i][0] + pts[i + 1][0]) / 2
            mid_y = (pts[i][1] + pts[i + 1][1]) / 2
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*colors[ci])
            self.text(mid_x - 2, mid_y - 4, str(i + 1))

        self.set_font("Helvetica", "I", 8)
        self.set_text_color(80)
        self.text(x, y0 + 4, "Wave 2  (sharp)         Wave 4  (flat/sideways)")
        self.text(x, y0 + 10, "If Wave 2 is sharp, expect Wave 4 to be flat, and vice versa")

    def draw_fibonacci_retrace(self, x, y, w):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(20, 60, 120)
        self.cell(0, 5, "Fibonacci Retracement Levels", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        y0 = y + 5
        x0 = x + 20
        seg_w = w * 0.6
        h_wave = 40

        # Draw a swing up
        self.set_draw_color(0, 180, 0)
        self.set_line_width(2)
        self.line(x0, y0 + h_wave, x0, y0)
        self.line(x0, y0, x0 + seg_w, y0)
        self.set_draw_color(200, 0, 0)
        self.line(x0 + seg_w, y0, x0 + seg_w, y0 + h_wave * 0.618)

        # Labels
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(0, 150, 0)
        self.text(x0 - 14, y0 + h_wave, "Start")
        self.text(x0 - 14, y0 - 4, "Top")

        # Retracement labels
        levels = [(0.0, "0% (no retrace)"), (0.236, "23.6%"), (0.382, "38.2%"), (0.5, "50%"), (0.618, "61.8%"), (0.786, "78.6%"), (1.0, "100%")]
        self.set_font("Helvetica", "", 8)
        for pct, lbl in levels:
            yy = y0 + h_wave - h_wave * pct
            self.set_draw_color(180, 180, 180)
            self.set_line_width(0.3)
            self.set_text_color(100)
            if pct in (0.382, 0.618):
                self.set_dash_pattern(2, 1)
                self.set_draw_color(200, 100, 0)
                self.set_line_width(0.6)
                self.line(x0, yy, x0 + seg_w + 8, yy)
                self.set_text_color(200, 100, 0)
                self.set_font("Helvetica", "B", 8)
                self.text(x0 + seg_w + 10, yy - 2, f"{lbl} (key)")
                self.set_font("Helvetica", "", 8)
                self.set_dash_pattern()
            else:
                self.line(x0 + seg_w + 2, yy, x0 + seg_w + 6, yy)
                self.text(x0 + seg_w + 8, yy - 2, lbl)

        self.set_font("Helvetica", "I", 8)
        self.set_text_color(80)
        self.text(x, y0 + h_wave + 8, "Common retracement: Wave 2 = 50-61.8%, Wave 4 = 38.2% of Wave 3")

    def draw_fibonacci_extensions(self, x, y, w):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(20, 60, 120)
        self.cell(0, 5, "Fibonacci Extension Targets", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        y0 = y + 5
        x0 = x + 20
        seg_w = w * 0.55

        # Simple impulse with targets
        pts = [(x0, y0 + 35), (x0 + seg_w * 0.2, y0 + 5), (x0 + seg_w * 0.4, y0 + 18),
               (x0 + seg_w * 0.6, y0 + 2), (x0 + seg_w * 0.8, y0 + 15), (x0 + seg_w, y0 + 2)]

        colors = [(0, 180, 0), (200, 0, 0), (0, 180, 0), (200, 0, 0), (0, 180, 0)]
        self.set_line_width(1.2)
        for i in range(len(pts) - 1):
            self.set_draw_color(*colors[i])
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*colors[i])
            self.text((pts[i][0] + pts[i + 1][0]) / 2 - 2, (pts[i][1] + pts[i + 1][1]) / 2 - 4, str(i + 1))

        # Extension arrows
        self.set_draw_color(180, 120, 0)
        self.set_line_width(0.8)
        ex_x = x0 + seg_w + 10
        ext_targets = [(1.272, "127.2%"), (1.414, "141.4%"), (1.618, "161.8%"), (2.0, "200%"), (2.618, "261.8%")]
        for pct, lbl in ext_targets:
            yy = y0 + 35 - (35 - 2) * pct
            if yy > y0 + 35:
                yy = y0 + 35
            if yy < self.t_margin:
                continue
            self.set_dash_pattern(2, 1)
            self.line(x0 + seg_w + 2, yy, x0 + seg_w + 8, yy)
            self.set_dash_pattern()
            self.set_font("Helvetica", "", 8)
            self.set_text_color(140, 80, 0)
            self.text(x0 + seg_w + 10, yy - 2, f"{lbl}")

        self.set_font("Helvetica", "I", 8)
        self.set_text_color(80)
        self.text(x, y0 + 42, "Common Wave 3 extension: 161.8% of Wave 1. Wave 5: 61.8-161.8% of Wave 1.")

    def draw_channel(self, x, y, w, label="Channeling Technique"):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(20, 60, 120)
        self.cell(0, 5, label, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        seg_w = w / 6
        y0 = y + 35
        pts = [(x, y0), (x + seg_w, y0 - 20), (x + 2 * seg_w, y0 - 14),
               (x + 3 * seg_w, y0 - 28), (x + 4 * seg_w, y0 - 22), (x + 5 * seg_w, y0 - 30)]

        # Channel lines
        self.set_draw_color(100, 100, 200)
        self.set_line_width(0.4)
        self.set_dash_pattern(2, 1)
        self.line(pts[0][0], pts[0][1], pts[4][0], pts[4][1])
        self.line(pts[1][0], pts[1][1], pts[5][0], pts[5][1])
        self.set_dash_pattern()

        # Wave
        colors = [(0, 180, 0), (200, 0, 0), (0, 180, 0), (200, 0, 0), (0, 180, 0)]
        self.set_line_width(1.5)
        for i in range(len(pts) - 1):
            self.set_draw_color(*colors[i])
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*colors[i])
            self.text((pts[i][0] + pts[i + 1][0]) / 2 - 2, (pts[i][1] + pts[i + 1][1]) / 2 - 4, str(i + 1))

        self.set_font("Helvetica", "I", 8)
        self.set_text_color(80)
        self.text(x, y + 3, "Connect waves 2-4 for lower channel, 1-3 for upper channel")

    def draw_motive_waves(self, x, y, w):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(20, 60, 120)
        self.cell(0, 5, "Motive Waves: Impulse vs Diagonal", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        # Impulse
        seg_w = w / 6
        y0 = y + 30
        pts = [(x, y0), (x + seg_w, y0 - 15), (x + 2 * seg_w, y0 - 10),
               (x + 3 * seg_w, y0 - 22), (x + 4 * seg_w, y0 - 16), (x + 5 * seg_w, y0 - 24)]
        colors = [(0, 180, 0), (200, 0, 0), (0, 180, 0), (200, 0, 0), (0, 180, 0)]
        self.set_line_width(1.2)
        for i in range(len(pts) - 1):
            self.set_draw_color(*colors[i])
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(*colors[i])
            self.text((pts[i][0] + pts[i + 1][0]) / 2 - 2, (pts[i][1] + pts[i + 1][1]) / 2 - 3, str(i + 1))
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(80)
        self.text(x, y + 4, "Impulse (W4 does not enter W1 price territory)")

        # Ending Diagonal
        x2 = x + w * 0.5
        pts2 = [(x2, y0), (x2 + seg_w, y0 - 12), (x2 + 2 * seg_w, y0 - 8),
                (x2 + 3 * seg_w, y0 - 15), (x2 + 4 * seg_w, y0 - 10), (x2 + 5 * seg_w, y0 - 12)]
        self.set_line_width(1.2)
        for i in range(len(pts2) - 1):
            self.set_draw_color(*colors[i])
            self.line(pts2[i][0], pts2[i][1], pts2[i + 1][0], pts2[i + 1][1])
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(*colors[i])
            self.text((pts2[i][0] + pts2[i + 1][0]) / 2 - 2, (pts2[i][1] + pts2[i + 1][1]) / 2 - 3, str(i + 1))
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(80)
        self.text(x2, y + 4, "Ending Diagonal (W4 overlaps W1)")

    def draw_rules_table(self, x, y, w):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(20, 60, 120)
        self.cell(0, 5, "Three Hard Rules of Elliott Wave", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        col_w = w / 3
        headers = ["Rule", "Description", "Violation"]
        rows = [
            ["Rule 1", "Wave 2 cannot retrace more than 100% of Wave 1", "Invalid count"],
            ["Rule 2", "Wave 3 is never the shortest impulse wave", "Invalid count"],
            ["Rule 3", "Wave 4 cannot overlap Wave 1's price territory", "Ending diagonal only"],
        ]

        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(20, 60, 120)
        self.set_text_color(255)
        for h in headers:
            self.cell(col_w, 6, f"  {h}", border=1, align="C", fill=True)
        self.ln()

        self.set_font("Helvetica", "", 8)
        self.set_text_color(30)
        for i, row in enumerate(rows):
            if i % 2 == 0:
                self.set_fill_color(235, 240, 250)
            else:
                self.set_fill_color(255, 255, 255)
            for j, val in enumerate(row):
                self.cell(col_w, 5, f"  {val}", border=1, fill=True)
            self.ln()

    def draw_diagonal_types(self, x, y, w, label="Diagonal Types"):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(20, 60, 120)
        self.cell(0, 5, label, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

        half = w / 2
        seg_w = half / 6
        y0 = y + 55

        # --- ENDING DIAGONAL (left) ---
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(180, 0, 0)
        self.text(x, y + 8, "Ending Diagonal (Type 1)")
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100)
        self.text(x, y + 16, "Sub-waves: 3-3-3-3-3")
        self.text(x, y + 22, "Appears in: Wave 5 or Wave C")
        self.text(x, y + 28, "Tapering wedge, W4 overlaps W1")

        # Upper trendline (contracting wedge)
        self.set_draw_color(160, 0, 0)
        self.set_line_width(0.5)
        self.line(x, y0 - 10, x + half - 5, y0 + 8)

        # Lower trendline
        self.line(x, y0 + 10, x + half - 5, y0 - 8)

        # 5 sub-waves internally
        self.set_line_width(1.5)
        colors = [(0, 180, 0), (200, 0, 0), (0, 180, 0), (200, 0, 0), (0, 180, 0)]
        pts = [
            (x + 2, y0 + 2),
            (x + seg_w, y0 - 6),
            (x + 2 * seg_w, y0 + 5),
            (x + 3 * seg_w, y0 - 4),
            (x + 4 * seg_w, y0 + 3),
            (x + half - 5, y0 - 1),
        ]
        for i in range(len(pts) - 1):
            self.set_draw_color(*colors[i])
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(*colors[i])
            self.text((pts[i][0] + pts[i + 1][0]) / 2 - 2, (pts[i][1] + pts[i + 1][1]) / 2 - 5, str(i + 1))

        # Overlap annotation
        self.set_draw_color(100, 100, 100)
        self.set_line_width(0.3)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(140)
        self.set_dash_pattern(2, 1)
        self.line(x + 4 * seg_w, pts[4][1], x + 4 * seg_w, pts[0][1] + 5)
        self.set_dash_pattern()

        # --- LEADING DIAGONAL (right) ---
        x2 = x + half
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(0, 100, 180)
        self.text(x2, y + 8, "Leading Diagonal (Type 2)")
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100)
        self.text(x2, y + 16, "Sub-waves: 5-3-5-3-5")
        self.text(x2, y + 22, "Appears in: Wave 1 or Wave A")
        self.text(x2, y + 28, "Wedge shape, W4 may overlap W1")

        self.set_draw_color(0, 100, 180)
        self.set_line_width(0.5)
        self.line(x2, y0 - 8, x2 + half - 5, y0 + 10)
        self.line(x2, y0 + 8, x2 + half - 5, y0 - 10)

        self.set_line_width(1.5)
        pts2 = [
            (x2 + 2, y0 - 1),
            (x2 + seg_w, y0 - 8),
            (x2 + 2 * seg_w, y0 + 3),
            (x2 + 3 * seg_w, y0 - 6),
            (x2 + 4 * seg_w, y0 + 2),
            (x2 + half - 5, y0 - 3),
        ]
        for i in range(len(pts2) - 1):
            self.set_draw_color(*colors[i])
            self.line(pts2[i][0], pts2[i][1], pts2[i + 1][0], pts2[i + 1][1])
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(*colors[i])
            self.text((pts2[i][0] + pts2[i + 1][0]) / 2 - 2, (pts2[i][1] + pts2[i + 1][1]) / 2 - 5, str(i + 1))

        # Comparison table below
        yt = y + 68
        col_w = half / 2
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(20, 60, 120)
        self.set_text_color(255)
        headers2 = ["Feature", "Ending Diag.", "Leading Diag."]
        for h in headers2:
            self.cell(col_w, 5, f"  {h}", border=1, align="C", fill=True)
        self.set_xy(x, yt)
        # must flush the cell row
        self.set_xy(x, yt)
        # Actually let me redo this properly
        self.ln()

        def diag_row(a, b, c):
            self.set_font("Helvetica", "", 7)
            self.set_text_color(30)
            self.cell(col_w, 4, f"  {a}", border=1)
            self.cell(col_w, 4, f"  {b}", border=1, align="C")
            self.cell(col_w, 4, f"  {c}", border=1, align="C")
            self.ln()

        diag_row("Structure", "3-3-3-3-3", "5-3-5-3-5")
        diag_row("Position", "Wave 5 or C", "Wave 1 or A")
        diag_row("W4 overlap", "Always", "Often")
        diag_row("After formation", "Sharp reversal", "Brief pullback then trend")
        diag_row("Volume", "Declining", "Declining")

    def draw_triangle_types(self, x, y, w, label="Triangle Patterns"):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(20, 60, 120)
        self.cell(0, 5, label, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

        # Three types shown side by side
        third = w / 3
        y0 = y + 50

        def _draw_triangle(cx, cy, half_w, h, color, label, sublabel):
            # Draw bounding lines
            self.set_draw_color(*color)
            self.set_line_width(0.6)
            pts = [(cx - half_w, cy), (cx, cy - h / 2), (cx + half_w, cy)]
            n = 5
            seg_w = (2 * half_w) / n
            pts_wave = [(cx - half_w + i * seg_w, cy - (h / 2) * (1 - abs(-1 + 2 * i / n)) + 3 * ((-1) ** i)) for i in range(n + 1)]
            # Constrain to the triangle shape
            for i, (px, py) in enumerate(pts_wave):
                t = i / n
                # upper boundary
                upper_y = cy - (h / 2) * (1 - abs(2 * t - 1))
                lower_y = cy + (h / 2) * (1 - abs(2 * t - 1))
                if py < upper_y:
                    pts_wave[i] = (px, upper_y + 2)
                if py > lower_y:
                    pts_wave[i] = (px, lower_y - 2)

            # Draw boundary triangle
            self.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1])
            self.line(pts[1][0], pts[1][1], pts[2][0], pts[2][1])
            self.line(pts[0][0], pts[0][1], pts[2][0], pts[2][1])

            # Draw wave
            wave_colors = [color, (200, 0, 0), color, (200, 0, 0), color]
            self.set_line_width(1.3)
            labels = ["A", "B", "C", "D", "E"]
            for i in range(len(pts_wave) - 1):
                self.set_draw_color(*wave_colors[i])
                self.line(pts_wave[i][0], pts_wave[i][1], pts_wave[i + 1][0], pts_wave[i + 1][1])
                mid_x = (pts_wave[i][0] + pts_wave[i + 1][0]) / 2
                mid_y = (pts_wave[i][1] + pts_wave[i + 1][1]) / 2
                self.set_font("Helvetica", "B", 9)
                self.set_text_color(*wave_colors[i])
                self.text(mid_x - 3, mid_y - 4, labels[i])

            self.set_font("Helvetica", "I", 7)
            self.set_text_color(80)
            self.text(cx - half_w, cy + h / 2 + 2, sublabel)

        # Contracting Triangle
        cx = x + third / 2
        _draw_triangle(cx, y0, third * 0.35, 45, (180, 120, 0), "Contracting", "A > B > C > D > E (most common)")

        # Expanding Triangle
        cx2 = x + third + third / 2
        _draw_triangle(cx2, y0, third * 0.2, 45, (200, 80, 0), "Expanding", "A < B < C < D < E (rare)")

        # Neutral Triangle
        cx3 = x + 2 * third + third / 2
        self.set_draw_color(100, 100, 200)
        self.set_line_width(0.6)
        # Horizontal boundaries for neutral
        y0_n = y0
        self.line(cx3 - third * 0.35, y0_n - 22, cx3 + third * 0.35, y0_n - 22)
        self.line(cx3 - third * 0.35, y0_n + 22, cx3 + third * 0.35, y0_n + 22)
        # diagonal lines connecting
        self.line(cx3 - third * 0.35, y0_n - 22, cx3 + third * 0.35, y0_n + 22)
        self.line(cx3 + third * 0.35, y0_n - 22, cx3 - third * 0.35, y0_n + 22)

        n = 5
        seg_w = (2 * third * 0.35) / n
        pts_wave = [(cx3 - third * 0.35 + i * seg_w, y0_n - 22 + (i - 2) * 6) for i in range(n + 1)]
        # Clamp
        for i in range(len(pts_wave)):
            if pts_wave[i][1] < y0_n - 22: pts_wave[i] = (pts_wave[i][0], y0_n - 20)
            if pts_wave[i][1] > y0_n + 22: pts_wave[i] = (pts_wave[i][0], y0_n + 20)

        wave_colors = [(100, 100, 200), (200, 0, 0), (100, 100, 200), (200, 0, 0), (100, 100, 200)]
        self.set_line_width(1.3)
        labels = ["A", "B", "C", "D", "E"]
        for i in range(len(pts_wave) - 1):
            self.set_draw_color(*wave_colors[i])
            self.line(pts_wave[i][0], pts_wave[i][1], pts_wave[i + 1][0], pts_wave[i + 1][1])
            mid_x = (pts_wave[i][0] + pts_wave[i + 1][0]) / 2
            mid_y = (pts_wave[i][1] + pts_wave[i + 1][1]) / 2
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*wave_colors[i])
            self.text(mid_x - 3, mid_y - 4, labels[i])

        self.set_font("Helvetica", "I", 7)
        self.set_text_color(80)
        self.text(cx3 - third * 0.35, y0_n + 26, "Neutral (parallel boundaries)")

        # Common rules table below
        yt2 = y + 85
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(20, 60, 120)
        self.text(x, yt2 - 3, "Triangle Rules & Characteristics:")
        self.ln(14)

        rows = [
            ["Sub-waves", "Each of 5 legs (A-B-C-D-E) is a 3-wave (3-3-3-3-3)"],
            ["Position", "Wave 4, Wave B, Wave X, or final wave of a correction"],
            ["Breakout", "Sharp thrust equal to the widest part of the triangle"],
            ["Volume", "Declines steadily as the triangle progresses"],
            ["After triangle", "Usually a strong, fast move (the 'thrust') in the direction of the prior trend"],
            ["Fibonacci help", "Retracement of prior trend is often 38-50% at triangle's end"],
        ]
        col_w = third * 0.7
        self.set_font("Helvetica", "B", 7)
        self.set_fill_color(20, 60, 120)
        self.set_text_color(255)
        self.cell(col_w, 5, "  Aspect", border=1, fill=True)
        self.cell(w - col_w, 5, "  Description", border=1, fill=True)
        self.ln()
        self.set_font("Helvetica", "", 7)
        self.set_text_color(30)
        for r in rows:
            self.cell(col_w, 4, f"  {r[0]}", border=1)
            self.cell(w - col_w, 4, f"  {r[1]}", border=1)
            self.ln()

    def draw_guidelines_table(self, x, y, w):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(20, 60, 120)
        self.cell(0, 5, "Common Guidelines (not hard rules)", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        col_w = w / 3
        headers = ["Guideline", "Typical Behavior", "Significance"]
        rows = [
            ["Alternation", "Wave 2 sharp, Wave 4 sideways (or vice versa)", "High probability"],
            ["Channeling", "Waves contained within parallel lines", "Confirms structure"],
            ["Equality", "Wave 5 is often equal to Wave 1", "Extension target"],
            ["Retracement", "Wave 2 retraces 50-61.8% of Wave 1", "Entry zone"],
            ["Fibonacci", "Wave 3 extends 161.8%+ of Wave 1", "Strongest wave"],
        ]

        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(20, 60, 120)
        self.set_text_color(255)
        for h in headers:
            self.cell(col_w, 6, f"  {h}", border=1, align="C", fill=True)
        self.ln()

        self.set_font("Helvetica", "", 8)
        self.set_text_color(30)
        for i, row in enumerate(rows):
            if i % 2 == 0:
                self.set_fill_color(235, 240, 250)
            else:
                self.set_fill_color(255, 255, 255)
            for j, val in enumerate(row):
                self.cell(col_w, 5, f"  {val}", border=1, fill=True)
            self.ln()


pdf = ElliottWavePDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)

# =========== COVER PAGE ===========
pdf.add_page()
pdf.ln(50)
pdf.set_font("Helvetica", "B", 28)
pdf.set_text_color(20, 60, 120)
pdf.cell(0, 15, "Elliott Wave Theory", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 18)
pdf.set_text_color(60, 100, 160)
pdf.cell(0, 12, "Complete Tutorial Guide", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(8)
pdf.set_draw_color(20, 60, 120)
pdf.line(60, pdf.get_y(), 150, pdf.get_y())
pdf.ln(8)
pdf.set_font("Helvetica", "I", 11)
pdf.set_text_color(100)
pdf.cell(0, 7, "Ralph Nelson Elliott (1871-1948)", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 7, "Market behavior follows recognizable wave patterns", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 7, "driven by investor psychology (fear and greed)", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(15)
pdf.set_font("Helvetica", "", 10)
pdf.set_text_color(130)
pdf.cell(0, 6, "Applies to: Stocks, Crypto, Forex, Commodities, Indices", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 6, "Timeframes: Minutes to Centuries", align="C", new_x="LMARGIN", new_y="NEXT")

# =========== PAGE 2: TABLE OF CONTENTS ===========
pdf.add_page()
pdf.chapter_title("Table of Contents")
pdf.set_font("Helvetica", "", 11)
pdf.set_text_color(30)
toc = [
    "1. Introduction to Elliott Wave Theory",
    "2. Core Principle: The Fractal Nature of Markets",
    "3. The Basic Pattern: 5-Wave Impulse + 3-Wave Correction",
    "4. Motive Waves: Impulse and Diagonal",
    "    4.1 Impulse Waves",
    "    4.2 Diagonal Waves (Ending & Leading)",
    "5. Corrective Waves: Zigzag, Flat, Triangle, Double Three",
    "    5.1 Zigzag (5-3-5)",
    "    5.2 Flat (3-3-5)",
    "    5.3 Triangle (3-3-3-3-3) - All Types",
    "    5.4 Double and Triple Threes",
    "6. Wave Degrees and Nesting",
    "7. The Three Hard Rules",
    "8. Guidelines and Typical Behavior",
    "9. Fibonacci Relationships in Elliott Wave",
    "10. Channeling Technique",
    "11. Rule of Alternation",
    "12. Common Counting Mistakes",
    "13. Practical Application Workflow",
    "14. Advanced Concepts",
    "15. Summary Cheat Sheet",
]
for t in toc:
    pdf.cell(0, 7, f"     {t}", new_x="LMARGIN", new_y="NEXT")

# =========== SECTION 1: INTRODUCTION ===========
pdf.add_page()
pdf.chapter_title("1. Introduction to Elliott Wave Theory")
pdf.body_text(
    "Elliott Wave Theory was developed by Ralph Nelson Elliott in the 1930s. After studying 75 years of stock market data, "
    "Elliott discovered that market prices unfold in specific recurring patterns he called 'waves'. These patterns reflect "
    "the collective psychology of market participants, oscillating between optimism and pessimism."
)
pdf.body_text(
    "The theory is built on the premise that mass psychology moves from pessimism to optimism and back in a natural sequence, "
    "creating recognizable patterns. These patterns appear at every degree of trend, from minute tick charts to century-long "
    "movements -- a property known as self-similarity or fractality."
)
pdf.body_text(
    "Unlike many technical analysis methods that are purely descriptive, Elliott Wave provides a structured framework for "
    "anticipating price movements, identifying high-probability reversal zones, and managing risk with clearly defined rules."
)

# =========== SECTION 2: FRACTAL NATURE ===========
pdf.add_page()
pdf.chapter_title("2. Core Principle: The Fractal Nature of Markets")
pdf.body_text(
    "The most important concept in Elliott Wave is fractality: the same wave structure repeats across all timeframes. "
    "A 5-wave impulse on a 1-minute chart has the same shape and rules as a 5-wave impulse on a weekly chart."
)
pdf.body_text(
    "Each wave of a larger degree is composed of smaller waves of the next lower degree:"
)
pdf.bullet("An impulse wave (5 waves) at a higher degree breaks down into 5 smaller waves at the next degree")
pdf.bullet("A corrective wave (3 waves) at a higher degree breaks down into 3 smaller waves at the next degree")
pdf.bullet("This nesting continues across at least 9 degrees, from Subminuette to Grand Supercycle")
pdf.ln(2)
pdf.draw_wave_degrees(pdf.l_margin, pdf.get_y(), pdf.w - 2 * pdf.l_margin)

# =========== SECTION 3: THE BASIC PATTERN ===========
pdf.add_page()
pdf.chapter_title("3. The Basic Pattern: 5-Wave Impulse + 3-Wave Correction")
pdf.body_text(
    "The fundamental building block consists of two phases:"
)
pdf.bullet("Motive phase (Impulse): 5 sub-waves in the direction of the main trend (labeled 1-2-3-4-5)")
pdf.bullet("Corrective phase: 3 sub-waves against the main trend (labeled A-B-C)")
pdf.ln(2)
pdf.draw_impulse_wave(pdf.l_margin + 10, pdf.get_y() + 2, 80, 40)
pdf.ln(40)
pdf.draw_corrective_wave(pdf.l_margin + 10, pdf.get_y() + 2, 60, 35)
pdf.ln(35)

pdf.body_text(
    "Together, one complete cycle is: 5 waves up + 3 waves down = 8 waves total. "
    "This 8-wave cycle then becomes two sub-waves of the next higher degree cycle."
)

# =========== SECTION 4: MOTIVE WAVES ===========
pdf.add_page()
pdf.chapter_title("4. Motive Waves: Impulse and Diagonal")
pdf.body_text(
    "Motive waves move in the direction of the larger trend. There are two types:"
)
pdf.section_title("4.1 Impulse Waves")
pdf.body_text(
    "This is the most common motive wave. Rules: Wave 3 is never the shortest; Wave 2 cannot retrace more than 100% of Wave 1; "
    "Wave 4 cannot overlap Wave 1. Wave 3 often shows the strongest momentum and volume. Sub-waves of an impulse are 5-3-5-3-5."
)
pdf.ln(2)
pdf.draw_motive_waves(pdf.l_margin + 10, pdf.get_y(), pdf.w - 2 * pdf.l_margin - 10)
pdf.ln(30)

pdf.section_title("4.2 Diagonal Waves")
pdf.body_text(
    "Diagonals are motive waves that form wedge-shaped patterns. They replace impulses in specific positions "
    "and have the unique property that Wave 4 overlaps Wave 1 (which is forbidden in a standard impulse). "
    "There are two types:"
)
pdf.ln(2)
pdf.draw_diagonal_types(pdf.l_margin + 5, pdf.get_y(), pdf.w - 2 * pdf.l_margin - 5)
pdf.ln(60)

pdf.section_title("4.2.1 Ending Diagonal (Type 1)")
pdf.body_text(
    "Also called a 'wedge' or 'terminal pattern'. Appears exclusively in Wave 5 of an impulse or Wave C of a correction. "
    "Its internal structure is 3-3-3-3-3 (all sub-waves are corrective zigzags). "
    "The pattern converges as it progresses, with decreasing volume. "
    "After completion, the market typically reverses sharply - this is known as the 'throw-over' or 'back-test'. "
    "Key characteristics:"
)
pdf.bullet("Wave 1 is the longest, Wave 3 is next, Wave 5 is the shortest")
pdf.bullet("Price action forms a contracting wedge between two converging trendlines")
pdf.bullet("Wave 4 almost always overlaps Wave 1")
pdf.bullet("Volume declines throughout, often with a spike on the final leg")
pdf.bullet("Followed by a fast reversal (at least back to where the diagonal started)")

pdf.section_title("4.2.2 Leading Diagonal (Type 2)")
pdf.body_text(
    "Appears in Wave 1 of an impulse or Wave A of a correction. Its internal structure is 5-3-5-3-5 - "
    "sub-waves 1, 3, and 5 are themselves impulses, while 2 and 4 are corrections. "
    "Leading diagonals often appear at the beginning of new trends after a prolonged correction. "
    "Key characteristics:"
)
pdf.bullet("Sub-waves 1, 3, 5 are 5-wave impulses (unlike ending diagonals)")
pdf.bullet("Wave 4 may or may not overlap Wave 1")
pdf.bullet("The post-diagonal move is a brief pullback, then the trend continues strongly")
pdf.bullet("Less common than ending diagonals")

# =========== SECTION 5: CORRECTIVE WAVES ===========
pdf.add_page()
pdf.chapter_title("5. Corrective Waves: Zigzag, Flat, Triangle, Double Three")
pdf.body_text(
    "Corrective waves move against the larger trend. They are more varied than impulse waves and harder to identify. "
    "The main types are:"
)

pdf.section_title("5.1 Zigzag (5-3-5)")
pdf.body_text(
    "A sharp correction that moves strongly against the prior trend. Wave A is 5 sub-waves, Wave B retraces 38-50% of A, "
    "and Wave C extends beyond A. Often found in Wave 2 of an impulse."
)
pdf.draw_zigzag(pdf.l_margin + 10, pdf.get_y(), 70, 30)
pdf.ln(30)

pdf.section_title("5.2 Flat (3-3-5)")
pdf.body_text(
    "A sideways correction where waves A and B are both 3 sub-waves. Wave B often retraces 90-100% of A. "
    "Wave C ends near or slightly beyond A. Common in Wave 4."
)
pdf.draw_flat(pdf.l_margin + 10, pdf.get_y(), 55, 30)
pdf.ln(30)

pdf.section_title("5.3 Triangle (3-3-3-3-3)")
pdf.body_text(
    "Triangles are sideways corrective patterns consisting of 5 sub-waves labeled A-B-C-D-E, "
    "each of which is a 3-wave structure (3-3-3-3-3). "
    "They commonly appear in Wave 4 of an impulse, Wave B of a correction, or as the final pattern in a double/triple three. "
    "Triangles indicate a period of indecision where the market contracts or expands within converging/diverging boundary lines."
)
pdf.ln(2)
pdf.draw_triangle_types(pdf.l_margin + 5, pdf.get_y(), pdf.w - 2 * pdf.l_margin - 5)
pdf.ln(65)

pdf.section_title("5.3.1 Contracting Triangle (most common)")
pdf.body_text(
    "The most frequent triangle type. Each successive wave is smaller than the previous one (A > B > C > D > E). "
    "Boundary lines converge toward an apex. "
    "Types of contracting triangles based on boundary slopes:"
)
pdf.bullet("Ascending: Upper boundary flat, lower boundary rising")
pdf.bullet("Descending: Upper boundary falling, lower boundary flat")
pdf.bullet("Symmetrical: Both boundaries converging (most common)")

pdf.section_title("5.3.2 Expanding Triangle (rare)")
pdf.body_text(
    "Also called a 'reverse triangle'. Each successive wave is larger (A < B < C < D < E). "
    "Boundary lines diverge. This pattern is rare and typically signals extreme volatility "
    "and emotional trading. It is usually followed by a relatively weak thrust."

)

pdf.section_title("5.3.3 Neutral Triangle")
pdf.body_text(
    "The boundary lines are parallel (one flat, one sloping or both sloping same direction). "
    "This creates a channel-like correction. It behaves similarly to a contracting triangle "
    "but is less predictable in its breakout thrust."

)

pdf.section_title("5.3.4 Triangle Trading Guidelines")
pdf.body_text(
    "1. The triangle must have exactly 5 waves (A-B-C-D-E). Never 3 or 7.\n"
    "2. Each leg is a 3-wave pattern (zigzag, flat, or another triangle).\n"
    "3. Wave E may exceed the A-C trendline (this is called a 'throwover') or fall short.\n"
    "4. The breakout should occur between 75-100% of the distance to the apex.\n"
    "5. The minimum price target after breakout = the widest part of the triangle (height at Wave A).\n"
    "6. Volume typically declines through the triangle, then expands on the breakout."
)

pdf.section_title("5.4 Double and Triple Threes")
pdf.body_text(
    "When a single correction pattern is insufficient, the market forms combinations: two corrective patterns "
    "connected by an X-wave (Double Three) or three patterns connected by two X-waves (Triple Three). "
    "These are sideways, time-consuming corrections that frustrate traders."
)

# =========== SECTION 6: WAVE DEGREES ===========
pdf.add_page()
pdf.chapter_title("6. Wave Degrees and Nesting")
pdf.body_text(
    "Elliott identified 9 degrees of waves, from the smallest to the largest. Each degree has its own labeling convention:"
)
pdf.draw_wave_degrees(pdf.l_margin, pdf.get_y(), pdf.w - 2 * pdf.l_margin)
pdf.ln(50)
pdf.body_text(
    "The practical implication: a 'Wave 1' on a daily chart might itself be a complete 5-wave impulse on an hourly chart. "
    "Always start your analysis on the higher timeframe first, then zoom in to lower timeframes for entries."
)

# =========== SECTION 7: THREE HARD RULES ===========
pdf.add_page()
pdf.chapter_title("7. The Three Hard Rules")
pdf.body_text(
    "These rules are mandatory. Violating any of them means the wave count is invalid:"
)
pdf.ln(2)
pdf.draw_rules_table(pdf.l_margin, pdf.get_y(), pdf.w - 2 * pdf.l_margin)
pdf.ln(30)
pdf.body_text(
    "Note: 'Wave 3 is never the shortest' means it cannot be the shortest among waves 1, 3, and 5. "
    "Waves 1 and 5 can be shorter than each other, but Wave 3 must be longer than at least one of them."
)
pdf.body_text(
    "Overlap rule: Wave 4 cannot enter the price territory of Wave 1 (closing prices for daily). "
    "The only exception is in diagonal waves, where overlap is permitted."
)

# =========== SECTION 8: GUIDELINES ===========
pdf.add_page()
pdf.chapter_title("8. Guidelines and Typical Behavior")
pdf.body_text(
    "These are not mandatory rules but probabilistic observations that improve counting accuracy:"
)
pdf.draw_guidelines_table(pdf.l_margin, pdf.get_y(), pdf.w - 2 * pdf.l_margin)
pdf.ln(35)
pdf.section_title("Volume Guidelines")
pdf.bullet("Wave 3 typically has the highest volume and widest price range")
pdf.bullet("Wave 5 shows declining volume and momentum divergence")
pdf.bullet("Wave A often starts with increasing volume as the correction begins")
pdf.bullet("Wave C frequently matches Wave A in volume or shows capitulation")

pdf.section_title("Wave Personality")
pdf.bullet("Wave 1: Often the most deceptive; many mistake it for a counter-trend bounce")
pdf.bullet("Wave 3: The strongest, most extended; the 'sweet spot' for traders")
pdf.bullet("Wave 5: Weaker momentum; divergences appear; final leg before a reversal")
pdf.bullet("Wave A: Initially looks like a pullback within the prior trend")
pdf.bullet("Wave B: 'The sucker's rally' -- traps bulls expecting a resumption of trend")
pdf.bullet("Wave C: Panic/despair; often equals Wave A in length")

# =========== SECTION 9: FIBONACCI ===========
pdf.add_page()
pdf.chapter_title("9. Fibonacci Relationships in Elliott Wave")
pdf.body_text(
    "Elliott Wave and Fibonacci ratios are deeply connected. The Fibonacci sequence (0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55...) "
    "and its key ratios (0.382, 0.500, 0.618, 0.786, 1.272, 1.618, 2.618) define the proportional relationships between waves."
)
pdf.section_title("9.1 Retracement Levels")
pdf.body_text(
    "Wave 2 typically retraces 50% to 61.8% of Wave 1.\n"
    "Wave 4 typically retraces 38.2% of Wave 3 (rarely more than 50%).\n"
    "Wave B typically retraces 38.2% to 78.6% of Wave A.\n"
    "Wave X in double/triple threes: 50% to 61.8% retracement of the preceding pattern."
)
pdf.draw_fibonacci_retrace(pdf.l_margin + 5, pdf.get_y(), pdf.w - 2 * pdf.l_margin - 5)
pdf.ln(60)

pdf.section_title("9.2 Extension Levels")
pdf.body_text(
    "Wave 3 often extends to 161.8% to 261.8% of Wave 1.\n"
    "Wave 5 is commonly 61.8% to 161.8% of the distance from Wave 1 low to Wave 3 high (net).\n"
    "Wave C often equals 100% or 161.8% of Wave A.\n"
    "When Wave 3 is extended, Waves 1 and 5 tend to be approximately equal."
)
pdf.draw_fibonacci_extensions(pdf.l_margin + 5, pdf.get_y(), pdf.w - 2 * pdf.l_margin - 5)

# =========== SECTION 10: CHANNELING ===========
pdf.add_page()
pdf.chapter_title("10. Channeling Technique")
pdf.body_text(
    "Elliott Wave channels help confirm the wave count and project price targets. "
    "To draw channels:"
)
pdf.bullet("In an impulse: draw a line connecting the ends of Waves 2 and 4 (lower channel line), "
           "then draw a parallel line touching the top of Wave 3 (upper channel line)")
pdf.bullet("Wave 5 often ends near the upper channel line")
pdf.bullet("If Wave 3 is exceptionally strong, draw a parallel line touching Wave 1's top instead")
pdf.ln(2)
pdf.draw_channel(pdf.l_margin + 10, pdf.get_y(), pdf.w - 2 * pdf.l_margin - 10)
pdf.ln(35)
pdf.body_text(
    "Channeling also applies to corrections: connect Waves A and C or use the trendline of the preceding impulse."
)

# =========== SECTION 11: ALTERNATION ===========
pdf.add_page()
pdf.chapter_title("11. Rule of Alternation")
pdf.body_text(
    "The guideline of alternation states that Wave 2 and Wave 4 of an impulse will alternate in form:"
)
pdf.bullet("If Wave 2 is a sharp correction (zigzag), Wave 4 is likely a sideways correction (flat, triangle)")
pdf.bullet("If Wave 2 is sideways, Wave 4 is likely sharp")
pdf.bullet("Alternation also applies to corrections: if Wave A is a 5-wave zigzag, Wave B is likely a 3-wave flat")
pdf.ln(2)
pdf.draw_rule_of_alternation(pdf.l_margin + 10, pdf.get_y(), pdf.w - 2 * pdf.l_margin - 10)
pdf.ln(45)
pdf.body_text(
    "Alternation is probabilistic, not deterministic. However, when both Wave 2 and Wave 4 are similar in form, "
    "it often indicates a more complex corrective structure is unfolding."
)

# =========== SECTION 12: COMMON MISTAKES ===========
pdf.add_page()
pdf.chapter_title("12. Common Counting Mistakes")
pdf.body_text("Even experienced analysts make these errors. Avoid them:")

pdf.section_title("Mistake 1: Forcing the Count")
pdf.body_text(
    "The most common mistake. If the price action doesn't clearly fit a wave structure, don't force it. "
    "Sometimes the market is in a 'complex correction' or a 'failure' (truncated 5th wave)."
)
pdf.section_title("Mistake 2: Ignoring the Higher Timeframe")
pdf.body_text(
    "Always establish the larger trend first. A 'Wave 3' on a 15-minute chart might just be a Wave C of a "
    "larger correction on the hourly chart."
)
pdf.section_title("Mistake 3: Misidentifying Corrective Patterns")
pdf.body_text(
    "Corrective waves are notoriously tricky. A flat pattern (3-3-5) can look very similar to a zigzag (5-3-5). "
    "Look at the internal structure of Wave A to distinguish them."
)
pdf.section_title("Mistake 4: Overlapping in Impulse Waves")
pdf.body_text(
    "If Wave 4 overlaps Wave 1, it cannot be an impulse. Re-label as a diagonal or a corrective pattern."
)
pdf.section_title("Mistake 5: Using Only Elliott Wave")
pdf.body_text(
    "No method is 100% accurate. Combine Elliott Wave with support/resistance, volume, RSI/MACD divergences, "
    "and candlestick patterns for confirmation."
)

# =========== SECTION 13: PRACTICAL WORKFLOW ===========
pdf.add_page()
pdf.chapter_title("13. Practical Application Workflow")
pdf.body_text("Step-by-step approach to analyzing any market:")

pdf.set_font("Helvetica", "B", 10)
pdf.set_text_color(20, 60, 120)
steps = [
    ("Step 1: Higher Timeframe Analysis",
     "Start with weekly/monthly charts to identify the dominant trend and major waves."),
    ("Step 2: Daily Chart Structure",
     "Label the current position within the larger trend. Is this Wave 3 of a larger impulse? Wave C of a correction?"),
    ("Step 3: Validate with Rules",
     "Check the three hard rules. Measure Fibonacci retracements and extensions. Draw channels."),
    ("Step 4: Drop to Lower Timeframes",
     "Use 4H/1H charts to see the internal structure of the current wave. Identify entry zones on Wave 2 or Wave 4 completions."),
    ("Step 5: Confluence",
     "Look for confluence: Fibonacci levels, support/resistance, divergence on RSI/MACD, volume patterns."),
    ("Step 6: Plan the Trade",
     "Entry: After Wave 2 completes (for Wave 3), or after Wave 4 completes (for Wave 5). "
     "Stop: Below Wave 1 low (for a Wave 3 entry) or below Wave 4 low. "
     "Target: Fibonacci extensions of the prior wave."),
    ("Step 7: Manage and Review",
     "Monitor the count as price develops. Be willing to adjust. Keep a trading journal."),
]
for title, desc in steps:
    pdf.cell(0, 6, f"  {title}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(60)
    pdf.multi_cell(0, 5, f"     {desc}")
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(20, 60, 120)

# =========== SECTION 14: ADVANCED CONCEPTS ===========
pdf.add_page()
pdf.chapter_title("14. Advanced Concepts")

pdf.section_title("14.1 Truncated Fifth (Failure)")
pdf.body_text(
    "When Wave 5 fails to exceed the high of Wave 3. This is a strong reversal signal, often seen at the end "
    "of a larger trend. It indicates that the trend has exhausted prematurely."
)

pdf.section_title("14.2 Extended Waves")
pdf.body_text(
    "An extension is a wave that is significantly longer than the other waves. Wave 3 is most commonly extended. "
    "When an extension occurs, the sub-waves of the extended wave have similar magnitude to the non-extended waves. "
    "Extensions suggest strong momentum and trend continuation."
)

pdf.section_title("14.3 Running Corrections")
pdf.body_text(
    "A correction that fails to retrace deeply before resuming the trend. For example, a running flat where "
    "Wave B makes a new high (in a bull market) and Wave C barely retraces. This signals exceptional strength."
)

pdf.section_title("14.4 Irregular Corrections")
pdf.body_text(
    "When Wave B exceeds the start of Wave A (making a new high in a bull correction or new low in a bear correction). "
    "These indicate strong underlying momentum in the direction of the larger trend."
)

pdf.section_title("14.5 Fibonacci Time Zones")
pdf.body_text(
    "Fibonacci ratios can also be applied to time. Common timing relationships:\n"
    "- The time from Wave 1 start to Wave 3 end: 61.8% of total impulse time\n"
    "- Wave 2 and Wave 4 often take similar amounts of time\n"
    "- Corrective waves (A-B-C) often take 1.618x the time of the preceding impulse"
)

pdf.section_title("14.6 Multiple Timeframe Analysis (MTF)")
pdf.body_text(
    "The most reliable setups occur when waves align across multiple degrees:\n"
    "- Higher timeframe: clear 5-wave structure completed (e.g., weekly Wave C)\n"
    "- Medium timeframe: Wave 2 or Wave 4 just completed (e.g., daily)\n"
    "- Entry timeframe: sub-wave 2 of Wave 3 completed with a reversal pattern (e.g., 4H)"
)

# =========== SECTION 15: CHEAT SHEET ===========
pdf.add_page()
pdf.chapter_title("15. Summary Cheat Sheet")
pdf.ln(2)

pdf.section_title("Three Hard Rules")
pdf.set_font("Helvetica", "", 9)
pdf.set_text_color(30)
pdf.cell(0, 5, "  1. Wave 2 cannot retrace more than 100% of Wave 1", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  2. Wave 3 is never the shortest of Waves 1, 3, and 5", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  3. Wave 4 cannot overlap Wave 1 price territory", new_x="LMARGIN", new_y="NEXT")
pdf.ln(3)

pdf.section_title("Wave Labels by Degree")
pdf.set_font("Helvetica", "", 9)
pdf.set_text_color(30)
pdf.cell(0, 5, "  Grand Supercycle: [I] [II] [III] [IV] [V] + [A] [B] [C]", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Supercycle: (I) (II) (III) (IV) (V) + (A) (B) (C)", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Cycle: I II III IV V + A B C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Primary: [1] [2] [3] [4] [5] + [a] [b] [c]", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Intermediate: (1) (2) (3) (4) (5) + (a) (b) (c)", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Minor: 1 2 3 4 5 + a b c", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Minute: i ii iii iv v + a b c", new_x="LMARGIN", new_y="NEXT")
pdf.ln(3)

pdf.section_title("Fibonacci Quick Reference")
pdf.set_font("Helvetica", "", 9)
pdf.set_text_color(30)
pdf.cell(0, 5, "  Wave 2 retracement: 50-61.8% of Wave 1", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Wave 3 extension: 161.8-261.8% of Wave 1", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Wave 4 retracement: 38.2% (max 50%) of Wave 3", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Wave 5 target: 61.8-161.8% of Wave 1 (or 0-1 channel)", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Wave C: 100% or 161.8% of Wave A", new_x="LMARGIN", new_y="NEXT")
pdf.ln(3)

pdf.section_title("Corrective Pattern Quick Guide")
pdf.set_font("Helvetica", "", 9)
pdf.set_text_color(30)
pdf.cell(0, 5, "  Zigzag (5-3-5): Sharp, steep, Wave A is 5 waves", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Flat (3-3-5): Sideways, Wave A is 3 waves", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Triangle (3-3-3-3-3): Contracting/expanding, 5 legs", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Double Three: Two corrective patterns + X wave", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Triple Three: Three corrective patterns + 2 X waves", new_x="LMARGIN", new_y="NEXT")
pdf.ln(3)

pdf.section_title("Common Divergence Signals")
pdf.set_font("Helvetica", "", 9)
pdf.set_text_color(30)
pdf.cell(0, 5, "  Wave 3 vs Wave 5: RSI/MACD bearish divergence = trend exhaustion", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Wave C vs Wave A: RSI/MACD bullish divergence = trend reversal", new_x="LMARGIN", new_y="NEXT")
pdf.ln(3)

pdf.section_title("Trading Plan Template")
pdf.set_font("Helvetica", "", 9)
pdf.set_text_color(30)
pdf.cell(0, 5, "  Trend: [Up / Down / Sideways]", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Current Wave: [1/2/3/4/5/A/B/C]", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Entry Zone: [After Wave 2 complete / After Wave 4 complete]", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Stop Loss: [Below Wave 1 low / Below Wave 4 low]", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Target 1: [Fib extension level]", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Target 2: [Channel upper line / next Fib level]", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 5, "  Confirmation: [Divergence / Support-Resistance / Volume]", new_x="LMARGIN", new_y="NEXT")

# =========== FINAL NOTE ===========
pdf.ln(8)
pdf.set_draw_color(20, 60, 120)
pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
pdf.ln(5)
pdf.set_font("Helvetica", "I", 9)
pdf.set_text_color(100)
pdf.multi_cell(0, 5,
    "Final Note: Elliott Wave Theory is a powerful framework, but it is not a crystal ball. "
    "Always practice proper risk management. The market is the ultimate judge of the count. "
    "When in doubt, assume the market is in a correction. Most complex corrections are misidentified as new trends."
)

# Save
output_path = "D:\\VIBE_CODE\\Crypto_Analysis_AI\\Elliott_Wave_Theory_Complete_Tutorial.pdf"
pdf.output(output_path)
print(f"PDF saved to: {output_path}")
print(f"Total pages: {pdf.page_no()}")
