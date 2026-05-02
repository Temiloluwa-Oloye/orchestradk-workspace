# OrchestrADK Project Structure Setup Script (PowerShell)
# This script creates the complete directory structure and empty files

Write-Host "Creating OrchestrADK project structure..." -ForegroundColor Green

# Create root-level files
New-Item -ItemType File -Path "README.md" -Force | Out-Null
New-Item -ItemType File -Path "pyproject.toml" -Force | Out-Null
New-Item -ItemType File -Path "requirements.txt" -Force | Out-Null

# Create src/orchestradk structure
New-Item -ItemType Directory -Path "src/orchestradk/orchestrator" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/__init__.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/orchestrator/__init__.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/orchestrator/coordinator.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/orchestrator/router.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/orchestrator/validator.py" -Force | Out-Null

# Create agents structure
New-Item -ItemType Directory -Path "src/orchestradk/agents/scaffolder/templates" -Force | Out-Null
New-Item -ItemType Directory -Path "src/orchestradk/agents/configurator/templates" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/agents/__init__.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/agents/base_agent.py" -Force | Out-Null

# Scaffolder agent files
New-Item -ItemType File -Path "src/orchestradk/agents/scaffolder/__init__.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/agents/scaffolder/agent.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/agents/scaffolder/parser.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/agents/scaffolder/generator.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/agents/scaffolder/templates/state.py.jinja2" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/agents/scaffolder/templates/nodes.py.jinja2" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/agents/scaffolder/templates/graph.py.jinja2" -Force | Out-Null

# Configurator agent files
New-Item -ItemType File -Path "src/orchestradk/agents/configurator/__init__.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/agents/configurator/agent.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/agents/configurator/yaml_generator.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/agents/configurator/json_generator.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/agents/configurator/schema_validator.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/agents/configurator/templates/agent.yaml.jinja2" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/agents/configurator/templates/skills.yaml.jinja2" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/agents/configurator/templates/config.json.jinja2" -Force | Out-Null

# Create adk structure
New-Item -ItemType Directory -Path "src/orchestradk/adk" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/adk/__init__.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/adk/integration.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/adk/schemas.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/adk/validators.py" -Force | Out-Null

# Create llm structure
New-Item -ItemType Directory -Path "src/orchestradk/llm" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/llm/__init__.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/llm/client.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/llm/prompts.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/llm/watsonx.py" -Force | Out-Null

# Create utils structure
New-Item -ItemType Directory -Path "src/orchestradk/utils" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/utils/__init__.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/utils/file_ops.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/utils/logging.py" -Force | Out-Null
New-Item -ItemType File -Path "src/orchestradk/utils/exceptions.py" -Force | Out-Null

# Create cli structure
New-Item -ItemType Directory -Path "src/cli" -Force | Out-Null
New-Item -ItemType File -Path "src/cli/__init__.py" -Force | Out-Null
New-Item -ItemType File -Path "src/cli/main.py" -Force | Out-Null

# Create tests structure
New-Item -ItemType Directory -Path "tests/unit" -Force | Out-Null
New-Item -ItemType Directory -Path "tests/integration" -Force | Out-Null
New-Item -ItemType Directory -Path "tests/fixtures/expected_outputs" -Force | Out-Null
New-Item -ItemType File -Path "tests/__init__.py" -Force | Out-Null
New-Item -ItemType File -Path "tests/unit/test_scaffolder.py" -Force | Out-Null
New-Item -ItemType File -Path "tests/unit/test_configurator.py" -Force | Out-Null
New-Item -ItemType File -Path "tests/unit/test_orchestrator.py" -Force | Out-Null
New-Item -ItemType File -Path "tests/integration/test_end_to_end.py" -Force | Out-Null
New-Item -ItemType File -Path "tests/integration/test_adk_integration.py" -Force | Out-Null
New-Item -ItemType File -Path "tests/fixtures/sample_requests.json" -Force | Out-Null

# Create output directory
New-Item -ItemType Directory -Path "output" -Force | Out-Null
New-Item -ItemType File -Path "output/.gitkeep" -Force | Out-Null

# Create docs structure
New-Item -ItemType Directory -Path "docs/examples" -Force | Out-Null
New-Item -ItemType File -Path "docs/architecture.md" -Force | Out-Null
New-Item -ItemType File -Path "docs/agent_specifications.md" -Force | Out-Null
New-Item -ItemType File -Path "docs/adk_integration.md" -Force | Out-Null
New-Item -ItemType File -Path "docs/examples/simple_agent.md" -Force | Out-Null
New-Item -ItemType File -Path "docs/examples/complex_workflow.md" -Force | Out-Null

# Create config structure
New-Item -ItemType Directory -Path "config/adk_schemas" -Force | Out-Null
New-Item -ItemType File -Path "config/adk_schemas/agent_schema.json" -Force | Out-Null
New-Item -ItemType File -Path "config/adk_schemas/skill_schema.json" -Force | Out-Null
New-Item -ItemType File -Path "config/llm_config.yaml" -Force | Out-Null

# Create .bob mode-specific rules directories
New-Item -ItemType Directory -Path ".bob/rules-code" -Force | Out-Null
New-Item -ItemType Directory -Path ".bob/rules-advance" -Force | Out-Null
New-Item -ItemType Directory -Path ".bob/rules-ask" -Force | Out-Null
New-Item -ItemType Directory -Path ".bob/rules-plan" -Force | Out-Null
New-Item -ItemType File -Path ".bob/rules-code/AGENTS.md" -Force | Out-Null
New-Item -ItemType File -Path ".bob/rules-advance/AGENTS.md" -Force | Out-Null
New-Item -ItemType File -Path ".bob/rules-ask/AGENTS.md" -Force | Out-Null
New-Item -ItemType File -Path ".bob/rules-plan/AGENTS.md" -Force | Out-Null

Write-Host "`n✅ Project structure created successfully!" -ForegroundColor Green
Write-Host "`nDirectory structure created as per AGENTS.md specification" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Review the created structure" -ForegroundColor White
Write-Host "2. Begin Phase 1 implementation" -ForegroundColor White
Write-Host "3. Initialize git repository if needed" -ForegroundColor White
Write-Host "`nRun 'tree /F /A' to view the complete structure" -ForegroundColor Gray

# Made with Bob
