# Complete Self System

**Version 2.0.0**

A comprehensive, modular, and extensible AI assistant system with skills, plugins, and tools for various tasks including web search, code analysis, data processing, summarization, and more.

## Features

- **Modular Architecture**: Skills and plugins can be added, removed, or modified independently
- **Extensible**: Easy to add new skills, plugins, and tools
- **Multi-Provider Support**: Works with various AI providers (OpenAI, Anthropic, Google, Ollama, etc.)
- **Vector Memory**: Semantic search and memory capabilities
- **Database Backend**: SQLite-based storage for facts, notes, knowledge, and history
- **Scheduling**: Built-in task scheduling and automation
- **Termux Support**: Full installation and setup guide for Termux on Android

## Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- Git (optional, for cloning)

### Installation

#### Method 1: Standard Installation

```bash
# Clone the repository
git clone https://github.com/abdulraheemnohri/self-system.git
cd self-system

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment file
cp .env.example .env
# Edit .env with your configuration

# Run the system
python -m app.main
```

#### Method 2: Docker Installation

```bash
# Build the Docker image
docker-compose build

# Run the container
docker-compose up -d

# View logs
docker-compose logs -f
```

#### Method 3: Termux Installation (Android)

**Complete Termux setup guide for running Self System on Android devices:**

##### Step 1: Install Termux

