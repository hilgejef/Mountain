# MOUNTAIN - A FOUNTAIN PARSER AND HTML GENERATOR
# Mountain is a Python-based tool to convert text files 
# written in the Fountain screenwriting syntax into HTML.
#
# To use Mountain, invoke the mountain.py script with either
# 1. input file and output file as arguments or 
# 2. input file, output file and an optional CSS file
# (The CSS file will be incorporated into the HTML output)
#
# TODO: Generate a default CSS file (perhaps one that can be
# used to convert directly into PDF?)


import sys
from mountain_parser import parse
from mountain_builder import build


if __name__ == "__main__":
	if len(sys.argv) == 3:
		script = build(parse(sys.argv[1])).format("")

		with open(sys.argv[2], 'w') as o:
			o.write(script)

	elif len(sys.argv) == 4:
		with open(sys.argv[3], 'r') as c:
			css = c.read()

		script = build(parse(sys.argv[1])).format(css)

		with open(sys.argv[2], 'w') as o:
			o.write(script)

	else:
		print "Incorrect number of arguments!"
