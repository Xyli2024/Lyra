_PLIST     = com.xinyuli.lyra.daemon.plist
_AGENTS    = $(HOME)/Library/LaunchAgents

.PHONY: run cli icon app install install-daemon uninstall-daemon clean

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

install-daemon:
	@cp $(_PLIST) $(_AGENTS)/
	@launchctl load -w $(_AGENTS)/$(_PLIST)
	@echo "Daemon installed and started. Logs: /tmp/lyra-daemon.log"

uninstall-daemon:
	@launchctl unload -w $(_AGENTS)/$(_PLIST) 2>/dev/null || true
	@rm -f $(_AGENTS)/$(_PLIST)
	@echo "Daemon removed."

clean:
	rm -rf build dist __pycache__ lyra/__pycache__
