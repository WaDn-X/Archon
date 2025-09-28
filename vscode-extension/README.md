# Zippy Archon Orchestrator - VS Code Extension

A comprehensive VS Code extension that transforms your development workflow into a multi-agent orchestration platform with trust validation and marketplace integration.

## 🚀 Features

### Core Functionality
- **Multi-Agent Orchestration**: Coordinate multiple AI agents across Git worktrees
- **Trust Validation**: Real-time trust scoring for all generated artifacts
- **Marketplace Integration**: Direct access to ZippyCoin marketplace from VS Code
- **Worktree Management**: Automated Git worktree creation and management
- **Visual Task Tracking**: Interactive task overlay with progress indicators

### Advanced Features
- **Genome Selection**: Choose between Aggressive, Balanced, and Conservative agent behaviors
- **Contract Graph Visualization**: Interactive dependency and relationship graphs
- **Real-time Telemetry**: Live agent status, trust scores, and performance metrics
- **Integrated QA**: Automated quality assurance with trust validation
- **Pull Request Automation**: Seamless PR creation from completed worktrees

## 📦 Installation

### Prerequisites
- VS Code 1.74.0 or later
- Node.js 16.x or later
- Git (for worktree functionality)

### Install from Source
```bash
# Clone the repository
git clone https://github.com/your-org/zippy-archon.git
cd zippy-archon/vscode-extension

# Install dependencies
npm install

# Compile the extension
npm run compile

# Package the extension
npx vsce package

# Install the .vsix file in VS Code
code --install-extension zippy-archon-orchestrator-0.1.0.vsix
```

### Install from Marketplace (Future)
```bash
# Once published to VS Code Marketplace
code --install-extension zippy-archon-orchestrator
```

## 🏁 Getting Started

### 1. Initialize Project
1. Open your project in VS Code
2. Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
3. Run `Zippy: Initialize Project`
4. This creates the required directory structure and configuration

### 2. Create Your First Task
1. Open Command Palette
2. Run `Zippy: Create Worktree from Task`
3. Select or create a task from the task list
4. The extension automatically:
   - Creates a Git worktree
   - Assigns an AI agent
   - Starts the development lifecycle

### 3. Monitor Progress
- View real-time status in the **Zippy Orchestrator** sidebar
- Track agent activity in the status bar
- Monitor trust scores and completion metrics
- View the contracts graph for dependency visualization

## 🎯 Key Workflows

### Development Lifecycle
1. **Task Creation**: Define features with trust-scored requirements
2. **Worktree Generation**: Automatic Git worktree creation per task
3. **Agent Assignment**: Intelligent agent selection based on genome
4. **Lifecycle Execution**: Automated progression through phases:
   - 📋 Requirements Analysis
   - 🎨 Design Generation
   - ⚡ Implementation
   - ✅ Quality Assurance
   - 🔀 Pull Request Creation

### Quality Assurance
- **Automated Testing**: Built-in test execution and validation
- **Trust Scoring**: Real-time trust assessment of generated code
- **Code Quality**: Static analysis and best practice validation
- **Security Checks**: Vulnerability scanning and secure coding validation

### Marketplace Integration
- **Browse Assets**: Access spec templates, A/B test results, and more
- **Purchase & Download**: Seamless integration with ZippyCoin transactions
- **Publish Artifacts**: Share your successful implementations
- **Trust Validation**: All marketplace items validated for quality

## 🛠️ Configuration

### Extension Settings
```json
{
  "zippy.serverUrl": "http://localhost:8000",
  "zippy.defaultGenome": "balanced",
  "zippy.autoInitialize": false,
  "zippy.trustThreshold": 0.7
}
```

### Genome Options
- **Aggressive**: Fast execution, higher risk tolerance
- **Balanced**: Moderate speed with balanced risk management
- **Conservative**: Thorough validation, lower risk tolerance

## 📊 User Interface

### Sidebar Panel
The **Zippy Orchestrator** panel provides:
- **Tasks**: Backlog, active, and completed tasks with trust indicators
- **Worktrees**: Active Git worktrees with agent assignments
- **Agents**: Running agents with genome, status, and performance metrics
- **Contracts**: Dependency graphs and relationship visualization

