// Gameplay

const perfectRange = 80;
const greatRange = 100;
const earlyMissRange = 110;

playSpeed = 1;

const logicIntervalLength = 1000 / 60; // equal to 1000 / fps

timeOffset = 20; // the larger the offset is (in milliseconds), the earlier the music appears
// Layout

chartSpeed = 1.0; // pixel per ms
const keyHeight = 26; // todo hardwired in CSS

// Colors

const keyPressColor = "#ADC";
const perfectColor = "#DFD";
const greatColor = "#EE5";
const earlyMissColor = "#C23";

state = "selection"; // selection, play, endgame
tbl = document.getElementById("main");
form = document.getElementById("start");
chartField = document.getElementById("chart");
musicField = document.getElementById("music");
logicIntervalId = null;
syncIntervalId = null;
t0 = 0

chartFile = null;
musicFile = null;
musicPlayer = null;
scoreDisplay = null;
statsDisplay = null;
noteDivs = [];

function clear() {
    if (logicIntervalId != null) {
        clearInterval(logicIntervalId);
    }
    if (syncIntervalId != null) {
        clearInterval(syncIntervalId);
    }
    if (musicPlayer != null) {
        URL.revokeObjectURL(musicPlayer.src);
        musicPlayer.pause();
        musicPlayer.remove();
    }
    tbl.innerHTML = "";
    form.style.display = "none";
    tbl.style.display = "none";
    for (d of noteDivs) {
        d.remove();
    }
    noteDivs = [];
    if (scoreDisplay != null) {
        scoreDisplay.remove();
        scoreDisplay = null;
    }
    if (statsDisplay != null) {
        statsDisplay.remove();
        statsDisplay = null;
    }
}

function _getTop(e) {
    var offset = e.offsetTop;
    if (e.offsetParent != null) offset += _getTop(e.offsetParent);
    return offset;
}

function _getLeft(e) {
    var offset = e.offsetLeft;
    if (e.offsetParent != null) offset += _getLeft(e.offsetParent);
    return offset;
}

function getAbsolutePosition(obj) {
    return _getLeft(obj), _getTop(obj);
}

const keyrail = new Map([
    [65, 0], // a
    [83, 1], // s
    [75, 2], // k
    [76, 3] // l
]);
var held = new Set();

function buildPlay() {
    clear();
    /*       |    |    |    |    |
     * Lspan | R1 | R2 | R3 | R4 | Rspan
     *       |____|____|____|____|
     *       |_K1_|_K2_|_K3_|_K4_|
     *       |                   |
     */
    tbl.style.display = "";
    railRow = document.createElement("tr");
    tbl.appendChild(railRow);
    lSpan = document.createElement("td");
    lSpan.className = "space"
    lSpan.setAttribute("rowspan", 3);
    railRow.appendChild(lSpan);
    rails = new Array(4);
    for (var i = 0; i < 4; i += 1) {
        rails[i] = document.createElement("td");
        rails[i].className = "rail";
        railRow.appendChild(rails[i]);
    }
    rSpan = document.createElement("td");
    rSpan.className = "space";
    rSpan.setAttribute("rowspan", 3);
    railRow.appendChild(rSpan);
    railLeft = new Array(4);
    railRight = new Array(4);

    keyRow = document.createElement("tr");
    tbl.appendChild(keyRow);
    keys = new Array(4);
    for (var i = 0; i < 4; i += 1) {
        keys[i] = document.createElement("td");
        keys[i].className = "key";
        keyRow.appendChild(keys[i]);
    }
    for (var [e, i] of keyrail.entries()) {
        keys[i].innerHTML = String.fromCharCode(e);
    }

    missRow = document.createElement("tr");
    missRow.className = "miss";
    tbl.appendChild(missRow);

    // UL corner: score
    // center: combo, acc, results
    scoreDisplay = document.createElement("div");
    scoreDisplay.innerHTML = "000000000";
    scoreDisplay.className = "score";
    document.body.appendChild(scoreDisplay);

    statsDisplay = document.createElement("div");
    statsDisplay.innerHTML = "<h1>0</h1><p>&nbsp;</p><small>0.0%</small>";
    statsDisplay.className = "stats";
    document.body.appendChild(statsDisplay);

    // song
    if (musicFile != null) {
        musicPlayer = document.createElement("audio");
        musicPlayer.src = URL.createObjectURL(musicFile);
        // todo remember to revoke url
    }
    playSpeed = parseFloat(document.getElementById("speed").value);
    playSpeed = isNaN(playSpeed) ? 1.0 : playSpeed;

    chartSpeed = parseFloat(document.getElementById("chartspeed").value);
    chartSpeed = isNaN(chartSpeed) ? 1.0 / playSpeed : chartSpeed / playSpeed;
    state = "play";
}

