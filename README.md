# arcadia
little plateformer made with python 3.8.5 arcade pymunk

todo : clean code,fix unstoppable mechanics platform after launched.  level up with stairs, shooting enemies , slippery iced surface...

28th april: added electric mechanics platforms handlers , shoot on it with left mouse button to start moving platforms.
-------
This is electric two-way. it's buggy : need 2 shot to launch , and it seems unstoppable effect yet
---------

26th april: unlocking locks and opening doors, deadly traps, funny BUG: you become a ghost after death

25th april: 
yellow key is pickable, removable , and goes inside inventory which is displayed (dirty)
keys ,locks, and doors are now belonging to objects layer inside tmx tiled files which gives handy custom properties
picking up coins and dirty display score, fixed corrupted resources path for tilemap, basic moving mechanics platforms

23th april: 
Easy startposition implemented , just chose it with tiled to work the tmx map file.
collision with lava trap but NO respawn yet ; trouble to detect spikes collision (far right side on the map)
picking up items like coins or keys will crash , dont know how to fix that

20th april 2021 : Gamepad support added (not firing yet) ; might need exit and re-launch

---
Coming soon:
shooting enemies, ice blocks slippery low friction physics

