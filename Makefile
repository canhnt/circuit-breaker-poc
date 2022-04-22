.PHONY: lint
lint:
	pycodestyle ./**/*.py

.PHONY: test
test:
	python3 -m unittest discover -s ./src -p 'test_*.py'
