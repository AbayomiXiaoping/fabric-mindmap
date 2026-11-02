import React from 'react';
import { GraphSummary } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { vscode } from '../vscodeApi';

interface Props {
  summary: GraphSummary | null;
  onNavigate: (view: 'mindmap' | 'tableDetails' | 'governance') => void;
  onSelectTable: (tableId: string) => void;
}

export const Overview: React.FC<Props> = ({ summary, onNavigate }) => {
  const lakehouseId = summary?.lakehouse_id || 'lh-banking-prod-01';

  const handleBuild = () => {
    vscode.postMessage({ type: 'buildGraph', lakehouseId });
  };

  const handleRefresh = () => {
    vscode.postMessage({ type: 'refreshGraph', lakehouseId });
  };

  const handleEnrich = () => {
    vscode.postMessage({ type: 'enrichMetadata', lakehouseId });
  };

  const handleSync = () => {
    vscode.postMessage({ type: 'syncDelta', lakehouseId });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '6px' }}>
            {summary?.lakehouse_id ? 'Fabric_Retail_Banking_Lakehouse' : 'Fabric Lakehouse Intelligence'}
          </h2>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <span style={{ color: '#888' }}>Version:</span>
            <strong>v{summary?.graph_version || 1}</strong>
            <span style={{ color: '#888', marginLeft: '10px' }}>Storage:</span>
            <StatusBadge status={summary?.sync_status || 'LOCAL_ONLY'} />
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={handleBuild}>Build Graph</button>
          <button className="secondary" onClick={handleRefresh}>Refresh Metadata</button>
          <button style={{ background: '#6f42c1', color: 'white' }} onClick={handleEnrich}>
            ✨ Enrich with AI
          </button>
          <button style={{ background: '#0078d4', color: 'white' }} onClick={handleSync}>
            ☁️ Sync to Delta
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <div className="card">
          <div style={{ color: '#888', fontSize: '12px', textTransform: 'uppercase' }}>Tables</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', margin: '8px 0', color: 'var(--link-color)' }}>
            {summary?.table_count || 4}
          </div>
          <button className="secondary" style={{ width: '100%' }} onClick={() => onNavigate('tableDetails')}>
            Explore Tables →
          </button>
        </div>

        <div className="card">
          <div style={{ color: '#888', fontSize: '12px', textTransform: 'uppercase' }}>Columns</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', margin: '8px 0', color: '#4cd964' }}>
            {summary?.column_count || 21}
          </div>
          <span style={{ fontSize: '12px', color: '#888' }}>Normalized & Fingerprinted</span>
        </div>

        <div className="card">
          <div style={{ color: '#888', fontSize: '12px', textTransform: 'uppercase' }}>Relationships</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', margin: '8px 0', color: '#ffcc00' }}>
            {summary?.edge_count ? Math.max(0, summary.edge_count - 25) : 3}
          </div>
          <button className="secondary" style={{ width: '100%' }} onClick={() => onNavigate('mindmap')}>
            Open Mindmap →
          </button>
        </div>

        <div className="card">
          <div style={{ color: '#888', fontSize: '12px', textTransform: 'uppercase' }}>Governance</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', margin: '8px 0', color: '#e06c75' }}>
            Review Queue
          </div>
          <button className="secondary" style={{ width: '100%' }} onClick={() => onNavigate('governance')}>
            Open Reviews →
          </button>
        </div>
      </div>
    </div>
  );
};
