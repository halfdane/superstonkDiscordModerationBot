SHELL := /bin/bash

.PHONY: run
run: venv
	./venv/bin/python src/superstonkDiscordModerationBot.py

deploy:
	-/usr/bin/pkill -f superstonkDiscordModerationBot
	git pull --rebase
	nohup ./venv/bin/python src/superstonkDiscordModerationBot.py > std.out.log 2> std.err.log &

venv: venv/bin/activate

venv/bin/activate: src/requirements.txt
	python3 -m pip install virtualenv
	python3 -m virtualenv -p python3 venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r "src/requirements.txt"

clean:
	rm -rf venv __pycache__
	find -iname "*.pyc" -delete
	find -iname "__pycache__" -delete