function buildSummary() {
    // TODO deviation histogram
    //    Score : %09d
    //  Perfect : %9d
    //    Great : %9d
    //     Miss : %9d
    //Max Combo : %9d
    clear();
    tbl.style.display = "";
    tbl.innerHTML = "<tr class=\"scoremargin\"></tr>" +
        "<tr><td>Score</td><td>" + Math.floor(score * 100000000 / totalKeys) + "</td></tr>" +
        "<tr><td>Perfect</td><td>" + perfectCount + "</td></tr>" +
        "<tr><td>Great</td><td>" + greatCount + "</td></tr>" +
        "<tr><td>Miss</td><td>" + missCount + "</td></tr>" +
        "<tr><td>Max Combo</td><td>" + maxCombo + "</td></tr><tr class=\"scoremargin\"></tr>";
    state = "endgame";
}

function getCoord() {
    // judgementLinePosition = _getTop(missRow);
    judgementLinePosition = missRow.getBoundingClientRect().top;
    for (var i = 0; i < 4; i += 1) {
        var b = keys[i].getBoundingClientRect();
        railLeft[i] = b.left;
        railRight[i] = b.right;
    }
    gameRect = tbl.getBoundingClientRect();
}

function computeAbsolutePosition(r, dist) {
    // computes the absolute position
    // r is the rail id
    // dist is the distance to the judgement line
    // returns (left, right, *top)
    return [railLeft[r], railRight[r] - railLeft[r], judgementLinePosition - dist]
}

function setAbsolutePosition(obj, r, dist, height) {
    // TODO: take border into account maybe?
    if (height <= 0) {
        obj.style.display = "none";
        return;
    }
    obj.style.left = railLeft[r];
    if (judgementLinePosition - dist <= gameRect.top ||
        judgementLinePosition - dist - height >= gameRect.bottom) {
        obj.style.display = "none";
        return;
    }
    obj.style.display = "";
    obj.style.width = railRight[r] - railLeft[r];
    obj.style.top = judgementLinePosition - dist - height;
    obj.style.height = height;
}

/*
chart is a list of 
note_type, note_rail, times..
0 - note
1 - hold
2 - hold held
3 - hold broken
4 - hold missed

time is in millisecs

speed_raw: a list of (t0, speed_factor)
speed: a list of (t0, x0, speed_factor)
*/

function* calcTimeNode(speedInfo, effectInfo) {
    var bpmInit = speedInfo[0][1];
    var t0 = 0;
    var b0Last = [0, 0, 1];
    var bpmLast = speedInfo[0][1];
    for (var [b0, bpm] of speedInfo) {
        t0 += 60000 / bpmLast * (b0[0] + b0[1] / b0[2] - b0Last[0] - b0Last[1] / b0Last[2]);
    }
    while (effectInfo.length > 0 && effectInfo[0]["beat"] < b0) {
        yield [calcTime(speedInfo, ...effectInfo[0]["beat"]), bpmLast, effectInfo[0]["scroll"] * (1 + bpmLast / bpmInit) / 2];
        effectInfo.shift();
    }
    yield [t0, bpm, (1 + bpm / bpmInit) / 2];
    bpmLast = bpm;
    b0Last = b0;
    while (effectInfo.length > 0) {
        yield [calcTime(speedInfo, ...effectInfo[0]["beat"]), bpmLast, effectInfo[0]["scroll"] * (1 + bpmLast / bpmInit) / 2];
        effectInfo.shift();
    }
}

function calcTime(speed, beat, subbeat, division) {
    var t0 = 0,
        b0Last = [0, 0, 1],
        bpmLast = speed[0][1],
        dbeatLast = 0.;
    var dbeat;
    for (var [b0, bpm] of speed) {
        dbeat = beat + (subbeat / division) - (b0[0] + b0[1] / b0[2])
        if (dbeat <= 0) {
            return t0 + 60000 / bpmLast * dbeatLast;
        }
        t0 += 60000 / bpmLast * (b0[0] + b0[1] / b0[2] - b0Last[0] - b0Last[1] / b0Last[2])
        bpmLast = bpm
        b0Last = b0
        dbeatLast = dbeat
    }
    return t0 + 60000 / bpmLast * dbeatLast
}

