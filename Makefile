clean-notebooks:
	jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace notebooks/*.ipynb

clean:
	rm -rf dist build *.egg-info

build:
	hatch build

publish:
	twine upload dist/*

sync:
	bash scripts/sync.sh