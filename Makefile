.PHONY: run cli icon app clean

run:
	python3 -m apple_lyrics

cli:
	python3 -m apple_lyrics --cli

icon:
	python3 scripts/make_icon.py

app: icon
	pyinstaller --clean --noconfirm apple_lyrics.spec
	@echo "\nBuild complete → dist/Apple Lyrics.app"
	@echo "Drag to /Applications to install."

clean:
	rm -rf build dist __pycache__ apple_lyrics/__pycache__
