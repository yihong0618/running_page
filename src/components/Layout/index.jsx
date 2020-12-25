import React from 'react';
import PropTypes from 'prop-types';
import { Helmet } from 'react-helmet';
import useSiteMetadata from 'src/hooks/useSiteMetadata';
import Header from 'src/components/Header';
import 'src/styles/index.scss';
import styles from './style.module.scss';

const Layout = ({ children }) => {
  const { title, description } = useSiteMetadata();

  return (
    <>
      <Helmet
        title={title}
        meta={[
          {
            name: 'description',
            content: description,
          },
          { name: 'keywords', content: 'running' },
        ]}
        bodyAttributes={{ class: styles.body }}
      >
        <html lang="en" />
      </Helmet>
      <Header siteTitle={title} />
      <div className="pa3 pa5-l">{children}</div>
    </>
  );
};

Layout.propTypes = {
  children: PropTypes.node.isRequired,
};

export default Layout;
