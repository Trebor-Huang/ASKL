import json
def calc_time(speed_info, beat, subbeat, division):
    t0 = 0
    b0_last = [0, 0, 1]
    bpm_last = 1
    dbeat_last = 0.
    for b0, bpm in speed_info:
        dbeat = beat + (subbeat / division) - (b0[0] + b0[1] / b0[2])
        if dbeat <= 0:
            return t0 + 60 / bpm_last * dbeat_last
        t0 += 60 / bpm_last * (b0[0] + b0[1] / b0[2] - b0_last[0] - b0_last[1] / b0_last[2])
        bpm_last = bpm
        b0_last = b0
        dbeat_last = dbeat
    return t0 + 60 / bpm_last * dbeat_last

# to be improved

def calc_time_node(speed_info, effect_info):
    bpm_init = speed_info[0][1]
    t0 = 0
    b0_last = [0, 0, 1]
    bpm_last = speed_info[0][1]
    for b0, bpm in speed_info:
        t0 += 60 / bpm_last * (b0[0] + b0[1] / b0[2] - b0_last[0] - b0_last[1] / b0_last[2])
        while effect_info and effect_info[0]["beat"] < b0:
            yield calc_time(speed_info, *effect_info[0]["beat"]), bpm_last, effect_info[0]["scroll"]*(1 + bpm_last / bpm_init)/2
            effect_info.pop(0)
        yield t0, bpm, (1 + bpm / bpm_init)/2
        bpm_last = bpm 
        b0_last = b0
    while effect_info:
        yield calc_time(speed_info, *effect_info[0]["beat"]), bpm_last, effect_info[0]["scroll"]*(1 + bpm_last / bpm_init)/2
        effect_info.pop(0)

def read_malody(chart_name = "chart.mc"):
    f = open(chart_name, "rb")
    json_source = f.read()
    chart = json.JSONDecoder().decode(json_source.decode("utf-8"))
    speed_info = chart["time"]
    if "effect" in chart:
        effect_info = chart["effect"]
    else:
        effect_info = []
    speed = []
    for i in speed_info:
        speed.append((i["beat"], i["bpm"]))
    speed_raw = list(calc_time_node(speed, effect_info))
    i = 0
    j = 0
    while i < len(speed_raw)-1:
        i += 1
        while speed_raw[i][0] == speed_raw[j][0]:
            del speed_raw[j]
            if i >= len(speed_raw)-1:
                break
        j = i
    notes_raw = chart["note"][:-1]
    song_data = chart["note"][-1]
    notes = []

    offset = song_data["offset"] #?
    for n in notes_raw:
        if "endbeat" in n:
            beat, subbeat, division = n["beat"]
            beat1, subbeat1, division1 = n["endbeat"]
            notes.append((
                1,
                n["column"],
                offset/1000 + calc_time(speed, beat, subbeat, division),
                offset/1000 + calc_time(speed, beat1, subbeat1, division1)
            ))
        else:
            beat, subbeat, division = n["beat"]
            notes.append((
                0,
                n["column"],
                offset/1000 + calc_time(speed, beat, subbeat, division)
            ))
    

    f.close()
    return notes, song_data["sound"], speed_raw


