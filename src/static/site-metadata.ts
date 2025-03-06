interface ISiteMetadataResult {
  siteTitle: string;
  siteUrl: string;
  description: string;
  logo: string;
  navLinks: {
    name: string;
    url: string;
  }[];
}

const data: ISiteMetadataResult = {
  siteTitle: 'Running Page',
  siteUrl: 'https://run.chensoul.cc',
  logo: 'https://blog.chensoul.cc/images/favicon.webp',
  description: 'Personal site and blog',
  navLinks: [
    {
      name: 'Blog',
      url: 'https://blog.chensoul.cc',
    },
    {
      name: 'About',
      url: 'https://github.com/chensoul',
    },
  ],
};

export default data;