import tkinter as tk
import time, winsound
import malody
import math

# autorepeat on linux: os.system('xset r off')

# chart: a list of (key_type, key_rail, time...)
# speed_raw: a list of (t0, beat, speed_factor)

# TODO
# - automated color mixer
# - choose songs
# - osu charts
# - pause?
# - view replay

AUTO = False
CHART_WIDTH = 350
HEIGHT = 700
WIDTH = 1200
MISS_HEIGHT = 50
KEY_HEIGHT = 40

GREAT_RANGE = 0.10
PERFECT_RANGE = 0.08
EARLY_MISS_RANGE = 0.11

OFFSET = 0.0 # the larger the offset is, the earlier the music appears

CHART_SPEED = 1500 # pixel per second
CHART_OFFSET = 0  # the larger the offset is, the further the chart moves upwards

HISTOGRAM_WIDTH = 10
HISTOGRAM_COLOR = "#212140"
HISTOGRAM_MAX = 150

BG_COLOR = "#1F1E33"
BG_MISSED_COLOR = ["#201E30", "#2E1425", "#3A0A19"]
MAXLEVEL = 2

KEYPRESS_COLOR = "#ADC"
PERFECT_COLOR = "#DFD"
GREAT_COLOR = "#EE5"
EARLY_MISS_COLOR = "#C23"

NOTE_COLOR = "#FFF"
HOLD_COLOR = "#99D9EA"
HOLDING_COLOR = "#28A5C4"
GREAT_HOLD_COLOR = "#CC1"
MISSED_HOLD_COLOR = "#555"
RES_COLOR = "#2C5"
LINE_COLOR = "#FFF"

KEY_ID = {
    "d":0, "e":0, "a":0,
    "f":1, "s":1,
    "j":2,
    "k":2, "o":3, "l":3,
}


RESULTS =  ["LATE MISS       ",
            "EARLY MISS ",
            "GREAT      ",
            "PERFECT    "]

class AutoKeyboardEvent:
    def __init__(self, ch):
        self.char = ch

