import PropTypes from 'prop-types';
import React from 'react';
import { Helmet } from 'react-helmet-async';
import Header from '@/components/Header';
import useSiteMetadata from '@/hooks/useSiteMetadata';
import styles from './style.module.scss';

const Layout = ({ children }: React.PropsWithChildren) => {
  const { siteTitle, description, keywords } = useSiteMetadata();

  return (
    <>
      <Helmet bodyAttributes={{ class: styles.body }}>
        <html lang="en" />
        <title>{siteTitle}</title>
        <meta name="description" content={description} />
        <meta name="keywords" content={keywords} />
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1, shrink-to-fit=no"
        />
      </Helmet>
      <Header />
      <div className="pa3 pa5-l mb5 cf">{children}</div>
    </>
  );
};

Layout.propTypes = {
  children: PropTypes.node.isRequired,
};

export default Layout;
