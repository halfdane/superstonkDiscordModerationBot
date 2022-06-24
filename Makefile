SHELL := /bin/bash

.PHONY: run
run: venv
	-/usr/bin/pkill -f "python src/superstonkDiscordModerationBot.py" || true
	venv/bin/python src/superstonkDiscordModerationBot.py

.PHONY: force_pull
force_pull:
	git fetch --all
	git reset --hard origin/main
	git pull --rebase

.PHONY: bot
bot: force_pull run

.PHONY: test
test: venv
	venv/bin/pytest -vv

install:
	mkdir -p ~/.config/systemd/user/
	cp superstonkModerationBot.service ~/.config/systemd/user/
	systemctl --user daemon-reload
	systemctl --user enable superstonkModerationBot.service
	systemctl --user start superstonkModerationBot.service


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
