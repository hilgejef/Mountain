# MOUNTAIN PARSER
# The Mountain parser expects a text file formatted in the
# Fountain screenwriting language, and outputs a script class (list of
# blocks containing text elements). See the class definitions
# for more information.


import re


### CLASS DEFINITIONS

class Script:
	def __init__(self):
		self.blocks = []

	def __repr__(self):
		return "".join(['\t{}\n{}'.format(block.type, str(block)) for block in self.blocks])

	def prevBlock(self):
		return self.blocks[-2] if len(self.blocks) > 1 else None

	def currentBlock(self):
		return self.blocks[-1] if self.blocks else None

	def addBlock(self):
		self.blocks.append(Block())

# 8 block types - Boneyard, Character, DualCharacter, LineBreak, PageBreak,
# 				  TitlePage, and Text(Standard/Other)
class Block:
	def __init__(self, blockType=""):
		self.elements = []
		self.type = blockType

	def __repr__(self):
		elements = "\n".join([str(element) for element in self.elements])
		return elements

	def currentElement(self):
		if len(self.elements) == 0:
			return None

		return self.elements[-1]

	def addElement(self, element):
		self.elements.append(element)

	def containsElement(self, eletype):
		for element in self.elements:
			if element.type == eletype:
				break
		else:
			return False
		return True

	def setElementsTo(self, eletype):
		for element in self.elements:
			element.type = eletype

class Element:
	def __init__(self, eletype, text):
		self.type = eletype
		self.text = text

	def __repr__(self):
		return "\t{}: {}".format(self.type, self.text)


### TITLE PAGE REGEX DEFINITIONS

r_title_key_value = re.compile(r'^(.+)\: (.+)$')
r_titlekey = re.compile(r'^([^:]+)\:$')
r_titlevalue = re.compile(r'^(\t|   )[\s]*(.+)$')
r_titlebreak = re.compile(r'^$')

titleregs = [
	("Key", r_titlekey),
	("KeyValue", r_title_key_value),
	("Value", r_titlevalue)
]


### ELEMENT REGEX DEFINITIONS

# FORCED REGEXES
r_forced_heading = re.compile(r'^\.(.+)$')
r_forced_action = re.compile(r'^\!(.+)$')
r_forced_character = re.compile(r'^\@(.+)$')
r_forced_lyrics = re.compile(r'^\~(.+)$')
r_forced_transition = re.compile(r'^\>(.+)[^<]$')

# STANDARD REGEXES
r_heading = re.compile(r'^((?:(?:EXT|EST.?)|(?:INT\.?(?:\/EXT.?)?)|(?:I\.?\/E\.?)).+)$', re.IGNORECASE)
r_char = re.compile(r'^([^a-z]+)$')
r_transition = re.compile(r'^([^a-z]+TO:)$')
r_parenthetical = re.compile(r'^(\(.+\))$')
r_center = re.compile(r'\>\s*(.+)\s*\<')
r_pagebreak = re.compile(r'^(\=\=\=)$')
r_text = re.compile(r'^(.+)$')
r_linebreak = re.compile(r'^$')

regexs = [
	("PageBreak", r_pagebreak),
	("Heading", r_forced_heading),
	("Action", r_forced_action),
	("Character", r_forced_character),
	("Lyrics", r_forced_lyrics),
	("Transition", r_forced_transition),
	("Heading", r_heading), 
	("Transition", r_transition), 
	("Center", r_center),
	("Character", r_char), 
	("Parenthetical", r_parenthetical),
	("Text", r_text), 
	("LineBreak", r_linebreak)
]

# Additional dual dialogue regex, only used in the situation where
# eletype is Character and prevBlock is Character. 
r_dual = re.compile(r'^([^a-z]+)\^$')


### DISCARD REGEX DEFINITIONS

r_boneyard_start = re.compile(r'^(.*)(\/\*.*)$')
r_boneyard_end = re.compile(r'^(.*\*\/)(.*)$')
r_boneyard_start_end = re.compile(r'^(.*)(\/\*.*\*\/)(.*)$')
r_note_start = re.compile(r'^(.*)(\[\[.*)$')
r_note_end = re.compile(r'^(.*\]\])(.*)$')
r_note_start_end = re.compile(r'^(.*)(\[\[.*\]\])(.*)$')
r_section = re.compile(r'^(\#.*)$')
r_synopsis = re.compile(r'^\=(?!\=\=).*$')