function readMalody(json_raw) {
    //! TODO this contains awful logic
    //! But since it's only used once per game
    //! I have never bothered to changed it
    var rawChart;
    try {
        rawChart = JSON.parse(json_raw);
    } catch (error) {
        alert("Unsupported format.");
        return false;
    }
    metaInfo = rawChart["meta"];
    if (metaInfo["mode"] != 0 ||
        ("mode_ext" in metaInfo &&
            (!("column" in metaInfo["mode_ext"]) ||
                metaInfo["mode_ext"]["column"] != 4))) {
        alert("Unsupported format.");
        return false;
    }
    var speedInfo = rawChart["time"];
    var effectInfo = ("effect" in rawChart) ? rawChart["effect"] : new Array();

    var speed = new Array();
    for (i of speedInfo) {
        speed.push([i["beat"], i["bpm"]]);
    }
    speed_raw = Array.from(calcTimeNode(speed, effectInfo));
    var i = 0,
        j = 0;
    while (i < speed_raw.length - 1) {
        i += 1;
        while (speed_raw[i][0] == speed_raw[j][0]) {
            speed_raw.splice(j, 1);
            if (i >= speed_raw.length - 1) {
                break;
            }
        }
        j = i;
    }
    var notesRaw = rawChart["note"];
    songData = notesRaw.pop();
    chart = new Array();

    var offset = songData["offset"] + calcTime(speed, ...songData["beat"]);
    for (n of notesRaw) {
        if ("endbeat" in n) {
            chart.push([1, n["column"], -offset + calcTime(speed, ...n["beat"]), -offset + calcTime(speed, ...n["endbeat"])])
        } else {
            chart.push([0, n["column"], -offset + calcTime(speed, ...n["beat"])])
        }
    }
    // sets chart, speed_raw, songData, metaInfo
    return true;
}

function calculateChart() {
    speed = new Array();
    var x0 = 0.;
    var last_t0 = 0.;
    speed.push([0., 0., 1.]);
    var speed_factor = 1.;
    var lsf = 1.;
    var t0 = 0.;
    for ([t0, bpm, speed_factor] of speed_raw) {
        x0 += (t0 - last_t0) * chartSpeed * lsf;
        last_t0 = t0;
        lsf = speed_factor;
        speed.push([t0, x0, speed_factor]);
    }

    chartPositions = chart.map(calculateNote);
}

function calculatePosition(tpos) {
    // return chartSpeed * tpos  // const
    var i = speed.length - 2;
    for (; i > 0; i -= 1) {
        if (tpos > speed[i][0]) {
            return chartSpeed * (tpos - speed[i][0]) * speed[i][2] + speed[i][1];
        }
    }
    return chartSpeed * (tpos - speed[i][0]) * speed[i][2] + speed[i][1];
}

function calculateNote(note, tpos = 0.) {
    switch (note[0]) {
        case 0:
            return [0, note[1], calculatePosition(note[2])];
        case 1:
        case 2:
        case 3:
        case 4:
            return [note[0], note[1],
                calculatePosition(note[2]),
                calculatePosition(note[3])
            ];
        default:
            console.error("Encountered anomalous note:", note);
    }
}

function createNote(note) {
    // assumes note_type is always 0/1
    switch (note[0]) {
        case 0:
            var d = document.createElement("div");
            d.className = "note";
            //d.style.display = "none"; // save rendering cost?
            setAbsolutePosition(d, note[1], note[2], keyHeight);
            return d;
        case 1:
            var d = document.createElement("div");
            d.className = "hold";
            //d.style.display = "none";
            setAbsolutePosition(d, note[1], note[2], note[3] - note[2]);
            return d;
        default:
            console.error("Encountered anomalous note:", note);
    }
}

function moveNote(i, camera) {
    var note = chartPositions[i];
    switch (note[0]) {
        case 0:
            setAbsolutePosition(noteDivs[i], note[1], note[2] - camera, keyHeight);
            break;
        case 1:
        case 4:
            setAbsolutePosition(noteDivs[i], note[1], note[2] - camera, note[3] - note[2]);
            break;
        case 2:
        case 3:
            setAbsolutePosition(noteDivs[i], note[1], 0., note[3] - camera);
            break;
    }
}

