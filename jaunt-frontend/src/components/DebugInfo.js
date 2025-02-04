import React from 'react';

const DebugInfo = () => {
    return (
        <div style={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            background: '#f0f0f0',
            padding: '10px',
            fontSize: '12px'
        }}>
            <pre>
                API URL: {process.env.REACT_APP_API_URL || 'undefined'}
                {'\n'}
                NODE ENV: {process.env.NODE_ENV}
            </pre>
        </div>
    )
};

export default DebugInfo;