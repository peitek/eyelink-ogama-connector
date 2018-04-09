# EyelinkOgamaConnector

EyelinkOgamaConnector is a Python script, which reads converted log files from [Eyelink](http://www.sr-research.com/mount_longrange_1000plus.html) and creates a .csv compatible with [Ogama](http://www.ogama.net).

**Disclaimer: I am not a Python programmer. I'm always grateful for feedback on how to improve my code.**


## Setup ##

The project should run in any Python environment. It was developed and tested with the [PyCharms IDE](https://www.jetbrains.com/pycharm/).

## File Names

all in same path
eye tracking: probandenkuerze.asc
response: probandenkuerzel_response_log
physio: probandenkuerzel_physio.log

TODO provide sample data

## Work Flow ##

Getting ready to use EyelinkOgamaConnector:

* Get `.edf` log file from EyeLink
* Convert `.edf` file to an ASCII-file `.asc` with EyeLink's `edf2asc`-Tool.
* Move `.asc` file to the project's `/input` folder

Use EyelinkOgamaConnector:

* Edit and run `OgamaConnector.py`

Possible Post-Usages:

* Import to Ogama
* Direct analyses on the `.csv` file

# License #

```
MIT License

Copyright (c) 2017 Norman Peitek
```