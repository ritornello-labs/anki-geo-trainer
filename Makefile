WORKBENCH ?= uvx --from 'anki-addon-workbench[gui]==0.4.1' anki-workbench
DOCKER_IMAGE ?= anki-geo-trainer-workbench
WORKBENCH_DOCKERFILE ?= .tmp/anki-workbench/Dockerfile

.PHONY: help bundle apkg test workbench-dockerfile workbench-smoke check clean

help:
	@printf "GeoTrainer make targets:\n"
	@printf "  make bundle            Build scope bundles (data/bundles/*.json)\n"
	@printf "  make apkg              Build the APKG into dist/\n"
	@printf "  make test              Cross-engine Playwright tests (Chromium + WebKit)\n"
	@printf "  make workbench-smoke   Build APKG and run disposable Anki deck smoke in Docker\n"
	@printf "  make check             bundle + apkg + test\n"

bundle:
	uv run python scripts/build_bundle.py

apkg: bundle
	uv run python scripts/build_apkg.py
	uv run python scripts/emit_card_fixture.py

test:
	npx playwright test

workbench-dockerfile:
	$(WORKBENCH) dockerfile --out $(WORKBENCH_DOCKERFILE)

workbench-smoke: apkg workbench-dockerfile
	docker build -f $(WORKBENCH_DOCKERFILE) -t $(DOCKER_IMAGE) .
	docker run --rm --mount type=bind,source="$(CURDIR)",target=/workspace -w /workspace $(DOCKER_IMAGE)

check: apkg test

clean:
	rm -rf dist .tmp test-results test-out.json test-err.log
