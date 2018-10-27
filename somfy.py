#!/usr/bin/env python
# -*- coding: utf-8 -*-

import locale
import time
import datetime as dt
import ephem
import pigpio
import traceback

TXGPIO=4 # 433.42 MHz emitter on GPIO 4

#Button values
boutonHaut = 0x2
boutonStop = 0x1
boutonBas = 0x4
boutonProg = 0x8

frame = bytearray(7)

homeLocation = ephem.Observer()
homeLocation.lat, homeLocation.lon = '42.764457', '5.066435' #PUT YOUR OWN COORDINATES HERE (check on Google Maps for instance)
locale.setlocale(locale.LC_TIME,'')


def envoi_commande(telco, bouton, repetition): #Sending a frame
# Sending more than two repetitions after the original frame means a button kept pressed and moves the blind in steps 
# to adjust the tilt. Sending the original frame and three repetitions is the smallest adjustment, sending the original
# frame and more repetitions moves the blinds up/down for a longer time.
# To activate the program mode (to register or de-register additional remotes) of your Somfy blinds, long press the 
# prog button (at least thirteen times after the original frame to activate the registration.
   
   checksum = 0
   
   with open("somfy/" + telco + ".txt", 'r') as file:# the files are in a subfolder "somfy"
      data = file.readlines()

   teleco = int(data[0], 16)
   code = int(data[1])
   data[1] = str(code + 1)

   print hex(teleco)
   print code

   with open("somfy/" + telco + ".txt", 'w') as file:
      file.writelines(data)

   pi = pigpio.pi() # connect to Pi

   if not pi.connected:
      exit()

   pi.wave_add_new()
   pi.set_mode(TXGPIO, pigpio.OUTPUT)


   print "Remote  :      " + "0x%0.2X" % teleco
   print "Button  :      " + "0x%0.2X" % bouton
   print "Rolling code : " + str(code)
   print ""

   frame[0] = 0xA7;       # Encryption key. Doesn't matter much
   frame[1] = bouton << 4 # Which button did  you press? The 4 LSB will be the checksum
   frame[2] = code >> 8               # Rolling code (big endian)
   frame[3] = (code & 0xFF)           # Rolling code
   frame[4] = teleco >> 16            # Remote address
   frame[5] = ((teleco >>  8) & 0xFF) # Remote address
   frame[6] = (teleco & 0xFF)         # Remote address

   print "Frame  :    ",
   for octet in frame:
      print "0x%0.2X" % octet,
   print ""

   for i in range(0, 7):
      checksum = checksum ^ frame[i] ^ (frame[i] >> 4)

   checksum &= 0b1111; # We keep the last 4 bits only

   frame[1] |= checksum;

   print "With cks  : ",
   for octet in frame:
      print "0x%0.2X" % octet,
   print ""

   for i in range(1, 7):
      frame[i] ^= frame[i-1];

   print "Obfuscated :",
   for octet in frame:
      print "0x%0.2X" % octet,
   print ""

#This is where all the awesomeness is happening. You're telling the daemon what you wanna send
   wf=[]
   wf.append(pigpio.pulse(1<<TXGPIO, 0, 9415)) # wake up pulse
   wf.append(pigpio.pulse(0, 1<<TXGPIO, 89565)) # silence
   for i in range(2): # hardware synchronization
      wf.append(pigpio.pulse(1<<TXGPIO, 0, 2560))
      wf.append(pigpio.pulse(0, 1<<TXGPIO, 2560))
   wf.append(pigpio.pulse(1<<TXGPIO, 0, 4550)) # software synchronization
   wf.append(pigpio.pulse(0, 1<<TXGPIO,  640))

   for i in range (0, 56): # manchester enconding of payload data
      if ((frame[i/8] >> (7 - (i%8))) & 1):
         wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))
         wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
      else:
         wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
         wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))

   wf.append(pigpio.pulse(0, 1<<TXGPIO, 30415)) # interframe gap

      for j in range(1,repetition): # repeating frames
            for i in range(7): # hardware synchronization
                  wf.append(pigpio.pulse(1<<TXGPIO, 0, 2560))
                  wf.append(pigpio.pulse(0, 1<<TXGPIO, 2560))
            wf.append(pigpio.pulse(1<<TXGPIO, 0, 4550)) # software synchronization
            wf.append(pigpio.pulse(0, 1<<TXGPIO,  640))

            for i in range (0, 56): # manchester enconding of payload data
                  if ((frame[i/8] >> (7 - (i%8))) & 1):
                        wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))
                        wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
                  else:
                        wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
                        wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))

            wf.append(pigpio.pulse(0, 1<<TXGPIO, 30415)) # interframe gap

   pi.wave_add_generic(wf)
   wid = pi.wave_create()
   pi.wave_send_once(wid)
   while pi.wave_tx_busy():
      pass
   pi.wave_delete(wid)

   pi.stop()
   

