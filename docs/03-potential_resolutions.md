
## Potential Resolutions:

The 5d2 sensor outputs analog values (no on chip ADC) with 4 channel readout.
The camera drives the sensor with a 24Mhz pixel clock. It is unclear how much faster the sensor can
be driven.

Required sample rates (purely theoretical; there will be some overhead):

| Format          | resolution | framerate | pixel rate / 4 [Mpix/s] |
| :-------------- | :--------- | :-------- | :---------------------- |
| FHD             | 1920x1080  | 24        | 12.4416                 |
| FHD actual cam  | 1872x1248  | 24        | 14.01753                |
| FHD             | 1920x1080  | 30        | 15.552                  |
| FHD actual cam  | 1872x1248  | 30        | 17.52192                | 
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
  for the FHD video output.
* It is unclear what other row / column subsampling modes are possible with the sensor interface (concerns HALF, FHD and CROP modes)
* 4k DCI would have a crop factor of 1.371 (vs 1.6 for APSC)
* USB 3.0 can theoretically transport 500Mbyte/s as a theoretical maximum and probably not much more than 400Mbyte/s in practice.
* Actual ADC speed would need to be twice as high for correlated double sampling (CDS) or would require additional analog circutry
