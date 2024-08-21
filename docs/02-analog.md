# Analog output of the CMOS

The image sensor outputs at four channels differentially. after each pixel, the differential output
goes to 0mV differential value. This is probably to enable Correlated Double Sampling (CDS).
Each side (positive and negative) is centered at ~1.4V and has 300-400mv Swing. The differential
values range from -600mV to +600mV.


## Possible ADCS

| part          | channels | sample rate [Msa/s] | bit depth | price   | notes    |
| :------------ | :------- | :------------------ | :-------- | :------ | :------- |
| VSP5622       | 4        | 70                  | 16        | 14$     | obsolete |
| ADDI7004BBBCZ | 4        | 72                  | 14        | 65$     |          |
| ADC34J45IRGZR | 4        | 160                 | 14        | 81$     | only ADC |
| ADC3244       | 2        | 125                 | 14        | 26$ @1k | only ADC |
| HMCAD1520     | 4        | 160                 | 12        | 121$    | only ADC |
| HMCAD1511     | 4        | 125                 | 8         | 13$     | only ADC |

There is a test-board with a HMCAD1511 in the [zynq-test-board/](zynq-test-board/) folder.


### HMCAD1511

I invested some efford trying to get 12 bit output from the HMCAD1511. This however is not trivial
and maybe outright impossible. It is not just the same die as the HMCAD1520 or at least it is 
configured a bit differently.

One possibility would be to use multiple 8 bit ADCs in an "Alexa Style" configuration with different
gains to reach higher dynamic range.