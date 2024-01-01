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
  siteTitle: 'Echos Running Page',
  siteUrl: 'https://donghao526.github.io/running/',
  logo: 'https://cdn-icons-png.flaticon.com/512/4721/4721050.png',
  description: 'Personal site and blog',
  navLinks: [
    {
      name: 'Blog',
      url: 'https://donghao526.github.io/',
    },
    {
      name: 'About',
      url: 'https://github.com/donghao526',
    },
  ],
};

export default data;
