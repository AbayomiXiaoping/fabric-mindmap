import * as vscode from 'vscode';
import { RuntimeManager } from './runtime/RuntimeManager';
import { LakehouseExplorerProvider } from './views/LakehouseExplorerProvider';
import { WebviewPanelManager } from './webview/WebviewPanelManager';
import { Logger } from './utils/logger';

let runtimeManager: RuntimeManager;

export async function activate(context: vscode.ExtensionContext) {
  const logger = new Logger('extension');
  logger.info('Lakehouse Intelligence Explorer activating...');

  // Initialize runtime manager
  runtimeManager = new RuntimeManager(context, logger);

  // Initialize tree view providers
  const explorerProvider = new LakehouseExplorerProvider(runtimeManager, logger);

  // Initialize webview panel manager
  const webviewManager = new WebviewPanelManager(context, runtimeManager, logger);

  // Register tree views
  const explorerView = vscode.window.createTreeView('lakehouseExplorer', {
    treeDataProvider: explorerProvider,
    showCollapseAll: true,
  });

  // Register commands
  context.subscriptions.push(
    explorerView,
    vscode.commands.registerCommand('lakehouse.connect', () => explorerProvider.connect()),
    vscode.commands.registerCommand('lakehouse.disconnect', () => explorerProvider.disconnect()),
    vscode.commands.registerCommand('lakehouse.buildGraph', () => explorerProvider.buildGraph()),
    vscode.commands.registerCommand('lakehouse.refreshGraph', () => explorerProvider.refreshGraph()),
    vscode.commands.registerCommand('lakehouse.openMindmap', () => webviewManager.openMindmap()),
    vscode.commands.registerCommand('lakehouse.openTableDetails', (tableId: string) =>
      webviewManager.openTableDetails(tableId),
    ),
    vscode.commands.registerCommand('lakehouse.selectLakehouse', () =>
      explorerProvider.selectLakehouse(),
    ),
  );

  // Auto-start runtime if configured
  const config = vscode.workspace.getConfiguration('lakehouseIntelligence');
  if (config.get<boolean>('runtime.autoStart', true)) {
    await runtimeManager.start();
  }

  logger.info('Lakehouse Intelligence Explorer activated');
}

export async function deactivate() {
  if (runtimeManager) {
    await runtimeManager.stop();
  }
}
