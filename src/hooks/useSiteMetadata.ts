import { graphql, useStaticQuery } from 'gatsby';

interface ISiteMetadataResult {
  site: {
    siteMetadata: {
      siteTitle: string;
      siteUrl: string;
      description: string;
      logo: string;
      navLinks: {
        name: string;
        url: string;
      }[];
    };
  };
}

const useSiteMetadata = () => {
  const { site } = useStaticQuery<ISiteMetadataResult>(
    graphql`
      query SiteMetaData {
        site {
          siteMetadata {
            siteTitle
            siteUrl
            description
            logo
            navLinks {
              name
              url
            }
          }
        }
      }
    `
  );
  return site.siteMetadata;
};

export default useSiteMetadata;
