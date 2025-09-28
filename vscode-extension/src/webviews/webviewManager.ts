import * as vscode from 'vscode';
import * as path from 'path';

export class ZippyWebviewManager {
  private context: vscode.ExtensionContext;
  private panels: Map<string, vscode.WebviewPanel> = new Map();

  constructor(context: vscode.ExtensionContext) {
    this.context = context;
  }

  async showContractsGraph(): Promise<void> {
    const panelId = 'zippyContractsGraph';

    // Check if panel already exists
    let panel = this.panels.get(panelId);

    if (panel) {
      panel.reveal(vscode.ViewColumn.One);
      return;
    }

    // Create new panel
    panel = vscode.window.createWebviewPanel(
      'zippyContractsGraph',
      'Zippy Contracts Graph',
      vscode.ViewColumn.One,
      {
        enableScripts: true,
        localResourceRoots: [
          vscode.Uri.file(path.join(this.context.extensionPath, 'media'))
        ]
      }
    );

    this.panels.set(panelId, panel);

    // Set up panel content
    panel.webview.html = this.getContractsGraphHtml(panel.webview);

    // Handle panel disposal
    panel.onDidDispose(() => {
      this.panels.delete(panelId);
    });

    // Handle messages from webview
    panel.webview.onDidReceiveMessage(async (message) => {
      await this.handleWebviewMessage(message, panel!);
    });
  }

