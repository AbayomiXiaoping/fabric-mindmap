export type WebviewMessage =
  | { type: 'ready' }
  | { type: 'navigate'; view: string; params?: Record<string, string> }
  | { type: 'requestData'; requestId: string; endpoint: string; params?: Record<string, unknown> }
  | { type: 'buildGraph'; lakehouseId: string }
  | { type: 'refreshGraph'; lakehouseId: string };

export type ExtensionMessage =
  | { type: 'init'; baseUrl: string; lakehouseId?: string; view: string }
  | { type: 'dataResponse'; requestId: string; data: unknown; error?: string }
  | { type: 'scanProgress'; scanId: string; status: string; progress?: number }
  | { type: 'notification'; level: 'info' | 'warn' | 'error'; message: string };
