#!/bin/bash

# OrchestrADK Project Structure Setup Script
# This script creates the complete directory structure and empty files

echo "Creating OrchestrADK project structure..."

# Create root-level files
touch README.md
touch pyproject.toml
touch requirements.txt

# Create src/orchestradk structure
mkdir -p src/orchestradk/orchestrator
touch src/orchestradk/__init__.py
touch src/orchestradk/orchestrator/__init__.py
touch src/orchestradk/orchestrator/coordinator.py
touch src/orchestradk/orchestrator/router.py
touch src/orchestradk/orchestrator/validator.py

# Create agents structure
mkdir -p src/orchestradk/agents/scaffolder/templates
mkdir -p src/orchestradk/agents/configurator/templates
touch src/orchestradk/agents/__init__.py
touch src/orchestradk/agents/base_agent.py

# Scaffolder agent files
touch src/orchestradk/agents/scaffolder/__init__.py
touch src/orchestradk/agents/scaffolder/agent.py
touch src/orchestradk/agents/scaffolder/parser.py
touch src/orchestradk/agents/scaffolder/generator.py
touch src/orchestradk/agents/scaffolder/templates/state.py.jinja2
touch src/orchestradk/agents/scaffolder/templates/nodes.py.jinja2
touch src/orchestradk/agents/scaffolder/templates/graph.py.jinja2

# Configurator agent files
touch src/orchestradk/agents/configurator/__init__.py
touch src/orchestradk/agents/configurator/agent.py
touch src/orchestradk/agents/configurator/yaml_generator.py
touch src/orchestradk/agents/configurator/json_generator.py
touch src/orchestradk/agents/configurator/schema_validator.py
touch src/orchestradk/agents/configurator/templates/agent.yaml.jinja2
touch src/orchestradk/agents/configurator/templates/skills.yaml.jinja2
touch src/orchestradk/agents/configurator/templates/config.json.jinja2

# Create adk structure
mkdir -p src/orchestradk/adk
touch src/orchestradk/adk/__init__.py
touch src/orchestradk/adk/integration.py
touch src/orchestradk/adk/schemas.py
touch src/orchestradk/adk/validators.py

# Create llm structure
mkdir -p src/orchestradk/llm
touch src/orchestradk/llm/__init__.py
touch src/orchestradk/llm/client.py
touch src/orchestradk/llm/prompts.py
touch src/orchestradk/llm/watsonx.py

# Create utils structure
mkdir -p src/orchestradk/utils
touch src/orchestradk/utils/__init__.py
touch src/orchestradk/utils/file_ops.py
touch src/orchestradk/utils/logging.py
touch src/orchestradk/utils/exceptions.py

# Create cli structure
mkdir -p src/cli
touch src/cli/__init__.py
touch src/cli/main.py

# Create tests structure
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/fixtures/expected_outputs
touch tests/__init__.py
touch tests/unit/test_scaffolder.py
touch tests/unit/test_configurator.py
touch tests/unit/test_orchestrator.py
touch tests/integration/test_end_to_end.py
touch tests/integration/test_adk_integration.py
touch tests/fixtures/sample_requests.json

# Create output directory
mkdir -p output
touch output/.gitkeep

# Create docs structure
mkdir -p docs/examples
touch docs/architecture.md
touch docs/agent_specifications.md
touch docs/adk_integration.md
touch docs/examples/simple_agent.md
touch docs/examples/complex_workflow.md

# Create config structure
mkdir -p config/adk_schemas
touch config/adk_schemas/agent_schema.json
touch config/adk_schemas/skill_schema.json
touch config/llm_config.yaml

# Create .bob mode-specific rules directories
mkdir -p .bob/rules-code
mkdir -p .bob/rules-advance
mkdir -p .bob/rules-ask
mkdir -p .bob/rules-plan
touch .bob/rules-code/AGENTS.md
touch .bob/rules-advance/AGENTS.md
touch .bob/rules-ask/AGENTS.md
touch .bob/rules-plan/AGENTS.md

echo "✅ Project structure created successfully!"
echo ""
echo "Directory tree:"
echo "==============="

# Display the created structure (works on both Unix and Windows with Git Bash)
if command -v tree &> /dev/null; then
    tree -L 3 -I 'bob_sessions'
else
    echo "Note: Install 'tree' command for better visualization"
    echo "Structure created as per AGENTS.md specification"
fi

echo ""
echo "Next steps:"
echo "1. Review the created structure"
echo "2. Begin Phase 1 implementation"
echo "3. Initialize git repository if needed"

# Made with Bob
