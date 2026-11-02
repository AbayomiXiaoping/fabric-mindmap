import React, { useState } from 'react';

interface Props {
  placeholder?: string;
  onSearch: (query: string) => void;
}

export const SearchBar: React.FC<Props> = ({ placeholder = 'Search tables or columns...', onSearch }) => {
  const [val, setVal] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const q = e.target.value;
    setVal(q);
    onSearch(q);
  };

  return (
    <div style={{ position: 'relative', width: '100%', maxWidth: '400px' }}>
      <input
        type="text"
        value={val}
        onChange={handleChange}
        placeholder={placeholder}
        style={{
          width: '100%',
          padding: '8px 12px',
          borderRadius: '4px',
          border: '1px solid var(--border-color)',
          background: 'var(--card-bg)',
          color: 'var(--text-color)',
          fontSize: '13px',
          outline: 'none',
        }}
      />
    </div>
  );
};

