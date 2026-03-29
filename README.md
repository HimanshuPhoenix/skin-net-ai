# SKIn-Net: 

Smart Kin Insight Network  - An Autonomous Multi-Agent System for Intelligent Elderly Care

### Smart Kin Insight Network  
**An Autonomous Multi-Agent System for Intelligent Elderly Care**

---

## ❤️ Overview

**SKIN Net** is a next-generation AI system designed to provide **reliable, human-like care for the elderly**.

It goes beyond traditional chatbots by combining:
- 🧠 AI reasoning (Gemini via ADK)
- 🔗 Real-world tool integration (MCP)
- 💾 Persistent memory (Database)
- 🤖 Multi-agent orchestration

👉 The goal:  
**Deliver care that feels like family — always present, always aware.**

---

## 🚨 Problem

Elderly care today is:
- Reactive (only responds after issues occur)
- Fragmented (multiple disconnected systems)
- Manual (requires constant human supervision)

There is no intelligent system that can:
- Monitor health proactively
- Ensure medication adherence
- Assist with daily logistics
- Respond instantly in emergencies

---

## 💡 Solution

**SKIN Net** introduces a **multi-agent AI architecture** that:

✅ Understands user intent  
✅ Connects to real-world data sources  
✅ Executes intelligent workflows  
✅ Maintains persistent memory  
✅ Provides proactive care & alerts  

---

## 🏗️ Architecture
```text
User Input
↓
Root Agent (Coordinator)
↓
MCP Tool Layer
├── 🩺 Health & Medicine Agent
├── 📊 Database Agent (MySQL / AlloyDB)
├── 🗺️ Logistics Agent (Maps MCP)
└── 🚨 Emergency SOS Agent
↓
Processing & Reasoning (Gemini)
↓
Action / Response / Storage
```

---

## ⚙️ Core Features

### 🧠 Multi-Agent Intelligence
- Root agent orchestrates specialized agents
- Dynamic routing based on user intent

### 🔗 MCP Integration (Model Context Protocol)
- Secure tool access (DB, Maps, APIs)
- Separation of reasoning & execution

### 💊 Medication Safety
- Multimodal analysis (images, prescriptions)
- Grounded validation against datasets

### 📊 Health & Inventory Tracking
- Automated logging via database tools
- Persistent state across sessions

### 🚨 Emergency Response
- Detects anomalies or distress signals
- Triggers SOS workflows instantly

### 🔁 Memory & Retrieval
- Stores user data & history
- Enables contextual continuity

---

## 🔄 Workflow

### 🟢 New Session
1. User provides input
2. Root agent captures intent
3. Sub-agent executes task via MCP
4. Data is stored in database
5. Response is generated

### 🔵 Retrieval
1. User provides ID / context
2. System queries database
3. Returns structured results

---

## 🧪 Tech Stack

| Layer | Technology |
|------|------------|
| 🤖 AI Agent | Google ADK |
| 🧠 Model | Gemini (3.x) |
| 🔗 Tool Integration | MCP (Model Context Protocol) |
| 💾 Database | MySQL / AlloyDB |
| 🌐 Deployment | Cloud Run |
| 🧰 Tools | LangChain, Wikipedia, arXiv |

---

## 🔐 Security & Privacy

- 🔒 No sensitive data stored in LLM  
- 🔑 Secure MCP connections (API keys, tokens)  
- 🧾 Principle of least privilege (IAM roles)  
- 📦 Data accessed only during execution context  

---

## 🚀 Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Run MCP toolbox
./toolbox --tools-file="tools.yaml" --ui

# Run agent locally
adk run

# Deploy to Cloud Run
adk deploy cloud_run --with_ui
```

# 🌍 Vision

We are moving from:

❌ AI tools that respond
➡️
✅ Autonomous systems that understand, act, and care

# 💡 Future Scope
📱 Caregiver dashboard UI
📞 SMS / WhatsApp alerts
📄 PDF export of reports
🤝 Agent-to-Agent (A2A) communication
🧠 Predictive health insights
🏆 Why SKIN Net?

Because care should feel:

Personal
Reliable
Always present

“A network that cares like family.”

# 👤 Author

Himanshu Saxena

# ⭐ Support

If you found this project interesting:

👉 Star ⭐ the repo
👉 Share feedback
👉 [Connect on LinkedIn](https://www.linkedin.com/in/phoenix-himanshu/)
