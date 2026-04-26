.PHONY: run cli icon app install clean

run:
	python3 -m lyra

cli:
	python3 -m lyra --cli

icon:
	python3 scripts/make_icon.py

app: icon
	pyinstaller --clean --noconfirm lyra.spec
	@echo "\nBuild complete → dist/Lyra.app"
	@echo "Drag to /Applications to install."

install:
	@printf '#!/bin/zsh\nPYTHONPATH=$(CURDIR) \\\nexec /opt/homebrew/opt/python@3.12/bin/python3.12 -m lyra "$$@"\n' > /opt/homebrew/bin/lyra
	@chmod +x /opt/homebrew/bin/lyra
	@echo "Installed: lyra command → /opt/homebrew/bin/lyra"

clean:
	rm -rf build dist __pycache__ lyra/__pycache__
