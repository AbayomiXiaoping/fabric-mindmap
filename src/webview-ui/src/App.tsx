import React, { useState, useEffect } from 'react';
import { Overview } from './views/Overview';
import { Mindmap } from './views/Mindmap';
import { TableExplorer } from './views/TableExplorer';
import { GovernanceQueue } from './views/GovernanceQueue';
import { GraphSummary } from './types';
import { vscode } from './vscodeApi';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'overview' | 'mindmap' | 'tableDetails' | 'governance'>('overview');
  const [selectedTableId, setSelectedTableId] = useState<string | undefined>();
  const [summary, setSummary] = useState<GraphSummary | null>(null);

  useEffect(() => {
    // Listen for extension messages
    const listener = (event: MessageEvent) => {
      const msg = event.data;
      if (msg.type === 'init') {
        if (msg.view) {
          setCurrentView(msg.view);
        }
        if (msg.tableId) {
          setSelectedTableId(msg.tableId);
        }
      }
    };
    window.addEventListener('message', listener);
    vscode.postMessage({ type: 'ready' });
    return () => window.removeEventListener('message', listener);
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', padding: '16px', gap: '16px' }}>
      {/* Top Navigation Bar */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
        <button
          className={currentView === 'overview' ? '' : 'secondary'}
          onClick={() => setCurrentView('overview')}
        >
          Overview
        </button>
        <button
          className={currentView === 'mindmap' ? '' : 'secondary'}
          onClick={() => setCurrentView('mindmap')}
        >
          Mindmap
        </button>
        <button
          className={currentView === 'tableDetails' ? '' : 'secondary'}
          onClick={() => setCurrentView('tableDetails')}
        >
          Table Explorer
        </button>
        <button
          className={currentView === 'governance' ? '' : 'secondary'}
          onClick={() => setCurrentView('governance')}
        >
          Governance
        </button>
      </div>

      {/* Main View Area */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {currentView === 'overview' && (
          <Overview
            summary={summary}
            onNavigate={(v) => setCurrentView(v)}
            onSelectTable={(tid) => {
              setSelectedTableId(tid);
              setCurrentView('tableDetails');
            }}
          />
        )}
        {currentView === 'mindmap' && (
          <Mindmap
            onSelectTable={(tid) => {
              setSelectedTableId(tid);
              setCurrentView('tableDetails');
            }}
          />
        )}
        {currentView === 'tableDetails' && (
          <TableExplorer selectedTableId={selectedTableId} />
        )}
        {currentView === 'governance' && <GovernanceQueue />}
      </div>
    </div>
  );
};

