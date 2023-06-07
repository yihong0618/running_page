/* eslint-disable no-undef */
// eslint-disable-next-line no-undef
module.exports = {
  pathPrefix: process.env.PATH_PREFIX || '/',
  siteMetadata: {
    siteTitle: 'GAOHAO \'s Running Page',
    siteUrl: 'https://efish2002.github.io/running_page/',
    logo: 'https://avatars.githubusercontent.com/u/10509616?s=400&u=e356a1490ddac5624847d822af8f0faec4892ab4&v=4',
    description: 'Personal site and blog',
    navLinks: [
      {
        name: 'Blog',
        url: 'https://github.com/efish2002/running_page/wiki',
      },
      {
        name: 'About',
        url: 'https://github.com/efish2002/running_page/blob/master/README-CN.md',
      },
    ],
  },
  plugins: [
    'gatsby-transformer-json',
    'gatsby-plugin-react-helmet',
    'gatsby-plugin-offline',

    {
      resolve: 'gatsby-plugin-vercel',
      options: {
        // (optional) Prints metrics in the console when true
        debug: false,
      },
    },
    {
      resolve: 'gatsby-source-filesystem',
      options: {
        path: './src/static/',
      },
    },
    {
      resolve: 'gatsby-source-filesystem',
      options: {
        path: './src/images/',
      },
    },
    {
      resolve: 'gatsby-alias-imports',
      options: {
        rootFolder: '.',
      },
    },
    {
      resolve: 'gatsby-plugin-sass',
      options: {
        cssLoaderOptions: {
          esModule: false,
          modules: {
            namedExport: false,
          },
        },
      },
    },
    {
      resolve: 'gatsby-plugin-react-svg',
      options: {
        rule: {
          include: /assets/,
        },
      },
    },
    {
      resolve: 'gatsby-plugin-manifest',
      options: {
        name: 'gatsby-starter-default',
        short_name: 'starter',
        start_url: '/',
        background_color: '#e1e1e1',
        theme_color: '#e1e1e1',
        display: 'standalone',
        icon: 'src/images/favicon.png', // This path is relative to the root of the site.
      },
    },
  ],
};
