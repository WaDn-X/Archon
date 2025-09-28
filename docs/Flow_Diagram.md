# Zippy Archon User Process Flow Diagram

## Overview

This document outlines the comprehensive user process flows for the Zippy Archon platform, covering both standard Archon V6 operations and enhanced agentic workflow capabilities.

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend UI   │    │   Backend API   │    │   Database      │
│   (React/TS)    │◄──►│   (FastAPI)     │◄──►│   (Supabase)    │
│   Port: 3737    │    │   Port: 8181    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Server    │    │   AI Agents     │    │   Crawler       │
│   Port: 8051    │    │   Port: 8052    │    │   Service        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Primary User Flows

### 1. Initial Setup & Onboarding Flow

```mermaid
graph TD
    A[User Access Application] --> B{Backend Health Check}
    B --> C{Backend Ready?}
    C -->|No| D[Show Backend Startup Error]
    C -->|Yes| E[Check Configuration]
    E --> F{First Time User?}
    F -->|Yes| G[Redirect to Onboarding]
    F -->|No| H{Configuration Valid?}
    H -->|No| G
    H -->|Yes| I[Load Main Application]

    D --> J[Retry Connection]
    J --> B

    G --> K[Configure AI Providers]
    K --> L[Configure RAG Strategy]
    L --> M[Set API Keys]
    M --> N[Test Configuration]
    N --> O{Configuration Valid?}
    O -->|No| P[Show Error & Retry]
    O -->|Yes| Q[Complete Onboarding]
    Q --> I

    P --> K
```

### 2. Knowledge Base Management Flow

```mermaid
graph TD
    A[Access Knowledge Base Page] --> B[Display Knowledge Items]
    B --> C{User Action}

    C -->|Upload Document| D[Document Upload Modal]
    D --> E[Select File]
    E --> F[Configure Settings]
    F --> G[Upload to Server]
    G --> H[Processing Status]
    H --> I{Processing Complete?}
    I -->|No| J[Show Progress]
    J --> I
    I -->|Yes| K[Index Document]
    K --> L[Update Knowledge Base]
    L --> B

    C -->|Crawl Website| M[Website Crawl Modal]
    M --> N[Enter URL]
    N --> O[Configure Crawl Settings]
    O --> P[Start Crawling]
    P --> Q[Crawling Progress]
    Q --> R{Crawl Complete?}
    R -->|No| S[Show Progress]
    S --> R
    R -->|Yes| T[Process Content]
    T --> U[Index Content]
    U --> L

    C -->|Search Knowledge| V[Search Interface]
    V --> W[Enter Query]
    W --> X[Execute Search]
    X --> Y{Search Results?}
    Y -->|Yes| Z[Display Results]
    Y -->|No| AA[Show No Results]
    Z --> BB[User Interaction]
    BB -->|View Details| CC[Knowledge Item Details]
    BB -->|Edit Item| DD[Edit Modal]
    BB -->|Delete Item| EE[Delete Confirmation]
```

### 3. Project Management Flow

```mermaid
graph TD
    A[Access Project Management] --> B[Display Project List]
    B --> C{User Action}

    C -->|Create New Project| D[Project Creation Modal]
    D --> E[Enter Project Details]
    E --> F[Configure Sources]
    F --> G[Select Knowledge Sources]
    G --> H[Configure Features]
    H --> I[Submit Project]
    I --> J[Project Creation Progress]
    J --> K{Agentic Processing}
    K --> L[Document Agent Analysis]
    L --> M[Generate Requirements]
    M --> N[Create Task Breakdown]
    N --> O[Initialize Project Structure]
    O --> P{Processing Complete?}
    P -->|No| Q[Show Progress]
    Q --> P
    P -->|Yes| R[Display Project Details]
    R --> S[Show Generated Tasks]
    S --> B

    C -->|View Existing Project| T[Select Project]
    T --> U[Project Dashboard]
    U --> V{Project Section}
    V -->|Tasks| W[Task Management]
    V -->|Docs| X[Document Management]
    V -->|Features| Y[Feature Management]
    V -->|Data| Z[Data Management]

    W --> AA{Task Actions}
    AA -->|Create Task| BB[New Task Modal]
    AA -->|Update Status| CC[Drag & Drop Update]
    AA -->|Edit Task| DD[Task Edit Modal]
    AA -->|Delete Task| EE[Delete Confirmation]
```

### 4. Settings & Configuration Flow

