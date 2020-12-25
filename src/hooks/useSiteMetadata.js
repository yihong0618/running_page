import { useStaticQuery, graphql } from 'gatsby';

const useSiteMetadata = () => {
  const { site } = useStaticQuery(
    graphql`
      query SiteMetaData {
        site {
          siteMetadata {
            title
            siteUrl
            description
          }
        }
      }
    `
  );
  return site.siteMetadata;
};

export default useSiteMetadata;
