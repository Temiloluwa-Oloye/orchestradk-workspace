# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Overview

**OrchestrADK** is an AI-accelerated developer workflow tool that automates the creation of watsonx Orchestrate agents through a multi-agent system architecture.

---

## System Architecture

### Multi-Agent System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                     OrchestrADK System                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Orchestrator Layer                          │  │
│  │  - Task routing and coordination                         │  │
│  │  - Agent communication protocol                          │  │
│  │  - Validation and error handling                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                     │
│           ┌───────────────┴───────────────┐                    │
│           ▼                               ▼                    │
│  ┌─────────────────┐            ┌─────────────────┐           │
│  │   Agent A:      │            │   Agent B:      │           │
│  │  The Scaffolder │            │ The Configurator│           │
│  │                 │            │                 │           │
│  │ - Parse NL      │            │ - Generate YAML │           │
│  │   requests      │            │ - Generate JSON │           │
│  │ - Generate      │            │ - ADK config    │           │
│  │   LangGraph     │            │   files         │           │
│  │   boilerplate   │            │ - Validate      │           │
│  │ - Create Python │            │   schemas       │           │
│  │   modules       │            │                 │           │
│  └─────────────────┘            └─────────────────┘           │
│           │                               │                    │
│           └───────────────┬───────────────┘                    │
│                           ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           watsonx Orchestrate ADK Output                 │  │
│  │  - Python LangGraph implementation                       │  │
│  │  - YAML/JSON configuration files                         │  │
│  │  - Ready-to-deploy agent package                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Responsibilities

#### **Agent A: The Scaffolder**
- **Input**: Natural language developer request
- **Processing**:
  - Parse intent and extract requirements
  - Identify required LangGraph nodes and edges
  - Determine state schema structure
  - Map to ADK patterns
- **Output**: Python LangGraph boilerplate code
  - State definitions
  - Node implementations (stubs)
  - Graph structure
  - Entry/exit points

#### **Agent B: The Configurator**
- **Input**: Scaffolder output + developer requirements
- **Processing**:
  - Generate ADK-compliant YAML configurations
  - Create JSON schema definitions
  - Map LangGraph components to ADK metadata
  - Validate against ADK specifications
- **Output**: Configuration files
  - `agent.yaml` - Agent metadata
  - `skills.yaml` - Skill definitions
  - `config.json` - Runtime configuration
  - `schema.json` - Input/output schemas

---

## Directory Structure

```
orchestradk-workspace/
├── AGENTS.md                          # This file
├── README.md                          # Project documentation
├── pyproject.toml                     # Python project configuration
├── requirements.txt                   # Python dependencies
│
├── src/
│   ├── orchestradk/
│   │   ├── __init__.py
│   │   ├── orchestrator/              # Main orchestration logic
│   │   │   ├── __init__.py
│   │   │   ├── coordinator.py         # Agent coordination
│   │   │   ├── router.py              # Task routing
│   │   │   └── validator.py           # Output validation
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py          # Base agent interface
│   │   │   ├── scaffolder/            # Agent A implementation
│   │   │   │   ├── __init__.py
│   │   │   │   ├── agent.py           # Main scaffolder logic
│   │   │   │   ├── parser.py          # NL request parser
│   │   │   │   ├── generator.py       # Code generation
│   │   │   │   └── templates/         # LangGraph templates
│   │   │   │       ├── state.py.jinja2
│   │   │   │       ├── nodes.py.jinja2
│   │   │   │       └── graph.py.jinja2
│   │   │   │
│   │   │   └── configurator/          # Agent B implementation
│   │   │       ├── __init__.py
│   │   │       ├── agent.py           # Main configurator logic
│   │   │       ├── yaml_generator.py  # YAML generation
│   │   │       ├── json_generator.py  # JSON generation
│   │   │       ├── schema_validator.py # Schema validation
│   │   │       └── templates/         # Config templates
│   │   │           ├── agent.yaml.jinja2
│   │   │           ├── skills.yaml.jinja2
│   │   │           └── config.json.jinja2
│   │   │
│   │   ├── adk/
│   │   │   ├── __init__.py
│   │   │   ├── integration.py         # ADK integration layer
│   │   │   ├── schemas.py             # ADK schema definitions
│   │   │   └── validators.py          # ADK-specific validators
│   │   │
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── client.py              # LLM client wrapper
│   │   │   ├── prompts.py             # Prompt templates
│   │   │   └── watsonx.py             # watsonx.ai integration
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_ops.py            # File operations
│   │       ├── logging.py             # Logging configuration
│   │       └── exceptions.py          # Custom exceptions
│   │
│   └── cli/
│       ├── __init__.py
│       └── main.py                    # CLI entry point
│
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_scaffolder.py
│   │   ├── test_configurator.py
│   │   └── test_orchestrator.py
│   ├── integration/
│   │   ├── test_end_to_end.py
│   │   └── test_adk_integration.py
│   └── fixtures/
│       ├── sample_requests.json
│       └── expected_outputs/
│
├── output/                            # Generated agent outputs
│   └── .gitkeep
│
├── docs/
│   ├── architecture.md
│   ├── agent_specifications.md
│   ├── adk_integration.md
│   └── examples/
│       ├── simple_agent.md
│       └── complex_workflow.md
│
├── config/
│   ├── adk_schemas/                   # ADK schema references
│   │   ├── agent_schema.json
│   │   └── skill_schema.json
│   └── llm_config.yaml                # LLM configuration
│
└── .bob/                              # Mode-specific rules
    ├── rules-code/
    │   └── AGENTS.md
    ├── rules-advance/
    │   └── AGENTS.md
    ├── rules-ask/
    │   └── AGENTS.md
    └── rules-plan/
        └── AGENTS.md
```

