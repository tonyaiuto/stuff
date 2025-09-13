

unmask:
	@python3 unmask.py key.txt puzzle1.txt
	@python3 unmask.py key.txt puzzle2.txt
	@python3 unmask.py key.txt puzzle3.txt

x:
	python3 gen_convert.py

# Tool to tell me the punches
punch_guide:
	python3 guide.py <google.txt

sample:
	./punch.py '0123456789 abcdefghijklmnopqrstuvwxyz +- / .,'

test:
	python3 punch_test.py


# Convert a card image to an svg so we can try to laser cut it
# This is a bad idea. The cutter is precise, but the burn holes
# are ugly.
google.svg:	punch2svg.py google.txt
	./punch2svg.py <google.txt >$@