# The discard group of regexes is for elements that should not appear
# in the resulting pdf/html/etc. They are ultimately discarded 
# because they are "useless" to the transpiler and meant, like
# programming language comments, only for the writer/programmer.
discards = [
	("BoneStart", r_boneyard_start),
	("BoneEnd", r_boneyard_end),
	("BonedStartEnd", r_boneyard_start_end),
	("NoteStart", r_note_start),
	("NoteEnd", r_note_end),
	("NoteStartEnd", r_note_start_end),
	("Section", r_section),
	("Synopsis", r_synopsis)
]


### PARSING FUNCTIONS

def parse(filename):
	# Initialize script and starting block
	script = Script()
	script.addBlock()
	currentBlock = script.currentBlock()

	# These booleans are used to determine if the starting lines
	# are part of a title page (defined as k: v pairs, or k: and 
	# an indeterminate amount of \tv lines)
	checkTitle = True
	isTitlePage = False

	# These booleans are used to determine if the current line is
	# part of the boneyard or part of a note. Notes can only span carriage 
	# returns, but boneyard can span line breaks.
	isBoneyard = False
	isNote = False

	# Discarded elements should consume the next linebreak. This boolean
	# provides that functionality.
	consumeLineBreak = False

	# Open file, read line by line
	with open(filename) as fountain:
		for line in fountain:

			line = line.rstrip('\n')

			# Boneyard handler -- since the boneyard (defined as
			# /* followed by */) overrides everything, it should
			# be checked and handled first.
			# Boneyards can be inline and span multiple lines.
			if isBoneyard:
				# Check if the boneyard ends. If it doesn't, skip
				# the line (it's not needed).
				match = re.match(r_boneyard_end, line)

				# Case 1 - No match, skip to next line
				if not match:
					continue
				else:
					isBoneyard = False

					# Case 2 - Boneyard end found, after match
					if match.group(2):
						line = match.group(2)
					# Case 3 - Boneyard end found, no after match
					# Just continue to the next line
					else:
						continue

			# Now check for boneyard start/ends
			match = re.match(r_boneyard_start_end, line)

			if match:
				# Case 1 - Before/After boneyard matches
				if match.group(1) and match.group(3):
					line = "{}{}".format(match.group(1), match.group(3))

				# Case 2 - Before boneyard match
				elif match.group(1):
					line = match.group(1)

				# Case 3 - After boneyard match
				elif match.group(3):
					line = match.group(3)

				# Case 4 - Neither before/after match
				# In this case just skip through to the next line.
				else:
					continue

			# Check for boneyard starts
			match = re.match(r_boneyard_start, line)

			if match:
				isBoneyard = True

				# Case 1 - Before boneyard start match
				if match.group(1):
					line = match.group(1)
				# Case 2 - No before boneyard -- discard line
				else:
					continue

			# Note section -- notes are similar to the boneyard,
			# excepting that when a line break occurs, the note
			# section ends.
			if isNote:
				# Check if the note ends. If it doesn't, skip the
				# line completely.
				match = re.match(r_note_end, line)

				# Case 1 - No match
				if not match:
					# Line break check here is necessary because notes
					# can not span line breaks
					match = re.match(r_linebreak, line)
					if match:
						isNote = False

					continue
				else:
					isNote = False

					# Case 2 - Note end found, after match found
					if match.group(2):
						line = match.group(2)

					# Case 3 - Note end found, no after match
					else:
						continue

			# Now look for note start/ends and discard them
			match = re.match(r_note_start_end, line)

			if match:
				# Case 1 - Before/after note matches
				if match.group(1) and match.group(3):
					line = "{}{}".format(match.group(1), match.group(3))

				# Case 2 - Before note match
				elif match.group(1):
					line = match.group(1)

				# Case 3 - After match
				elif match.group(3):
					line = match.group(3)

				# Case 4 - No before/after match
				# Just skip to the next line
				else:
					continue

			# Now look for note starts
			match = re.match(r_note_start, line)

			if match:
				isNote = True

				# Case 1 - before note match
				if match.group(1):
					line = match.group(1)

				# Case 2 - no before match
				else:
					continue

			# Last of the discard steps, check for sections/synopses
			# and then discard them
			match = re.match(r_section, line)

			if match:
				continue

			match = re.match(r_synopsis, line)

			if match:
				continue

			# Title page section -- check if there's a title page
			# then loop through until it's done.
			if checkTitle:
				for titlereg in titleregs[:2]:
					eletype, pattern = titlereg

					if re.match(pattern, line):
						isTitlePage = True
						currentBlock.type = "TitlePage"
				checkTitle = False

			if isTitlePage:
				for titlereg in titleregs:
					eletype, pattern = titlereg

					match = re.match(pattern, line)
					
					if match:

						# Determine if match is k, kv, or v and 
						# respond appropriately
						if eletype == "Key":
							key = match.group(1)

						elif eletype == "KeyValue":
							key = match.group(1)
							value = match.group(2)

							element = Element(key, value)
							currentBlock.addElement(element)

						elif eletype == "Value": 
							value = match.group(2)

							element = Element(key, value)
							currentBlock.addElement(element)

						break

				# No more title page matches, begin main section
				else:
					isTitlePage = False
					script.addBlock()
					currentBlock = script.currentBlock()

				# Check the next line, continue trying to match
				# title page regexes if isTitlePage	
				continue

			# Default matching section, looks for character/heading
			# /parenthetical/text/transitions/linebreaks/etc
			# Go through each regex pattern and match against line
			for regex in regexs:
				eletype, pattern = regex
				match = re.match(pattern, line)

				if match:

					# Set matched text to the first matching group, 
					# if there is a matching group, otherwise ""
					# Generally set to "" when there's a line break
					if match.groups():
						matchText = match.group(1)
					else: 
						matchText = ""

					# Redetermine eletype if it's Text based on whether
					# this is a Character or Text block
					if eletype == "Text":
						if "Character" in currentBlock.type:
							eletype = "Dialogue"
						else:
							eletype = "Action"

					# If the eletype is Character, a check needs to
					# be performed here to see if this is a dual
					# dialogue element.
					if eletype == "Character":
						matchDual = re.match(r_dual, line)
						prevBlock = script.prevBlock()

						if matchDual and prevBlock and prevBlock.type == "Character":
							prevBlock.type = "DualCharacter"
							currentBlock.type = "DualCharacter"
							line = matchDual.group(1)

					# Create the element using eletype and line
					element = Element(eletype, matchText)

					# Line breaks close blocks and add new blocks
					# If current block has no type and eletype is 
					# line break, then a linebreak block is added
					if eletype == "LineBreak":

						# Just continue if it doesn't need to close a block
						if not currentBlock.type:
							continue

						# Handle the situation where character block
						# does not contain a corresponding dialogue
						# element (i.e. it should be action)
						elif "Character" in currentBlock.type:
							if not currentBlock.containsElement("Dialogue"):
								currentBlock.type = "Text"
								currentBlock.setElementsTo("Action")

						script.addBlock()
						currentBlock = script.currentBlock()

					# If the current block is a line break, a new
					# block is added. Otherwise, the element is 
					# appended to the current block. 
					else:
						if not currentBlock.type:
							if eletype == "Character":	
								currentBlock.type = eletype
							else:
								currentBlock.type = "Text"

						currentBlock.addElement(element)

					# Stop matching regexes once a match has been 
					# found.
					break

		# Else block handles end of loop code, most importantly it corrects
		# the last element 
		else:
			# Handle case where block matching character regex is followed by EOF
			# without corresponding dialogue element, i.e. it should be action (text)
			if "Character" in currentBlock.type:
				if not currentBlock.containsElement("Dialogue"):
					currentBlock.type = "Text"
					currentBlock.setElementsTo("Action")

	return script


### MAIN PROGRAM FLOW

if __name__ == "__main__":
	### HARDCODED FILE FOR NOW
	script = parse("C:\Users\Hilger\Dropbox\MyScripts\Test.fountain")

	for block in script.blocks:
		print "{}\n{}".format(block.type, block)
