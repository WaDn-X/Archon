import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs/promises';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'backlog' | 'active' | 'in-review' | 'completed';
  priority: 'low' | 'medium' | 'high';
  tags: string[];
  createdAt: string;
  assignedAgent?: string;
  trustScore?: number;
}

export interface Worktree {
  id: string;
  name: string;
  path: string;
  taskId: string;
  status: 'active' | 'completed' | 'failed';
  agentGenome: string;
  createdAt: string;
  branchName: string;
}

export interface Agent {
  id: string;
  name: string;
  genome: string;
  status: 'idle' | 'working' | 'completed' | 'error';
  currentTask?: string;
  trustScore: number;
  lastActive: string;
}

export class ZippyOrchestrator {
  private context: vscode.ExtensionContext;
  private tasks: Map<string, Task> = new Map();
  private worktrees: Map<string, Worktree> = new Map();
  private agents: Map<string, Agent> = new Map();
  private currentGenome: string = 'balanced';
  private serverUrl: string;

  constructor(context: vscode.ExtensionContext) {
    this.context = context;
    this.serverUrl = vscode.workspace.getConfiguration('zippy').get('serverUrl', 'http://localhost:8000');
    this.loadState();
  }

  async initializeProject(projectPath: string): Promise<void> {
    // Create project structure
    const contractsDir = path.join(projectPath, 'contracts');
    const contextDir = path.join(projectPath, 'context');
    const designDir = path.join(projectPath, 'design');
    const tasksDir = path.join(projectPath, 'tasks');

    await fs.mkdir(contractsDir, { recursive: true });
    await fs.mkdir(contextDir, { recursive: true });
    await fs.mkdir(designDir, { recursive: true });
    await fs.mkdir(path.join(tasksDir, 'backlog'), { recursive: true });
    await fs.mkdir(path.join(tasksDir, 'active'), { recursive: true });
    await fs.mkdir(path.join(tasksDir, 'in-review'), { recursive: true });

    // Create initial configuration
    const config = {
      initialized: true,
      createdAt: new Date().toISOString(),
      version: '0.1.0',
      genome: this.currentGenome
    };

    await fs.writeFile(
      path.join(projectPath, '.zippy.json'),
      JSON.stringify(config, null, 2)
    );

    // Initialize git worktrees if in a git repo
    try {
      await execAsync('git rev-parse --git-dir', { cwd: projectPath });
      await this.initializeWorktrees(projectPath);
    } catch (error) {
      // Not a git repo, skip worktree initialization
    }
  }

  async isProjectInitialized(projectPath: string): Promise<boolean> {
    try {
      await fs.access(path.join(projectPath, '.zippy.json'));
      return true;
    } catch {
      return false;
    }
  }

  private async initializeWorktrees(projectPath: string): Promise<void> {
    // Create main worktree directory
    const worktreesDir = path.join(projectPath, '.worktrees');
    await fs.mkdir(worktreesDir, { recursive: true });

    // Initialize main worktree
    await execAsync('git worktree add .worktrees/main main', { cwd: projectPath });
  }

  async createWorktree(taskId: string): Promise<void> {
    const task = this.tasks.get(taskId);
    if (!task) {
      throw new Error('Task not found');
    }

    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
      throw new Error('No workspace folder');
    }

    const worktreeId = `wt_${Date.now()}`;
    const branchName = `agent/${taskId}`;
    const worktreePath = path.join(workspaceFolder.uri.fsPath, '.worktrees', worktreeId);

    // Create git worktree
    await execAsync(`git worktree add ${worktreePath} -b ${branchName}`, {
      cwd: workspaceFolder.uri.fsPath
    });

    // Create worktree record
    const worktree: Worktree = {
      id: worktreeId,
      name: `Worktree for ${task.title}`,
      path: worktreePath,
      taskId: taskId,
      status: 'active',
      agentGenome: this.currentGenome,
      createdAt: new Date().toISOString(),
      branchName: branchName
    };

    this.worktrees.set(worktreeId, worktree);

    // Update task status
    task.status = 'active';
    task.assignedAgent = worktreeId;

    this.saveState();