```mermaid
graph TD
    A[Access Settings Page] --> B[Display Settings Categories]
    B --> C{Settings Category}

    C -->|API Keys| D[API Keys Section]
    D --> E[Display Current Keys]
    E --> F{User Action}
    F -->|Add Key| G[Add API Key Modal]
    F -->|Edit Key| H[Edit API Key Modal]
    F -->|Delete Key| I[Delete Confirmation]
    F -->|Test Key| J[Test API Key]
    J --> K{Test Result}
    K -->|Success| L[Show Success]
    K -->|Failure| M[Show Error Details]

    C -->|RAG Settings| N[RAG Configuration]
    N --> O[Display Current Settings]
    O --> P{Setting Type}
    P -->|Embeddings| Q[Embedding Configuration]
    P -->|Search Strategy| R[Search Strategy Config]
    P -->|Reranking| S[Reranking Settings]
    P -->|Agentic RAG| T[Agentic RAG Config]

    C -->|Code Extraction| U[Code Extraction Settings]
    U --> V[Display Settings]
    V --> W[Configure Extractors]
    W --> X[Test Extraction]
    X --> Y{Test Result}
    Y -->|Success| Z[Show Success]
    Y -->|Failure| AA[Show Error]

    C -->|Features| BB[Feature Toggles]
    BB --> CC[Display Feature Status]
    CC --> DD{Toggle Feature}
    DD -->|Enable| EE[Enable Feature]
    DD -->|Disable| FF[Disable Feature]
    EE --> GG[Update Configuration]
    FF --> GG
```

### 5. MCP Server Integration Flow

```mermaid
graph TD
    A[Access MCP Page] --> B[Display MCP Clients]
    B --> C{User Action}

    C -->|View Clients| D[Client List]
    D --> E[Client Details]
    E --> F{Client Status}
    F -->|Connected| G[Show Active Tools]
    F -->|Disconnected| H[Show Connection Error]
    F -->|Connecting| I[Show Connection Progress]

    C -->|Test Tools| J[Tool Testing Panel]
    J --> K[Select Tool]
    K --> L[Configure Test Parameters]
    L --> M[Execute Test]
    M --> N{Test Result}
    N -->|Success| O[Show Success Output]
    N -->|Failure| P[Show Error Details]
    N -->|Timeout| Q[Show Timeout Error]

    C -->|Configure Client| R[Client Configuration]
    R --> S[Edit Connection Settings]
    S --> T[Validate Configuration]
    T --> U{Validation Result}
    U -->|Valid| V[Save Configuration]
    U -->|Invalid| W[Show Validation Errors]
    W --> S
```

## Agentic Workflow Flows

### 6. Advanced Agentic Processing Flow

```mermaid
graph TD
    A[Access Agentic Workflow] --> B[Initialize Orchestrator]
    B --> C[Load Workflow Graph]
    C --> D[Display Workflow Interface]
    D --> E{User Interaction}

    E -->|Start Conversation| F[User Input]
    F --> G[Define Scope with Reasoner]
    G --> H[Process with Coder Agent]
    H --> I{Continue Conversation?}
    I -->|Yes| J[Get Next User Message]
    I -->|No| K[Finish Conversation]

    E -->|Create Tool| L[Tool Generation Request]
    L --> M[Generate Tool Code]
    M --> N[Finalize New Tool]
    N --> O[Register Tool]
    O --> P[Update Plugin Registry]

    E -->|Diagnose Issues| Q[Error Detection]
    Q --> R[Diagnostic Agent Analysis]
    R --> S[Generate Resolution]
    S --> T{Resolution Applied?}
    T -->|Yes| U[Update Status]
    T -->|No| V[Escalate Issue]
```

### 7. Plugin Management Flow

```mermaid
graph TD
    A[Access Plugin Management] --> B[Scan Plugin Directory]
    B --> C[Load Plugin Modules]
    C --> D[Validate Plugin Structure]
    D --> E{Plugin Valid?}
    E -->|Yes| F[Register Plugin]
    E -->|No| G[Log Validation Error]
    G --> H[Skip Plugin]

    F --> I[Initialize Plugin Instance]
    I --> J{Plugin Type}
    J -->|Tool| K[Register Tool]
    J -->|Service| L[Register Service]
    J -->|Integration| M[Register Integration]

    K --> N[Add to Tool Registry]
    L --> O[Add to Service Registry]
    M --> P[Add to Integration Registry]

    N --> Q[Update Orchestrator]
    O --> Q
    P --> Q

    Q --> R[Display Plugin Status]
    R --> S{User Action}
    S -->|Execute Tool| T[Execute Plugin Tool]
    S -->|Configure Plugin| U[Plugin Configuration]
    S -->|Remove Plugin| V[Unregister Plugin]
```

## Data Flow Patterns

### 8. Real-time Communication Flow

```mermaid
graph TD
    A[User Action] --> B[Frontend Event]
    B --> C[Socket.IO Client]
    C --> D[WebSocket Connection]
    D --> E[Backend Socket Handler]
    E --> F{Event Type}
    F -->|Project Update| G[Project Socket Handler]
    F -->|Task Update| H[Task Socket Handler]
    F -->|Knowledge Update| I[Knowledge Socket Handler]
    F -->|Progress Update| J[Progress Socket Handler]

    G --> K[Broadcaster Service]
    H --> K
    I --> K
    J --> K

    K --> L[Broadcast to Clients]
    L --> M[Update UI Components]
    M --> N[Real-time UI Update]
```

