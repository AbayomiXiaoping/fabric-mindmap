import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { RuntimeManager } from '../runtime/RuntimeManager';
import { Logger } from '../utils/logger';
import { ExtensionMessage, WebviewMessage } from './messageTypes';

export class WebviewPanelManager {
  private panels: Map<string, vscode.WebviewPanel> = new Map();

  constructor(
    private context: vscode.ExtensionContext,
    private runtimeManager: RuntimeManager,
    private logger: Logger,
  ) {}

  openMindmap(): void {
    this.createOrShowPanel('mindmap', 'Lakehouse Mindmap Explorer');
  }

  openTableDetails(tableId: string): void {
    this.createOrShowPanel('tableDetails', 'Table Details', { tableId });
  }

  private createOrShowPanel(viewType: string, title: string, params: Record<string, string> = {}): void {
    const existing = this.panels.get(viewType);
    if (existing) {
      existing.reveal(vscode.ViewColumn.One);
      this.postMessage(existing, {
        type: 'init',
        baseUrl: this.runtimeManager.getBaseUrl(),
        view: viewType,
        ...params,
      });
      return;
    }

    const panel = vscode.window.createWebviewPanel(
      `lakehouse.${viewType}`,
      title,
      vscode.ViewColumn.One,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
        localResourceRoots: [
          vscode.Uri.file(path.join(this.context.extensionPath, '..', 'webview-ui', 'dist')),
        ],
      },
    );

    panel.webview.html = this.getHtmlForWebview(panel.webview, viewType, params);

    panel.webview.onDidReceiveMessage(async (msg: WebviewMessage) => {
      this.handleWebviewMessage(panel, msg);
    });

    panel.onDidDispose(() => {
      this.panels.delete(viewType);
    });

    this.panels.set(viewType, panel);
  }

  private postMessage(panel: vscode.WebviewPanel, message: ExtensionMessage): void {
    panel.webview.postMessage(message);
  }

  private async handleWebviewMessage(panel: vscode.WebviewPanel, msg: WebviewMessage): Promise<void> {
    const client = this.runtimeManager.getClient();
    switch (msg.type) {
      case 'ready':
        this.postMessage(panel, {
          type: 'init',
          baseUrl: this.runtimeManager.getBaseUrl(),
          lakehouseId: 'lh-banking-prod-01',
          view: 'mindmap',
        });
        break;

      case 'buildGraph':
        try {
          const res = await client.buildGraph(msg.lakehouseId);
          this.postMessage(panel, {
            type: 'notification',
            level: 'info',
            message: `Graph built: version ${res.graph_version}`,
          });
        } catch (err) {
          this.postMessage(panel, {
            type: 'notification',
            level: 'error',
            message: `Build graph failed: ${err}`,
          });
        }
        break;

      case 'refreshGraph':
        try {
          const res = await client.refreshGraph(msg.lakehouseId);
          this.postMessage(panel, {
            type: 'notification',
            level: 'info',
            message: `Graph refreshed: version ${res.graph_version}`,
          });
        } catch (err) {
          this.postMessage(panel, {
            type: 'notification',
            level: 'error',
            message: `Refresh failed: ${err}`,
          });
        }
        break;
    }
  }

  private getHtmlForWebview(
    webview: vscode.Webview,
    viewType: string,
    params: Record<string, string>,
  ): string {
    const webviewDist = path.join(this.context.extensionPath, '..', 'webview-ui', 'dist');
    const indexPath = path.join(webviewDist, 'index.html');

    if (fs.existsSync(indexPath)) {
      let html = fs.readFileSync(indexPath, 'utf-8');
      const scriptUri = webview.asWebviewUri(
        vscode.Uri.file(path.join(webviewDist, 'assets', 'index.js')),
      );
      const cssUri = webview.asWebviewUri(
        vscode.Uri.file(path.join(webviewDist, 'assets', 'index.css')),
      );

      html = html
        .replace(/\/assets\/index\.js/g, scriptUri.toString())
        .replace(/\/assets\/index\.css/g, cssUri.toString());
      return html;
    }

    // Fallback embedded UI while webview bundle builds
    const csp = `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline' ${webview.cspSource};">`;
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  ${csp}
  <title>Lakehouse Intelligence</title>
  <style>
    body { font-family: var(--vscode-font-family, sans-serif); padding: 24px; color: var(--vscode-foreground); background: var(--vscode-editor-background); }
    .card { background: var(--vscode-editorWidget-background); border: 1px solid var(--vscode-widget-border, #333); border-radius: 8px; padding: 20px; max-width: 600px; margin: 20px auto; }
    h2 { color: var(--vscode-textLink-foreground); margin-top: 0; }
    button { background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 14px; margin-right: 8px; }
    button:hover { background: var(--vscode-button-hoverBackground); }
    .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; background: #28a745; color: white; font-size: 12px; font-weight: bold; }
  </style>
</head>
<body>
  <div class="card">
    <h2>Fabric Lakehouse Intelligence Explorer</h2>
    <p>Target: <strong>Fabric_Retail_Banking_Lakehouse</strong> <span class="badge">LOCAL CACHE</span></p>
    <p>Connected to Python Runtime: <code>${this.runtimeManager.getBaseUrl()}</code></p>
    <hr style="border: 0; border-top: 1px solid var(--vscode-widget-border, #444); margin: 20px 0;">
    <button onclick="vscode.postMessage({type: 'buildGraph', lakehouseId: 'lh-banking-prod-01'})">Build Knowledge Graph</button>
    <button onclick="vscode.postMessage({type: 'refreshGraph', lakehouseId: 'lh-banking-prod-01'})">Refresh Metadata</button>
  </div>
  <script>
    const vscode = acquireVsCodeApi();
  </script>
</body>
</html>`;
  }
}
