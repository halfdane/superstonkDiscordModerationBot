SHELL := /bin/bash

.PHONY: run
run: venv
	./venv/bin/python src/bot.py

.PHONY: run_deployed
run_deployed: venv
	./venv/bin/python build/bot.py


.PHONY: deploy
deploy: venv
	rsync -av --force --delete src/ ./build
	cp .live_envrc ./build/.envrc
	cd ./build && direnv allow

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
