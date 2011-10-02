.PHONY: test coverage_test

MANAGE_PY := ./yawf_sample/manage.py

test:
	$(MANAGE_PY) test yawf simple

coverage_test:
	coverage run $(MANAGE_PY) test yawf simple
	coverage html
