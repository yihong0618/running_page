import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import siteMetadata from './static/site-metadata';

// Set document title from site metadata
document.title = siteMetadata.siteTitle;

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
