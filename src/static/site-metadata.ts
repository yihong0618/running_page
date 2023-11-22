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
  siteUrl: 'https://run.xmylog.com',
  logo: 'https://s1.ax1x.com/2023/09/03/pPDnMZR.jpg',
  description: '离开乏味的皮囊,自由的灵魂在路上',
  navLinks: [
    {
      name: 'Blog',
      url: 'https://www.xmylog.com',
    },
    {
      name: 'About',
      url: 'https://www.xmylog.com/about',
    },
  ],
};

export default data;