---

## Implementation Phases

### **Phase 1: Foundation Setup** (Week 1)

**Objective**: Establish project structure and core infrastructure

**Tasks**:
1. Initialize Python project with [`pyproject.toml`](pyproject.toml)
2. Set up directory structure as defined above
3. Configure logging and exception handling in [`src/orchestradk/utils/`](src/orchestradk/utils/)
4. Implement base agent interface in [`src/orchestradk/agents/base_agent.py`](src/orchestradk/agents/base_agent.py)
5. Create LLM client wrapper in [`src/orchestradk/llm/client.py`](src/orchestradk/llm/client.py)

**Deliverables**:
- Working project skeleton
- Base classes and interfaces
- Configuration files
- Initial test structure

---

### **Phase 2: Agent A - The Scaffolder** (Week 2-3)

**Objective**: Build natural language to LangGraph code generation

**Tasks**:
1. **NL Parser** ([`src/orchestradk/agents/scaffolder/parser.py`](src/orchestradk/agents/scaffolder/parser.py)):
   - Extract intent from developer requests
   - Identify required components (nodes, edges, state)
   - Map to LangGraph patterns

2. **Code Generator** ([`src/orchestradk/agents/scaffolder/generator.py`](src/orchestradk/agents/scaffolder/generator.py)):
   - Create state class definitions
   - Generate node function stubs
   - Build graph structure code
   - Add type hints and docstrings

3. **Template System** ([`src/orchestradk/agents/scaffolder/templates/`](src/orchestradk/agents/scaffolder/templates/)):
   - Jinja2 templates for Python code
   - State definition template
   - Node implementation template
   - Graph construction template

4. **Scaffolder Agent** ([`src/orchestradk/agents/scaffolder/agent.py`](src/orchestradk/agents/scaffolder/agent.py)):
   - Orchestrate parsing and generation
   - Validate generated code syntax
   - Handle edge cases and errors

**Deliverables**:
- Functional scaffolder agent
- LangGraph code templates
- Unit tests for parser and generator
- Sample generated outputs

---

### **Phase 3: Agent B - The Configurator** (Week 4-5)

**Objective**: Generate ADK-compliant configuration files

**Tasks**:
1. **ADK Schema Integration** ([`src/orchestradk/adk/schemas.py`](src/orchestradk/adk/schemas.py)):
   - Load ADK schema definitions
   - Create validation rules
   - Map LangGraph components to ADK metadata

2. **YAML Generator** ([`src/orchestradk/agents/configurator/yaml_generator.py`](src/orchestradk/agents/configurator/yaml_generator.py)):
   - Generate `agent.yaml` with metadata
   - Create `skills.yaml` with skill definitions
   - Ensure ADK compliance

3. **JSON Generator** ([`src/orchestradk/agents/configurator/json_generator.py`](src/orchestradk/agents/configurator/json_generator.py)):
   - Generate `config.json` for runtime
   - Create `schema.json` for I/O validation
   - Handle nested structures

4. **Schema Validator** ([`src/orchestradk/agents/configurator/schema_validator.py`](src/orchestradk/agents/configurator/schema_validator.py)):
   - Validate against ADK schemas
   - Check for required fields
   - Verify data types and formats

5. **Configurator Agent** ([`src/orchestradk/agents/configurator/agent.py`](src/orchestradk/agents/configurator/agent.py)):
   - Coordinate YAML/JSON generation
   - Validate all outputs
   - Package configuration files

**Deliverables**:
- Functional configurator agent
- ADK configuration templates
- Schema validation system
- Unit tests for generators and validators

---

### **Phase 4: Orchestrator Layer** (Week 6)

**Objective**: Coordinate multi-agent workflow

