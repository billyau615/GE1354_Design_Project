from microbit import *
import music

# Set tempo to 114 BPM (the actual speed of the song)
# Ticks=16 allows us to do very fine rhythmic adjustments
music.set_tempo(bpm=114, ticks=16)

# The iconic melody with specific 80s syncopation
# 4 = 16th note, 8 = 8th note, 16 = quarter note, 32 = half note
rickroll_perfect = [
    # --- "Never gonna" ---
    "G4:4", "A4:4", "C5:4", "A4:4", 
    # --- "give you up" --- (Held notes)
    "E5:10", "R:2", "E5:10", "R:2", "D5:20", "R:4",
    
    # --- "Never gonna" ---
    "G4:4", "A4:4", "C5:4", "A4:4", 
    # --- "let you down" ---
    "D5:10", "R:2", "D5:10", "R:2", "C5:4", "B4:4", "A4:12", "R:4",
    
    # --- "Never gonna" ---
    "G4:4", "A4:4", "C5:4", "A4:4", 
    # --- "run around and" ---
    "C5:12", "D5:4", "B4:6", "R:2", "A4:4", "G4:8", "R:4",
    
    # --- "desert you" ---
    "G4:8", "D5:16", "C5:24"
]

display.show(Image.MUSIC_QUAVER)

while True:
    if button_a.was_pressed():
        display.show(Image.HAPPY)
        # Use pin=pin1 for your buzzers
        music.play(rickroll_perfect, pin=pin1, wait=True)
        display.show(Image.MUSIC_QUAVER)
    
    if button_b.was_pressed():
        music.stop(pin1)
        display.clear()
        
    sleep(100)