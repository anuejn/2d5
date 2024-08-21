# Pinout of the Sensor

For driving the sensor outside the camera, it is important to figure out its pinout. In the 5d2 the
sensor is mounted on a flex pcb. I will first focus on figuring out the connections of this flex-pcb.
After this, figuring out the pinout of the actual CMOS should be trivial if needed.

## Connectors

The sensor assembly has 3 connectors:

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

Figuring out the pinout is a tricky process that I started with looking at the mainboard visually (see gimp files in `pictures/`),
using a continuity tester and doing different other measurements. After that, I measured voltages
at different pins and looked at the signals with an oscilloscope. Later, I also used different 
logic analyzer setups to trace the signals (see the `traces/` directory).
Throughout the process a warm round of guesswork guided me.
During the probing it was immensely helpful to have the breakout PCBs ordered with
white silkscreen to be able to write results directly to the breakout boards.

The results of my analysis can be found in the [connector pinouts table](../connector_pinouts.ods).
In the whole project, I refer to the pins using their coordinates in this spreadsheet.

The sensor outputs its analog data using differential pairs and requires
a bunch of different power supplies. To get a glimpse on how the interface could look like, see the
[datasheet of the Cypress IBIS4-14000](interesting_datasheets/Cypress_Semiconductor-IBIS4-14000-M-datasheet.pdf).
