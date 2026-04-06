.PHONY: install test lint fmt lat-install lat-check lat-policy

install:
	pip install -e ".[all,dev]"

test:
	pytest tests/ -v

lint:
	ruff check agent_evolve/

fmt:
	ruff format agent_evolve/

# lat.md knowledge graph
lat-install:
	@command -v lat >/dev/null 2>&1 && echo "lat already installed" || npm install -g --prefix $$HOME/.npm-global lat.md
	@git config core.hooksPath .githooks
	@echo "Done. lat.md and git hooks ready."

lat-check:
	@export LAT_LLM_KEY=$${LAT_LLM_KEY:-unused} && lat check

lat-policy:
	@STAGED="$$(git diff --cached --name-only)"; \
	if [ -n "$$STAGED" ]; then \
		NEEDS=0; HAS=0; \
		echo "$$STAGED" | grep -qE '(^\.github/workflows/|^ansible/|^scripts/|^deploy/|Makefile|Dockerfile|docker-compose\.ya?ml|flake\.nix|shell\.nix|^agent_evolve/llm/|^agent_evolve/engine/)' && NEEDS=1 || true; \
		echo "$$STAGED" | grep -qE '^lat\.md/' && HAS=1 || true; \
		if [ "$$NEEDS" -eq 1 ] && [ "$$HAS" -eq 0 ]; then \
			echo "BLOCKED: infra/engine files staged but lat.md/ not updated."; \
			exit 1; \
		fi; \
	fi
	@echo "lat sync policy OK"
