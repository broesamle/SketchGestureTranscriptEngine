#!/usr/bin/env python 

#import inkex, simplepath, simplestyle, simplepath
from Woz_AnnotatedTranscriptXML import *
import os
import codecs
import random
import math
from logging import info

from logging import info
import logging

#import numpy

LOG_FILENAME = 'Woz_ContextualizerA.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)



#corpus_fname = 'minicorpus.xml'
corpus_fname = 'Korpus_HospitalFreiburg 3.xml'

#corpus_fname = 'C:\Programme\Inkscape\WozardCorpus\Korpus_V205-bereinigenDerAnnotationen-D.xml'
#corpus_fname = 'C:\Programme\Inkscape\WozardCorpus\TextCorpus_current.xml'
#corpus_fname = 'C:\Dokumente und Einstellungen\wozard\Eigene Dateien\MultimodalCorpus\VerbalData\VerbalCorpus-BlockA.xml'

corpus = CorpusDocument(corpus_fname)

pars = corpus.getAllParagraphs()

random.shuffle(pars)

f = codecs.open(corpus_fname + '_extrakt.cvs', 'w', "utf8" )

#f = open (corpus_fname + '_extrakt.cvs', 'w')

for i in pars:
	f.write (i.asCVS())

f.close()
