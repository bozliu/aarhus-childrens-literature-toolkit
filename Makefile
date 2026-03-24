SHELL := /bin/zsh

.PHONY: \
	setup bootstrap bootstrap-python bootstrap-r inventory manifest legacy modern readme report smoke python-assets release-assets \
	py-inventory py-manifest py-legacy py-modern py-render py-report \
	r-legacy r-modern r-readme r-report install-backends

setup:
	./scripts/setup_dl_runtime.sh

bootstrap: bootstrap-python bootstrap-r

bootstrap-python:
	./scripts/bootstrap_python.sh

bootstrap-r:
	./scripts/run_r.sh scripts/bootstrap.R

py-inventory:
	conda run -n dl python -m childlit_toolkit inventory

inventory: py-inventory

py-manifest:
	conda run -n dl python -m childlit_toolkit manifest

manifest: py-manifest

python-assets:
	conda run -n dl python -m childlit_toolkit all

py-legacy:
	conda run -n dl python -m childlit_toolkit legacy

legacy:
	./scripts/run_entrypoint.sh legacy

r-legacy:
	./scripts/run_r.sh scripts/run_targets.R legacy

py-modern:
	conda run -n dl python -m childlit_toolkit modern

modern:
	./scripts/run_entrypoint.sh modern

r-modern:
	./scripts/run_r.sh scripts/run_targets.R modern

py-render:
	conda run -n dl python -m childlit_toolkit render

readme:
	./scripts/run_entrypoint.sh readme

r-readme:
	./scripts/run_r.sh scripts/render_readme.R

py-report:
	conda run -n dl python -m childlit_toolkit report

report:
	./scripts/run_entrypoint.sh report

r-report:
	./scripts/run_r.sh scripts/render_report.R

release-assets: python-assets readme report

install-backends:
	./scripts/install_modern_backends.sh

smoke:
	conda run -n dl python -m childlit_toolkit smoke
