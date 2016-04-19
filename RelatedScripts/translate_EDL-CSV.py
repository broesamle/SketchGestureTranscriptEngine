from sys import argv

import codecs

from WTextServicesB import WRegexpTranslator

if len(argv) != 3:
	print "USAGE: python translateFileRE.py <infile> <outfile>"
	exit(1)
	
#fnamePat = argv[1]
fnameIn = argv[1]
fnameOut  = argv[2]
encoding = "utf-8"

print ( "PATTERN:  %s\nINPUT:    %s\nOUTPUT:   %s\nENCODING:  utf-8 (by default for all files)" % ("(no pattern file read)", fnameIn, fnameOut) )

#patf = codecs.open (fnamePat,'r',encoding)
inf = codecs.open (fnameIn,'r',encoding)
outf = codecs.open (fnameOut,'w',encoding)

contents = inf.read()


## transform EDL to CSV
tr = WRegexpTranslator()
tr.addReplacer(r"[\r\n]+REEL", r"\tREEL\t")			### Zeichenmarken
tr.addReplacer(r"[\r\n]+", r"\tLINEEND\n")		### Zeitmarken retten
contents = tr.translate(contents)


tr2 = WRegexpTranslator()
tr2.addReplacer(r"[\t ]+", r"\t")			### Zeichenmarken
contents = tr2.translate(contents)


outf.write(contents)

outf.close()
inf.close