.PHONY: test test-keep-alive test-stop help

help:
	@echo "Budget.rip Backend - Available commands:"
	@echo ""
	@echo "  make test            Run tests with automatic database setup and cleanup"
	@echo "  make test-keep-alive Run tests and keep databases running after"
	@echo "  make test-stop       Stop test databases"
	@echo "  make help            Show this help message"
	@echo ""
	@echo "For more options, run: python run_tests.py --help"

test:
	python run_tests.py

test-keep-alive:
	python run_tests.py --keep-alive

test-stop:
	python run_tests.py --stop-only
