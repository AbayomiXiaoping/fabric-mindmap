export type WebviewMessage =
  | { type: 'ready' }
  | { type: 'navigate'; view: string; params?: Record<string, string> }
  | { type: 'requestData'; requestId: string; endpoint: string; params?: Record<string, unknown> }
  | { type: 'buildGraph'; lakehouseId: string }
  | { type: 'refreshGraph'; lakehouseId: string }
  | { type: 'enrichMetadata'; lakehouseId: string }
  | { type: 'fetchGovernanceQueue'; lakehouseId: string }
  | { type: 'approveReview'; lakehouseId: string; reviewId: string; comments?: string }
  | { type: 'rejectReview'; lakehouseId: string; reviewId: string; reason?: string }
  | { type: 'modifyReview'; lakehouseId: string; reviewId: string; modifiedDomain: string; comments?: string };

export type ExtensionMessage =
  | { type: 'init'; baseUrl: string; lakehouseId?: string; view: string }
  | { type: 'dataResponse'; requestId: string; data: unknown; error?: string }
  | { type: 'governanceQueueLoaded'; items: unknown[] }
  | { type: 'scanProgress'; scanId: string; status: string; progress?: number }
  | { type: 'notification'; level: 'info' | 'warn' | 'error'; message: string };
