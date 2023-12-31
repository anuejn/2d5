# Reverse engineering 5D mark II (5D2) image sensor

This repository contains notes tools for reverse engineering the image sensor of the Canon EOS 5D mark II
DSLR. The image sensor is relatively cheap available (~80$) and has a "full frame" sized active area
(36mm × 24mm) with 5,616px × 3,744px (21.0 MP). The 5D mark II important in popularizing DSLR cameras
for video making and the Magic Lantern firmware was originally written for this camera.

## Connectors

The sensor has 3 connectors:

* larger stacking 20*2 position connector ![a closeup of the 40 pin connector](pictures/connector_20x2.JPG)
* smaller stacking 15*2 position connector ![a closeup of the 30 pin connector](pictures/connector_15x2.JPG)
* other 4 position connector probably going to the vibration cleaning of the sensor

The stacking connectors have the same pitch (0.466mm - 0.475mm measured probably 0.5mm) and are likely of the same series.
Mating height is ~1.5mm.

* Panasonic AXK5F should be fitting (probably original)
* TXGA FBB05001-F40S1003W5M / FBB05001-M40S1013W5M should fit (but is hard to obtain)
* Atom-connector BTB050040-F1S03201 / BTB050040-M1S03201 should fit
* XKB Connectivity X0511FVS-40B-LPV01 / X0511WVS-40A-LPV01 should fit and is on lcsc

A breakout board for intercepting communications between the camera and the sensor can be found
in the [connector_breakout](connector/breakout) directory. It fits onto the mainboard and adapts the
connectors to 0.1" headers.
![a picture of the breakout boards installed on the camera mainboard](pictures/with_breakouts.JPG)

## Pinout

To this point only static analysis of the pinout has been done. The results of this can be found in
the [connector pinouts table](connector_pinouts.ods). To obtain the results in the table
a warm round of guesswork guided by a multimeter and some PCB tracing (see gimp files in `pictures/`)
have been used. During the probing it was immensely helpful to have the breakout PCBs ordered with
white silkscreen to be able to write results directly to the breakout boards.

The sensor most likely outputs its analog data using differential pairs and requires
a bunch of different power supplies. To get a glimpse on how the interface could look like, see the
[datasheet of the Cypress IBIS4-14000](interesting_datasheets/Cypress_Semiconductor-IBIS4-14000-M-datasheet.pdf).

The next step is to probe the sensor in-camera with a logic analyser / oscilloscope / multimeter to
obtain information about the power supply rails, the exact pinout and the scheme of driving the
sensor. Some basic testing was with a logic analyser was done and the traces can be found in the traces directory.

## Readout

The 5d2 sensor outputs analog values (no on chip ADC) with 4 channel readout.

Required sample rates (purely theoretical):

| Format          | resolution | framerate | pixel rate / 4 [Mpix/s] |
| :-------------- | :--------- | :-------- | :---------------------- |
| FHD             | 1920x1080  | 24        | 12.4416                 |
| FHD             | 1920x1080  | 30        | 15.552                  |
| HALF 16:9       | 2808x1580  | 24        | 26.61984                |
| FHD             | 1920x1080  | 60        | 31.104                  |
| HALF            | 2808x1872  | 24        | 31.53945                |
| HALF 16:9       | 2808x1580  | 30        | 33.2748                 |
| HALF            | 2808x1872  | 30        | 39.42432                |
| camera 1080p    | 5568x1044  | 30        | 43.59744                |
| FULL 3-lineskip | 5568x1248  | 30        | 52.11648                |
| 4k 16:9 (CROP)  | 4096x2304  | 24        | 56.62310                |
| HALF 16:9       | 2808x1580  | 60        | 66.5496                 |
| 4k 16:9 (CROP)  | 4096x2304  | 30        | 70.77888                |
| HALF            | 2808x1872  | 60        | 78.84864                |
| FULL 21:9       | 5616x2407  | 24        | 81.10627                |
| FULL 21:9       | 5616x2407  | 30        | 101.3828                |
| FULL 16:9       | 5616x3159  | 24        | 106.4456                |
| FULL            | 5616x3744  | 24        | 126.1578                |
| FULL 16:9       | 5616x3159  | 30        | 133.0570                |
| 4k 16:9 (CROP)  | 4096x2304  | 60        | 141.5577                |
| FULL            | 5616x3744  | 30        | 157.6972                |

Notes:

* The camera is [reported to use a column 3x binning and row 3x skipping](https://www.magiclantern.fm/forum/index.php?topic=16516.0)
  in its video mode. The FHD mode seems to use on-chip row and column skipping and a slightly-less than FHD readout with digital upscaling
  for the FHD video output. The readout clock used in the camera is ~24Mhz.
* It is unclear if row / column subsampling is possible with the sensor interface (concerns HALF, FHD and CROP modes)
* 4k DCI would have a crop factor of 1.371 (vs 1.6 for APSC)
* USB 3.0 can theoretically transport 500Mbyte/s as a theoretical maximum and probably not much more than 400Mbyte/s in practice.

some possible ADCs:
| part          | channels | sample rate [Msa/s] | bit depth | price   | notes                                    |
| :------------ | :------- | :------------------ | :-------- | :------ | :--------------------------------------- |
| VSP5622       | 4        | 70                  | 16        | 14$     | obsolete                                 |
| ADDI7004BBBCZ | 4        | 72                  | 14        | 65$     |                                          |
| ADC34J45IRGZR | 4        | 160                 | 14        | 81$     | only ADC                                 |
| ADC3244       | 2        | 125                 | 14        | 26$ @1k | only ADC                                 |
| HMCAD1520     | 4        | 160                 | 12        | 121$    | only ADC; possibly same die as HMCAD1511 |
| HMCAD1511     | 4        | 125                 | 8         | 13$     | only ADC; possibly same die as HMCAD1511 |

There is a test-board with a HMCAD1511 in the [zynq-test-board/](zynq-test-board/) folder.

# Analog output

The image sensor outputs at four channels differentially. after each pixel, the differential output
goes to 0mV differential value (maybe blacklevel compensation).
Each side (positive and negative) is centered at ~1.4V and has 300-400mv Swing. The differential
values range from -600mV to +600mV.
