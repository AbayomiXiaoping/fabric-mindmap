import React, { useState, useEffect } from 'react';
import { vscode } from '../vscodeApi';
import { StatusBadge } from '../components/StatusBadge';

interface ReviewProposal {
  proposed_domain?: string;
  rationale?: string;
  evidence?: { confidence?: number; table?: string };
}

interface ReviewItem {
  review_id: string;
  review_type: string;
  entity_id: string;
  entity_name: string;
  status: string;
  priority: string;
  created_at: string;
  proposal: ReviewProposal;
}

export const GovernanceQueue: React.FC = () => {
  const lakehouseId = 'lh-banking-prod-01';
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [tab, setTab] = useState<'pending' | 'audit'>('pending');
  const [modifyId, setModifyId] = useState<string | null>(null);
  const [modifiedName, setModifiedName] = useState<string>('');

  useEffect(() => {
    // Request governance queue on mount
    vscode.postMessage({ type: 'fetchGovernanceQueue', lakehouseId });

    const listener = (event: MessageEvent) => {
      const msg = event.data;
      if (msg.type === 'governanceQueueLoaded' && Array.isArray(msg.items)) {
        setItems(msg.items);
      }
    };
    window.addEventListener('message', listener);
    return () => window.removeEventListener('message', listener);
  }, []);

  const handleApprove = (reviewId: string) => {
    vscode.postMessage({
      type: 'approveReview',
      lakehouseId,
      reviewId,
      comments: 'Approved via Governance UI',
    });
  };

  const handleReject = (reviewId: string) => {
    const reason = prompt('Enter rejection reason:') || 'Rejected by developer review';
    vscode.postMessage({
      type: 'rejectReview',
      lakehouseId,
      reviewId,
      reason,
    });
  };

  const handleModify = (reviewId: string) => {
    if (!modifiedName.trim()) return;
    vscode.postMessage({
      type: 'modifyReview',
      lakehouseId,
      reviewId,
      modifiedDomain: modifiedName.trim(),
      comments: 'Modified during review',
    });
    setModifyId(null);
    setModifiedName('');
  };

  const pendingItems = items.filter((i) => i.status === 'PENDING');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Knowledge Governance & Review Queue</h2>
          <p style={{ color: '#888', fontSize: '13px' }}>
            Enforcing developer approval for AI-suggested business domains and inferred relationships
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className={tab === 'pending' ? '' : 'secondary'}
            onClick={() => setTab('pending')}
          >
            Pending Reviews ({pendingItems.length})
          </button>
          <button
            className={tab === 'audit' ? '' : 'secondary'}
            onClick={() => setTab('audit')}
          >
            Audit History
          </button>
          <button
            style={{ background: '#6f42c1', color: 'white' }}
            onClick={() => vscode.postMessage({ type: 'enrichMetadata', lakehouseId })}
          >
            ✨ Run AI Enrichment
          </button>
        </div>
      </div>

      {tab === 'pending' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {pendingItems.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '30px', color: '#888' }}>
              <p style={{ fontSize: '14px', marginBottom: '8px' }}>No pending proposals awaiting review.</p>
              <p style={{ fontSize: '12px' }}>
                Click <strong>"Run AI Enrichment"</strong> above to analyze table metadata and generate business domain proposals.
              </p>
            </div>
          ) : (
            pendingItems.map((item) => {
              const conf = item.proposal.evidence?.confidence;
              const isModifying = modifyId === item.review_id;

              return (
                <div key={item.review_id} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '11px', color: '#888' }}>PROPOSED DOMAIN FOR:</span>
                        <strong style={{ fontSize: '14px' }}>{item.entity_name}</strong>
                        <StatusBadge status={item.priority} />
                      </div>
                      <div style={{ fontSize: '16px', fontWeight: 'bold', color: 'var(--link-color)', marginTop: '4px' }}>
                        📁 {item.proposal.proposed_domain || 'Unclassified'}
                      </div>
                    </div>
                    {conf !== undefined && (
                      <span className="badge badge-blue">
                        {(conf * 100).toFixed(0)}% Confidence
                      </span>
                    )}
                  </div>

                  <p style={{ fontSize: '13px', color: '#bbb', background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: '4px' }}>
                    💡 <strong>Rationale:</strong> {item.proposal.rationale || 'No rationale provided'}
                  </p>

                  {isModifying ? (
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '6px' }}>
                      <input
                        type="text"
                        value={modifiedName}
                        onChange={(e) => setModifiedName(e.target.value)}
                        placeholder="Enter custom domain name..."
                        style={{
                          flex: 1,
                          padding: '6px 10px',
                          background: 'var(--bg-color)',
                          color: 'var(--text-color)',
                          border: '1px solid var(--border-color)',
                          borderRadius: '4px',
                        }}
                      />
                      <button onClick={() => handleModify(item.review_id)}>Save & Approve</button>
                      <button className="secondary" onClick={() => setModifyId(null)}>Cancel</button>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '4px' }}>
                      <button
                        style={{ background: '#28a745' }}
                        onClick={() => handleApprove(item.review_id)}
                      >
                        ✓ Approve Domain
                      </button>
                      <button
                        className="secondary"
                        onClick={() => {
                          setModifyId(item.review_id);
                          setModifiedName(item.proposal.proposed_domain || '');
                        }}
                      >
                        ✏️ Modify Name
                      </button>
                      <button
                        style={{ background: '#d73a49' }}
                        onClick={() => handleReject(item.review_id)}
                      >
                        ✕ Reject
                      </button>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {tab === 'audit' && (
        <div className="card">
          <h3 style={{ fontSize: '14px', marginBottom: '12px' }}>Audit Log & Validated Decisions</h3>
          <p style={{ fontSize: '12px', color: '#888', marginBottom: '16px' }}>
            All approvals, modifications, and rejections are logged as immutable audit events with actor, timestamp, and evidence fingerprint.
          </p>
          <div style={{ padding: '12px', border: '1px dashed var(--border-color)', borderRadius: '4px', textAlign: 'center', color: '#888' }}>
            Resolved decisions are stored in <code>kg_user_decisions</code> and reflected in <code>kg_business_domains</code>.
          </div>
        </div>
      )}
    </div>
  );
};
