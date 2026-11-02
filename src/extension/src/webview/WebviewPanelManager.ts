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
          view: 'overview',
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

      case 'enrichMetadata':
        try {
          const res = await client.triggerEnrichment(msg.lakehouseId);
          this.postMessage(panel, {
            type: 'notification',
            level: 'info',
            message: `AI Enrichment complete: ${res.stats.domains_suggested} domains suggested, ${res.stats.reviews_queued} queued for review`,
          });
        } catch (err) {
          this.postMessage(panel, {
            type: 'notification',
            level: 'error',
            message: `Enrichment failed: ${err}`,
          });
        }
        break;

      case 'fetchGovernanceQueue':
        try {
          const items = await client.getGovernanceQueue(msg.lakehouseId);
          this.postMessage(panel, {
            type: 'governanceQueueLoaded',
            items,
          });
        } catch (err) {
          this.logger.error('Failed to fetch governance queue', err);
        }
        break;

      case 'approveReview':
        try {
          await client.approveReview(msg.lakehouseId, msg.reviewId, 'developer', msg.comments);
          this.postMessage(panel, {
            type: 'notification',
            level: 'info',
            message: 'Domain proposal approved and assigned.',
          });
          // Refresh queue
          const items = await client.getGovernanceQueue(msg.lakehouseId);
          this.postMessage(panel, { type: 'governanceQueueLoaded', items });
        } catch (err) {
          this.postMessage(panel, {
            type: 'notification',
            level: 'error',
            message: `Approval failed: ${err}`,
          });
        }
        break;

      case 'rejectReview':
        try {
          await client.rejectReview(msg.lakehouseId, msg.reviewId, 'developer', msg.reason);
          this.postMessage(panel, {
            type: 'notification',
            level: 'info',
            message: 'Domain proposal rejected (will not be re-suggested).',
          });
          const items = await client.getGovernanceQueue(msg.lakehouseId);
          this.postMessage(panel, { type: 'governanceQueueLoaded', items });
        } catch (err) {
          this.postMessage(panel, {
            type: 'notification',
            level: 'error',
            message: `Rejection failed: ${err}`,
          });
        }
        break;

      case 'modifyReview':
        try {
          await client.modifyReview(
            msg.lakehouseId,
            msg.reviewId,
            msg.modifiedDomain,
            'developer',
            msg.comments,
          );
          this.postMessage(panel, {
            type: 'notification',
            level: 'info',
            message: `Modified domain '${msg.modifiedDomain}' approved.`,
          });
          const items = await client.getGovernanceQueue(msg.lakehouseId);
          this.postMessage(panel, { type: 'governanceQueueLoaded', items });
        } catch (err) {
          this.postMessage(panel, {
            type: 'notification',
            level: 'error',
            message: `Modify failed: ${err}`,
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

    return `<!DOCTYPE html><html><body>Webview dist not found. Run npm run build in webview-ui.</body></html>`;
  }
}
