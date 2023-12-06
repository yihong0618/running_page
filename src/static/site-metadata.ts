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
  siteTitle: "Tianhui's Outdoor Journey",
  siteUrl: 'https://outdoor-journey-tianhui.vercel.app/',
  logo: 'assets/logo.png',
  description: "Tianhui's Outdoor Journey",
  navLinks: [
    {
      name: 'Strava',
      url: 'https://www.strava.com/athletes/105920909',
    },
    {
      name: 'About',
      url: 'https://github.com/TianhuiXu',
    },
  ],
};

export default data;