  private getContractsGraphHtml(webview: vscode.Webview): string {
    // Get the local path to script and css files
    const scriptUri = webview.asWebviewUri(
      vscode.Uri.file(path.join(this.context.extensionPath, 'media', 'contracts-graph.js'))
    );
    const styleUri = webview.asWebviewUri(
      vscode.Uri.file(path.join(this.context.extensionPath, 'media', 'contracts-graph.css'))
    );

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zippy Contracts Graph</title>
    <link href="${styleUri}" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
</head>
<body>
    <div class="header">
        <h1>🕸️ Zippy Contracts Graph</h1>
        <div class="controls">
            <button id="refreshBtn">🔄 Refresh</button>
            <button id="exportBtn">📤 Export</button>
            <select id="filterSelect">
                <option value="all">All Contracts</option>
                <option value="active">Active Only</option>
                <option value="high-trust">High Trust (>80%)</option>
            </select>
        </div>
    </div>

    <div class="stats-panel">
        <div class="stat-card">
            <h3>📋 Tasks</h3>
            <div class="stat-value" id="taskCount">0</div>
        </div>
        <div class="stat-card">
            <h3>🌳 Worktrees</h3>
            <div class="stat-value" id="worktreeCount">0</div>
        </div>
        <div class="stat-card">
            <h3>🤖 Agents</h3>
            <div class="stat-value" id="agentCount">0</div>
        </div>
        <div class="stat-card">
            <h3>🔗 Contracts</h3>
            <div class="stat-value" id="contractCount">0</div>
        </div>
    </div>

    <div class="graph-container">
        <div id="mermaid-graph" class="mermaid">
            graph TD
                A[Initialize Project] --> B[Create Task]
                B --> C[Generate Worktree]
                C --> D[Assign Agent]
                D --> E[Run Lifecycle]
                E --> F[Requirements]
                E --> G[Design]
                E --> H[Implementation]
                E --> I[QA]
                I --> J[Create PR]
        </div>
    </div>

    <div class="contract-details">
        <h2>📋 Active Contracts</h2>
        <div id="contractList" class="contract-list">
            <!-- Contract items will be populated here -->
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();

        // Initialize Mermaid
        mermaid.initialize({
            startOnLoad: true,
            theme: 'dark',
            themeVariables: {
                primaryColor: '#00ff88',
                primaryTextColor: '#ffffff',
                primaryBorderColor: '#00ff88',
                lineColor: '#00ff88',
                secondaryColor: '#2d3748',
                tertiaryColor: '#4a5568'
            }
        });

        // Event listeners
        document.getElementById('refreshBtn').addEventListener('click', () => {
            vscode.postMessage({ command: 'refresh' });
        });

        document.getElementById('exportBtn').addEventListener('click', () => {
            vscode.postMessage({ command: 'export' });
        });

        document.getElementById('filterSelect').addEventListener('change', (e) => {
            vscode.postMessage({
                command: 'filter',
                filter: e.target.value
            });
        });

        // Handle messages from extension
        window.addEventListener('message', event => {
            const message = event.data;

            switch (message.command) {
                case 'updateStats':
                    updateStats(message.stats);
                    break;
                case 'updateGraph':
                    updateGraph(message.graphData);
                    break;
                case 'updateContracts':
                    updateContracts(message.contracts);
                    break;
            }
        });

        function updateStats(stats) {
            document.getElementById('taskCount').textContent = stats.tasks || 0;
            document.getElementById('worktreeCount').textContent = stats.worktrees || 0;
            document.getElementById('agentCount').textContent = stats.agents || 0;
            document.getElementById('contractCount').textContent = stats.contracts || 0;
        }

        function updateGraph(graphData) {
            const graphElement = document.getElementById('mermaid-graph');
            graphElement.innerHTML = graphData;
            mermaid.init(undefined, graphElement);
        }

        function updateContracts(contracts) {
            const contractList = document.getElementById('contractList');
            contractList.innerHTML = '';

            contracts.forEach(contract => {
                const contractItem = document.createElement('div');
                contractItem.className = 'contract-item';
                contractItem.innerHTML = \`
                    <div class="contract-header">
                        <span class="contract-title">\${contract.title}</span>
                        <span class="contract-status status-\${contract.status}">\${contract.status}</span>
                    </div>
                    <div class="contract-meta">
                        <span>🔗 \${contract.dependencies} dependencies</span>
                        <span>🎯 \${contract.completeness}% complete</span>
                        <span>🛡️ Trust: \${contract.trustScore}%</span>
                    </div>
                \`;
                contractList.appendChild(contractItem);
            });
        }

        // Initial data request
        vscode.postMessage({ command: 'initialize' });
    </script>
</body>
</html>`;
  }

  private async handleWebviewMessage(message: any, panel: vscode.WebviewPanel): Promise<void> {
    switch (message.command) {
      case 'initialize':
        await this.sendInitialData(panel);
        break;

      case 'refresh':
        await this.sendUpdatedData(panel);
        break;

      case 'export':
        await this.exportGraphData();
        break;

      case 'filter':
        await this.sendFilteredData(panel, message.filter);
        break;

      default:
        console.log('Unknown webview message:', message);
    }
  }

  private async sendInitialData(panel: vscode.WebviewPanel): Promise<void> {
    // Mock data - in real implementation, this would come from the orchestrator
    const mockData = {
      stats: {
        tasks: 5,
        worktrees: 3,
        agents: 2,
        contracts: 8
      },
      contracts: [
        {
          title: 'User Authentication',
          status: 'active',
          dependencies: 3,
          completeness: 75,
          trustScore: 85
        },
        {
          title: 'Payment Processing',
          status: 'pending',
          dependencies: 5,
          completeness: 45,
          trustScore: 72
        },
        {
          title: 'Data Analytics',
          status: 'completed',
          dependencies: 2,
          completeness: 100,
          trustScore: 92
        }
      ]
    };

    panel.webview.postMessage({
      command: 'updateStats',
      stats: mockData.stats
    });

    panel.webview.postMessage({
      command: 'updateContracts',
      contracts: mockData.contracts
    });
  }

  private async sendUpdatedData(panel: vscode.WebviewPanel): Promise<void> {
    // Simulate refreshing data
    await this.sendInitialData(panel);

    vscode.window.showInformationMessage('Contracts graph refreshed');
  }

  private async sendFilteredData(panel: vscode.WebviewPanel, filter: string): Promise<void> {
    // Simulate filtered data based on filter type
    let filteredContracts = [];

    switch (filter) {
      case 'active':
        filteredContracts = [
          {
            title: 'User Authentication',
            status: 'active',
            dependencies: 3,
            completeness: 75,
            trustScore: 85
          }
        ];
        break;

      case 'high-trust':
        filteredContracts = [
          {
            title: 'Data Analytics',
            status: 'completed',
            dependencies: 2,
            completeness: 100,
            trustScore: 92
          }
        ];
        break;

      default:
        await this.sendInitialData(panel);
        return;
    }

    panel.webview.postMessage({
      command: 'updateContracts',
      contracts: filteredContracts
    });
  }

  private async exportGraphData(): Promise<void> {
    const uri = await vscode.window.showSaveDialog({
      filters: {
        'PNG Files': ['png'],
        'SVG Files': ['svg'],
        'JSON Files': ['json']
      },
      defaultUri: vscode.Uri.file('zippy-contracts-graph.png')
    });

    if (uri) {
      vscode.window.showInformationMessage(`Graph exported to: ${uri.fsPath}`);
    }
  }

  dispose(): void {
    // Dispose of all panels
    this.panels.forEach(panel => panel.dispose());
    this.panels.clear();
  }
}
