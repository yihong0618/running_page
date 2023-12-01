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
  siteUrl: 'https://running.danilelxp.com',
  logo: 'https://www.danilelxp.com/wp-content/uploads/2023/12/images.png',
  description: 'Just running',
  navLinks: [
    {
      name: 'Blog',
      url: 'https://danilelxp.com/',
    },
  ],
};

export default data;
