import json
def read_malody(chart_name = "chart.mc"):
    f = open(chart_name, "rb")
    json_source = f.read()
    chart = json.JSONDecoder().decode(json_source.decode("utf-8"))
    bpm = chart["time"][0]["bpm"]
    notes_raw = chart["note"][:-1]
    song_data = chart["note"][-1]
    notes = []

    sec_per_beat = 60 / bpm
    if "offset" in song_data:
        offset = song_data["offset"] #?
    else:
        offset = 0
    for n in notes_raw:
        if "endbeat" in n:
            beat, subbeat, division = n["beat"]
            beat1, subbeat1, division1 = n["endbeat"]
            notes.append((
                          offset/1000 + sec_per_beat * (beat + subbeat/division),
                          n["column"],
                          # offset/1000 + sec_per_beat * (beat1 + subbeat1/division1)
                          ))
        else:
            beat, subbeat, division = n["beat"]
            notes.append((offset/1000 + sec_per_beat * (beat + subbeat/division), n["column"]))

    f.close()
    return notes, song_data["sound"]