**Tasks**:
1. **Coordinator** ([`src/orchestradk/orchestrator/coordinator.py`](src/orchestradk/orchestrator/coordinator.py)):
   - Manage agent lifecycle
   - Handle inter-agent communication
   - Coordinate sequential execution

2. **Router** ([`src/orchestradk/orchestrator/router.py`](src/orchestradk/orchestrator/router.py)):
   - Route tasks to appropriate agents
   - Handle task dependencies
   - Manage execution flow

3. **Validator** ([`src/orchestradk/orchestrator/validator.py`](src/orchestradk/orchestrator/validator.py)):
   - Validate agent outputs
   - Check cross-agent consistency
   - Ensure complete package generation

**Deliverables**:
- Working orchestrator
- Agent coordination logic
- Integration tests
- End-to-end workflow validation

---

### **Phase 5: CLI and Integration** (Week 7)

**Objective**: Create user interface and ADK integration

**Tasks**:
1. **CLI Interface** ([`src/cli/main.py`](src/cli/main.py)):
   - Command-line argument parsing
   - Interactive mode for requests
   - Progress reporting
   - Error handling and user feedback

2. **ADK Integration** ([`src/orchestradk/adk/integration.py`](src/orchestradk/adk/integration.py)):
   - Package generated outputs
   - Validate against ADK requirements
   - Generate deployment artifacts

3. **Documentation**:
   - User guide
   - API documentation
   - Example workflows
   - Troubleshooting guide

**Deliverables**:
- Functional CLI tool
- Complete ADK integration
- User documentation
- Example projects

---

### **Phase 6: Testing and Refinement** (Week 8)

**Objective**: Comprehensive testing and optimization

**Tasks**:
1. **Unit Testing**:
   - Test all components individually
   - Achieve >80% code coverage
   - Mock external dependencies

2. **Integration Testing**:
   - Test agent interactions
   - Validate end-to-end workflows
   - Test ADK integration

3. **Performance Optimization**:
   - Profile code generation
   - Optimize LLM calls
   - Reduce latency

4. **Error Handling**:
   - Comprehensive error messages
   - Graceful failure handling
   - Recovery mechanisms

**Deliverables**:
- Complete test suite
- Performance benchmarks
- Bug fixes and improvements
- Production-ready system

---

## Required Tools and MCP Servers

### **Core Dependencies**

#### Python Packages
```toml
[tool.poetry.dependencies]
python = "^3.10"
langgraph = "^0.2.0"              # LangGraph framework
langchain = "^0.3.0"              # LangChain core
pydantic = "^2.0"                 # Data validation
jinja2 = "^3.1"                   # Template engine
pyyaml = "^6.0"                   # YAML processing
click = "^8.1"                    # CLI framework
rich = "^13.0"                    # Terminal formatting
ibm-watsonx-ai = "^1.0"          # watsonx.ai SDK
```

#### Development Tools
```toml
[tool.poetry.group.dev.dependencies]
pytest = "^8.0"                   # Testing framework
pytest-cov = "^5.0"              # Coverage reporting
black = "^24.0"                   # Code formatting
ruff = "^0.5"                     # Linting
mypy = "^1.10"                    # Type checking
```

---

### **MCP (Model Context Protocol) Servers**

#### **1. Filesystem MCP Server**
**Purpose**: File operations for generated code and configs

**Configuration**:
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "./output"],
      "env": {}
    }
  }
}
```

**Usage**:
- Write generated Python files
- Create YAML/JSON configurations
- Organize output directory structure
- Read template files

---

#### **2. GitHub MCP Server**
**Purpose**: Version control and repository management

**Configuration**:
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<token>"
      }
    }
  }
}
```

**Usage**:
- Create repositories for generated agents
- Push generated code to GitHub
- Manage agent versions
- Track changes and iterations

---

#### **3. Sequential Thinking MCP Server**
**Purpose**: Complex reasoning for code generation

**Configuration**:
```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
      "env": {}
    }
  }
}
```

**Usage**:
- Break down complex agent requirements
- Plan LangGraph structure
- Reason about state transitions
- Validate logical flow

---

#### **4. Memory MCP Server**
**Purpose**: Maintain context across agent interactions

**Configuration**:
```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {}
    }
  }
}
```

**Usage**:
- Store developer preferences
- Remember previous agent generations
- Track project context
- Maintain conversation history

---

#### **5. Custom ADK MCP Server** (To Be Developed)
**Purpose**: Direct integration with watsonx Orchestrate ADK

**Planned Capabilities**:
- Validate against ADK schemas
- Query ADK documentation
- Test agent deployments
- Retrieve ADK examples

**Implementation Priority**: Phase 5

---

### **watsonx.ai Integration**

