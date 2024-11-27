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
  siteTitle: 'ClF3\'s Running Page',
  siteUrl: 'https://clf3.github.io/running_page',
  logo: 'https://icons.clf3.org/tianyi.ico',
  description: 'Personal site and blog',
  navLinks: [
    {
      name: 'Blog',
      url: 'https://blog.clf3.org',
    },
    {
      name: 'About',
      url: 'https://github.com/yihong0618/running_page/blob/master/README-CN.md',
    },
  ],
};

export default data;
