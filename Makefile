
.PHONY: lint
lint:
	-pylava libestg3b
	-isort --recursive --check-only libestg3b

.PHONY: fixlint
fixlint:
	-isort --recursive libestg3b
