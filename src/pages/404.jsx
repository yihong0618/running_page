import React from 'react';
import Layout from 'src/components/Layout';

const NotFoundPage = () => (
  <Layout>
    <h1 className="f-headline">404</h1>
    <p>This page doesn&#39;t exist.</p>
    <p className="moon-gray">
      If you wanna more message, you could visit{' '}
      <a
        className="moon-gray b"
        href="https://github.com/yihong0618/running_page"
      >
        https://github.com/yihong0618/running_page
      </a>
    </p>
  </Layout>
);

export default NotFoundPage;
