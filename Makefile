SHELL := /bin/bash

.PHONY: run
run: venv
	$(VENV)/python src/superstonkDiscordModerationBot.py

.PHONY: force_pull
force_pull:
	git fetch --all
	git reset --hard origin/main
	git pull --rebase

.PHONY: bot
bot: force_pull run

.PHONY: test
test: venv
	$(VENV)/pytest -vv

install:
	mkdir -p ~/.config/systemd/user/
	cp superstonkModerationBot.service ~/.config/systemd/user/
	systemctl --user daemon-reload
	systemctl --user enable superstonkModerationBot.service
	systemctl --user start superstonkModerationBot.service
	sudo loginctl enable-linger $USER


clean: clean-venv
	find -iname "*.pyc" -delete
	find -iname "__pycache__" -delete
	rm -rf .pytest_cache

include Makefile.venv