ancienJour = dt.datetime.now().day
varChambreUP, varChambreDOWN, varCuiSdbUP, varScheyeDOWN, varSoirDOWN, varGeneralDOWN, varSS, varMatinUp = (0,)*8

while 1:
   if(ancienJour != dt.datetime.now().day):
      varChambreUP, varChambreDOWN, varCuiSdbUP, varScheyeDOWN, varSoirDOWN, varGeneralDOWN, varSS, varMatinUp = (0,)*8
   ancienJour = dt.datetime.now().day
   
   homeLocation.date = dt.datetime.now().strftime("%Y/%m/%d 00:00:00")
   sunrise = ephem.localtime(homeLocation.next_rising(ephem.Sun()))
   sunset = ephem.localtime(homeLocation.next_setting(ephem.Sun()))
   print "Sunset :  " + str(sunset)

   for i in range(1, 120):
      if(dt.time(8, 00) < dt.datetime.now().time() < dt.time(8, 02)) and varChambreUP == 0:
         print "Test Chambre"
         try:
            envoi_commande("chambre", boutonHaut,2)
            time.sleep(4)
            envoi_commande("chambre", boutonStop,2)
            time.sleep(1)
            varChambreUP = 1
         except:
            print "Impossible d'ouvrir chambre"
            print traceback.format_exc()
            time.sleep(15)

      if(dt.time(8, 05) < dt.datetime.now().time() < dt.time(8, 07)) and varMatinUp == 0:
         print "Cuisine UP"
         try:
            envoi_commande("cuisine", boutonHaut,2)
            time.sleep(1)
            envoi_commande("sdb", boutonHaut,2)
            time.sleep(1)
            envoi_commande("salon", boutonHaut,2)
            time.sleep(1)
            varMatinUp = 1
         except:
            print "Impossible d'ouvrir cuisine, salon & sdb"
            print traceback.format_exc()
            time.sleep(15)


      if((sunset + dt.timedelta(minutes=45)) < (dt.datetime.now()) < (sunset + dt.timedelta(minutes=48))) and varSoirDOWN == 0:
         print "Salon à " + str(dt.datetime.now().time())
         try:
            envoi_commande("salon", boutonBas,2)
            time.sleep(1)
            envoi_commande("ss", boutonBas,2)
            time.sleep(1)
            envoi_commande("chambre", boutonBas,2)
            time.sleep(1)
            varSoirDOWN = 1
         except:
            print "Impossible de fermer salon++"
            print traceback.format_exc()
            time.sleep(15)

      if(dt.time(21, 00) < dt.datetime.now().time()) and (sunset + dt.timedelta(minutes=60)) < (dt.datetime.now()) and varGeneralDOWN == 0:
         print "Fermeture générale à " + str(dt.datetime.now().time())
         try:
            envoi_commande("salon", boutonBas,2)
            time.sleep(1)
            envoi_commande("cuisine", boutonBas,2)
            time.sleep(1)
            envoi_commande("sdb", boutonBas,2)
            time.sleep(1)
            envoi_commande("chambre", boutonBas,2)
            time.sleep(1)
            envoi_commande("ss", boutonBas,2)
            time.sleep(1)
            varGeneralDOWN = 1
         except:
            print "Impossible de fermer le général"
            print traceback.format_exc()
            time.sleep(15)

      time.sleep(30)
