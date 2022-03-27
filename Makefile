SHELL := /bin/bash

.PHONY: run
run: venv
	CHANNEL_IDS='953241687814197278' USER_INVESTIGATION_CHANNELS='953241687814197278' ./venv/bin/python src/bot.py

.PHONY: deploy_run
deploy_run: venv
	rsync -av --force --delete src/ ./build
	CHANNEL_IDS='954779897123966997' USER_INVESTIGATION_CHANNELS='847155652702765067' ./venv/bin/python build/bot.py

venv: venv/bin/activate

venv/bin/activate: src/requirements.txt
	python3 -m pip install virtualenv
	python3 -m virtualenv -p python3 venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r "src/requirements.txt"

clean:
	rm -rf venv build __pycache__
	find -iname "*.pyc" -delete
	find -iname "__pycache__" -delete
