import Layout from '@/components/Layout';
import useSiteMetadata from '@/hooks/useSiteMetadata';

const NotFoundPage = () => {
  const { siteUrl } = useSiteMetadata();
  return (
    <Layout>
      <h1 className="my-2.5 text-5xl font-bold italic">404</h1>
      <p>This page doesn&#39;t exist.</p>
      <p className="text-gray-400">
        If you wanna more message, you could visit{' '}
        <a className="font-bold text-gray-400" href={siteUrl}>
          {siteUrl}
        </a>
      </p>
    </Layout>
  );
};

export default NotFoundPage;
