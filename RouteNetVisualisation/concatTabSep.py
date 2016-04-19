### concat tab separated data files and add one column identifying from which original file the data came.
### ausbaufähig!


from sys import argv,stdout,exit

###########################
### get commandline options
###########################
if len(argv) != 6 :
	print ('USAGE: python concatTabSep.py FILE1 FILE2 TAG1 TAG2 TAGVARIABLE ')
	exit(1)

fn1 = argv[1]
fn2 = argv[2]
tag1 = argv[3]
tag2 = argv[4]
tagvar = argv[5]

f1 = open (fn1,'r')
f2 = open (fn2,'r')

for l1 in f1: 
	break	## get exactly one line

for l2 in f2:
	break	## get exactly one line

if l1 != l2:
	raise Exception, "Headlines are different"
	exit(1)

stdout.write (tagvar + "\t" + l1)

for l1 in f1:
	stdout.write (tag1 + "\t" + l1)

for l2 in f2:
	stdout.write (tag2 + "\t" + l2)