### Status Bar
Real-time indicators showing:
- Current genome selection
- Overall project trust score
- Active agent count
- Worktree completion status

### Commands
- `Zippy: Initialize Project` - Set up project structure
- `Zippy: Create Worktree` - Generate worktree for selected task
- `Zippy: Run Lifecycle` - Execute agent lifecycle
- `Zippy: Open Contracts Graph` - View dependency visualization
- `Zippy: QA Current Worktree` - Run quality assurance
- `Zippy: Switch Agent Genome` - Change agent behavior
- `Zippy: View Agent Logs` - Access detailed agent activity

## 🔧 Advanced Usage

### Custom Genome Configuration
```json
{
  "zippy.genomes": {
    "custom": {
      "speed": 0.8,
      "creativity": 0.6,
      "caution": 0.7
    }
  }
}
```

### API Integration
```typescript
import { ZippyOrchestrator } from 'vscode-zippy-archon';

// Initialize orchestrator
const orchestrator = new ZippyOrchestrator();

// Create task programmatically
await orchestrator.createTask({
  title: 'Implement Authentication',
  description: 'Add user authentication system',
  priority: 'high',
  tags: ['security', 'backend']
});
```

### Custom Agent Behaviors
```typescript
// Define custom agent behavior
const customAgent = {
  genome: 'custom',
  prompts: {
    requirements: 'Focus on security requirements...',
    design: 'Emphasize scalable architecture...',
    implementation: 'Follow TDD principles...'
  },
  trustThreshold: 0.8
};
```

## 🐛 Troubleshooting

### Common Issues

**Worktree Creation Fails**
```
Error: Git worktree creation failed
```
- Ensure Git is installed and repository is initialized
- Check write permissions in project directory
- Verify no conflicting worktree names

**Agent Connection Issues**
```
Error: Cannot connect to Zippy server
```
- Verify server is running on configured port
- Check network connectivity
- Review server logs for connection issues

**Trust Scoring Errors**
```
Error: Trust calculation failed
```
- Ensure all required dependencies are installed
- Check API key configuration
- Verify network access to trust registry

### Debug Mode
Enable debug logging:
```json
{
  "zippy.debug": true
}
```

Access logs via:
1. Open Command Palette
2. Run `Developer: Show Logs`
3. Select `Zippy Archon Orchestrator`

## 🤝 Contributing

### Development Setup
```bash
# Clone and setup
git clone https://github.com/your-org/zippy-archon.git
cd zippy-archon/vscode-extension

# Install dependencies
npm install

# Start development
npm run watch

# Debug in VS Code
# Press F5 to launch extension development host
```

### Testing
```bash
# Run tests
npm test

# Run linting
npm run lint

# Compile for production
npm run compile
```

### Code Structure
```
src/
├── extension.ts          # Main extension entry point
├── orchestrator.ts       # Core orchestration logic
├── providers/
│   └── treeDataProvider.ts  # Sidebar tree view
├── webviews/
│   └── webviewManager.ts    # Interactive dashboards
└── statusBar.ts         # Status bar integration
```

## 📋 Roadmap

### Phase 1 (Current)
- ✅ Basic multi-agent orchestration
- ✅ Git worktree management
- ✅ Trust scoring integration
- ✅ Marketplace access

### Phase 2 (Next Release)
- 🔄 Advanced genome configurations
- 🔄 Custom agent behaviors
- 🔄 Enhanced telemetry
- 🔄 Collaborative features

### Phase 3 (Future)
- 🔄 Multi-repository support
- 🔄 Enterprise integrations
- 🔄 Advanced analytics
- 🔄 AI model marketplace

## 📄 License

This extension is part of the Zippy-Archon project and is licensed under the MIT License.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/zippy-archon/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/zippy-archon/discussions)
- **Documentation**: [Full Documentation](https://zippy-archon.dev/docs)

---

**Transform your development workflow with AI-powered orchestration!** 🚀
