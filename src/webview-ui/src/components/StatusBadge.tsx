import React from 'react';

interface Props {
  status: string;
}

export const StatusBadge: React.FC<Props> = ({ status }) => {
  const s = status.toUpperCase();
  let colorClass = 'badge-gray';

  if (s === 'ACTIVE' || s === 'SUCCESS' || s === 'COMPLETED' || s === 'IN_SYNC' || s === 'APPROVED') {
    colorClass = 'badge-green';
  } else if (s === 'PENDING' || s === 'BUILDING' || s === 'SUGGESTED' || s === 'REVIEW_REQUIRED') {
    colorClass = 'badge-yellow';
  } else if (s === 'LOCAL_ONLY' || s === 'DELTA' || s === 'DETECTED') {
    colorClass = 'badge-blue';
  }

  return <span className={`badge ${colorClass}`}>{status}</span>;
};
