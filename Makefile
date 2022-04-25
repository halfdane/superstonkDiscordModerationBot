SHELL := /bin/bash

.PHONY: run
run: venv
	-/usr/bin/pkill -f "python src/superstonkDiscordModerationBot.py"
	./venv/bin/python src/superstonkDiscordModerationBot.py

install:
	cp superstonkModerationBot.service /etc/systemd/system/
	systemctl daemon-reload
	systemctl enable superstonkModerationBot.service
	systemctl start superstonkModerationBot.service

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
