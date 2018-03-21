# EyelinkOgamaConnector

EyelinkOgamaConnector is a Python script, which reads converted log files from [Eyelink](http://www.sr-research.com/mount_longrange_1000plus.html) and creates a .csv compatible with [Ogama](http://www.ogama.net).

**Disclaimer: I am not a Python programmer. I'm grateful for feedback on how to improve the code.**


## Setup ##

The project should run in any Python IDE. It was developed and tested with [PyCharms](https://www.jetbrains.com/pycharm/).

## Work Flow ##

* Get `.edf` log file from EyeLink
* Convert `.edf` file to an ASCII-file `.asc` with EyeLink's `edf2asc`-Tool.
* Move `.asc` file to the project's `/input` folder
* Edit and run `OgamaConnector.py`


# License #

```
MIT License

Copyright (c) 2017 Norman Peitek
```