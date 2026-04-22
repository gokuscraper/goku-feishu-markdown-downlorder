config:
	python mian.py config set

auth:
	python mian.py auth

tui:
	python mian.py tui

upload:
	rm -rf dist && python -m build  && twine upload dist/*
