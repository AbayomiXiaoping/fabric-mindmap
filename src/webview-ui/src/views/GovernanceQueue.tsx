import React from 'react';

export const GovernanceQueue: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Knowledge Governance & Review Queue</h2>
        <p style={{ color: '#888', fontSize: '13px' }}>
          Human-in-the-loop validation for AI-suggested business domains and inferred relationships
        </p>
      </div>

      <div className="card">
        <h3 style={{ fontSize: '14px', marginBottom: '8px' }}>Pending Proposals (P1 Preview)</h3>
        <p style={{ fontSize: '13px', color: '#aaa', marginBottom: '16px' }}>
          In accordance with frozen governance rules: All AI-inferred relationships and business domains remain proposals until explicitly approved by a developer.
        </p>
        <div style={{ padding: '12px', border: '1px dashed var(--border-color)', borderRadius: '4px', textAlign: 'center', color: '#888' }}>
          No pending approvals for active snapshot v1.
        </div>
      </div>
    </div>
  );
};
