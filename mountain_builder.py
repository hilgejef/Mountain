# MOUNTAIN BUILDER
# The Mountain builder expects a script class (list of blocks 
# containing text elements), loops through the blocks and builds
# an html string. 


from mountain_parser import parse
import re


### MARKUP REGEX DEFINITIONS

r_bold_and_italic = re.compile(r'\*\*\*(.+)\*\*\*')
r_bold = re.compile(r'\*\*([^*]+)\*\*')
r_italic = re.compile(r'\*([^*]+)\*')
r_underline = re.compile(r'\_(.+)\_')

markups = [
	("BoldItalic", r_bold_and_italic),
	("Bold", r_bold),
	("Italic", r_italic),
	("Underline", r_underline)
]


### HTML STRING

html_string = \
"""
<html>
	<head>
		<title>{}</title>
		<style>{{}}</style>
	</head>

	<body>
		<div id="Script">
		{}
		</div>
	</body>
</html>
"""


### BUILDER

# Helper function for use with markup regex
def markup_repl(m):
	return """<span class="Element {{}}">{}</span>""".format(m.group(1))

# Accepts a list of script blocks and returns a completed
# html string
def build(s):
	title_string = ""

	blocks = ""
	for block in s.blocks:
		block_string = """<div class="Block {}">{}</div>"""

		elements = ""
		for element in block.elements:
			
			if block.type == "TitlePage":
				if element.type == "Title":
					title_string = element.text

			element_string = """<div class="Element {}">{}</div>"""

			for markup in markups:
				name, pattern = markup

				if re.match(pattern, element.text):
					element.text = re.sub(pattern, markup_repl, element.text)
					element.text = element.text.format(name)

			elements += element_string.format(element.type, element.text)


		blocks += block_string.format(block.type, elements)

	return html_string.format(title_string, blocks)

if __name__ == "__main__":
	script = parse("C:\Users\Hilger\Dropbox\MyScripts\Test.fountain")
	print build(script)