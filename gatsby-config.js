const path = require("path");

module.exports = {
  siteMetadata: {
    title: "Yihong0618",
    siteUrl: "https://yihong.run",
    description: "Personal site and blog",
  },
  plugins: [
    "gatsby-plugin-react-helmet",
    {
      resolve: "gatsby-transformer-remark",
      options: {
        plugins: [
          "gatsby-remark-responsive-iframe",
          "gatsby-remark-smartypants",
          "gatsby-remark-widows",
          "gatsby-remark-external-links",
          {
            resolve: "gatsby-remark-autolink-headers",
            options: {
              className: "header-link",
            },
          },
          {
            resolve: "gatsby-remark-images",
            options: {
              maxWidth: 600,
              quality: 80,
              withWebp: { quality: 80 },
            },
          },
        ],
      },
    },
    {
      resolve: "gatsby-source-filesystem",
      options: {
        name: "src",
        path: `${__dirname}/posts`,
      },
    },
    {
      resolve: "gatsby-plugin-sass",
      options: {
        precision: 8,
      },
    },
    "gatsby-transformer-yaml",
    "gatsby-transformer-json",
    {
      resolve: "gatsby-source-filesystem",
      options: {
        path: "./data/",
      },
    },
    {
      resolve: "gatsby-source-filesystem",
      options: {
        name: "images",
        path: `${__dirname}/posts/images`,
      },
    },
    {
      resolve: "gatsby-source-filesystem",
      options: {
        name: "static_images",
        path: `${__dirname}/src/images`,
        ignore: ["**/.(js|jsx|scss)"],
      },
    },
    {
      resolve: 'gatsby-plugin-react-svg',
      options: {
        rule: {
          include: /assets/
        }
      }
    },
    "gatsby-transformer-sharp",
    "gatsby-plugin-sharp",
    //"gatsby-redirect-from",
    "gatsby-plugin-sitemap",
    {
      resolve: "gatsby-plugin-robots-txt",
      options: {
        policy: [{ userAgent: "*", allow: "/" }],
      },
    },
  ],
};
