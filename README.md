# ASKL
A simple HTML player for 4K Malody charts.

## Usage

Download `main.htm`, `logic.js` and `style.css` and put them in a folder.

- Simply open `main.htm` in your favourite browser (I've only tested this on Chrome and Safari).
- Drag and drop the chart (`*.mc` file) and music (probably `*.ogg`, but for other formats that your browser.
supports, you can also use the upload button).
- Set the chart speed (pixels per millisecond, 0.5~1.3 px/ms is about right for most players).
- Set the music speed if you want to make the music quicker or slower. `1.0` is the normal speed.
- Play!

**Remember that the music is paused by default in the beginning.** Press space to unpause.

I have no idea where you can get those `*.mc` charts. I just got it from a friend of mine who plays Malody.

I've set `ASKL` as the default keys. You can change it in the code (the `keyrail` in `logic.js`).
You can also change the time offset, in case the music comes too early or too late (the `timeOffset` in milliseconds).
There are all sorts of other stuff you can play with, located at the top of `logic.js`.

You can fiddle with the appearance in `style.css`.

## Features

Supports bpm changes and effects. The scoring system is slightly different.

Press space to pause/unpause; press \` (the tilde key on the topleft) to retry. If you want to start a new song, refresh.

## Other versions

The other folders contain old versions I've made along the way.
They only work on Windows with Python installed, for they rely on the `winsound` module in Python.
