import * as vscode from 'vscode';

export class ZippyStatusBar {
  private statusBarItem: vscode.StatusBarItem;
  private genomeItem: vscode.StatusBarItem;
  private trustItem: vscode.StatusBarItem;
  private agentCountItem: vscode.StatusBarItem;

  constructor() {
    this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    this.genomeItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 99);
    this.trustItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 98);
    this.agentCountItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 97);
  }

  initialize(): void {
    // Main status bar item
    this.statusBarItem.text = "$(robot) Zippy";
    this.statusBarItem.tooltip = "Zippy Archon Orchestrator - Click to open dashboard";
    this.statusBarItem.command = "zippy.openContractsGraph";
    this.statusBarItem.show();

    // Genome indicator
    this.updateGenome("balanced");

    // Trust score (initially hidden until calculated)
    this.trustItem.text = "$(shield) Trust: --";
    this.trustItem.tooltip = "Overall project trust score";
    this.trustItem.show();

    // Agent count
    this.updateAgentCount(0);

    // Set up periodic updates
    this.startPeriodicUpdates();
  }

  updateGenome(genome: string): void {
    const genomeIcons = {
      'aggressive': "$(zap)",
      'balanced': "$(scale)",
      'conservative': "$(shield-check)"
    };

    const genomeColors = {
      'aggressive': "$(zap)",
      'balanced': "$(scale)",
      'conservative': "$(shield-check)"
    };

    this.genomeItem.text = `${genomeIcons[genome as keyof typeof genomeIcons] || "$(robot)"} Genome: ${genome}`;
    this.genomeItem.tooltip = `Current agent genome: ${genome}\n\nAggressive: Fast, risky\nBalanced: Moderate speed/risk\nConservative: Slow, safe`;
    this.genomeItem.command = "zippy.switchAgentGenome";
    this.genomeItem.show();
  }

  updateTrustScore(score: number): void {
    const trustIcon = this.getTrustIcon(score);
    const trustColor = this.getTrustColor(score);

    this.trustItem.text = `${trustIcon} Trust: ${(score * 100).toFixed(1)}%`;
    this.trustItem.tooltip = `Project trust score: ${(score * 100).toFixed(1)}%\n\nHigh: >80% | Medium: 60-80% | Low: <60%`;
    this.trustItem.color = trustColor;
    this.trustItem.show();
  }

  updateAgentCount(count: number): void {
    const agentIcon = count > 0 ? "$(person)" : "$(person-outline)";

    this.agentCountItem.text = `${agentIcon} Agents: ${count}`;
    this.agentCountItem.tooltip = `Active agents: ${count}\n\nClick to view agent logs`;
    this.agentCountItem.command = "zippy.viewAgentLogs";
    this.agentCountItem.show();
  }

  updateWorktreeStatus(activeCount: number, completedCount: number): void {
    const totalCount = activeCount + completedCount;
    const completionRate = totalCount > 0 ? (completedCount / totalCount * 100) : 0;

    this.statusBarItem.text = `$(robot) Zippy (${activeCount} active, ${(completionRate).toFixed(0)}% complete)`;
    this.statusBarItem.tooltip = `Zippy Archon Orchestrator\n\nActive Worktrees: ${activeCount}\nCompleted Worktrees: ${completedCount}\nCompletion Rate: ${(completionRate).toFixed(1)}%\n\nClick to open dashboard`;
  }

  private getTrustIcon(score: number): string {
    if (score >= 0.9) return "$(shield-check)";
    if (score >= 0.7) return "$(shield)";
    if (score >= 0.5) return "$(warning)";
    return "$(error)";
  }

  private getTrustColor(score: number): vscode.ThemeColor | undefined {
    if (score >= 0.9) return new vscode.ThemeColor("charts.green");
    if (score >= 0.7) return new vscode.ThemeColor("charts.yellow");
    if (score >= 0.5) return new vscode.ThemeColor("charts.orange");
    return new vscode.ThemeColor("charts.red");
  }

  private startPeriodicUpdates(): void {
    // Update status every 30 seconds
    setInterval(() => {
      this.updatePeriodicStatus();
    }, 30000);
  }

  private async updatePeriodicStatus(): Promise<void> {
    try {
      // In a real implementation, this would fetch current stats from the orchestrator
      // For now, we'll simulate some dynamic updates

      // Simulate trust score changes
      const currentTrust = this.getCurrentTrustScore();
      const newTrust = Math.max(0.1, Math.min(1.0, currentTrust + (Math.random() - 0.5) * 0.1));
      this.updateTrustScore(newTrust);

      // Simulate agent count changes
      const currentAgents = this.getCurrentAgentCount();
      const newAgents = Math.max(0, currentAgents + Math.floor((Math.random() - 0.5) * 2));
      this.updateAgentCount(newAgents);

    } catch (error) {
      console.error('Failed to update status bar:', error);
    }
  }

  private getCurrentTrustScore(): number {
    // Extract current trust score from status bar text
    const match = this.trustItem.text.match(/Trust: (\d+\.?\d*)%/);
    return match ? parseFloat(match[1]) / 100 : 0.5;
  }

  private getCurrentAgentCount(): number {
    // Extract current agent count from status bar text
    const match = this.agentCountItem.text.match(/Agents: (\d+)/);
    return match ? parseInt(match[1]) : 0;
  }

  showProgress(message: string, increment?: number): vscode.StatusBarItem {
    const progressItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 0);
    progressItem.text = `$(sync~spin) ${message}`;

    if (increment !== undefined) {
      progressItem.text += ` (${increment}%)`;
    }

    progressItem.show();

    // Auto-hide after 5 seconds
    setTimeout(() => {
      progressItem.hide();
      progressItem.dispose();
    }, 5000);

    return progressItem;
  }

  showSuccess(message: string): vscode.StatusBarItem {
    const successItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 0);
    successItem.text = `$(check) ${message}`;
    successItem.color = new vscode.ThemeColor("charts.green");
    successItem.show();

    // Auto-hide after 3 seconds
    setTimeout(() => {
      successItem.hide();
      successItem.dispose();
    }, 3000);

    return successItem;
  }

  showError(message: string): vscode.StatusBarItem {
    const errorItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 0);
    errorItem.text = `$(error) ${message}`;
    errorItem.color = new vscode.ThemeColor("charts.red");
    errorItem.show();

    // Auto-hide after 5 seconds
    setTimeout(() => {
      errorItem.hide();
      errorItem.dispose();
    }, 5000);

    return errorItem;
  }

  showWarning(message: string): vscode.StatusBarItem {
    const warningItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 0);
    warningItem.text = `$(warning) ${message}`;
    warningItem.color = new vscode.ThemeColor("charts.orange");
    warningItem.show();

    // Auto-hide after 4 seconds
    setTimeout(() => {
      warningItem.hide();
      warningItem.dispose();
    }, 4000);

    return warningItem;
  }

  dispose(): void {
    this.statusBarItem.dispose();
    this.genomeItem.dispose();
    this.trustItem.dispose();
    this.agentCountItem.dispose();
  }
}
