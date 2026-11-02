import { Logger } from '../utils/logger';

export interface HealthStatus {
  status: string;
  version: string;
}

export interface TableSummary {
  table_id: string;
  name: string;
  schema_name: string;
  format: string;
  column_count: number;
  description?: string;
  status: string;
}

export interface NodeInfo {
  node_id: string;
  node_type: string;
  name: string;
  qualified_name: string;
  technical_status: string;
  has_children: boolean;
  child_count: number;
}

export interface GraphSummary {
  lakehouse_id: string;
  graph_version: number;
  snapshot_id?: string;
  node_count: number;
  edge_count: number;
  table_count: number;
  column_count: number;
  last_scan_at?: string;
  sync_status: string;
}

export interface TableDetails {
  node: Record<string, unknown>;
  table_metadata: Record<string, unknown>;
  columns: Array<Record<string, unknown>>;
  relationships: Array<Record<string, unknown>>;
}

export interface ScanStatus {
  status: string;
  snapshot_id: string;
  graph_version: number;
  node_count: number;
  edge_count: number;
}

export interface ReviewItem {
  review_id: string;
  review_type: string;
  entity_id: string;
  entity_name: string;
  status: string;
  priority: string;
  created_at: string;
  proposal: {
    proposed_domain?: string;
    rationale?: string;
    evidence?: Record<string, unknown>;
    confidence?: number;
    relationship_type?: string;
  };
}

export interface UserDecision {
  decision_id: string;
  review_id: string;
  actor_id: string;
  action: string;
  previous_value_json: string;
  new_value_json: string;
  comments?: string;
  evidence_fingerprint: string;
  created_at: string;
}

export class RuntimeClient {
  private baseUrl: string;
  private logger: Logger;

  constructor(baseUrl: string, logger: Logger) {
    this.baseUrl = baseUrl;
    this.logger = logger;
  }

  setBaseUrl(url: string): void {
    this.baseUrl = url;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
      }

      return (await response.json()) as T;
    } catch (err) {
      this.logger.error(`Runtime request failed: ${endpoint}`, err);
      throw err;
    }
  }

  async getHealth(): Promise<HealthStatus> {
    return this.request<HealthStatus>('/health');
  }

  async listTables(lakehouseId: string): Promise<TableSummary[]> {
    return this.request<TableSummary[]>(`/api/v1/lakehouses/${lakehouseId}/tables`);
  }

  async getTableDetails(lakehouseId: string, tableId: string): Promise<TableDetails> {
    return this.request<TableDetails>(`/api/v1/lakehouses/${lakehouseId}/tables/${encodeURIComponent(tableId)}`);
  }

  async buildGraph(lakehouseId: string, lakehouseName?: string): Promise<ScanStatus> {
    return this.request<ScanStatus>(`/api/v1/lakehouses/${lakehouseId}/graph/build`, {
      method: 'POST',
      body: JSON.stringify({ lakehouse_name: lakehouseName }),
    });
  }

  async refreshGraph(lakehouseId: string, lakehouseName?: string): Promise<ScanStatus> {
    return this.request<ScanStatus>(`/api/v1/lakehouses/${lakehouseId}/graph/refresh`, {
      method: 'POST',
      body: JSON.stringify({ lakehouse_name: lakehouseName }),
    });
  }

  async getGraph(lakehouseId: string): Promise<GraphSummary> {
    return this.request<GraphSummary>(`/api/v1/lakehouses/${lakehouseId}/graph`);
  }

  async getNodeChildren(lakehouseId: string, nodeId: string): Promise<NodeInfo[]> {
    return this.request<NodeInfo[]>(
      `/api/v1/lakehouses/${lakehouseId}/graph/nodes/${encodeURIComponent(nodeId)}/children`,
    );
  }

  // --- AI & Governance ---

  async triggerEnrichment(lakehouseId: string): Promise<{ status: string; stats: Record<string, number> }> {
    return this.request<{ status: string; stats: Record<string, number> }>(
      `/api/v1/lakehouses/${lakehouseId}/enrich`,
      { method: 'POST' },
    );
  }

  async getGovernanceQueue(lakehouseId: string): Promise<ReviewItem[]> {
    return this.request<ReviewItem[]>(`/api/v1/lakehouses/${lakehouseId}/governance/queue`);
  }

  async approveReview(
    lakehouseId: string,
    reviewId: string,
    actorId: string = 'developer',
    comments?: string,
  ): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>(
      `/api/v1/lakehouses/${lakehouseId}/governance/reviews/${reviewId}/approve`,
      {
        method: 'POST',
        body: JSON.stringify({ actor_id: actorId, comments }),
      },
    );
  }

  async rejectReview(
    lakehouseId: string,
    reviewId: string,
    actorId: string = 'developer',
    reason?: string,
  ): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>(
      `/api/v1/lakehouses/${lakehouseId}/governance/reviews/${reviewId}/reject`,
      {
        method: 'POST',
        body: JSON.stringify({ actor_id: actorId, reason }),
      },
    );
  }

  async modifyReview(
    lakehouseId: string,
    reviewId: string,
    modifiedDomainName: string,
    actorId: string = 'developer',
    comments?: string,
  ): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>(
      `/api/v1/lakehouses/${lakehouseId}/governance/reviews/${reviewId}/modify`,
      {
        method: 'POST',
        body: JSON.stringify({
          modified_domain_name: modifiedDomainName,
          actor_id: actorId,
          comments,
        }),
      },
    );
  }

  async getGovernanceHistory(lakehouseId: string): Promise<UserDecision[]> {
    return this.request<UserDecision[]>(`/api/v1/lakehouses/${lakehouseId}/governance/history`);
  }
}