    // Create initial task file
    await this.createTaskFile(worktree, task);
  }

  private async createTaskFile(worktree: Worktree, task: Task): Promise<void> {
    const taskContent = `# ${task.title}

## Description
${task.description}

## Status
${task.status}

## Priority
${task.priority}

## Tags
${task.tags.join(', ')}

## Created
${task.createdAt}

## Assigned Agent
${worktree.id} (${worktree.agentGenome} genome)

## Trust Score
${task.trustScore || 'Not calculated'}

---

## Task Progress

### Current Phase
🔄 Initializing worktree and agent setup

### Next Steps
1. Agent will analyze requirements
2. Generate design artifacts
3. Implement solution
4. Run quality checks
5. Create pull request

---

## Generated Files
- \`task.md\` - This task file
- \`plan.md\` - Implementation plan (to be created)
- \`design/\` - Design artifacts (to be created)
- \`impl/\` - Implementation files (to be created)
`;

    await fs.writeFile(path.join(worktree.path, 'task.md'), taskContent);
  }

  async runTaskLifecycle(taskId: string): Promise<void> {
    const task = this.tasks.get(taskId);
    if (!task) {
      throw new Error('Task not found');
    }

    // Find associated worktree
    const worktree = Array.from(this.worktrees.values())
      .find(wt => wt.taskId === taskId);

    if (!worktree) {
      throw new Error('No worktree found for task');
    }

    await this.runWorktreeLifecycle(worktree.id);
  }

  async runWorktreeLifecycle(worktreeId: string): Promise<void> {
    const worktree = this.worktrees.get(worktreeId);
    if (!worktree) {
      throw new Error('Worktree not found');
    }

    // Create agent for this worktree
    const agent = await this.createAgent(worktree);

    // Run the agent lifecycle
    await this.runAgentLifecycle(agent, worktree);
  }

  private async createAgent(worktree: Worktree): Promise<Agent> {
    const agentId = `agent_${Date.now()}`;

    const agent: Agent = {
      id: agentId,
      name: `Agent ${worktree.agentGenome}`,
      genome: worktree.agentGenome,
      status: 'working',
      currentTask: worktree.taskId,
      trustScore: 0.5, // Initial trust score
      lastActive: new Date().toISOString()
    };

    this.agents.set(agentId, agent);
    this.saveState();

    return agent;
  }

  private async runAgentLifecycle(agent: Agent, worktree: Worktree): Promise<void> {
    try {
      // Phase 1: Requirements Analysis
      agent.status = 'working';
      await this.runPhase(worktree, 'requirements', agent);

      // Phase 2: Design Generation
      await this.runPhase(worktree, 'design', agent);

      // Phase 3: Implementation
      await this.runPhase(worktree, 'implementation', agent);

      // Phase 4: Quality Assurance
      await this.runPhase(worktree, 'qa', agent);

      // Phase 5: Completion
      agent.status = 'completed';
      worktree.status = 'completed';

      this.saveState();

    } catch (error) {
      agent.status = 'error';
      worktree.status = 'failed';
      this.saveState();
      throw error;
    }
  }

  private async runPhase(worktree: Worktree, phase: string, agent: Agent): Promise<void> {
    const phaseFiles = {
      requirements: 'requirements.md',
      design: 'design.md',
      implementation: 'implementation.md',
      qa: 'qa_report.md'
    };

    const fileName = phaseFiles[phase as keyof typeof phaseFiles];
    const filePath = path.join(worktree.path, fileName);

    // Update task file with progress
    await this.updateTaskProgress(worktree, phase, agent);

    // Simulate agent work (in real implementation, this would call the backend)
    await this.simulateAgentWork(worktree, phase, agent);

    // Update agent last active time
    agent.lastActive = new Date().toISOString();
    this.saveState();
  }

  private async updateTaskProgress(worktree: Worktree, phase: string, agent: Agent): Promise<void> {
    const taskFilePath = path.join(worktree.path, 'task.md');

    try {
      let content = await fs.readFile(taskFilePath, 'utf8');

      const phaseIndicators = {
        requirements: '🔍 Analyzing requirements',
        design: '🎨 Generating design',
        implementation: '⚡ Implementing solution',
        qa: '✅ Running quality checks'
      };

      content = content.replace(
        /### Current Phase\n.*/,
        `### Current Phase\n${phaseIndicators[phase as keyof typeof phaseIndicators]}`
      );

      await fs.writeFile(taskFilePath, content);
    } catch (error) {
      // Task file might not exist yet
    }
  }

  private async simulateAgentWork(worktree: Worktree, phase: string, agent: Agent): Promise<void> {
    // Simulate work duration based on phase
    const durations = {
      requirements: 2000,
      design: 3000,
      implementation: 5000,
      qa: 2000
    };

    await new Promise(resolve => setTimeout(resolve, durations[phase as keyof typeof durations]));

    // Create phase output file
    const content = `# ${phase.charAt(0).toUpperCase() + phase.slice(1)} Phase

## Executed by Agent: ${agent.name}
## Genome: ${agent.genome}
## Timestamp: ${new Date().toISOString()}

## Results

This phase has been completed successfully by the ${agent.genome} agent.

### Trust Score: ${(agent.trustScore * 100).toFixed(1)}%

### Next Steps
${phase === 'qa' ? 'Ready for pull request creation' : `Proceed to next phase`}
`;

    const fileName = `${phase}.md`;
    await fs.writeFile(path.join(worktree.path, fileName), content);
  }

  async runQA(worktreeId: string): Promise<any> {
    const worktree = this.worktrees.get(worktreeId);
    if (!worktree) {
      throw new Error('Worktree not found');
    }

    // Simulate QA checks
    const qaResults = {
      passed: 8,
      failed: 1,
      skipped: 0,
      qualityScore: 85,
      trustScore: 0.82,
      issues: [
        {
          type: 'warning',
          message: 'Missing unit tests for new functions',
          severity: 'medium'
        }
      ]
    };

    // Create QA report file
    const reportPath = path.join(worktree.path, 'qa_report.md');
    const report = `# QA Report

## Summary
- ✅ Passed: ${qaResults.passed}
- ❌ Failed: ${qaResults.failed}
- ⏭️ Skipped: ${qaResults.skipped}

## Quality Score
${qaResults.qualityScore}/100

## Trust Score
${(qaResults.trustScore * 100).toFixed(1)}%

## Issues Found
${qaResults.issues.map(issue => `- ${issue.type.toUpperCase()}: ${issue.message}`).join('\n')}

## Recommendations
${qaResults.failed > 0 ? '- Address failed checks before proceeding' : '- Ready for production deployment'}
`;

    await fs.writeFile(reportPath, report);

    return qaResults;
  }

  async createPR(worktreeId: string): Promise<void> {
    const worktree = this.worktrees.get(worktreeId);
    if (!worktree) {
      throw new Error('Worktree not found');
    }

    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
      throw new Error('No workspace folder');
    }

    // Create pull request using GitHub CLI or REST API
    try {
      await execAsync(`git push -u origin ${worktree.branchName}`, {
        cwd: worktree.path
      });

      // In a real implementation, this would create a PR via GitHub API
      // For now, we'll just show the command that would be used
      const prCommand = `gh pr create --title "Worktree: ${worktree.name}" --body "Generated by Zippy Archon Agent"`;

      vscode.window.showInformationMessage(`Pull request ready. Run: ${prCommand}`);
    } catch (error) {
      throw new Error(`Failed to create PR: ${error}`);
    }
  }

  async switchGenome(genome: string): Promise<void> {
    this.currentGenome = genome;
    this.saveState();

    // Update all active agents to use new genome
    for (const agent of this.agents.values()) {
      if (agent.status === 'idle') {
        agent.genome = genome;
      }
    }

    this.saveState();
  }

  async getAgentLogs(agentId: string): Promise<string> {
    const agent = this.agents.get(agentId);
    if (!agent) {
      return 'Agent not found';
    }

    // Simulate agent logs
    return `Agent Logs for ${agent.name}

Genome: ${agent.genome}
Status: ${agent.status}
Last Active: ${agent.lastActive}
Trust Score: ${(agent.trustScore * 100).toFixed(1)}%

Recent Activity:
- ${new Date().toISOString()}: Agent initialized
- ${new Date().toISOString()}: Started task processing
- ${new Date().toISOString()}: Completed current phase
- ${new Date().toISOString()}: Updated trust score to ${(agent.trustScore * 100).toFixed(1)}%
`;
  }

  async getCurrentWorktree(): Promise<Worktree | null> {
    // In a real implementation, this would detect the current git worktree
    // For now, return the most recently created worktree
    const worktrees = Array.from(this.worktrees.values())
      .filter(wt => wt.status === 'active')
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

    return worktrees.length > 0 ? worktrees[0] : null;
  }

  // Data management methods
  private loadState(): void {
    const state = this.context.globalState.get('zippyOrchestratorState', {});
    this.tasks = new Map(Object.entries(state.tasks || {}));
    this.worktrees = new Map(Object.entries(state.worktrees || {}));
    this.agents = new Map(Object.entries(state.agents || {}));
    this.currentGenome = state.currentGenome || 'balanced';
  }

  private saveState(): void {
    const state = {
      tasks: Object.fromEntries(this.tasks),
      worktrees: Object.fromEntries(this.worktrees),
      agents: Object.fromEntries(this.agents),
      currentGenome: this.currentGenome
    };

    this.context.globalState.update('zippyOrchestratorState', state);
  }

  // Public getters for UI components
  getTasks(): Task[] {
    return Array.from(this.tasks.values());
  }

  getWorktrees(): Worktree[] {
    return Array.from(this.worktrees.values());
  }

  getAgents(): Agent[] {
    return Array.from(this.agents.values());
  }

  dispose(): void {
    // Clean up resources
    this.saveState();
  }
}