function removeNote(i) {
    chart[i] = [-1];
    chartPositions[i] = [-1];
    noteDivs[i].style.display = "none";
}

function createChart() {
    noteDivs = new Array();
    for (var note of chartPositions) {
        var d = createNote(note);
        noteDivs.push(d);
        document.body.appendChild(d);
    }
}

function buildChart() {
    calculateChart();
    createChart();
}

function _pdf(e) {
    e.preventDefault();
    e.stopPropagation();
}

document.addEventListener("dragenter", _pdf, false);
document.addEventListener("dragover", _pdf, false);
document.addEventListener("dragleave", _pdf, false);
document.addEventListener("drop", function(e) {
    _pdf(e);
    var df = e.dataTransfer;
    if (df.items !== undefined) {
        // Chrome
        for (var i = 0; i < df.items.length; i++) {
            var item = df.items[i];
            if (item.kind === "file" && item.webkitGetAsEntry().isFile) {
                var f = item.getAsFile();
                if (f.name.endsWith(".mc")) {
                    chartField.files = df.files;
                } else if (f.name.endsWith(".ogg") || f.name.endsWith(".wav")) {
                    musicField.files = df.files;
                }
                return;
            }
        }
    } else {
        alert("Doesn't support other browsers yet");
        return;
    }
    alert("Cannot recognize chart file");
}, false);

async function loadChart() {
    var reader = new FileReader();
    reader.readAsText(chartFile);
    reader.onload = function() {
        if (readMalody(this.result)) {
            buildPlay();
            document.addEventListener("keydown", kd);
            document.addEventListener("keyup", ku);
            getCoord();
            window.addEventListener("resize", getCoord);
            logicInit();
        }
    }
}

function onPlayButtonClicked(e) {
    e.preventDefault();
    if (chartField.files.length == 1) {
        chartFile = chartField.files[0];
    } else {
        return;
    }
    if (musicField.files.length == 1) {
        musicFile = musicField.files[0];
    } else {
        musicFile = null;
    }
    loadChart();
}

function logicInit() {
    buildChart();
    paused = true;
    totalKeys = chart.length;
    maxTime = Math.max(...chart.map((c) => c[c.length - 1])) + 1000;
    score = 0.;
    combo = 0;
    maxCombo = 0;
    perfectCount = 0;
    greatCount = 0;
    missCount = 0;
    if (musicFile != null) {
        musicPlayer.currentTime = 0;
        musicPlayer.pause();
        musicPlayer.playbackRate = playSpeed;
        syncIntervalId = setInterval(sync, 100);
        sync();
    } else {
        t0 = performance.now() + timeOffset;
    }
    logicIntervalId = setInterval(logic, logicIntervalLength);

}

function sync(hard = false) {
    if (musicFile != null) {
        var t1 = performance.now() - musicPlayer.currentTime * 1000 / playSpeed + timeOffset;
        if (hard) {
            if (Math.abs(t0 - t1) > 200) {
                t0 = t1;
                console.warn("Sync!");
            }
        } else {
            t0 = (t0 * 9 + t1) / 10;
        }
    }
}

function logic() {
    if (paused) {
        return;
    }
    tpos = (performance.now() - t0) * playSpeed;
    var camera = calculatePosition(tpos);
    if (musicPlayer.ended) {
        buildSummary();
    }
    for (var i = 0; i < chart.length; i += 1) {
        var c = chart[i];
        // Late Miss
        switch (c[0]) {
            case 0:
                if (c[2] - tpos < -greatRange) {
                    combo = 0;
                    missCount += 1;
                    removeNote(i);
                    showResults(0);
                }
                break;
            case 1:
                if (c[2] - tpos < -greatRange) {
                    missCount += 1;
                    combo = 0;
                    c[0] = 4;
                    chartPositions[i][0] = 4
                    noteDivs[i].className = "missed";
                }
                break;
            case 2: //Hold
                if (c[2] - greatRange <= tpos && tpos <= c[3] - perfectRange) {
                    var h = false;
                    for (e of held) {
                        h |= c[1] == keyrail.get(e);
                    }
                    if (!h) {
                        combo = 0;
                        c[0] = 3;
                        chartPositions[i][0] = 3;
                        noteDivs[i].className = "broken";
                        showResults(-1);
                    }
                }
        }
        moveNote(i, camera);
    }
}
const results = ["LATE MISS",
    "EARLY MISS",
    "GREAT",
    "PERFECT"
]

