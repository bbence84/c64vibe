# 🎮 C64Vibe - AI-Powered Commodore 64 Game Creator

C64Vibe is an AI agent specialized in creating games for the Commodore 64 computer using BASIC V2.0. It leverages modern AI models to design, code, test, and optionally run C64 programs on real hardware or emulators.

**Created by Bence Blaske - 2025**

## ✨ Features

- **AI-Powered Game Design**: Uses advanced LLMs (Google Gemini, Anthropic Claude, OpenAI GPT) to create complete game designs
- **Automatic Code Generation**: Generates syntactically correct C64 BASIC V2.0 code
- **Syntax Checking**: Built-in LLM-based and rule-based syntax validation
- **Hardware Integration**: Optional support for real C64 hardware via:
  - KungFu Flash USB device for program loading
  - C64 keyboard control
  - Video capture for screen analysis
- **Dual Interface**: 
  - **Web UI** (Chainlit): User-friendly web interface with file downloads and emulator integration
  - **CLI**: Terminal-based interface for command-line enthusiasts
- **Multiple LLM Providers**: Support for Google AI, Anthropic, OpenAI, and OpenRouter

## 📋 Requirements

- Python 3.12+
- API key from one of the supported AI providers:
  - Google AI Studio
  - Anthropic
  - OpenAI
  - OpenRouter (provides access to multiple models with one key)

### Optional Hardware
- KungFu Flash USB device, with modified firmware (for loading programs on real C64)
- USB keyboard interface for C64
- Video capture device (for screen capture analysis)

## 🚀 Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd c64vibe
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp env_template .env
```

Edit `.env` and add your AI provider credentials:
```
AI_MODEL_PROVIDER=google_genai
AI_MODEL_NAME=gemini-3-flash-preview
API_KEY=your_api_key_here

# Optional: For LangSmith tracing
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your_langsmith_key_here
```
Possible AI providers: anthropic, openai, azure_openai, google_genai, openrouter
For OpenRouter, use the model name with the prefix as shown on the OpenRouter model page, i.e. google/gemini-3-flash-preview

## 🎯 Usage

### Web Interface (Recommended)

```bash
chainlit run main.py
```

The web interface will open at `http://localhost:8000`. You can:
- Set your AI model and API key in the settings panel (⚙️ icon)
- Chat with the agent to create C64 games
- Download generated `.bas` and `.prg` files
- Launch programs directly in an online C64 emulator

### Command Line Interface

```bash
python c64vibe_cli.py
```

The CLI provides a terminal-based interface with rich formatting and markdown support.

## 📁 Folder Structure

```
c64vibe/
│
├── main.py           # Main Chainlit web interface
├── c64vibe_cli.py          # Command-line interface
├── chainlit.md             # Chainlit welcome message
├── requirements.txt        # Python dependencies
├── env_template            # Environment variables template
├── README.md               # This file
│
├── .chainlit/              # Chainlit configuration
│   ├── config.toml         # Chainlit settings
│   └── translations/       # UI translations (multiple languages)
│
├── tools/                  # Agent tools and state management
│   ├── agent_state.py      # Agent state schema
│   ├── coding_tools.py     # Code generation and syntax checking tools
│   ├── game_design_tools.py    # Creates detailed design based on user request
│   ├── testing_tools.py    # Testing and validation tools
│   └── hw_access_tools.py  # Hardware interaction tools (C64, KungFu Flash)
│
├── utils/                  # Utility modules
│   ├── llm_access.py       # LLM provider abstraction
│   ├── agent_utils.py      # Agent helper functions
│   ├── chainlit_middleware.py  # Chainlit integration middleware
│   ├── c64_syntax_checker.py   # C64 BASIC syntax validation
│   ├── bas2prg.py          # BASIC to PRG converter
│   ├── c64_hw.py           # C64 hardware interface
│   ├── c64_keymaps.py      # C64 keyboard mappings
│   ├── kungfuflash_usb.py  # KungFu Flash USB communication
│   └── formatting.py       # Output formatting utilities
│
├── resources/              # Resource files
│   └── examples/           # Example C64 BASIC programs
│       ├── adv.bas
│       └── gengszter.bas
│
├── output/                 # Generated programs output directory
│
└── public/                 # Web interface assets
    ├── avatars/           # Chat avatars
    └── elements/          # Custom UI elements
        └── EmulatorLink.jsx  # Emulator launch component
```

