import React, { useState } from 'react';
import { MOCK_TABLES } from '../mocks/graphData';
import { TableSummary } from '../types';

interface Props {
  onSelectTable: (tableId: string) => void;
}

export const Mindmap: React.FC<Props> = ({ onSelectTable }) => {
  const [expandedTables, setExpandedTables] = useState<Record<string, boolean>>({
    'lakehouse:lh1:table:dbo.customers': true,
    'lakehouse:lh1:table:dbo.accounts': true,
  });

  const toggleTable = (id: string) => {
    setExpandedTables((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const schemas = Array.from(new Set(MOCK_TABLES.map((t) => t.schema_name)));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '16px', fontWeight: 600 }}>Interactive Knowledge Mindmap</h2>
          <p style={{ color: '#888', fontSize: '12px' }}>
            Hierarchical exploration of Lakehouse objects with lazy-expanded schemas and tables
          </p>
        </div>
      </div>

      {/* Visual Canvas Representation */}
      <div
        className="card"
        style={{
          flex: 1,
          minHeight: '480px',
          overflow: 'auto',
          background: 'radial-gradient(#2d2d30 1px, transparent 1px)',
          backgroundSize: '20px 20px',
          padding: '24px',
        }}
      >
        {/* Lakehouse Root Node */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '32px' }}>
          <div
            style={{
              padding: '10px 20px',
              borderRadius: '8px',
              background: '#0e639c',
              color: 'white',
              fontWeight: 'bold',
              boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
              border: '2px solid #1177bb',
            }}
          >
            🏢 Fabric_Retail_Banking_Lakehouse
          </div>
        </div>

        {/* Schemas */}
        <div style={{ display: 'flex', justifyContent: 'space-around', gap: '30px' }}>
          {schemas.map((schema) => {
            const tablesInSchema = MOCK_TABLES.filter((t) => t.schema_name === schema);
            return (
              <div
                key={schema}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  flex: 1,
                  maxWidth: '380px',
                }}
              >
                {/* Schema Node */}
                <div
                  style={{
                    padding: '8px 16px',
                    borderRadius: '6px',
                    background: '#6f42c1',
                    color: 'white',
                    fontWeight: 600,
                    marginBottom: '20px',
                    boxShadow: '0 2px 6px rgba(0,0,0,0.2)',
                  }}
                >
                  📁 schema: {schema}
                </div>

                {/* Tables in this schema */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', width: '100%' }}>
                  {tablesInSchema.map((tbl) => {
                    const isExpanded = !!expandedTables[tbl.table_id];
                    return (
                      <div
                        key={tbl.table_id}
                        style={{
                          background: 'var(--card-bg)',
                          border: '1px solid var(--border-color)',
                          borderRadius: '6px',
                          overflow: 'hidden',
                          boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                        }}
                      >
                        <div
                          style={{
                            padding: '8px 12px',
                            background: '#2d3748',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            cursor: 'pointer',
                          }}
                          onClick={() => toggleTable(tbl.table_id)}
                        >
                          <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <span>{isExpanded ? '▼' : '►'}</span>
                            <span>📊 {tbl.name}</span>
                          </div>
                          <span style={{ fontSize: '11px', color: '#a0aec0' }}>
                            {tbl.column_count} cols
                          </span>
                        </div>

                        {isExpanded && (
                          <div style={{ padding: '10px', background: 'var(--bg-color)', fontSize: '12px' }}>
                            <p style={{ color: '#888', marginBottom: '8px', fontSize: '11px' }}>
                              {tbl.description}
                            </p>
                            <div style={{ display: 'flex', gap: '6px', marginTop: '8px' }}>
                              <button
                                style={{ fontSize: '11px', padding: '4px 8px' }}
                                onClick={() => onSelectTable(tbl.table_id)}
                              >
                                View Schema Details
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