class ChartDisplayer(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.hold = []
        self.create_widgets()
        self.histogram = {
            k:0
            for k in range(
                math.floor((-GREAT_RANGE*1000)/HISTOGRAM_WIDTH),
                math.floor((EARLY_MISS_RANGE)*1000/HISTOGRAM_WIDTH)+1
            )
        }
        self.logic_init()


    def chart_remove(self, cind):
        self.chart[cind] = (-1,)
        self.chart_pos[cind] = (-1,)
        self.canvas.delete(self.chart_id[cind])
        self.chart_id[cind] = -1
        
    @staticmethod
    def calculate_position(tpos, speed):
        return CHART_SPEED * tpos
        i = 0
        for i in range(len(speed)-1):
            if tpos < speed[i+1][0]:
                return CHART_SPEED * (tpos - speed[i][0]) * speed[i][2] + speed[i][1]
        return CHART_SPEED * (tpos - speed[i][0]) * speed[i][2] + speed[i][1]
        

    @staticmethod
    def calculate_key(c, speed):
        if c[0] == 0:
            return (0, c[1],
                    ChartDisplayer.calculate_position(c[2] + CHART_OFFSET, speed))
        elif c[0] == 1 or c[0] == 2 or c[0] == 3:
            return (c[0], c[1],
                    ChartDisplayer.calculate_position(c[2] + CHART_OFFSET, speed),
                    ChartDisplayer.calculate_position(c[3] + CHART_OFFSET, speed))
        else:
            return (-1,)
    
    @staticmethod
    def calculate_chart(chart, speed_raw):
        speed = []
        x0 = 0.
        for i in range(len(speed_raw)-1):
            speed.append((speed_raw[i][0], x0, speed_raw[i][2]))
            x0 += (speed_raw[i+1][0] - speed_raw[i][0]) * CHART_SPEED * speed_raw[i][2]
        speed.append((speed_raw[-1][0], x0, speed_raw[-1][2]))
        return speed, [ChartDisplayer.calculate_key(c, speed) for c in chart]

    def create_note(self, c):
        if c[0] == 0:
            return self.canvas.create_rectangle(
                (WIDTH-CHART_WIDTH)/2 + c[1]/4 * CHART_WIDTH,
                HEIGHT - c[2] - MISS_HEIGHT,
                (WIDTH-CHART_WIDTH)/2 + (c[1]+1)/4 * CHART_WIDTH,
                HEIGHT - c[2] - KEY_HEIGHT - MISS_HEIGHT,
                fill = NOTE_COLOR,
                outline = "",
                state = "hidden"
            )
        elif c[0] == 1:
            return self.canvas.create_rectangle(
                (WIDTH-CHART_WIDTH)/2 + c[1]/4 * CHART_WIDTH,
                HEIGHT - c[2] - MISS_HEIGHT,
                (WIDTH-CHART_WIDTH)/2 + (c[1]+1)/4 * CHART_WIDTH,
                HEIGHT - c[3] - MISS_HEIGHT,
                fill = HOLD_COLOR,
                outline = LINE_COLOR,
                state = "hidden"
            )
        else:
            return -1
        
    def show_chart(self):
        self.speed, self.chart_pos = ChartDisplayer.calculate_chart(self.chart, self.speed_raw)
        self.chart_id = [
            self.create_note(c)
            for c in self.chart_pos
        ]

    def move_note(self, tpos, ni):
        c = self.chart[ni]
        i = self.chart_id[ni]
        cpos_current = self.calculate_key(c, self.speed)
        t_pos = self.calculate_position(tpos, self.speed)
        if cpos_current[0] == 0:
            actual_pos = HEIGHT - cpos_current[2] + t_pos - KEY_HEIGHT - MISS_HEIGHT
            gst = self.canvas.itemcget(i, "state")
            if -KEY_HEIGHT < actual_pos < HEIGHT:
                self.canvas.moveto(i, "", actual_pos)
                if gst != "normal":
                    self.canvas.itemconfig(i, state="normal")
            elif gst == "normal":
                self.canvas.itemconfig(i, state="hidden")
        elif cpos_current[0] == 1:
            actual_pos1 = HEIGHT - cpos_current[2] + t_pos - MISS_HEIGHT
            actual_pos2 = HEIGHT - cpos_current[3] + t_pos - MISS_HEIGHT
            gst = self.canvas.itemcget(i, "state")
            if 0 < max(actual_pos1, actual_pos2) or\
               min(actual_pos1, actual_pos2) < HEIGHT:
                self.canvas.moveto(i, "", min(actual_pos1, actual_pos2))
                if gst != "normal":
                    self.canvas.itemconfig(i, state="normal")
            elif gst == "normal":
                self.canvas.itemconfig(i, state="hidden")
        elif cpos_current[0] == 2 or cpos_current[0] == 3:
            actual_pos1 = HEIGHT - cpos_current[2] + t_pos - MISS_HEIGHT
            actual_pos2 = HEIGHT - cpos_current[3] + t_pos - MISS_HEIGHT
            if min(actual_pos1, actual_pos2) < HEIGHT - MISS_HEIGHT:
                self.canvas.coords(
                    i,
                    (
                        (WIDTH-CHART_WIDTH)/2 + c[1]/4 * CHART_WIDTH,
                        min(actual_pos1, actual_pos2),
                        (WIDTH-CHART_WIDTH)/2 + (c[1]+1)/4 * CHART_WIDTH,
                        HEIGHT-MISS_HEIGHT
                    )
                )
                self.canvas.itemconfig(i, state="normal")
            elif self.canvas.itemcget(i, "state") == "normal":
                self.chart_remove(ni)

    def move_chart(self, tpos):
        for ni in range(len(self.chart_pos)):
            self.move_note(tpos, ni)

    def logic_init(self):
        self.chart, song, self.speed_raw = malody.read_malody()
        print(self.speed_raw)
        self.show_chart()
        self.canvas.tag_raise(self.combo_display, "all")
        self.total_keys = len(self.chart)
        self.maxtime = max(map(lambda t:t[-1], self.chart)) + 1
        self.score = 0.
        self.combo = 0
        self.maxcombo = 0
        self.perfect_count = 0
        self.great_count = 0
        self.miss_count = 0
        self.t0 = time.time() + OFFSET

    def _canvas_bg_callback(self, level=MAXLEVEL):
        if level == -1:
            self.canvas["bg"] = BG_COLOR
        else:
            self.canvas["bg"] = BG_MISSED_COLOR[level]
            if level == MAXLEVEL:
                self.after("cancel", self._canvas_bg_callback)
            self.after(50, self._canvas_bg_callback, level-1)

    def show_results(self, res, tdiff=0):
        self.canvas.itemconfig(
            self.score_display,
            text= format(int(100000000 * self.score / self.total_keys), "09d")
        )
        if self.combo == 0:
            self._canvas_bg_callback()
        if self.combo > 1:
            self.canvas.itemconfig(
                self.combo_display,
                text = str(self.combo)
            )
        else:
            self.canvas.itemconfig(
                self.combo_display,
                text = ""
            )
        kcount = self.perfect_count + self.great_count + self.miss_count
        acc = format(self.score/kcount if kcount > 0 else 0., "7.2%")
        if res == 0:
            self.canvas.itemconfig(
                self.result_display,
                text="%s\nACC: %s" % (RESULTS[0], acc)
                )
        elif res == -1:
            self.canvas.itemconfig(
                self.result_display,
                text="\nACC: %s" % acc
            )
        else:
            self.canvas.itemconfig(
                self.result_display,
                text="%s %+4d\nACC: %s" % (RESULTS[res], int(tdiff * 1000), acc)
                )
    
    def logic(self):
        tpos = time.time() - self.t0
        #if self.kps_rec:
        #    while tpos - self.kps_rec[0] > CUTOFF:
        #        self.kps_rec.pop(0)
        #kps = sum(ADSR(tpos - tt) for tt in self.kps_rec)
        #self.canvas.itemconfig(self.stats_display,
        #                       text = "KPS : %4.1f" % kps)
        # Late Miss logic
        for cind, c in enumerate(self.chart):
            if c[0] == 0:
                if AUTO and c[2] - tpos <= 0:
                    key_chr = next(j for j in KEY_ID if KEY_ID[j] == c[1])
                    self.press(AutoKeyboardEvent(key_chr), c[2] + self.t0)
                    self.release(AutoKeyboardEvent(key_chr))
                if c[2] - tpos < - GREAT_RANGE:
                    # LATE_MISS 0
                    self.combo = 0
                    self.miss_count += 1
                    self.chart_remove(cind)
                    self.show_results(0)
            elif c[0] == 1:
                if AUTO and c[2] - tpos <= 0:
                    key_chr = next(j for j in KEY_ID if KEY_ID[j] == c[1])
                    self.press(AutoKeyboardEvent(key_chr), c[2] + self.t0)
                if c[2] - tpos < - GREAT_RANGE\
                     and self.canvas.itemcget(self.chart_id[cind], "outline") == LINE_COLOR:
                    # Late Miss
                    self.miss_count += 1
                    self.combo = 0
                    self.canvas.itemconfig(
                        self.chart_id[cind],
                        fill=MISSED_HOLD_COLOR,
                        outline=""
                    )
                    self.show_results(0)
            # Hold logic
            elif c[0] == 2:
                if AUTO and c[3] - tpos <= 0:
                    key_chr = next(j for j in KEY_ID if KEY_ID[j] == c[1])
                    self.release(AutoKeyboardEvent(key_chr))
                    self.chart_remove(cind)
                if c[2] - GREAT_RANGE <= tpos <= c[3] - PERFECT_RANGE:
                    # Check if you are holding
                    if c[1] not in (KEY_ID[h] for h in self.hold):
                        # HOLD - BROKEN
                        self.combo = 0
                        self.chart[cind] = 3, *self.chart[cind][1:]
                        self.chart_pos[cind] = 3, *self.chart_pos[cind][1:]
                        self.canvas.itemconfig(
                            self.chart_id[cind],
                            fill=MISSED_HOLD_COLOR,
                            outline=""
                        )
                        self.show_results(-1)
                    
        if tpos <= self.maxtime:
            self.move_chart(tpos)
            self.after_idle(self.logic)
        else:
            #     Score : 000000000
            #   Perfect : 000000000
            #     Great : 000000000
            #      Miss : 000000000
            # Max Combo : 000000000
            result_string = "    Score : %09d\n  Perfect : %9d\n    Great : %9d\n     Miss : %9d\nMax Combo : %9d" %\
              (int(100000000 * self.score / self.total_keys),
               self.perfect_count,
               self.great_count,
               self.miss_count,
               self.maxcombo)
            self.canvas.delete(tk.ALL)
            
            # start drawing histogram
            BAR_WIDTH = WIDTH * 0.95 / len(self.histogram)
            MAX_STATS = max(self.histogram[i] for i in self.histogram)
            if MAX_STATS == 0:
                MAX_STATS = 1
            for i, k in enumerate(self.histogram):
                self.canvas.create_rectangle(
                    0.025 * WIDTH + BAR_WIDTH * i,
                    HEIGHT,
                    0.025 * WIDTH + BAR_WIDTH * (i+1),
                    HEIGHT - self.histogram[k] * HISTOGRAM_MAX / MAX_STATS,
                    fill = HISTOGRAM_COLOR,
                    outline = LINE_COLOR
                )
                if k == 0:
                    self.canvas.create_line(
                        0.025 * WIDTH + BAR_WIDTH * i,
                        HEIGHT,
                        0.025 * WIDTH + BAR_WIDTH * i,
                        HEIGHT - 1.1 * HISTOGRAM_MAX,
                        fill = LINE_COLOR,
                        width = 3
                    )
            
            self.canvas.create_text(
                WIDTH/2, HEIGHT/2,
                font = "fixedsys 24",
                fill = RES_COLOR,
                text = result_string
            )
            return


    def create_widgets(self):
        self.canvas = tk.Canvas(self,
                                height = HEIGHT,
                                width = WIDTH,
                                bg = BG_COLOR)
        # self.canvas.create_image(0, 0, anchor="nw", image=bg)
        self.canvas.create_line((WIDTH-CHART_WIDTH)/2, 0,
                                (WIDTH-CHART_WIDTH)/2, HEIGHT, fill=LINE_COLOR)
        self.canvas.create_line((WIDTH-CHART_WIDTH/2)/2, 0,
                                (WIDTH-CHART_WIDTH/2)/2, HEIGHT, fill=LINE_COLOR)
        self.canvas.create_line(WIDTH/2, 0,
                                WIDTH/2, HEIGHT, fill=LINE_COLOR)
        self.canvas.create_line((WIDTH+CHART_WIDTH/2)/2, 0,
                                (WIDTH+CHART_WIDTH/2)/2, HEIGHT, fill=LINE_COLOR)
        self.canvas.create_line((WIDTH+CHART_WIDTH)/2, 0,
                                (WIDTH+CHART_WIDTH)/2, HEIGHT, fill=LINE_COLOR)
        self.result_display = self.canvas.create_text(
            10, HEIGHT - 10,
            font = "fixedsys",
            anchor = "sw",
            fill = RES_COLOR
        )
        self.score_display = self.canvas.create_text(
            10, 10,
            font = "fixedsys 24",
            anchor = "nw",
            fill = RES_COLOR,
            text = "000000000"
        )
        self.combo_display = self.canvas.create_text(
            WIDTH/2, HEIGHT/3,
            font = "fixedsys 36",
            fill = RES_COLOR
        )
        self.stats_display = self.canvas.create_text(
            WIDTH - 10, 10,
            font = "fixedsys",
            anchor = "ne",
            fill = RES_COLOR,
            text = "KPS : ---.-"
        )
        self.pressed_effect_id = []
        for i in range(4):
            self.pressed_effect_id.append(
                self.canvas.create_rectangle(
                    (WIDTH-CHART_WIDTH)/2 + i/4 * CHART_WIDTH,
                    HEIGHT-MISS_HEIGHT,
                    (WIDTH-CHART_WIDTH)/2 + (i+1)/4 * CHART_WIDTH,
                    HEIGHT-MISS_HEIGHT-KEY_HEIGHT,
                    fill = "",
                    outline = LINE_COLOR)
                )
            self.canvas.create_text(
                (WIDTH-CHART_WIDTH)/2 + (i+0.5)/4 * CHART_WIDTH,
                HEIGHT-MISS_HEIGHT-KEY_HEIGHT/2, font = "fixedsys",
                text = next(j for j in KEY_ID if KEY_ID[j] == i), fill = RES_COLOR
            )
        self.canvas.create_line(
            (WIDTH-1.3*CHART_WIDTH)/2, HEIGHT-MISS_HEIGHT,
            (WIDTH+1.3*CHART_WIDTH)/2, HEIGHT-MISS_HEIGHT,
            width = 3,
            fill=LINE_COLOR
        )
        self.canvas.pack()
        self.focus_set() # IMPORTANT
        if not AUTO:
            self.bind(sequence="<KeyPress>", func=self.press)
            self.bind(sequence="<KeyRelease>", func=self.release)
        self.master.resizable(0,0)

    def press(self, event, auto_time=None):
        if event.char == "`":
            global stop
            stop = False
            self.master.destroy()
        elif event.char in KEY_ID:
            tpos = (time.time() if auto_time is None else auto_time) - self.t0
            if event.char not in self.hold:
                self.hold.append(event.char)
                self.canvas.itemconfig(
                    self.pressed_effect_id[KEY_ID[event.char]],
                    fill = KEYPRESS_COLOR
                )
                # self.kps_rec.append(tpos)
                # Pressed logic
                key_id = KEY_ID[event.char]
                for cind, c in enumerate(self.chart):
                    if c[0] == -1 or key_id != c[1]:
                        continue
                    if c[0] == 0:
                        if abs(c[2] - tpos) <= PERFECT_RANGE:
                            self.score += 1
                            self.combo += 1
                            self.perfect_count += 1
                            self.canvas.itemconfig(
                                self.pressed_effect_id[key_id],
                                fill=PERFECT_COLOR
                            )
                            self.show_results(3,c[2]-tpos)
                        elif abs(c[2] - tpos) <= GREAT_RANGE:
                            self.score += 0.7
                            self.combo += 1
                            self.great_count += 1
                            self.canvas.itemconfig(
                                self.pressed_effect_id[key_id],
                                fill=GREAT_COLOR
                            )
                            self.show_results(2,c[2]-tpos)
                        elif 0 < c[2] - tpos <= EARLY_MISS_RANGE:
                            self.combo = 0
                            self.miss_count += 1
                            self.canvas.itemconfig(
                                self.pressed_effect_id[key_id],
                                fill=EARLY_MISS_COLOR
                            )
                            self.show_results(1,c[2]-tpos)
                        else:
                            continue
                        self.chart_remove(cind)
                        self.histogram[math.floor((c[2] - tpos)*1000/HISTOGRAM_WIDTH)] += 1
                        self.maxcombo = max(self.maxcombo, self.combo)
                        return
                    if c[0] == 1:
                        if abs(c[2] - tpos) <= PERFECT_RANGE:
                            self.score += 1
                            self.combo += 1
                            self.perfect_count += 1
                            self.show_results(3,c[2]-tpos)
                            self.chart[cind] = 2, *self.chart[cind][1:]
                            self.chart_pos[cind] = 2, *self.chart_pos[cind][1:]
                            self.canvas.itemconfig(
                                self.chart_id[cind],
                                fill=HOLDING_COLOR
                            )
                            self.canvas.itemconfig(
                                self.pressed_effect_id[key_id],
                                fill=PERFECT_COLOR
                            )
                        elif abs(c[2] - tpos) <= GREAT_RANGE:
                            self.score += 0.6
                            self.combo += 1
                            self.great_count += 1
                            self.show_results(2,c[2]-tpos)
                            self.chart[cind] = 2, *self.chart[cind][1:]
                            self.chart_pos[cind] = 2, *self.chart_pos[cind][1:]
                            self.canvas.itemconfig(
                                self.chart_id[cind],
                                fill=GREAT_HOLD_COLOR
                            )
                            self.canvas.itemconfig(
                                self.pressed_effect_id[key_id],
                                fill=GREAT_COLOR
                            )
                        elif 0 < c[2] - tpos <= EARLY_MISS_RANGE:
                            self.combo = 0
                            self.miss_count += 1
                            self.show_results(1,c[2]-tpos)
                            self.chart[cind] = 3, *self.chart[cind][1:]
                            self.chart_pos[cind] = 3, *self.chart_pos[cind][1:]
                            self.canvas.itemconfig(
                                self.chart_id[cind],
                                fill=MISSED_HOLD_COLOR,
                                outline=""
                            )
                            self.canvas.itemconfig(
                                self.pressed_effect_id[key_id],
                                fill=EARLY_MISS_COLOR
                            )
                        else:
                            continue
                        self.histogram[math.floor((c[2] - tpos)*1000/HISTOGRAM_WIDTH)] += 1
                        self.maxcombo = max(self.maxcombo, self.combo)
                        return

    def release(self, event, auto_time=None):
        if event.char in KEY_ID:
            self.hold.remove(event.char)
            self.canvas.itemconfig(
                self.pressed_effect_id[KEY_ID[event.char]],
                fill = ""
            )
CUTOFF = 2.0
def ADSR(t):
    return math.exp(-1.1*t)*1.1
stop = False
while not stop:
    stop = True
    root = tk.Tk()
    bg = tk.PhotoImage(file='bg.gif') # TODO write a bg import
    app = ChartDisplayer(master=root)
    root.title("DFJK")
    app.after(10, app.logic)
    winsound.PlaySound("song.wav", winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_PURGE)
    app.mainloop()
