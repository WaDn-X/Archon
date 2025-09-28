import * as vscode from 'vscode';
import { ZippyOrchestrator, Task, Worktree, Agent } from '../orchestrator';

export class ZippyTreeDataProvider implements vscode.TreeDataProvider<TreeItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<TreeItem | undefined | null | void> = new vscode.EventEmitter<TreeItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<TreeItem | undefined | null | void> = this._onDidChangeTreeData.fire;

  private selectedItem: TreeItem | null = null;

  constructor(private orchestrator: ZippyOrchestrator) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getSelectedItem(): TreeItem | null {
    return this.selectedItem;
  }

  getTreeItem(element: TreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: TreeItem): Thenable<TreeItem[]> {
    if (!element) {
      // Root level - show main categories
      return Promise.resolve([
        new TreeItem('Tasks', vscode.TreeItemCollapsibleState.Expanded, 'category', 'tasks'),
        new TreeItem('Worktrees', vscode.TreeItemCollapsibleState.Expanded, 'category', 'worktrees'),
        new TreeItem('Agents', vscode.TreeItemCollapsibleState.Expanded, 'category', 'agents'),
        new TreeItem('Contracts', vscode.TreeItemCollapsibleState.Collapsed, 'category', 'contracts')
      ]);
    }

    switch (element.contextValue) {
      case 'category':
        return this.getCategoryChildren(element);
      case 'task':
        return this.getTaskChildren(element);
      case 'worktree':
        return this.getWorktreeChildren(element);
      case 'agent':
        return this.getAgentChildren(element);
      default:
        return Promise.resolve([]);
    }
  }

  private async getCategoryChildren(element: TreeItem): Promise<TreeItem[]> {
    switch (element.id) {
      case 'tasks':
        const tasks = this.orchestrator.getTasks();
        return tasks.map(task => this.createTaskItem(task));

      case 'worktrees':
        const worktrees = this.orchestrator.getWorktrees();
        return worktrees.map(worktree => this.createWorktreeItem(worktree));

      case 'agents':
        const agents = this.orchestrator.getAgents();
        return agents.map(agent => this.createAgentItem(agent));

      case 'contracts':
        return [
          new TreeItem('📋 Requirements Contracts', vscode.TreeItemCollapsibleState.None, 'contract', 'req-contracts'),
          new TreeItem('🎨 Design Contracts', vscode.TreeItemCollapsibleState.None, 'contract', 'design-contracts'),
          new TreeItem('⚡ Implementation Contracts', vscode.TreeItemCollapsibleState.None, 'contract', 'impl-contracts')
        ];

      default:
        return [];
    }
  }

  private async getTaskChildren(element: TreeItem): Promise<TreeItem[]> {
    // Could show subtasks, dependencies, etc.
    return Promise.resolve([
      new TreeItem('📝 Description', vscode.TreeItemCollapsibleState.None, 'task-detail', `${element.id}-desc`),
      new TreeItem('🏷️ Tags', vscode.TreeItemCollapsibleState.None, 'task-detail', `${element.id}-tags`),
      new TreeItem('📊 Progress', vscode.TreeItemCollapsibleState.None, 'task-detail', `${element.id}-progress`)
    ]);
  }

  private async getWorktreeChildren(element: TreeItem): Promise<TreeItem[]> {
    return Promise.resolve([
      new TreeItem('📁 Files', vscode.TreeItemCollapsibleState.None, 'worktree-detail', `${element.id}-files`),
      new TreeItem('📋 Task', vscode.TreeItemCollapsibleState.None, 'worktree-detail', `${element.id}-task`),
      new TreeItem('🤖 Agent', vscode.TreeItemCollapsibleState.None, 'worktree-detail', `${element.id}-agent`),
      new TreeItem('✅ Status', vscode.TreeItemCollapsibleState.None, 'worktree-detail', `${element.id}-status`)
    ]);
  }

  private async getAgentChildren(element: TreeItem): Promise<TreeItem[]> {
    return Promise.resolve([
      new TreeItem('🧬 Genome', vscode.TreeItemCollapsibleState.None, 'agent-detail', `${element.id}-genome`),
      new TreeItem('📊 Trust Score', vscode.TreeItemCollapsibleState.None, 'agent-detail', `${element.id}-trust`),
      new TreeItem('⚡ Status', vscode.TreeItemCollapsibleState.None, 'agent-detail', `${element.id}-status`),
      new TreeItem('📋 Current Task', vscode.TreeItemCollapsibleState.None, 'agent-detail', `${element.id}-task`)
    ]);
  }

  private createTaskItem(task: Task): TreeItem {
    const statusIcon = this.getTaskStatusIcon(task.status);
    const priorityIcon = this.getPriorityIcon(task.priority);
    const trustIcon = task.trustScore ? this.getTrustIcon(task.trustScore) : '❓';

    const label = `${statusIcon} ${priorityIcon} ${trustIcon} ${task.title}`;
    const collapsibleState = vscode.TreeItemCollapsibleState.Collapsed;

    const item = new TreeItem(label, collapsibleState, 'task', task.id);
    item.tooltip = `${task.description}\n\nStatus: ${task.status}\nPriority: ${task.priority}\nTrust: ${task.trustScore || 'N/A'}`;
    item.command = {
      command: 'vscode.open',
      title: 'Open Task',
      arguments: [vscode.Uri.parse(`zippy://task/${task.id}`)]
    };

    return item;
  }

  private createWorktreeItem(worktree: Worktree): TreeItem {
    const statusIcon = this.getWorktreeStatusIcon(worktree.status);
    const genomeIcon = this.getGenomeIcon(worktree.agentGenome);

    const label = `${statusIcon} ${genomeIcon} ${worktree.name}`;
    const collapsibleState = vscode.TreeItemCollapsibleState.Collapsed;

    const item = new TreeItem(label, collapsibleState, 'worktree', worktree.id);
    item.tooltip = `Path: ${worktree.path}\nBranch: ${worktree.branchName}\nGenome: ${worktree.agentGenome}\nCreated: ${worktree.createdAt}`;
    item.command = {
      command: 'vscode.openFolder',
      title: 'Open Worktree',
      arguments: [vscode.Uri.file(worktree.path)]
    };

    return item;
  }

  private createAgentItem(agent: Agent): TreeItem {
    const statusIcon = this.getAgentStatusIcon(agent.status);
    const trustIcon = this.getTrustIcon(agent.trustScore);

    const label = `${statusIcon} ${trustIcon} ${agent.name}`;
    const collapsibleState = vscode.TreeItemCollapsibleState.Collapsed;

    const item = new TreeItem(label, collapsibleState, 'agent', agent.id);
    item.tooltip = `Genome: ${agent.genome}\nStatus: ${agent.status}\nTrust: ${(agent.trustScore * 100).toFixed(1)}%\nLast Active: ${agent.lastActive}`;

    if (agent.currentTask) {
      item.tooltip += `\nCurrent Task: ${agent.currentTask}`;
    }

    return item;
  }

  private getTaskStatusIcon(status: string): string {
    switch (status) {
      case 'backlog': return '📋';
      case 'active': return '🔄';
      case 'in-review': return '👁️';
      case 'completed': return '✅';
      default: return '❓';
    }
  }

  private getPriorityIcon(priority: string): string {
    switch (priority) {
      case 'high': return '🔴';
      case 'medium': return '🟡';
      case 'low': return '🟢';
      default: return '⚪';
    }
  }

  private getWorktreeStatusIcon(status: string): string {
    switch (status) {
      case 'active': return '🟢';
      case 'completed': return '✅';
      case 'failed': return '❌';
      default: return '⚪';
    }
  }

  private getAgentStatusIcon(status: string): string {
    switch (status) {
      case 'idle': return '💤';
      case 'working': return '⚡';
      case 'completed': return '✅';
      case 'error': return '❌';
      default: return '⚪';
    }
  }

  private getGenomeIcon(genome: string): string {
    switch (genome) {
      case 'aggressive': return '🚀';
      case 'balanced': return '⚖️';
      case 'conservative': return '🛡️';
      default: return '🤖';
    }
  }

  private getTrustIcon(trustScore: number): string {
    if (trustScore >= 0.9) return '🟢';
    if (trustScore >= 0.7) return '🟡';
    if (trustScore >= 0.5) return '🟠';
    return '🔴';
  }
}

export class TreeItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly contextValue: string,
    public readonly id: string
  ) {
    super(label, collapsibleState);
    this.contextValue = contextValue;
    this.id = id;
  }
}