### 9. AI Processing Pipeline Flow

```mermaid
graph TD
    A[User Request] --> B[API Endpoint]
    B --> C[Validate Request]
    C --> D{Valid Request?}
    D -->|No| E[Return Error]
    D -->|Yes| F[Route to Service]

    F --> G{Request Type}
    G -->|Generation| H[AI Provider Service]
    G -->|Search| I[RAG Service]
    G -->|Analysis| J[Agent Service]

    H --> K[Select Provider]
    K --> L{Provider Available?}
    L -->|No| M[Fallback Provider]
    L -->|Yes| N[Execute Request]

    M --> O{All Providers Failed?}
    O -->|No| N
    O -->|Yes| P[Return Error]

    N --> Q[Process Response]
    Q --> R[Format Output]
    R --> S[Return Result]

    I --> T[Search Strategy]
    T --> U[Execute Search]
    U --> V[Apply Reranking]
    V --> W[Return Results]

    J --> X[Agent Orchestrator]
    X --> Y[Execute Workflow]
    Y --> Z[Process Results]
    Z --> S
```

## Error Handling & Recovery Flows

### 10. Error Recovery Flow

```mermaid
graph TD
    A[Error Occurs] --> B[Error Boundary]
    B --> C[Capture Error Details]
    C --> D[Log Error]
    D --> E{Error Type}

    E -->|Network Error| F[Check Connectivity]
    E -->|Authentication Error| G[Refresh Credentials]
    E -->|Validation Error| H[Show Validation Message]
    E -->|Server Error| I[Show Server Error]
    E -->|Client Error| J[Show Client Error]

    F --> K{Connection Restored?}
    K -->|Yes| L[Retry Operation]
    K -->|No| M[Show Offline Mode]

    G --> N{Credentials Valid?}
    N -->|Yes| L
    N -->|No| O[Redirect to Settings]

    L --> P{Retry Successful?}
    P -->|Yes| Q[Continue Normal Flow]
    P -->|No| R[Show Retry Failed]

    H --> S[Highlight Invalid Fields]
    I --> T[Show Error Details]
    J --> U[Show Error Message]

    R --> V{User Action}
    V -->|Retry| L
    V -->|Cancel| W[Cancel Operation]
    V -->|Report| X[Open Bug Report]
```

## Performance & Monitoring Flows

### 11. Health Monitoring Flow

```mermaid
graph TD
    A[Application Start] --> B[Initialize Health Monitoring]
    B --> C[Start Health Check Service]
    C --> D[Periodic Health Checks]

    D --> E{Check Backend}
    E --> F{Backend Healthy?}
    F -->|Yes| G[Check Database]
    F -->|No| H[Log Backend Error]

    G --> I{Database Healthy?}
    I -->|Yes| J[Check External Services]
    I -->|No| K[Log Database Error]

    J --> L{External Services OK?}
    L -->|Yes| M[Update Health Status]
    L -->|No| N[Log Service Error]

    H --> O[Attempt Recovery]
    K --> O
    N --> O

    O --> P{Recovery Successful?}
    P -->|Yes| Q[Resume Normal Operation]
    P -->|No| R[Escalate Alert]

    M --> S[Broadcast Health Status]
    S --> T[Update UI Indicators]
    T --> U[Display Status to User]
```

## Security & Authentication Flows

### 12. Authentication Flow

```mermaid
graph TD
    A[User Access Protected Resource] --> B[Check Authentication]
    B --> C{User Authenticated?}
    C -->|Yes| D[Check Authorization]
    C -->|No| E[Redirect to Login]

    D --> F{User Authorized?}
    F -->|Yes| G[Grant Access]
    F -->|No| H[Show Access Denied]

    E --> I[Authentication Service]
    I --> J{Auth Method}
    J -->|API Key| K[Validate API Key]
    J -->|JWT Token| L[Validate JWT Token]
    J -->|OAuth| M[OAuth Flow]

    K --> N{Key Valid?}
    L --> O{Token Valid?}
    M --> P{OAuth Valid?}

    N -->|Yes| Q[Set User Context]
    O -->|Yes| Q
    P -->|Yes| Q
    N -->|No| R[Invalid Credentials]
    O -->|No| R
    P -->|No| R

    Q --> G
    R --> S[Show Auth Error]
    S --> T{Retry Login?}
    T -->|Yes| E
    T -->|No| U[Access Denied]
```

This comprehensive flow diagram covers all major user journeys and system interactions within the Zippy Archon platform, providing a clear roadmap for understanding the application's behavior and identifying areas for improvement.