Download and install Termux from:
- [F-Droid](https://f-droid.org/en/packages/com.termux/) (Recommended)
- Or from [GitHub](https://github.com/termux/termux-app/releases)

##### Step 2: Update and Install Dependencies

```bash
# Update package lists
pkg update && pkg upgrade -y

# Install required packages
pkg install python git openssh curl wget -y

# Install pip (if not already installed)
pkg install python-pip -y

# Install additional utilities
pkg install nano vim tmux htop -y
```

##### Step 3: Clone the Repository

```bash
# Clone the self-system repository
git clone https://github.com/abdulraheemnohri/self-system.git
cd self-system
```

##### Step 4: Create Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

##### Step 5: Install Python Dependencies

```bash
# Install base requirements
pip install -r requirements.txt

# Install additional useful packages for Termux
pip install requests beautifulsoup4 psutil schedule sentence-transformers
```

##### Step 6: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit the environment file (using nano)
nano .env
```

Configure the following in `.env`:

```ini
# AI Provider Configuration
PROVIDER_BASE_URL=http://localhost:11434/v1
PROVIDER_API_KEY=your_api_key_here
PROVIDER_MODEL=llama3.1

# For OpenAI
# PROVIDER_BASE_URL=https://api.openai.com/v1
# PROVIDER_API_KEY=sk-your-openai-key
# PROVIDER_MODEL=gpt-4

# For Anthropic
# PROVIDER_BASE_URL=https://api.anthropic.com/v1
# PROVIDER_API_KEY=sk-your-anthropic-key
# PROVIDER_MODEL=claude-3-sonnet-20240229

# For Google
# PROVIDER_BASE_URL=https://generativelanguage.googleapis.com/v1beta
# PROVIDER_API_KEY=your-google-api-key
# PROVIDER_MODEL=gemini-pro

# For Ollama (local)
# PROVIDER_BASE_URL=http://localhost:11434/v1
# PROVIDER_API_KEY=ollama
# PROVIDER_MODEL=llama3.1
```

##### Step 7: Create Storage Directory

```bash
# Create storage directory for database and vectors
mkdir -p storage
```

##### Step 8: Run the System

```bash
# Run the main application
python -m app.main
```

##### Step 9: (Optional) Run in Background with tmux

```bash
# Install tmux (if not already installed)
pkg install tmux -y

# Create a new tmux session
tmux new -s selfsystem

# In the tmux session, run:
python -m app.main

# Detach from tmux (press Ctrl+B then D)

# To reattach later:
tmux attach -t selfsystem
```

##### Step 10: (Optional) Auto-start on Termux Boot

Create a script to auto-start the system:

```bash
# Create startup script
nano ~/start_selfsystem.sh
```

Add the following content:

```bash
#!/data/data/com.termux/files/usr/bin/bash
cd ~/self-system
source venv/bin/activate
python -m app.main
```

Make it executable:

```bash
chmod +x ~/start_selfsystem.sh
```

Then use Termux:Boot or Termux:Widget to run this script on startup.

##### Termux Tips

- Use `termux-setup-storage` to access device storage
- Install Termux:API for additional device integration
- Use `termux-clipboard-get` and `termux-clipboard-set` for clipboard operations
- Enable storage access: `termux-setup-storage`

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```ini
# Provider Settings
PROVIDER_BASE_URL=http://localhost:11434/v1
PROVIDER_API_KEY=
PROVIDER_MODEL=llama3.1
PROVIDER_USE_API_EMBEDDINGS=True
PROVIDER_EMBEDDING_MODEL=text-embedding-3-small

# Memory Settings
MEMORY_VECTOR_BACKEND=sqlite
MEMORY_QDRANT_URL=http://localhost:6333
MEMORY_QDRANT_COLLECTION=self_system

# Translation Settings
TRANSLATION_API=libretranslate
TRANSLATION_API_URL=https://libretranslate.de/translate
TRANSLATION_API_KEY=

# Database Settings
DATABASE_PATH=storage/self_system.db
```

### Supported AI Providers

The system supports multiple AI providers:

| Provider | Base URL | API Key Required | Notes |
|----------|----------|------------------|-------|
| Ollama (Local) | http://localhost:11434/v1 | No (use "ollama") | Run Ollama locally |
| OpenAI | https://api.openai.com/v1 | Yes | GPT-3.5, GPT-4 |
| Anthropic | https://api.anthropic.com/v1 | Yes | Claude models |
| Google | https://generativelanguage.googleapis.com/v1beta | Yes | Gemini models |
| OpenRouter | https://openrouter.ai/api/v1 | Yes | Multiple models |
| Mistral | https://api.mistral.ai/v1 | Yes | Mistral models |

### Config File

Edit `config.yaml` for additional configuration:

```yaml
# Provider configuration
provider:
  base_url: http://localhost:11434/v1
  api_key: ""
  model: llama3.1
  timeout: 120
  max_retries: 3

# Memory configuration
memory:
  vector_backend: sqlite
  qdrant_url: http://localhost:6333
  qdrant_collection: self_system

# Database configuration
database:
  path: storage/self_system.db
```

## Skills

The system includes the following skills:

### Core Skills

1. **Math Skill** (`app/math_skill.py`)
   - Mathematical calculations
   - Quadratic equation solving
   - Statistical analysis
   - Unit conversions
   - Geometric calculations
   - Financial calculations

2. **System Skill** (`app/system_skill.py`)
   - System information
   - Resource monitoring
   - Process management
   - Environment inspection
   - Command execution
   - Port checking
   - File system information

3. **Translation Skill** (`app/translation_skill.py`)
   - Language detection
   - Text translation
   - Batch translation
   - Multi-language support

4. **Knowledge Skill** (`app/knowledge_skill.py`)
   - Knowledge management
   - Semantic and keyword search
   - Knowledge statistics
   - Keyword extraction
   - Text summarization

5. **Automation Skill** (`app/automation_skill.py`)
   - Scheduled tasks
   - Background task execution
   - Workflow creation
   - Task monitoring

### Built-in Skills

- **Code Analysis** (`app/code_analysis.py`): Code quality analysis, linting, and metrics
- **Data Processing** (`app/data_processing.py`): Data manipulation, filtering, and transformation
- **Summarization** (`app/summarization.py`): Text summarization and extraction
- **Web Search** (`app/web_search.py`): Web search and information retrieval

## Plugins

The system includes the following plugins:

### Tool Plugins

1. **Web Tools** (`plugins/web_tools.py`)
   - Web search
   - URL fetching
   - Link extraction
   - URL information
   - Health checks
   - URL shortening

2. **File Tools** (`plugins/file_tools.py`)
   - File read/write
   - File existence checks
   - File information
   - Directory listing
   - File search
   - File operations (copy, move, delete)

3. **Code Tools** (`plugins/code_tools.py`)
   - Code formatting
   - Syntax checking
   - Code analysis
   - Git operations
   - Code generation

4. **Data Tools** (`plugins/data_tools.py`)
   - Data validation
   - Data transformation
   - Statistical calculations
   - Data filtering
   - CSV/JSON operations

5. **Security Tools** (`plugins/security_tools.py`)
   - Hash generation
   - Text encryption/decryption
   - Password generation
   - Password validation
   - File hashing
   - Token generation
   - Input sanitization