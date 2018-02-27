# Pi-Somfy

If you want to learn more about the Somfy RTS protocol, check out [Pushtack](https://pushstack.wordpress.com/somfy-rts-protocol/). It's because of this blog that I was able to write all my code.

I ported my [Arduino sketch](https://github.com/Nickduino/Somfy_Remote) onto the Pi because I wanted it to open and close my blinds automatically. I personally set it up to open the blinds everyday at 8 AM and close them in the evening 45 minutes after sunset but you can do whatever you want (close them during daylight if you're a vampire, open them when there's a full moon if you are a werewolf, you name it).

It's a script to open and close your Somfy (and SIMU) blinds using the RTS (or Hz) protocol with a Raspberry Pi and a cheap RF emitter. Your emitter has to use the 433.__42__ MHz frequency; the simplest might be to choose a common 433.93 MHz one and to swap its oscillator for a 433.42 MHz one bought separetely.
Then, connect it to your Raspberry Pi (I used GPIO 4 but you can change the value of __TXGPIO__ to whatever you want).

The script will use the __ephem library__ and __pigpiod daemon__ to open and close Somfy (or SIMU) blinds, depending on the time of sunrise/sunset (or whatever you feel like: open your blinds the first monday of the month if you want).
The remote address (which you'll create and will be recognised by your blinds as a new remote) and rolling code (incremented every time you send a frame) are stored in a specific file for each remote (one per blind, one per room, one per level, ...).
