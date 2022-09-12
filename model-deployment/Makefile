quality_checks:
	find . -type f -name "*.py" | xargs pipenv run pylint
	pipenv run black .
	pipenv run isort .

unit_tests: quality_checks
	pipenv run pytest tests/ 

integration_tests: unit_tests
	bash ./integration-tests/run.sh
