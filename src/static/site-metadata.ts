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
  siteTitle: 'Running Records',
  siteUrl: 'https://running.danilelxp.com',
  logo: 'https://www.danilelxp.com/wp-content/uploads/2023/12/images.png',
  description: 'Just running',
  navLinks: [
    {
      name: 'Home',
      url: 'https://running.danilelxp.com/',
    },
    {
      name: 'Blog',
      url: 'https://www.jiugoe.com/',
    },
    {
      name: 'Travel',
      url: 'https://www.jiugoe.com/about',
    },
  ],
};

export default data;
