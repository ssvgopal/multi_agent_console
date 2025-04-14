# MultiAgentConsole Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         MultiAgentConsole System                           │
└───────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                              Terminal UI Layer                             │
│                                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  Chat View  │  │ Config Panel│  │Memory Browser│  │ Status Bar  │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└───────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                              Agent System Layer                            │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │                        Coordinator Agent                         │      │
│  └─────────────────────────────────────────────────────────────────┘      │
│                                     │                                      │
│                                     ▼                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │    Code     │  │  Research   │  │   System    │  │    Data     │       │
│  │  Assistant  │  │  Assistant  │  │  Assistant  │  │  Assistant  │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└───────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                             Core Services Layer                            │
│                                                                           │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐│
│  │   Memory Manager    │  │    Tool Manager     │  │  Security Manager   ││
│  │┌───────────────────┐│  │┌───────────────────┐│  │┌───────────────────┐││
│  ││ Conversation Store││  ││  Advanced Tools   ││  ││   Permissions     │││
│  │└───────────────────┘│  │└───────────────────┘│  │└───────────────────┘││
│  │┌───────────────────┐│  │┌───────────────────┐│  │┌───────────────────┐││
│  ││   User Profiles   ││  ││  Multi-Modal      ││  ││   Sandboxing      │││
│  │└───────────────────┘│  │└───────────────────┘│  │└───────────────────┘││
│  │┌───────────────────┐│  │┌───────────────────┐│  │┌───────────────────┐││
│  ││ Context Enhancer  ││  ││  Workflow Tools   ││  ││ Credential Store  │││
│  │└───────────────────┘│  │└───────────────────┘│  │└───────────────────┘││
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘│
└───────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                         Communication Protocol Layer                       │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │                           MCP Server                             │      │
│  │                                                                  │      │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │      │
│  │  │ MCP Agents  │  │MCP Messages │  │    Plugin Manager       │  │      │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │      │
│  │                                     ┌─────────────┐ ┌──────────┐ │      │
│  │                                     │Logger Plugin│ │A2A Plugin│ │      │
│  │                                     └─────────────┘ └──────────┘ │      │
│  └─────────────────────────────────────────────────────────────────┘      │
│                                     │                                      │
│                                     ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │                        Thought Graph Analysis                    │      │
│  │                                                                  │      │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │      │
│  │  │Graph Analyzer   │  │Graph Manager    │  │Graph Plugins    │  │      │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  │      │
│  └─────────────────────────────────────────────────────────────────┘      │
└───────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                              External Systems                              │
│                                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ Google ADK  │  │  LLM APIs   │  │External Tools│  │A2A Protocol │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└───────────────────────────────────────────────────────────────────────────┘
```

## Component Descriptions

### Terminal UI Layer
- **Chat View**: Main interface for user interactions
- **Config Panel**: Settings and configuration options
- **Memory Browser**: Access to conversation history
- **Status Bar**: System status and active agent information

### Agent System Layer
- **Coordinator Agent**: Routes requests to specialized agents
- **Code Assistant**: Programming and development help
- **Research Assistant**: Information retrieval and synthesis
- **System Assistant**: System administration tasks
- **Data Assistant**: Data analysis and visualization

### Core Services Layer
- **Memory Manager**: Handles conversation history, user profiles, context
- **Tool Manager**: Manages various tool integrations
- **Security Manager**: Handles permissions, sandboxing, credentials

### Communication Protocol Layer
- **MCP Server**: Implements Multi-Agent Communication Protocol
- **Thought Graph Analysis**: Analyzes queries as concept networks

### External Systems
- **Google ADK**: Agent Development Kit integration
- **LLM APIs**: Language model providers
- **External Tools**: Git, databases, APIs, etc.
- **A2A Protocol**: Agent-to-Agent protocol integration
