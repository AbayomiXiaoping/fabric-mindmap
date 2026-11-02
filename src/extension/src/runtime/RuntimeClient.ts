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
}
