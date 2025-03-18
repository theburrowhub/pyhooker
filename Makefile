.PHONY: all help

help: ## This beautiful help
	@echo "Usage: make [command]"
	@echo
	@echo "Commands:"
	@echo
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-32s\033[0m %s\n", $$1, $$2}'

build: pip-install ## Build the application

run: .venv ## Run the application
	. .venv/bin/activate && \
	pip install -r requirements.txt && \
	python app.py

.venv: ## Create a virtual environment
	python3 -m venv .venv

pip-install: .venv ## Install the requirements
	. .venv/bin/activate && pip install -r requirements.txt

pip-freeze: .venv ## Freeze the requirements
	. .venv/bin/activate && pip freeze > requirements.txt

build-binary: pip-install ## Build a standalone binary using PyInstaller
	. .venv/bin/activate && pip install pyinstaller && pyinstaller --onefile --name pyhooker \
		--add-data "templates:templates" \
		--add-data "public:public" \
		pyhooker.py

install-local: build-binary ## Install the binary locally
	sudo cp dist/pyhooker /usr/local/bin/
	@echo "PyHooker has been installed successfully!"
	@echo "You can now run it from anywhere using the 'pyhooker' command."
