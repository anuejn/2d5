# Registers of the Sensor
* The Sensor seems to have 6 registers (0 - 5) with 12 bit each
* they are written with an SPI bus that is active when CS (C16) is high
* There are other devices on the SPI bus (probably the ADTGs), so not all trafic is for the sensor
* The clock is C15, data is on C14. Data is valid on the rising edge of the clock.
* The SPI bus has transactions with 16 bits each. The first 4 bits are the adress of the register
  while the last 12 bits are the value. 

There is documentation on the register map [in the magic lantern wiki](https://magiclantern.fandom.com/wiki/ADTG)
and in the magic lantern [adtg_gui code](https://github.com/reticulatedpines/magiclantern_simplified/blob/df4c7bd32ec0cd65a4b6aacdd7ec5cce1c560135/modules/dev_tools/adtg_gui/adtg_gui.c#L29).


## Register states in different situations: 
This section contains observations of the register set in different situations. 
They are the state during capture and are captured with either a glasgow or a logic analyzer.

### Different modes
```
photo:           0203 1C00 2008 3007 4242 5C05
normal liveview: 020f 1c00 240e 3005 4242 5c01
fhd:             020f 1c00 240e 3005 4242 5c01
```


### Experimentation with the LiveView Zoom
```
5x zoom center:              020f 1e6a 210e 3005 4242 5c01
5x zoom upper right corner:  020f 1d20 220e 3005 4242 5c01
5x zoom upper left corner:   020f 1d20 200e 3005 4242 5c01
5x zoom lower right corner:  020f 1c18 220e 3005 4242 5c01
5x zoom lower left corner:   020f 1c18 200e 3005 4242 5c01
```

10x modes have the exact same registers and are implemented in software.


### Experimentation with ISO (all of this is in LiveView)
```
ISO 100:  0203 1c00 240e 3005 4242 5c01
ISO 160:  0207 1c00 240e 3005 4242 5c01
ISO 320:  020b 1c00 240e 3005 4242 5c01
ISO 640:  020f 1c00 240e 3005 4242 5c01
ISO 1250: 0213 1c00 240e 3005 4244 5c01
ISO 2500: 0213 1c00 240e 3005 4244 5001
```

## Conclusions:

conclusions prefixed with "ML:" are not my findings but rather copied from the Magic Lantern

### CMOS[0]
```
---- ---- --xx ML: default 11, setting to 00 results in dark image with very low stdev
---- ---x xx-- ISO coarse (0 - 4)
---- xxx- ---- ML: ISO2
---x ---- ---- ML: ISO2 enable (according to ML)
--x- ---- ---- ML: enables vertical OB clamping maybe (setting it to 0 results in severe horizontal banding that looks like random walk)
-x-- ---- ---- ML: compresses the image horizontally (left side squashed, right side black)
0010 0000 0011 "normal"
```


### CMOS[1]
```
---- ---x xxx-  y start offset 0 - 12
1100 0000 0000 "normal"
1110 0110 1010 "zoom center"
1101 0010 0000 "zoom upper"
1100 0001 1000 "zoom lower"

top to bottom sweep zoomed in:
1101 0110 0010
1101 1010 0100
1101 1110 0110
1110 0010 1000
1110 0110 1010
1110 1010 1100
1110 1110 1110
1111 0011 0000
1111 0111 0010
1111 1011 0100
1111 1111 0110
1100 0001 1000
```


### CMOS[2]
```
-x-- ---- ---- binning?
--xx ---- ---- coarse x offset? (left = 0, center = 1, right = 2)
---- ---- -xx- only set in liveview-esque modes
0000 0000 1000 "photo"
0100 0000 1110 "liveview"
0001 0000 1110 "zoom center"
0010 0000 1110 "zoom right"
0000 0000 1110 "zoom left"
0010 0000 1100 Temporary cleanup state during zoomed in sweep in LV
```


### CMOS[3]
```
---- ---- --x-  magic photo bit?
0000 0000 0111 "photo"
0000 0000 0101 "liveview
```


### CMOS[4]
```
---- ---- -xx- analog mux (one hot) for high conversion gain? (0b01 = ISO < 1250; 0b10 = ISO >= 1250)
---x ---- ---- ML: looks like some vertical dual ISO
-x-- ---- ---- ML: seems to cleanup 0.2 or 0.25 stops of shadow noise
No effect observed on the other bits.
0010 0100 0010 ISO < 1250
0010 0100 0100 ISO >= 1250
```



### CMOS[5]
```
xx-- ---- ---- ISO related (00 = LOW ISO, 11 = ISO >= 2500)
---- ---- -x-- Photo Mode Bit
1100 0000 0101 Photo
1100 0000 0001 LV
0000 0000 0001 LV ISO >= 2500
0100 0000 0101 Temporary cleanup state during zoomed in sweep in LV
```
