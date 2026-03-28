import React from 'react';

const DiffViewer = ({ diff }) => {
  if (!diff) return null;

  return (
    <div className="diff-viewer">
      {Object.entries(diff).map(([key, value]) => (
        <div key={key} className="diff-item">
          <span className="label">{key}:</span>
          <span className="old">{value.before}</span>
          <span className="arrow">→</span>
          <span className="new">{value.after}</span>
        </div>
      ))}
    </div>
  );
};

export default DiffViewer;