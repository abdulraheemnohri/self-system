# Complete Self System - خود کار نظام

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![GitHub](https://img.shields.io/badge/GitHub-AbdulraheemNohari-purple.svg)](https://github.com/abdulraheemnohri/self-system)

**Complete Self System** ایک **خود کار AI ایجنٹ پلیٹ فارم** ہے جو مندرجہ ذیل خصوصیات فراہم کرتا ہے:

- 🧠 **LLM Integration** - OpenAI, Ollama, OpenRouter, Groq وغیرہ
- 📚 **Vector Memory** - SQLite, ChromaDB, Qdrant سپورٹ
- 🔧 **Tool Calling** - مختلف ٹولز کو کال کرنے کی صلاحیت
- 🤖 **Agent Planning** - خود کار منصوبہ بندی اور کام کرنے کی صلاحیت
- 🎯 **Skill Generation** - خود کار ہنرمندیوں کی تخلیق
- 🛡️ **Safety Governance** - حفاظتی کنٹرول اور منظوری کا عمل
- 🔄 **Self-Improvement** - خود کو بہتر بنانے کی صلاحیت

---

## 📋 Table of Contents / مواد کی فہرست

- [About / بارے میں](#about--بارے-میں)
- [Features / خصوصیات](#features--خصوصیات)
- [Installation / انسٹالیشن](#installation--انسٹالیشن)
- [Usage / استعمال](#usage--استعمال)
- [Configuration / کنفیگریشن](#configuration--کنفیگریشن)
- [Architecture / آرکیٹیکچر](#architecture--آرکیٹیکچر)
- [Commands / کمانڈز](#commands--کمانڈز)
- [API Providers / API فراہم کنندگان](#api-providers--api-فراہم-کندہ-گان)
- [Vector Databases / ویکٹر ڈیٹا بیسز](#vector-databases--ویکٹر-ڈیٹا-بیسز)
- [Safety / حفاظت](#safety--حفظات)
- [Autonomous Mode / خود کار موڈ](#autonomous-mode--خود-کار-موڈ)
- [Extending / توسیع](#extending--توسیع)
- [Contributing / شراکت](#contributing--شراکت)
- [License / لائسنس](#license--لائسنس)

---

## 🎯 About / بارے میں

**Complete Self System (خود کار نظام)** ایک **autonomous AI agent** ہے جو اپنے آپ کو بہتر بنا سکتا ہے، ٹولز استعمال کر سکتا ہے، اور یاد رکھ سکتا ہے۔

### English
The Complete Self System is an **autonomous AI agent platform** designed to understand and respond to user queries, remember information, use tools, plan actions, learn and improve over time.

### اردو
خود کار نظام ایک **خود کار AI ایجنٹ پلیٹ فارم** ہے جو صارف کے سوالات کو سمجھنا، معلومات یاد رکھنا، ٹولز استعمال کرنا، اقدامات کی منصوبہ بندی کرنا، اور وقت کے ساتھ سیکھنا اور بہتر بننا سکتا ہے۔

---

## ✨ Features / خصوصیات

### Core Features
- 🧠 **LLM Integration** - Connect to various LLM providers
- 📚 **Vector Memory** - Semantic search with embeddings
- 🔧 **Tool Calling** - Execute tools for various tasks
- 🤖 **Agent Planning** - Multi-step task execution
- 🎯 **Skill Generation** - Generate new capabilities
- 🛡️ **Safety Governance** - Protection and approval mechanisms

---

## 🚀 Installation / انسٹالیشن

### Prerequisites
- Python 3.11 or higher
- pip
- Git

### Quick Install
```bash
git clone https://github.com/abdulraheemnohri/self-system.git
cd self-system
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

---

## 🎮 Usage / استعمال

### Starting the System
```bash
python app/main.py
```

### Basic Commands
- /help - Show help
- /remember <key> <value> - Remember a fact
- /note <text> - Save a note
- /facts - List facts
- /tools - List tools
- /test - Run self-test
- /exit - Exit

---

## ⚙️ Configuration / کنفیگریشن

### Environment Variables
Create a .env file:
```bash
API_KEY=your_api_key
BASE_URL=https://api.openai.com/v1
MODEL=gpt-4o-mini
```

---

## 🏗️ Architecture / آرکیٹیکچر

Complete Self System consists of:
- Agent Core
- LLM Integration
- Memory Layer (Facts, Notes, Knowledge, Vector)
- Tool Registry
- Safety Layer
- Storage Layer

---

## 📜 License / لائسنس

MIT License - See LICENSE file for details.