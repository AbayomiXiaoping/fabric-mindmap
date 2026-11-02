import React, { useState } from 'react';
import { MOCK_TABLES } from '../mocks/graphData';
import { SearchBar } from '../components/SearchBar';
import { StatusBadge } from '../components/StatusBadge';

interface Props {
  selectedTableId?: string;
}

export const TableExplorer: React.FC<Props> = ({ selectedTableId }) => {
  const [activeId, setActiveId] = useState<string>(
    selectedTableId || MOCK_TABLES[0].table_id
  );
  const [search, setSearch] = useState('');

  const filtered = MOCK_TABLES.filter(
    (t) =>
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.schema_name.toLowerCase().includes(search.toLowerCase())
  );

  const activeTable = MOCK_TABLES.find((t) => t.table_id === activeId) || MOCK_TABLES[0];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '20px', height: '100%' }}>
      {/* Sidebar List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <SearchBar onSearch={setSearch} placeholder="Filter tables..." />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', overflowY: 'auto' }}>
          {filtered.map((tbl) => {
            const isSelected = tbl.table_id === activeId;
            return (
              <div
                key={tbl.table_id}
                onClick={() => setActiveId(tbl.table_id)}
                style={{
                  padding: '10px 12px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  background: isSelected ? 'var(--primary)' : 'var(--card-bg)',
                  color: isSelected ? 'var(--primary-fg)' : 'var(--text-color)',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600 }}>{tbl.name}</div>
                  <div style={{ fontSize: '11px', opacity: 0.8 }}>schema: {tbl.schema_name}</div>
                </div>
                <span style={{ fontSize: '11px', opacity: 0.7 }}>{tbl.column_count} cols</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Table Detail */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontSize: '12px', color: '#888', textTransform: 'uppercase' }}>
              {activeTable.schema_name} /
            </div>
            <h2 style={{ fontSize: '20px', fontWeight: 'bold' }}>{activeTable.name}</h2>
            <p style={{ color: '#aaa', marginTop: '4px' }}>{activeTable.description}</p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <StatusBadge status={activeTable.format} />
            <StatusBadge status={activeTable.status} />
          </div>
        </div>

        <hr style={{ border: 0, borderTop: '1px solid var(--border-color)' }} />

        {/* Columns Grid */}
        <div>
          <h3 style={{ fontSize: '14px', marginBottom: '10px' }}>Columns & Constraints</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)', color: '#888' }}>
                <th style={{ padding: '8px' }}>Column</th>
                <th style={{ padding: '8px' }}>Type</th>
                <th style={{ padding: '8px' }}>Nullable</th>
                <th style={{ padding: '8px' }}>Key</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                <td style={{ padding: '8px', fontWeight: 600 }}>id / primary_id</td>
                <td style={{ padding: '8px', color: '#4daafc' }}>BIGINT</td>
                <td style={{ padding: '8px', color: '#888' }}>No</td>
                <td style={{ padding: '8px' }}>
                  <span className="badge badge-yellow">PK</span>
                </td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                <td style={{ padding: '8px', fontWeight: 600 }}>name / reference</td>
                <td style={{ padding: '8px', color: '#4daafc' }}>STRING</td>
                <td style={{ padding: '8px', color: '#888' }}>Yes</td>
                <td style={{ padding: '8px' }}>-</td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                <td style={{ padding: '8px', fontWeight: 600 }}>created_at</td>
                <td style={{ padding: '8px', color: '#4daafc' }}>TIMESTAMP</td>
                <td style={{ padding: '8px', color: '#888' }}>No</td>
                <td style={{ padding: '8px' }}>-</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Provenance Box */}
        <div style={{ marginTop: 'auto', padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '4px' }}>
          <div style={{ fontSize: '11px', color: '#888' }}>
            <span>Extraction Source: Microsoft Fabric REST / OneLake Delta metadata</span>
            <br />
            <span>Fingerprint: <code>sha256-d7a8fbb94e...</code></span>
          </div>
        </div>
      </div>
    </div>
  );
};

