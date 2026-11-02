import * as vscode from 'vscode';

export interface ExtensionSettings {
  runtimeHost: string;
  runtimePort: number;
  autoStart: boolean;
  aiEnabled: boolean;
  fabricPersistenceEnabled: boolean;
}

export function getSettings(): ExtensionSettings {
  const config = vscode.workspace.getConfiguration('lakehouseIntelligence');
  return {
    runtimeHost: config.get<string>('runtime.host', '127.0.0.1'),
    runtimePort: config.get<number>('runtime.port', 9720),
    autoStart: config.get<boolean>('runtime.autoStart', true),
    aiEnabled: config.get<boolean>('ai.enabled', true),
    fabricPersistenceEnabled: config.get<boolean>('persistence.fabricEnabled', false),
  };
}
