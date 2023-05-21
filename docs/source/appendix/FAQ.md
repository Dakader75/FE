# Frequently Asked Questions

## Audio

### My music is playing at a different pitch?

LT is configured at 44100 Hz. Most likely, your music was sampled at 48000 Hz. You can use
[Audacity](https://superuser.com/questions/420531/audacity-resampling) to resample your track
to the appropriate frequency.

### Does LT support `.tmx` map files?

No. LT uses `.png` files for the graphical component of its maps, and uses internal data for terrain data.

### How do I soft reset the game?

Press whatever keys/buttons are mapped to your SELECT, BACK, and START actions at the same time. By default, this is "X" + "Z" + "S" on the keyboard.

### Can I stop certain tracks/songs from showing up in the Sound Room?

Any `Song` in the editor with a title that starts with an underscore (`_`) will be ignored in the Sound Room. This makes it useful for things like the prolonged Chapter Sound, ambience tracks, etc. to be excluded from the Sound Room.