import React from 'react';
import Layout from 'src/components/Layout';
import useSiteMetadata from 'src/hooks/useSiteMetadata';

const NotFoundPage = () => {
  const { siteUrl } = useSiteMetadata();
  return (
    <Layout>
      <h1 className="f-headline">404</h1>
      <p>This page doesn&#39;t exist.</p>
      <p className="moon-gray">
        If you wanna more message, you could visit{' '}
        <a className="moon-gray b" href={siteUrl}>
          {siteUrl}
        </a>
      </p>
    </Layout>
  );
};

export default NotFoundPage;
