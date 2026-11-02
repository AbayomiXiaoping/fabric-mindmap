import * as vscode from 'vscode';
import { RuntimeManager } from '../runtime/RuntimeManager';
import { Logger } from '../utils/logger';
import { ExplorerNode } from './ExplorerNode';

export class LakehouseExplorerProvider implements vscode.TreeDataProvider<ExplorerNode> {
  private _onDidChangeTreeData = new vscode.EventEmitter<ExplorerNode | undefined | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private activeLakehouseId: string = 'lh-banking-prod-01';
  private activeLakehouseName: string = 'Fabric_Retail_Banking_Lakehouse';
  private activeWorkspaceName: string = 'Retail_Analytics_Workspace';
  private isConnected: boolean = false;
  private isLiveFabric: boolean = false;

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
            'Connect to Microsoft Fabric Lakehouse',
            'action',
            vscode.TreeItemCollapsibleState.None,
            undefined,
            { command: 'lakehouse.connect' },
          ),
        ];
      }

      // Root Lakehouse node
      const statusLabel = this.isLiveFabric ? 'LIVE FABRIC' : 'DEMO LAKEHOUSE';
      const rootNode = new ExplorerNode(
        `${this.activeLakehouseName} [${statusLabel}]`,
        'lakehouse',
        vscode.TreeItemCollapsibleState.Expanded,
        `lakehouse:${this.activeLakehouseId}`,
      );
      rootNode.description = this.activeWorkspaceName;
      return [rootNode];
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
    this.logger.info('Initiating Fabric connection flow...');
    await this.runtimeManager.start();
    const client = this.runtimeManager.getClient();

    // Prompt for Authentication Method
    const authChoice = await vscode.window.showQuickPick(
      [
        {
          label: '$(azure) Azure CLI Identity',
          description: 'Uses active identity from "az login"',
          method: 'azure_cli',
        },
        {
          label: '$(browser) Interactive Browser Login',
          description: 'Pops up Microsoft Entra ID sign-in window',
          method: 'interactive_browser',
        },
        {
          label: '$(key) Service Principal (Client Secret)',
          description: 'Enter Client ID, Secret, and Tenant ID',
          method: 'client_secret',
        },
        {
          label: '$(database) Sample Banking Demo Workspace',
          description: 'Offline sandbox with pre-configured schemas and tables',
          method: 'mock',
        },
      ],
      {
        placeHolder: 'Select Microsoft Entra ID authentication method',
      },
    );

    if (!authChoice) return;

    if (authChoice.method === 'mock') {
      this.isConnected = true;
      this.isLiveFabric = false;
      this.activeLakehouseId = 'lh-banking-prod-01';
      this.activeLakehouseName = 'Fabric_Retail_Banking_Lakehouse';
      this.activeWorkspaceName = 'Retail_Analytics_Workspace';
      this.refresh();
      vscode.window.showInformationMessage('Connected to Sample Banking Demo Lakehouse');
      return;
    }

    // Live Fabric Auth
    try {
      let tenantId: string | undefined;
      let clientId: string | undefined;
      let clientSecret: string | undefined;

      if (authChoice.method === 'client_secret') {
        tenantId = await vscode.window.showInputBox({ prompt: 'Enter Entra Tenant ID' });
        if (!tenantId) return;
        clientId = await vscode.window.showInputBox({ prompt: 'Enter Client / Application ID' });
        if (!clientId) return;
        clientSecret = await vscode.window.showInputBox({
          prompt: 'Enter Client Secret',
          password: true,
        });
        if (!clientSecret) return;
      }

      await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: 'Authenticating with Microsoft Fabric...',
          cancellable: false,
        },
        async () => {
          const authRes = await client.configureAuth({
            method: authChoice.method,
            tenant_id: tenantId,
            client_id: clientId,
            client_secret: clientSecret,
          });

          if (!authRes.is_authenticated) {
            throw new Error(authRes.error || 'Authentication failed');
          }

          // Discover live workspaces
          const workspaces = await client.listWorkspaces();
          if (workspaces.length === 0) {
            throw new Error('No accessible Fabric workspaces found for your identity');
          }

          const wsChoice = await vscode.window.showQuickPick(
            workspaces.map((w) => ({
              label: `$(folder) ${w.name}`,
              description: w.workspace_id,
              workspace: w,
            })),
            { placeHolder: 'Select target Microsoft Fabric Workspace' },
          );
          if (!wsChoice) return;

          // Discover Lakehouses in chosen workspace
          const lakehouses = await client.listLakehousesInWorkspace(wsChoice.workspace.workspace_id);
          if (lakehouses.length === 0) {
            throw new Error(`No Lakehouses found in workspace '${wsChoice.workspace.name}'`);
          }

          const lhChoice = await vscode.window.showQuickPick(
            lakehouses.map((lh) => ({
              label: `$(database) ${lh.name}`,
              description: lh.lakehouse_id,
              lakehouse: lh,
            })),
            { placeHolder: 'Select Lakehouse to explore' },
          );
          if (!lhChoice) return;

          this.isConnected = true;
          this.isLiveFabric = true;
          this.activeWorkspaceName = wsChoice.workspace.name;
          this.activeLakehouseId = lhChoice.lakehouse.lakehouse_id;
          this.activeLakehouseName = lhChoice.lakehouse.name;
          this.refresh();

          vscode.window.showInformationMessage(
            `Connected to Fabric Lakehouse: ${this.activeLakehouseName} (${this.activeWorkspaceName})`,
          );
        },
      );
    } catch (err: any) {
      this.logger.error('Authentication or live discovery failed', err);
      vscode.window.showErrorMessage(`Fabric connection failed: ${err.message || err}`);
    }
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