## 🔧 How It Works

### Architecture Overview

C64Vibe is built on the **LangChain** framework for agent orchestration. The web interface uses **Chainlit** for a modern, interactive chat experience.

### Core Components

#### 1. Agent State Management (`tools/agent_state.py`)

The agent maintains state across interactions, storing the current C64 BASIC source code and any syntax errors detected. This allows the agent to:
- Iteratively refine code without losing context
- Track syntax errors across checking cycles
- Maintain conversation history and todo lists

#### 2. LLM Access Layer (`utils/llm_access.py`)

The `LLMAccessProvider` class provides a unified interface to multiple AI providers:

- **Model Mapping**: Translates user-friendly model names to provider-specific identifiers
- **Provider Support**: Google AI, Anthropic, OpenAI, and OpenRouter
- **Dynamic Initialization**: Allows runtime model switching without restart
- **API Key Management**: Securely handles credentials for different providers


#### 3. Agent Tools

The agent has access to three main tool categories:

##### **Coding Tools** (`tools/coding_tools.py`)
- **CreateUpdateC64BasicCode**: Generates or modifies C64 BASIC code based on design plans
- **SyntaxChecker**: Validates code syntax using LLM or rule-based checking
- **FixSyntaxErrors**: Automatically corrects syntax errors
- **ConvertCodeToPRG**: Converts BASIC text to C64 PRG binary format

##### **Games Design Tools** (`game_design_tools.py`)
- **DesignGamePlan**: Creates detailed game design documents using LLM

The code generation process:
1. User provides game concept
2. Agent creates detailed design plan
3. Design plan is passed to LLM coder model
4. Generated code is stored in agent state
5. Syntax checker validates the code
6. If errors exist, FixSyntaxErrors tool corrects them
7. Cycle repeats until code is error-free

##### **Testing Tools** (`tools/testing_tools.py`)
- **CaptureC64Screen**: Captures C64 screen via video input device and compares the screen reading to an expected result

##### **Hardware Access Tools** (`tools/hw_access_tools.py`)
- **RunC64Program**: Loads and executes programs on real C64 via KungFu Flash, using a modified firmware
- **RestartC64**: Resets the C64 hardware
- **TypeOnC64**: Sends keyboard input to C64

#### 4. Web Interface Flow (`main.py`)

The web interface starts by setting up the AI connection, checking if C64 hardware is connected, and displaying a welcome message. It then creates the agent with access to code generation tools, testing tools, and file management capabilities.

When a user sends a message, the agent processes it and streams the response back word-by-word for a natural chat experience. Users can change their AI model or API key at any time through the settings panel without needing to restart the application.

#### 5. Middleware Stack

The agent uses three key middleware layers:

1. **TodoListMiddleware**: Tracks agent's task progress
   - Breaks down complex requests into steps
   - Shows users what the agent is working on
   - Helps ensure systematic completion

2. **FilesystemMiddleware**: Manages file operations
   - Provides filesystem tools to agent
   - Handles file reading, writing, listing
   - Used for loading example programs

3. **ChainlitMiddlewareTracer**: Integrates with UI
   - Captures tool calls and displays them in chat
   - Formats tool outputs for user-friendly display
   - Handles file downloads and external links

#### 6. Code Generation Workflow

The complete workflow for creating a C64 game:

```mermaid
graph TD
    A[User Request] --> B[DesignGamePlan Tool]
    B --> C[Game Design Document]
    C --> D[CreateUpdateC64BasicCode Tool]
    D --> E[C64 BASIC Source Code]
    E --> F[Agent State]
    F --> G[SyntaxChecker Tool]
    G --> H{Errors Found?}
    H -->|Yes| I[FixSyntaxErrors Tool]
    I --> G
    H -->|No| J[ConvertCodeToPRG Tool]
    J --> K[.BAS and .PRG files]
    K --> L[Offer Download + Emulator Link]
    L --> M[Optional: RunC64Program Tool]
    M --> N[Real Hardware]
```

