import * as vscode from 'vscode';
import { ChildProcess, spawn } from 'child_process';
import * as path from 'path';
import { Logger } from '../utils/logger';
import { getSettings } from '../config/settings';
import { RuntimeClient } from './RuntimeClient';

export class RuntimeManager {
  private context: vscode.ExtensionContext;
  private logger: Logger;
  private process: ChildProcess | null = null;
  private isRunning: boolean = false;
  private statusBarItem: vscode.StatusBarItem;
  private client: RuntimeClient;
  private baseUrl: string;

  constructor(context: vscode.ExtensionContext, logger: Logger) {
    this.context = context;
    this.logger = logger;
    const settings = getSettings();
    this.baseUrl = `http://${settings.runtimeHost}:${settings.runtimePort}`;
    this.client = new RuntimeClient(this.baseUrl, logger);

    this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    this.statusBarItem.command = 'lakehouse.connect';
    this.updateStatusBar('🔴 Lakehouse Runtime: Stopped');
    this.statusBarItem.show();
    this.context.subscriptions.push(this.statusBarItem);
  }

  private updateStatusBar(text: string): void {
    this.statusBarItem.text = text;
  }

  getClient(): RuntimeClient {
    return this.client;
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  async start(): Promise<void> {
    if (this.isRunning) {
      return;
    }

    const settings = getSettings();
    this.updateStatusBar('🟡 Lakehouse Runtime: Starting...');

    // Locate the virtualenv python interpreter
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    const pythonPath = workspaceRoot
      ? path.join(workspaceRoot, 'src', 'runtime', '.venv', 'bin', 'python')
      : 'python3';

    this.logger.info(`Starting Python runtime using: ${pythonPath}`);

    try {
      this.process = spawn(
        pythonPath,
        [
          '-m',
          'lakehouse_intelligence.main',
          '--host',
          settings.runtimeHost,
          '--port',
          settings.runtimePort.toString(),
        ],
        {
          cwd: workspaceRoot ? path.join(workspaceRoot, 'src', 'runtime') : undefined,
          env: {
            ...process.env,
            PYTHONUNBUFFERED: '1',
          },
        },
      );

      this.process.stdout?.on('data', (data) => {
        this.logger.debug(`[Runtime] ${data.toString().trim()}`);
      });

      this.process.stderr?.on('data', (data) => {
        this.logger.debug(`[Runtime stderr] ${data.toString().trim()}`);
      });

      this.process.on('close', (code) => {
        this.logger.info(`Runtime process exited with code ${code}`);
        this.isRunning = false;
        this.updateStatusBar('🔴 Lakehouse Runtime: Stopped');
      });

      // Poll until healthy
      const healthy = await this.waitForReady(15000);
      if (healthy) {
        this.isRunning = true;
        this.updateStatusBar('🟢 Lakehouse Runtime: Ready');
        this.logger.info('Python runtime is healthy and ready');
      } else {
        this.updateStatusBar('⚠️ Lakehouse Runtime: Unhealthy');
      }
    } catch (err) {
      this.logger.error('Failed to spawn Python runtime', err);
      this.updateStatusBar('🔴 Lakehouse Runtime: Error');
    }
  }

  async waitForReady(timeoutMs: number = 15000): Promise<boolean> {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      try {
        const health = await this.client.getHealth();
        if (health.status === 'healthy') {
          return true;
        }
      } catch {
        // Retry
      }
      await new Promise((res) => setTimeout(res, 500));
    }
    return false;
  }

  async stop(): Promise<void> {
    if (this.process) {
      this.logger.info('Stopping Python runtime...');
      this.process.kill('SIGTERM');
      this.process = null;
      this.isRunning = false;
      this.updateStatusBar('🔴 Lakehouse Runtime: Stopped');
    }
  }
}

