

SpaDoAK: Spatial Domain Annotation Kit
======================================

**Annotation of Gestures and Sketches**

by Martin Brösamle

Initially developed for internal use at SFB/TR8, Spatial Cognition.
Currently unmaintained.


The software was used for data analysis of video-recorded architectural design sessions.


Installation
------------

Somewhere in a useful folder or directory...

1. Download and unpack the archive from https://github.com/broesamle/spadoak/archive/master.zip 

*OR* clone the repository:

`git clone git clone https://github.com/broesamle/spadoak.git`

2. Install locally as an editable python package using `pip`:

`pip install -e spadoak/`


`./spadoak` (the package directory)
-----------------------------------

Usage:

`python -m spadoak.makeTr`

`python -m spadoak.makeTr --help` for pringing options

+ Combine verbal and spatial annotation data into human readable form.

+ 15 min of video-recorded design activity will result in approx. 50 pages of PDF.

Gesture Annotation Workflow
---------------------------

![Data Analysis Workflow](data-analysis-workflow.jpg)

### Sample Transcript Page

![Sample Transcript Page](transcript-sample.jpg)

### Annotation Language Cheat Sheet

![Annotation Cheat Sheet](annotation-language-cheat-sheet.jpg)


