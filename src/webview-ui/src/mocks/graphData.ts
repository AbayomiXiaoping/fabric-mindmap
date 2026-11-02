import { GraphEdge, GraphNode, TableSummary } from '../types';

export const MOCK_TABLES: TableSummary[] = [
  {
    table_id: 'lakehouse:lh1:table:dbo.customers',
    name: 'customers',
    schema_name: 'dbo',
    format: 'DELTA',
    column_count: 6,
    description: 'Core retail and commercial banking customers',
    status: 'ACTIVE',
  },
  {
    table_id: 'lakehouse:lh1:table:dbo.accounts',
    name: 'accounts',
    schema_name: 'dbo',
    format: 'DELTA',
    column_count: 6,
    description: 'Demand deposit, savings, and credit accounts',
    status: 'ACTIVE',
  },
  {
    table_id: 'lakehouse:lh1:table:dbo.transactions',
    name: 'transactions',
    schema_name: 'dbo',
    format: 'DELTA',
    column_count: 6,
    description: 'Ledger of all debit and credit transaction movements',
    status: 'ACTIVE',
  },
  {
    table_id: 'lakehouse:lh1:table:analytics.daily_balances',
    name: 'daily_balances',
    schema_name: 'analytics',
    format: 'DELTA',
    column_count: 3,
    description: 'Aggregated end-of-day balances by account',
    status: 'ACTIVE',
  },
];

export const MOCK_NODES: GraphNode[] = [
  {
    node_id: 'lh1',
    lakehouse_id: 'lh1',
    node_type: 'LAKEHOUSE',
    name: 'Fabric_Retail_Banking_Lakehouse',
    qualified_name: 'Fabric_Retail_Banking_Lakehouse',
    technical_status: 'ACTIVE',
    first_seen_version: 1,
    last_seen_version: 1,
  },
  {
    node_id: 's_dbo',
    lakehouse_id: 'lh1',
    node_type: 'SCHEMA',
    name: 'dbo',
    qualified_name: 'Fabric_Retail_Banking_Lakehouse.dbo',
    parent_node_id: 'lh1',
    technical_status: 'ACTIVE',
    first_seen_version: 1,
    last_seen_version: 1,
  },
  {
    node_id: 's_analytics',
    lakehouse_id: 'lh1',
    node_type: 'SCHEMA',
    name: 'analytics',
    qualified_name: 'Fabric_Retail_Banking_Lakehouse.analytics',
    parent_node_id: 'lh1',
    technical_status: 'ACTIVE',
    first_seen_version: 1,
    last_seen_version: 1,
  },
];

