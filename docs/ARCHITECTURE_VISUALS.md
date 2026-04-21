# BackPocket OS — Architecture Visuals

> Presentation-ready diagrams for meeting. Render in any Mermaid viewer (GitHub, VS Code preview, Mermaid.live, HackMD).

---

## 1. System Architecture

How all services connect in the containerized ecosystem.

```mermaid
graph TD
    subgraph "User's Device"
        A[Flutter App]
    end

    subgraph "Docker Environment (Server)"
        B(Nginx Web Server)
        C(FastAPI Backend API)
        D(Paperless-ngx OCR Engine)
        E(PostgreSQL Database)
        F(Redis Message Broker)
    end

    subgraph "External AI Services"
        G[Cloud LLMs: OpenRouter / Gemini]
    end

    A -- "HTTP Request" --> B
    B -- "Proxies /api/ requests" --> C
    C -- "Uploads Docs & Gets Text" --> D
    D -- "Stores Data In" --> E
    D -- "Uses for Task Queues" --> F
    C -- "Sends Text for Analysis" --> G
    C -- "Stores Business Data in" --> E
```

---

## 2. Intelligent Document Pipeline

Raw document (PDF invoice, receipt photo) → structured, actionable business data.

```mermaid
graph TD
    A["1. User Uploads Document"] --> B{"2. FastAPI Receives File"}
    B --> C["3. File sent to Paperless-ngx for OCR"]
    subgraph "Polling Loop"
        B -- "Asks 'Are you done yet?'" --> C;
    end
    C -- "Returns Clean Text" --> B;
    B --> D["4. Clean text sent to Cloud AI Model"]
    D --> E["5. AI returns semantic analysis (dates, amounts, summary)"]
    E --> F["6. Analysis saved to database"]
```

---

## 3. Voice-to-Action Pipeline

Spoken commands from the tradie → completed system actions. Hands-free on the job site.

```mermaid
graph TD
    A["1. User speaks command"] --> B{"2. Audio transcribed to text"}
    B --> C["3. An AI 'Intent Classifier' identifies the goal (e.g. create_invoice)"]
    C --> D{"4. The system checks if it has all the needed info"}
    D -- "No, needs more info" --> A
    D -- "Yes, ready to execute" --> E["5. Action handler executed"]
    E --> F["6. PDF generated & quote status updated"]
```

---

## 4. MCP Orchestrator — Real-World Example

End-to-end: email arrives → AI extracts lead → generates quote → calculates travel → sends response.

```mermaid
graph TD
    A["📧 Email: Leaking tap, Parramatta, budget $200"] --> B["Gmail MCP finds email"]
    B --> C["BackPocket MCP: search_leads<br/>(Plumbing, Parramatta)"]
    C --> D["BackPocket MCP: get_quote_template<br/>(Plumbing = $150/hr)"]
    D --> E["Google Maps MCP: distance<br/>(Alexandria → Parramatta = 25min)"]
    E --> F["BackPocket MCP: create_quote<br/>(1.5hrs + $120 materials = $414)"]
    F --> G["BackPocket MCP: draft_follow_up_email"]
    G --> H["Gmail MCP: send_message"]
    H --> I{"🧑‍🔧 User Decision: Accept Job & Send Quote ($414)?"}
```

---

## 5. Personality Engine — How AI Learns Your Style

Two-stage process: filter noise from emails, then learn the tradie's communication style.

```mermaid
graph LR
    A["Raw Sent Emails"] --> B["Stage 1: IsolationForest Noise Filter"]
    B -- "Discard spam, auto-replies" --> C["Clean Emails (True Voice)"]
    C --> D["Stage 2: RAG Indexing (ChromaDB)"]
    D --> E["Searchable Style Knowledge Base"]
    E --> F["New Draft Request"]
    F --> G["AI retrieves similar past examples"]
    G --> H["Generated email matches user's tone"]
```

---

## 6. Full Business Pipeline (Lead → Payment)

Complete workflow from initial customer enquiry through to payment received.

```mermaid
graph LR
    A["📧 Customer Email"] --> B["🤖 AI Lead Extraction"]
    B --> C["Lead Created (new)"]
    C --> D["Quote Generated (materials + labor + markup)"]
    D --> E["Quote Sent (quoted)"]
    E --> F["Quote Accepted (accepted)"]
    F --> G["Invoice Sent (invoiced)"]
    G --> H["💰 Payment Received (paid)"]
```

---

## 7. Three AI Twins System

Specialized AI personas handling different business domains.

```mermaid
graph TD
    A["User Request"] --> B{"AI Router"}
    B --> C["🧮 Accountant Twin<br/>Financial analysis, budgets, costs"]
    B --> D["🔍 Auditor Twin<br/>Data validation, flags inconsistencies"]
    B --> E["📋 Admin Twin<br/>Workflow orchestration, state management"]
    C --> F["Response with financial insight"]
    D --> F
    E --> F
    F --> G["Learned patterns stored in session_memory"]
```

---

## 8. Agentic RAG Pipeline

How the system learns from past decisions and prevents hallucinations.

```mermaid
graph TD
    A["New Task / Question"] --> B["Query ChromaDB vector store"]
    B --> C["Retrieve relevant past decisions"]
    C --> D["Augment prompt with context"]
    D --> E["AI generates response"]
    E --> F{"User feedback?"}
    F -- "Correction: should have said Y" --> G["Store correction in RAG"]
    F -- "Approved" --> H["Store as validated pattern"]
    G --> B
    H --> B
```

---

## 9. Offline / Sovereign Mode

Pluggable AI architecture — switch between cloud and local models.

```mermaid
graph TD
    A["BackPocket API"] --> B{"AI_PROVIDER env var"}
    B -- "openrouter" --> C["☁️ OpenRouter Cloud<br/>(GPT-4, Claude, Gemini)"]
    B -- "ollama" --> D["🏠 Local Ollama<br/>(Llama, Mistral, Phi)"]
    B -- "gemini" --> E["☁️ Google Gemini Direct"]
    C --> F["Response"]
    D --> F
    E --> F
```

---

## How to View These Diagrams

| Method | Instructions |
|--------|-------------|
| **GitHub** | Push this file — GitHub renders Mermaid natively |
| **VS Code** | Install "Markdown Preview Mermaid Support" extension |
| **Mermaid.live** | Paste any code block at [mermaid.live](https://mermaid.live) |
| **HackMD / Notion** | Paste directly — both render Mermaid |
| **Slides** | Screenshot from mermaid.live → paste into Google Slides/Keynote |

---

*BackPocket OS — Architecture Presentation — April 2026*