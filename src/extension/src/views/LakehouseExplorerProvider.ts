import * as vscode from 'vscode';
import { RuntimeManager } from '../runtime/RuntimeManager';
import { Logger } from '../utils/logger';
import { ExplorerNode } from './ExplorerNode';

export class LakehouseExplorerProvider implements vscode.TreeDataProvider<ExplorerNode> {
  private _onDidChangeTreeData = new vscode.EventEmitter<ExplorerNode | undefined | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private activeLakehouseId: string = 'lh-banking-prod-01';
  private activeLakehouseName: string = 'Fabric_Retail_Banking_Lakehouse';
  private isConnected: boolean = false;

  constructor(
    private runtimeManager: RuntimeManager,
    private logger: Logger,
  ) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: ExplorerNode): vscode.TreeItem {
    return element;
  }

  async getChildren(element?: ExplorerNode): Promise<ExplorerNode[]> {
    const client = this.runtimeManager.getClient();

    if (!element) {
      // Root level
      if (!this.isConnected) {
        return [
          new ExplorerNode(
            'Connect to Fabric Lakehouse',
            'action',
            vscode.TreeItemCollapsibleState.None,
            undefined,
            { command: 'lakehouse.connect' },
          ),
        ];
      }

      // Root Lakehouse node
      return [
        new ExplorerNode(
          this.activeLakehouseName,
          'lakehouse',
          vscode.TreeItemCollapsibleState.Expanded,
          `lakehouse:${this.activeLakehouseId}`,
        ),
      ];
    }

    try {
      if (element.nodeId) {
        const children = await client.getNodeChildren(this.activeLakehouseId, element.nodeId);
        if (children.length === 0) {
          return [new ExplorerNode('No items discovered', 'empty', vscode.TreeItemCollapsibleState.None)];
        }

        return children.map((c) => {
          const typeLower = c.node_type.toLowerCase() as any;
          const collapsible = c.has_children
            ? vscode.TreeItemCollapsibleState.Collapsed
            : vscode.TreeItemCollapsibleState.None;

          const node = new ExplorerNode(c.name, typeLower, collapsible, c.node_id, {
            description: c.qualified_name,
          });

          if (c.node_type === 'TABLE') {
            node.command = {
              command: 'lakehouse.openTableDetails',
              title: 'Open Table Details',
              arguments: [c.node_id],
            };
          }
          return node;
        });
      }
    } catch (err) {
      this.logger.error('Failed to get children from runtime', err);
      return [new ExplorerNode('Error loading metadata', 'empty', vscode.TreeItemCollapsibleState.None)];
    }

    return [];
  }

  async connect(): Promise<void> {
    this.logger.info(`Connecting to Lakehouse: ${this.activeLakehouseName}`);
    await this.runtimeManager.start();
    this.isConnected = true;
    this.refresh();
    vscode.window.showInformationMessage(`Connected to ${this.activeLakehouseName}`);
  }

  async disconnect(): Promise<void> {
    this.isConnected = false;
    this.refresh();
    vscode.window.showInformationMessage('Disconnected from Lakehouse');
  }

  async buildGraph(): Promise<void> {
    const client = this.runtimeManager.getClient();
    vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: `Building Knowledge Graph for ${this.activeLakehouseName}...`,
        cancellable: false,
      },
      async () => {
        try {
          const res = await client.buildGraph(this.activeLakehouseId, this.activeLakehouseName);
          vscode.window.showInformationMessage(
            `Graph built successfully: v${res.graph_version} (${res.node_count} nodes, ${res.edge_count} edges)`,
          );
          this.refresh();
        } catch (err) {
          vscode.window.showErrorMessage(`Build graph failed: ${err}`);
        }
      },
    );
  }

  async refreshGraph(): Promise<void> {
    const client = this.runtimeManager.getClient();
    vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: `Refreshing metadata for ${this.activeLakehouseName}...`,
        cancellable: false,
      },
      async () => {
        try {
          const res = await client.refreshGraph(this.activeLakehouseId, this.activeLakehouseName);
          vscode.window.showInformationMessage(
            `Metadata refreshed: version ${res.graph_version} (${res.node_count} nodes)`,
          );
          this.refresh();
        } catch (err) {
          vscode.window.showErrorMessage(`Refresh failed: ${err}`);
        }
      },
    );
  }

  async selectLakehouse(): Promise<void> {
    const name = await vscode.window.showInputBox({
      prompt: 'Enter Fabric Lakehouse Name',
      value: this.activeLakehouseName,
    });
    if (name) {
      this.activeLakehouseName = name;
      this.activeLakehouseId = name.toLowerCase().replace(/[^a-z0-9_-]/g, '-');
      this.refresh();
    }
  }
}

