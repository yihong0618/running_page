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

const getBasePath = () => {
  const baseUrl = import.meta.env.BASE_URL;
  return baseUrl === '/' ? '' : baseUrl;
};

const data: ISiteMetadataResult = {
  siteTitle: 'Running Records',
  siteUrl: 'https://running.jiugoe.com',
  logo: 'https://www.jiugoe.com/wp-content/uploads/2023/12/images.png',
  description: 'Just running',
  navLinks: [
    {
      name: 'Home',
      url: 'https://running.jiugoe.com/',
    },
    {
      name: 'Blog',
      url: 'https://www.jiugoe.com/',
    },
    {
      name: 'Footprint',
      url: 'https://www.jiugoe.com/footprint',
    },
  ],
};

export default data;
