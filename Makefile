file = main.py

run:
	python $(file)

edit:
	nvim $(file)

install:
	ln -s $(realpath ./main.py) ~/.local/bin/eink