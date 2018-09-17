
.PHONY: lint
lint:
	-pylava libestg3b test
	-isort --recursive --check-only libestg3b test

.PHONY: fixlint
fixlint:
	-isort --recursive libestg3b test

.PHONY: test
test:
	-py.test test
