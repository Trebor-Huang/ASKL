import msvcrt, os
import random
import time
import threading, ctypes

import malody, winsound

class COORD(ctypes.Structure):
	 _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)] 
	 def __init__(self,x,y):
		 self.X = x
		 self.Y = y
input("Ready? (Resize the window)")
TERMCOL, TERMLINES = os.get_terminal_size()
LINES = TERMLINES - 7
LWIDTH = (TERMCOL-2)//2
RWIDTH = TERMCOL - LWIDTH - 4

OFFSET = -0.63  # the larger this is, the later the chart appears

class KeyboardReader (threading.Thread):
    def __init__(self):
        super().__init__()
        self.buffer = []
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            c = msvcrt.getch()
            self.buffer.append((time.time(),c))
            
STD_OUTPUT_HANDLE= -11
hOut = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
def move(x, y):
    ctypes.windll.kernel32.SetConsoleCursorPosition(hOut,COORD(x,y))

keyscode = {b"c":0, b"v":1, b"b":2, b"n":3,
            b"d":0, b"f":1, b"j":2, b"k":3}
key_seqs = [
    [0,1,3,2],
    [0,1,2,3],
    [1,0,2,3]
]

def rand_keys():
    mode = 0
    tpos = 2.
    while True:
        if mode == 0:
            prob_knockout = 0
            for i in range(16):
                prob_knockout = 0.6 - prob_knockout
                if random.random() >= prob_knockout:
                    yield tpos, random.randint(0,3)
                tpos += 0.2
        if mode == 1:
            i, j=random.choices([0,1,2,3], k=2)
            i, j = max(i,j), min(i,j)
            for _ in range(2*random.randint(2,8)):
                yield tpos, i
                yield tpos + 0.1, j
                tpos += 0.2
        if mode == 2:
            i, j=random.choices([0,1,2,3], k=2)
            if i == j:
                continue
            for _ in range(2*random.randint(2,4)):
                yield tpos, i
                yield tpos, j
                tpos += 0.2
        if mode == 3:
            key_reversed = random.randint(0,1)
            chosen_seq = random.choice(key_seqs)
            for _ in range(4):
                for k in chosen_seq:
                    yield tpos, (k if key_reversed else 3-k)
                    tpos += 0.05
        mode = random.choice([0,1,2,3])

GREAT_RANGE = 0.10
PERFECT_RANGE = 0.07
EARLY_MISS_RANGE = 0.15

CHART_SPEED = 35 # row per second

def calculate_chart(chart, tpos):
    # chart = [(time, key), ...]
    # tpos = t_now - t_start
    chart_pos = []
    for t, k in chart:
        pos = int((t-tpos) * CHART_SPEED - 0.)
        if pos >= LINES-3 or pos < -3:
            continue
        chart_pos.append((pos, k))
    return chart_pos # TODO: make it smarter? it may include a speed change function

def show_chart(chart_pos):
    ch = [["    "]*4 for _ in range(LINES)]
    for pos, k in chart_pos:
        if ch[pos+3][k] == "    ":
            ch[pos+3][k] = "****"
        else:
            ch[pos+3][k] = "$$$$"
    ch_raws = [("|" + "  ".join(chrow) + "|").center(TERMCOL-1) for chrow in ch[::-1]]
    ch_raws[-4] = ("-" + ch_raws[-4].strip().replace(" ", "-") + "-").center(TERMCOL-1)
    ch_raw = "\n".join(ch_raws)
    return ch_raw

def print_chart(chart, tpos):
    move(0,0)
    print(show_chart(calculate_chart(chart, tpos)))

RESULTS =  [" LATE MISS       ",
            " EARLY MISS ",
            " GREAT      ",
            " PERFECT    "]
def cls():
    move(0,0)
    print((" " * (TERMCOL-1) + "\n")*TERMLINES)

def game():
    # keys = rand_keys()
    # chart = [next(keys) for _ in range(400)]  # chart must have a shallow copy!
    chart, song = malody.read_malody()
    total_keys = len(chart)
    maxtime = max(map(lambda t:t[0], chart)) + 1
    score = 0
    combo = 0
    maxcombo = 0
    perfect_count = 0
    great_count = 0
    miss_count = 0
    kbbf = KeyboardReader()
    kbbf.start()
    cls()
    t0 = time.time() + OFFSET
    res = -1
    tdiff = 0.
    # os.system(r'''start C:\Users\Administrator\Desktop\dfjk\song.wav''')
    winsound.PlaySound("song.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
    while True:
        tpos = time.time() - t0
        for t_key, k in chart:
            if t_key - tpos < - GREAT_RANGE:
                # LATE_MISS 0
                res = 0
                combo = 0
                miss_count += 1
                chart.remove((t_key, k))
        chart_available = filter(lambda t: t[0] - tpos <= EARLY_MISS_RANGE, chart)
        if tpos <= maxtime:
            if len(kbbf.buffer) > 0:
                t, kg = kbbf.buffer.pop(0)
                if kg in keyscode:
                    for t_key, k in chart_available:
                        if k != keyscode[kg]:
                            continue
                        # format(int((t_key-tpos) * 1000), "+4d"
                        if abs(t_key - tpos) <= PERFECT_RANGE:
                            # PERFECT 3
                            # print("\n PERFECT    ", end = "")
                            res, tdiff = (3,t_key-tpos)
                            score += 1
                            combo += 1
                            perfect_count += 1
                        elif abs (t_key - tpos) <= GREAT_RANGE:
                            # GREAT 2
                            # print("\n GREAT      ", end = "")
                            res, tdiff = (2,t_key-tpos)
                            score += 0.7
                            combo += 1
                            great_count += 1
                        elif 0 < t_key - tpos <= EARLY_MISS_RANGE:
                            # EARLY_MISS 1
                            # print("\n EARLY MISS ", end = "")
                            res, tdiff = (1,t_key-tpos)
                            combo = 0
                            miss_count += 1
                        else:
                            continue
                        chart.remove((t_key, k))
                        break
            maxcombo = max(maxcombo, combo)
            print_chart(chart, tpos)
            if res == -1:
                pass
            elif res == 0:
                print(RESULTS[0], "Combo:", format(combo, "5d"),
                      "ACC:", format(score/(perfect_count + great_count + miss_count), "7.2%"))
            else:
                print(RESULTS[res], format(int(tdiff * 1000), "+4d"), "Combo:", format(combo, "5d"),
                      "ACC:", format(score/(perfect_count + great_count + miss_count), "7.2%"))
        else:
            cls()
            print_chart([], 0.)
            move(0, LINES + 1)
            print("Score".rjust(LWIDTH), ":", str(int(1000000 * score/total_keys)).ljust(RWIDTH))
            print("Perfect".rjust(LWIDTH), ":", str(perfect_count).ljust(RWIDTH))
            print("Great".rjust(LWIDTH), ":", str(great_count).ljust(RWIDTH))
            print("Miss".rjust(LWIDTH), ":", str(miss_count).ljust(RWIDTH))
            print("Max Combo".rjust(LWIDTH), ":", str(maxcombo).ljust(RWIDTH))
            kbbf.running = False
            return
    kbbf.running = False

game()
input()

