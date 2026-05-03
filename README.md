<div align="center">
  
# 🚀 OrchestrADK
**The AI-Accelerated watsonx Orchestrate Agent Builder**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.0+-green.svg)](https://python.langchain.com/docs/langgraph/)
[![IBM watsonx](https://img.shields.io/badge/Powered_by-IBM_watsonx-052FAD.svg)](https://www.ibm.com/watsonx)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*From natural language to enterprise-grade, schema-compliant LangGraph agents in under 12 seconds.*

</div>

---

## ⚡ The Vision

Building intelligent agents for IBM watsonx Orchestrate is powerful, but manually configuring strict YAML schemas, LangGraph state files, and edge routing is tedious and highly prone to validation errors. 

**OrchestrADK** bridges this gap. It is a deterministic, fault-tolerant CLI tool that absorbs the chaotic output of Large Language Models (specifically `ibm/granite-8b-code-instruct`) and mathematically forces it into perfectly compliant, syntactically correct enterprise architecture.

| ❌ The Old Way (Manual) | ✨ The OrchestrADK Way |
| :--- | :--- |
| **Hours** spent writing boilerplate Python code. | **Seconds** to scaffold a complete architecture. |
| **Endless debugging** of strict YAML schema validation errors. | **Zero-Error Guarantee** via dynamic, self-healing Jinja templates. |
| **Broken edges** when LLMs hallucinate node names. | **Auto-correction** using namespace tracking and fallback generation. |

---

## 🎯 Quick Start (Judge's Guide)

We value your time. OrchestrADK is designed for a zero-friction deployment. 

### 1. Setup Credentials
Clone the repository and configure your IBM Cloud environment.
```bash
git clone [https://github.com/Temiloluwa-Oloye/orchestradk-workspace.git](https://github.com/Temiloluwa-Oloye/orchestradk-workspace.git)
cd orchestradk-workspace
cp .env.example .env
```

### 2. Install Dependencies
Install the exact framework versions required to run the engine.

```Bash
pip install -r requirements.txt
(Docker support included: You can also build the environment using docker build -t orchestradk .)
```

### 3. Generate the Architecture
Run the AI-Accelerated Scaffolder using a natural language prompt:

```Bash
python -m src.cli.main create --request "Create an intelligent DevOps support agent that takes a user's error log, uses RAG to query internal documentation, and automatically generates a troubleshooting script."
```
The Output: Navigate to the /output/devops_agent directory. You will find 8 fully compiled, production-ready files, including the LangGraph Python logic (graph.py, nodes.py) and the IBM Orchestrate configurations (agent.yaml, skills.yaml).

## 🧠 Core Architecture: "Self-Healing" Generation
OrchestrADK doesn't just ask an LLM to write code. It uses a rigorous, multi-agent pipeline to ensure 100% execution reliability:

The Scaffolder: Parses the developer's natural language request using ibm/granite-8b-code-instruct and extracts the core logic into a strict JSON data contract.

The God-Mode Templates: Unlike naive code generators, OrchestrADK uses advanced Jinja2 templating with namespace tracking. If the LLM hallucinates a node or forgets a required array, the templates dynamically inject fallback functions and default schemas to prevent Python NameErrors and PyYAML NoneType crashes.

The Configurator: Compiles the validated data into IBM-compliant agent.yaml and skills.yaml files, ensuring every deployment passes the Orchestrate Schema Validator on the first try.

## 📂 Repository Structure

```bash
orchestradk-workspace/
├── src/
│   ├── cli/                  # Command Line Interface logic
│   ├── orchestradk/          
│   │   ├── llm/              # IBM watsonx Client integration
│   │   ├── agents/           # Scaffolder and Configurator Sub-Agents
│   │   │   ├── scaffolder/   # Dynamic Python (LangGraph) generation
│   │   │   └── configurator/ # Strict YAML/JSON (watsonx) generation
│   │   └── orchestrator/     # State management and pipeline coordination
├── output/                   # Directory for generated agent packages
├── config/                   # IBM ADK validation schemas
├── requirements.txt          # Frozen dependencies
├── Dockerfile                # Isolated container environment
└── .env.example              # Template for API credentials
```
## 🏆 Hackathon Value Proposition
Developer Experience (DX): Lowers the barrier to entry for building complex, multi-node agents on IBM Cloud.

Enterprise Reliability: Eliminates the "fragility" of standard AI code generators by separating natural language understanding from deterministic code compilation.

Extensibility: Built entirely on open-source standards (LangGraph, Pydantic, Jinja2), ready to scale into a full graphical interface.

### Built with 💻 and ☕ by Temiloluwa Oloye AI Engineer & Researcher