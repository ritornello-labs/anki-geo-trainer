WORKBENCH ?= uvx --from 'anki-addon-workbench[gui]==0.4.1' anki-workbench
DOCKER_IMAGE ?= anki-geo-trainer-workbench
WORKBENCH_DOCKERFILE ?= .tmp/anki-workbench/Dockerfile

.PHONY: help bundle apkg apkg-all lint test workbench-dockerfile workbench-smoke check clean

help:
	@printf "GeoTrainer make targets:\n"
	@printf "  make bundle            Build scope bundles (data/bundles/*.json)\n"
	@printf "  make apkg              Build the per-scope APKGs into dist/\n"
	@printf "  make apkg-all          Also build the combined geo-trainer-all.apkg (AnkiWeb)\n"
	@printf "  make lint              Static analysis of the Python build scripts (ruff)\n"
	@printf "  make test              Cross-engine Playwright tests (Chromium + WebKit)\n"
	@printf "  make workbench-smoke   Build APKG and run disposable Anki deck smoke in Docker\n"
	@printf "  make check             lint + apkg + test\n"

bundle:
	uv run python scripts/build_bundle.py

apkg: bundle
	uv run python scripts/build_apkg.py
	uv run python scripts/emit_card_fixture.py

apkg-all: bundle
	uv run python scripts/build_apkg.py --combined
	uv run python scripts/emit_card_fixture.py

lint:
	uv run ruff check scripts/

# Playwright 1.52 deadlocks silently (no error, no timeout) before loading any
# test file on Node 22+. The volta pin (package.json) keeps this on Node 20;
# this guard fails fast with guidance if some other Node is on PATH, so `make
# test` can never hang.
test:
	@node -e 'var m=+process.versions.node.split(".")[0]; if(m>=22){console.error("\n[geo-trainer] Playwright 1.52 hangs on Node "+process.versions.node+". Use Node 20 (pinned in package.json via Volta).\n  volta install node@20   # or: nvm use 20\n");process.exit(1)}'
	npx playwright test

workbench-dockerfile:
	$(WORKBENCH) dockerfile --out $(WORKBENCH_DOCKERFILE)

workbench-smoke: apkg workbench-dockerfile
	docker build -f $(WORKBENCH_DOCKERFILE) -t $(DOCKER_IMAGE) .
	docker run --rm --mount type=bind,source="$(CURDIR)",target=/workspace -w /workspace $(DOCKER_IMAGE)

check: lint apkg test

clean:
	rm -rf dist .tmp test-results test-out.json test-err.log
