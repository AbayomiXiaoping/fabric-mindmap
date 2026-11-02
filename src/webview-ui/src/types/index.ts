export type NodeType = 'LAKEHOUSE' | 'SCHEMA' | 'DOMAIN' | 'TABLE' | 'COLUMN' | 'BUSINESS_CONCEPT';

export type EdgeType = 'CONTAINS' | 'HAS_COLUMN' | 'REFERENCES' | 'DERIVED_FROM' | 'USED_BY' | 'SEMANTICALLY_RELATED';

export interface GraphNode {
  node_id: string;
  lakehouse_id: string;
  node_type: NodeType;
  name: string;
  qualified_name: string;
  parent_node_id?: string | null;
  technical_status: string;
  first_seen_version: number;
  last_seen_version: number;
}

export interface GraphEdge {
  edge_id: string;
  lakehouse_id: string;
  source_node_id: string;
  target_node_id: string;
  edge_type: EdgeType;
  evidence_type: string;
  confidence?: number | null;
  validation_status: string;
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

export interface ColumnDetail {
  column_id: string;
  column_name: string;
  data_type: string;
  source_data_type?: string;
  nullable?: boolean;
  ordinal_position?: number;
  description?: string;
  is_primary_key?: boolean;
  is_foreign_key?: boolean;
  fingerprint: string;
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

export interface WebviewState {
  view: 'overview' | 'mindmap' | 'tableDetails' | 'governance';
  selectedTableId?: string;
  lakehouseId: string;
  baseUrl: string;
}