function showResults(res, tdiff = 0) {
    var s = String(Math.floor(100000000 * score / totalKeys));
    scoreDisplay.innerHTML = "0".repeat(9 - s.length) + s;
    var noteCount = perfectCount + greatCount + missCount;
    var acc = String(Math.floor(1000 * score / noteCount));
    var accString = acc.slice(0, acc.length - 1) + "." + acc[acc.length - 1] + "%";
    var resString = (res == -1) ? "" : results[res]
    statsDisplay.innerHTML = "<h1>" + String(combo) + "</h1><p>" + resString + "</p><small>" + accString + "</small>";
}

async function kd(e) {
    var tpos = (performance.now() - t0) * playSpeed;
    if (e.keyCode == 192) { // ` for retry
        loadChart();
        return true;
    }
    if (e.keyCode == 32) { // space to pause
        paused = !paused;
        if (musicFile != null) {
            if (paused) {
                await musicPlayer.pause();
            } else {
                await musicPlayer.play();
            }
            sync(true);
        }
        return true;
    }
    if (paused) {
        return true;
    }
    if (e.repeat || !(keyrail.has(e.keyCode))) { return false; }
    held.add(e.keyCode);
    rail = keyrail.get(e.keyCode);
    keys[keyrail.get(e.keyCode)].style.background = keyPressColor;
    for (var cind = 0; cind < chart.length; cind += 1) {
        var c = chart[cind];
        if (rail != c[1]) {
            continue;
        }
        switch (c[0]) {
            case -1:
                continue;
            case 0:
                if (Math.abs(c[2] - tpos) <= perfectRange) {
                    score += 1;
                    combo += 1;
                    perfectCount += 1;
                    keys[keyrail.get(e.keyCode)].style.background = perfectColor;
                    showResults(3, c[2] - tpos);
                } else if (Math.abs(c[2] - tpos) <= greatRange) {
                    score += 0.6;
                    combo += 1;
                    greatCount += 1;
                    keys[keyrail.get(e.keyCode)].style.background = greatColor;
                    showResults(2, c[2] - tpos);
                } else if (0 < c[2] - tpos && c[2] - tpos <= earlyMissRange) {
                    combo = 0;
                    missCount += 1;
                    keys[keyrail.get(e.keyCode)].style.background = earlyMissColor;
                    showResults(1, c[2] - tpos);
                } else { continue; }
                removeNote(cind);
                maxCombo = Math.max(maxCombo, combo);
                return true;
            case 1:
                if (Math.abs(c[2] - tpos) <= perfectRange) {
                    score += 1;
                    combo += 1;
                    perfectCount += 1;
                    showResults(3, c[2] - tpos);
                    c[0] = 2;
                    chartPositions[cind][0] = 2;
                    keys[keyrail.get(e.keyCode)].style.background = perfectColor;
                    noteDivs[cind].className = "held";
                } else if (Math.abs(c[2] - tpos) <= greatRange) {
                    score += 0.6;
                    combo += 1;
                    greatCount += 1;
                    showResults(2, c[2] - tpos);
                    c[0] = 2;
                    chartPositions[cind][0] = 2;
                    keys[keyrail.get(e.keyCode)].style.background = greatColor;
                    noteDivs[cind].className = "great";
                } else if (0 < c[2] - tpos && c[2] - tpos <= earlyMissRange) {
                    combo = 0;
                    missCount += 1;
                    showResults(1, c[2] - tpos);
                    chartPositions[cind][0] = 3;
                    keys[keyrail.get(e.keyCode)].style.background = earlyMissColor;
                    noteDivs[cind].className = "missed";
                } else { continue; }
                maxCombo = Math.max(maxCombo, combo);
                return true;
        }
    }
    return true;
}

function ku(e) {
    if (paused) {
        return true;
    }
    if (e.repeat || !(keyrail.has(e.keyCode))) { return false; }
    held.delete(e.keyCode);
    keys[keyrail.get(e.keyCode)].style.background = "";
    return true;
}