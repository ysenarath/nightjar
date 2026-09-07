clean-notebooks:
	jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace notebooks/*.ipynb

clean:
	rm -rf dist build *.egg-info

build:
	uv build

publish:
	uv publish

test:
	uv pip install dist/nightjar-*.whl --force-reinstall
	uv run python -m unittest discover -v -s ./tests -p "test_*.py"
	uv pip install -e .

.PHONY: docs docs-build
docs:
	uv run --group docs mkdocs serve

docs-build:
	uv run --group docs mkdocs build --strict
