import * as vscode from 'vscode';

export type ExplorerNodeType =
  | 'lakehouse'
  | 'schema'
  | 'table'
  | 'column'
  | 'action'
  | 'empty';

export class ExplorerNode extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly nodeType: ExplorerNodeType,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly nodeId?: string,
    public readonly rawData?: Record<string, unknown>,
  ) {
    super(label, collapsibleState);
    this.contextValue = nodeType;
    this.iconPath = this.getIconForType(nodeType);
    this.tooltip = rawData?.description
      ? String(rawData.description)
      : `${nodeType.toUpperCase()}: ${label}`;
  }

  private getIconForType(type: ExplorerNodeType): vscode.ThemeIcon {
    switch (type) {
      case 'lakehouse':
        return new vscode.ThemeIcon('database');
      case 'schema':
        return new vscode.ThemeIcon('folder');
      case 'table':
        return new vscode.ThemeIcon('table');
      case 'column':
        return new vscode.ThemeIcon('symbol-field');
      case 'action':
        return new vscode.ThemeIcon('play');
      default:
        return new vscode.ThemeIcon('circle-outline');
    }
  }
}
