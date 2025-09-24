# `=`  延遲賦值，不可覆蓋
# `:=` 立即賦值，不可覆蓋
# `?=` 有預設值，可覆蓋
BOLD = \033[1m     # 粗體
GREEN = \033[0;32m # 綠色
NC = \033[0m       # 無色

lint:
	@ruff check --select I --fix
	@ruff format
	@ruff check
	@mypy
	@echo "\n$(GREEN)$(BOLD)🎉 All checks passed! 🎉$(NC)"

fix:
	@ruff check --fix --unsafe-fixes

noqa:
	@ruff check --ignore-noqa

toml-fmt:
	@taplo format -o array_auto_collapse=false -o indent_string="    "


clear_pyc:
	@find . -type d -name "__pycache__" -exec rm -r {} +
	@find . -type d -empty -delete
	@echo "$(GREEN)$(BOLD)All __pycache__ removed!$(NC)"

clear_cache:
	@rm -rf .ruff_cache
	@rm -rf .mypy_cache
	@echo "$(GREEN)$(BOLD)All cache removed!$(NC)"

clear_all: clear_pyc clear_cache


# 單獨更新 lock file
lock_update:
	uv lock --upgrade

# 安裝所有 dependencies
install:
	uv sync --all-groups

update:
	uv run src/x_utils/uv_up.py


# push commit without pre-push but run pre-commit
push:
	pre-commit run --all-files
	git push --no-verify

# dry run generate changelog
ch:
	@python3 ./src/x_utils/_cz_ch.py


run:
	python -m uvicorn src.idcard_extractor.backend.api.web_interface:app --reload  

web:
	streamlit run src/idcard_extractor/frontend/streamlit_app.py


help:
	@echo "lint - run ruff check and ruff format and mypy"
	@echo "fix - run ruff check with --fix and --unsafe-fix"
	@echo "noqa - run ruff check with --ignore-noqa"
	@echo "toml-fmt - format toml file"

	@echo "clear_pyc - remove all __pycache__ directories"
	@echo "clear_cache - remove .ruff_cache, .mypy_cache"
	@echo "clear_all - remove all __pycache__, linter cache"

	@echo "lock_update - update lock file"
	@echo "install - install all dependencies"
	@echo "update - update lock file and install all dependencies"

	@echo "push - run pre-commit and push to remote"
	@echo "ch - print changelog to console"

	@echo "run - run Uvicorn server"
	@echo "web - run Streamlit web interface"

	@echo "help - show this help message"
