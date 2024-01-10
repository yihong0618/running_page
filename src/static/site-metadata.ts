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
  siteUrl: 'https://run.miao.li',
  logo: 'https://cravatar.cn/avatar/c9352db5fa7f6da0f4ef3c5f9d64159c',
  description: 'Personal site and blog',
  navLinks: [
    {
      name: 'Blog',
      url: 'https://lizhimiao.com',
    },
    {
      name: 'About',
      url: 'https://miao.li/about.html',
    },
  ],
};

export default data;