#### **LLM Configuration**
```yaml
# config/llm_config.yaml
watsonx:
  url: "https://us-south.ml.cloud.ibm.com"
  project_id: "<project-id>"
  model_id: "ibm/granite-13b-chat-v2"
  parameters:
    decoding_method: "greedy"
    max_new_tokens: 2048
    temperature: 0.7
    top_p: 0.9
    top_k: 50
```

#### **Prompt Templates**
Located in [`src/orchestradk/llm/prompts.py`](src/orchestradk/llm/prompts.py):
- `SCAFFOLDER_SYSTEM_PROMPT`: Instructions for Agent A
- `CONFIGURATOR_SYSTEM_PROMPT`: Instructions for Agent B
- `CODE_GENERATION_PROMPT`: LangGraph code generation
- `CONFIG_GENERATION_PROMPT`: YAML/JSON generation

---

## Agent Communication Protocol

### **Message Format**
```python
from pydantic import BaseModel
from typing import Any, Dict, Optional

class AgentMessage(BaseModel):
    """Standard message format for inter-agent communication"""
    sender: str                    # Agent identifier
    receiver: str                  # Target agent
    message_type: str              # "request" | "response" | "error"
    payload: Dict[str, Any]        # Message content
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str
```

### **Workflow Sequence**
1. **User Request** → Orchestrator
2. **Orchestrator** → Agent A (Scaffolder)
3. **Agent A** generates Python code → Orchestrator
4. **Orchestrator** validates → Agent B (Configurator)
5. **Agent B** generates configs → Orchestrator
6. **Orchestrator** validates complete package → User

---

## Validation Requirements

### **Scaffolder Output Validation**
- [ ] Valid Python syntax
- [ ] Proper LangGraph structure
- [ ] Type hints present
- [ ] Docstrings included
- [ ] State class defined
- [ ] Nodes implemented
- [ ] Graph constructed

### **Configurator Output Validation**
- [ ] Valid YAML syntax
- [ ] Valid JSON syntax
- [ ] ADK schema compliance
- [ ] Required fields present
- [ ] Correct data types
- [ ] Schema references valid

### **Integration Validation**
- [ ] Python code references match config
- [ ] Skill names consistent
- [ ] Input/output schemas aligned
- [ ] No circular dependencies
- [ ] Complete package structure

---

## Error Handling Strategy

### **Error Categories**
1. **Parse Errors**: Invalid user input
2. **Generation Errors**: Code/config generation failures
3. **Validation Errors**: Schema or syntax violations
4. **Integration Errors**: ADK compatibility issues
5. **System Errors**: Infrastructure failures

### **Recovery Mechanisms**
- Retry with modified prompts
- Fallback to simpler templates
- Request user clarification
- Partial output preservation
- Detailed error logging

---

## Performance Targets

- **Request to Output**: < 60 seconds
- **Code Generation**: < 30 seconds
- **Config Generation**: < 20 seconds
- **Validation**: < 10 seconds
- **LLM Calls**: 2-4 per agent request

---

## Security Considerations

1. **Input Sanitization**: Validate all user inputs
2. **Code Injection Prevention**: Sandbox code generation
3. **API Key Management**: Secure credential storage
4. **Output Validation**: Prevent malicious code generation
5. **Audit Logging**: Track all operations

---

## Future Enhancements

### **Phase 7+**
- Web UI for visual agent design
- Multi-language support (beyond Python)
- Agent marketplace integration
- Real-time collaboration features
- Advanced debugging tools
- Performance analytics dashboard
- Custom template library
- Integration with CI/CD pipelines

---

## Getting Started (Post-Implementation)

```bash
# Install dependencies
pip install -e .

# Run CLI
orchestradk create --request "Create a customer support agent with FAQ lookup"

# Interactive mode
orchestradk interactive

# Validate existing agent
orchestradk validate --path ./output/my-agent
```

---

## Key Design Principles

1. **Separation of Concerns**: Each agent has a single, well-defined responsibility
2. **Modularity**: Components can be tested and developed independently
3. **Extensibility**: Easy to add new agent types or capabilities
4. **Validation-First**: Multiple validation layers ensure quality
5. **Developer-Friendly**: Clear error messages and helpful defaults
6. **ADK-Compliant**: All outputs meet watsonx Orchestrate requirements

---

## Critical Success Factors

- ✅ Accurate natural language understanding
- ✅ Valid LangGraph code generation
- ✅ ADK-compliant configuration files
- ✅ Robust error handling
- ✅ Fast generation times
- ✅ Comprehensive testing
- ✅ Clear documentation

---

**Last Updated**: 2026-05-02  
**Version**: 1.0.0  
**Status**: Architecture Complete - Ready for Implementation