import * as vscode from 'vscode';
import { ZippyOrchestrator } from './orchestrator';
import { ZippyTreeDataProvider } from './providers/treeDataProvider';
import { ZippyStatusBar } from './statusBar';
import { ZippyWebviewManager } from './webviews/webviewManager';

let orchestrator: ZippyOrchestrator;
let treeDataProvider: ZippyTreeDataProvider;
let statusBar: ZippyStatusBar;
let webviewManager: ZippyWebviewManager;

export function activate(context: vscode.ExtensionContext) {
  console.log('Zippy Archon Orchestrator is now active!');

  // Initialize core components
  orchestrator = new ZippyOrchestrator(context);
  treeDataProvider = new ZippyTreeDataProvider(orchestrator);
  statusBar = new ZippyStatusBar();
  webviewManager = new ZippyWebviewManager(context);

  // Register tree data provider
  vscode.window.registerTreeDataProvider('zippyOrchestrator', treeDataProvider);

  // Register commands
  const commands = [
    vscode.commands.registerCommand('zippy.initializeProject', initializeProject),
    vscode.commands.registerCommand('zippy.createWorktree', createWorktree),
    vscode.commands.registerCommand('zippy.runLifecycle', runLifecycle),
    vscode.commands.registerCommand('zippy.openContractsGraph', openContractsGraph),
    vscode.commands.registerCommand('zippy.qaCurrentWorktree', qaCurrentWorktree),
    vscode.commands.registerCommand('zippy.openPR', openPR),
    vscode.commands.registerCommand('zippy.switchAgentGenome', switchAgentGenome),
    vscode.commands.registerCommand('zippy.viewAgentLogs', viewAgentLogs)
  ];

  // Register webview serializers
  const webviewSerializer = vscode.window.registerWebviewPanelSerializer(
    'zippyContractsGraph',
    webviewManager
  );

  // Add to context subscriptions
  context.subscriptions.push(
    ...commands,
    webviewSerializer,
    orchestrator,
    treeDataProvider,
    statusBar,
    webviewManager
  );

  // Initialize status bar
  statusBar.initialize();

  // Check if project is already initialized
  checkProjectInitialization();
}

export function deactivate() {
  console.log('Zippy Archon Orchestrator is now deactivated!');
}

async function initializeProject(): Promise<void> {
  try {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
      vscode.window.showErrorMessage('No workspace folder found');
      return;
    }

    // Initialize project structure
    await orchestrator.initializeProject(workspaceFolder.uri.fsPath);

    // Refresh tree view
    treeDataProvider.refresh();

    vscode.window.showInformationMessage('Zippy Archon project initialized successfully!');
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to initialize project: ${error}`);
  }
}

async function createWorktree(): Promise<void> {
  try {
    // Get selected task from tree view
    const selectedItem = treeDataProvider.getSelectedItem();
    if (!selectedItem || selectedItem.type !== 'task') {
      vscode.window.showErrorMessage('Please select a task first');
      return;
    }

    // Create worktree for selected task
    await orchestrator.createWorktree(selectedItem.id);

    // Refresh tree view
    treeDataProvider.refresh();

    vscode.window.showInformationMessage('Worktree created successfully!');
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to create worktree: ${error}`);
  }
}

async function runLifecycle(): Promise<void> {
  try {
    const selectedItem = treeDataProvider.getSelectedItem();
    if (!selectedItem) {
      vscode.window.showErrorMessage('Please select an item first');
      return;
    }

    // Run lifecycle based on item type
    if (selectedItem.type === 'task') {
      await orchestrator.runTaskLifecycle(selectedItem.id);
    } else if (selectedItem.type === 'worktree') {
      await orchestrator.runWorktreeLifecycle(selectedItem.id);
    }

    // Refresh tree view
    treeDataProvider.refresh();

    vscode.window.showInformationMessage('Lifecycle executed successfully!');
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to run lifecycle: ${error}`);
  }
}

async function openContractsGraph(): Promise<void> {
  try {
    await webviewManager.showContractsGraph();
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to open contracts graph: ${error}`);
  }
}

async function qaCurrentWorktree(): Promise<void> {
  try {
    const currentWorktree = await orchestrator.getCurrentWorktree();
    if (!currentWorktree) {
      vscode.window.showErrorMessage('No active worktree found');
      return;
    }

    // Run QA checks
    const qaResults = await orchestrator.runQA(currentWorktree.id);

    // Show results
    const panel = vscode.window.createWebviewPanel(
      'zippyQA',
      'QA Results',
      vscode.ViewColumn.One,
      {}
    );

    panel.webview.html = generateQAReport(qaResults);
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to run QA: ${error}`);
  }
}

async function openPR(): Promise<void> {
  try {
    const currentWorktree = await orchestrator.getCurrentWorktree();
    if (!currentWorktree) {
      vscode.window.showErrorMessage('No active worktree found');
      return;
    }

    // Create pull request
    await orchestrator.createPR(currentWorktree.id);

    vscode.window.showInformationMessage('Pull request created successfully!');
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to create PR: ${error}`);
  }
}

async function switchAgentGenome(): Promise<void> {
  try {
    const genomes = ['aggressive', 'balanced', 'conservative'];
    const selectedGenome = await vscode.window.showQuickPick(genomes, {
      placeHolder: 'Select agent genome'
    });

    if (selectedGenome) {
      await orchestrator.switchGenome(selectedGenome);
      statusBar.updateGenome(selectedGenome);
      vscode.window.showInformationMessage(`Switched to ${selectedGenome} genome`);
    }
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to switch genome: ${error}`);
  }
}

async function viewAgentLogs(): Promise<void> {
  try {
    const selectedItem = treeDataProvider.getSelectedItem();
    if (!selectedItem || selectedItem.type !== 'agent') {
      vscode.window.showErrorMessage('Please select an agent first');
      return;
    }

    // Get agent logs
    const logs = await orchestrator.getAgentLogs(selectedItem.id);

    // Show logs in output channel
    const outputChannel = vscode.window.createOutputChannel('Zippy Agent Logs');
    outputChannel.clear();
    outputChannel.appendLine(logs);
    outputChannel.show();
  } catch (error) {
    vscode.window.showErrorMessage(`Failed to view agent logs: ${error}`);
  }
}

async function checkProjectInitialization(): Promise<void> {
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  if (!workspaceFolder) {
    return;
  }

  const isInitialized = await orchestrator.isProjectInitialized(workspaceFolder.uri.fsPath);
  vscode.commands.executeCommand('setContext', 'zippy.initialized', isInitialized);

  if (isInitialized) {
    // Refresh tree view with project data
    treeDataProvider.refresh();
  }
}

function generateQAReport(qaResults: any): string {
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>QA Results</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .success { color: green; }
        .warning { color: orange; }
        .error { color: red; }
        .metric { margin: 10px 0; padding: 10px; border: 1px solid #ccc; }
      </style>
    </head>
    <body>
      <h1>QA Results</h1>
      <div class="metric">
        <h3>Test Results</h3>
        <p>Passed: ${qaResults.passed || 0}</p>
        <p>Failed: ${qaResults.failed || 0}</p>
        <p>Skipped: ${qaResults.skipped || 0}</p>
      </div>
      <div class="metric">
        <h3>Code Quality</h3>
        <p>Score: ${qaResults.qualityScore || 0}/100</p>
      </div>
      <div class="metric">
        <h3>Trust Score</h3>
        <p>Score: ${(qaResults.trustScore || 0 * 100).toFixed(1)}%</p>
      </div>
    </body>
    </html>
  `;
}