#### 7. Hardware Integration

When C64 hardware is available:

- **KungFu Flash**: USB device that allows loading programs directly
- **C64 Keyboard**: Serial interface for sending keystrokes
- **Capture Device**: Video capture for screen analysis via OpenCV

The agent dynamically adjusts its system prompt based on hardware availability, enabling or disabling relevant tools.

#### 8. Error Handling & Validation

Multi-layered validation ensures code quality:

1. **LLM-based Syntax Checking**: Uses AI to understand context and find logical errors
2. **Rule-based Checking**: `c64_syntax_checker.py` validates BASIC syntax rules
3. **Iterative Refinement**: Agent loops until code passes all checks
4. **User Feedback**: Users can report issues and agent will fix them

### Example Interaction Flow

1. User: "Create a simple maze game"
2. Agent: Uses DesignGamePlan to create detailed design
3. Agent: Uses CreateUpdateC64BasicCode with full design plan
4. Agent: Stores code in `current_source_code` state
5. Agent: Runs SyntaxChecker to validate
6. Agent: If errors found, uses FixSyntaxErrors and rechecks
7. Agent: Converts to PRG format
8. Agent: Offers download and emulator link
9. (Optional) Agent: Loads on real C64 and captures screen

## 🎮 Example Games

The `resources/examples/` folder contains sample C64 BASIC programs:
- **adv.bas**: Text adventure game
- **gengszter.bas**: A hungarian text based adventure game

These examples are used by the LLM as few-shot examples for better syntax following and game design ideas.

## 🔑 Getting API Keys

### OpenRouter (Recommended)
1. Register at [openrouter.ai](https://openrouter.ai)
2. Add credits at [openrouter.ai/settings/credits](https://openrouter.ai/settings/credits)
3. Get API key at [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)
4. Provides access to multiple AI models with single key

### Direct Provider Keys
- **Google**: [aistudio.google.com/app/api-keys](https://aistudio.google.com/app/api-keys)
- **Anthropic**: [console.anthropic.com](https://console.anthropic.com)
- **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### Recommended Models
- **Best Performance**: Google Gemini 3.0 Flash Preview (fast & cost-effective)
- **Highest Quality**: Anthropic Claude 4.5 Sonnet (slower but potentially more capable)
- **Alternative**: OpenAI GPT-5.2 (balanced performance)

## 🐛 Troubleshooting

### API Key Issues
- Ensure API key is correctly entered in settings
- Check that you have credits/quota with your provider
- Verify the model name matches your provider's offerings

### Hardware Connection Issues
- Check USB connections for KungFu Flash and capture device
- Ensure C64 is powered on and KungFu Flash is properly initialized
- Run hardware tests in `tests/` folder to diagnose issues

### Code Generation Issues
- Be specific in your game descriptions
- Provide clear requirements and constraints
- Use the fix/modify feature if initial generation needs improvement

## 📝 Development Status

**Current Status**: BETA

### Completed Features
- ✅ Web and CLI interfaces
- ✅ Multiple LLM provider support
- ✅ Code generation and syntax checking
- ✅ Hardware integration
- ✅ File download and emulator links

### Planned Features
- 🔄 Enhanced error handling and logging
- 🔄 Test case generation and execution
- 🔄 Sprite and graphic asset generation using generative AI
- 🔄 Sound effect and music generation tools
- 🔄 User registration and conversation persistency
- 🔄 Multi-language UI support

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📄 License

MIT

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com) and [LangGraph](https://langchain-ai.github.io/langgraph/)
- Web UI powered by [Chainlit](https://chainlit.io)
- Hardware integration via KungFu Flash USB device (using a modified firmware)

---

**Note**: This is a beta release. Some features may be experimental or incomplete. Hardware integration requires specific USB devices and is optional for using the emulator-based features.