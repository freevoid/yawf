.PHONY: test coverage_test docs

MANAGE_PY := ./yawf_sample/manage.py

test:
	$(MANAGE_PY) test yawf simple

coverage_test:
	coverage erase
	coverage run $(MANAGE_PY) test yawf simple
	coverage html

docs:
	sphinx-apidoc -F -o docs yawf
	cd docs && make html
