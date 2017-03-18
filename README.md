# Pi-Somfy
A script to open and close your Somfy (and SIMU) blinds with a Raspberry Pi and an RF emitter. Your emitter has to use the 433.__42__ MHz frequency; the simplest might be to use a common 433.93 MHz one and to swap its oscillator for a 433.42 MHz one bought separetely.

The script will use the ephem library and pigpiod daemon to open and close Somfy (or SIMU) blinds, depending the the time of sunrise and sunset.
The remote address and rolling code (incremented every time you send a frame) are stored in a specific file for every remote.
