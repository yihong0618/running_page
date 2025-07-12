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
  siteTitle: "Dingkun's Running Page",
  siteUrl: 'https://running.yer1k.com/',
  logo: 'https://yer1k.gitlab.io/website/images/avatar.png',
  description: 'Personal site and blog',
  navLinks: [
    {
      name: 'Summary',
      url: `${getBasePath()}/summary`,
    },
    {
      name: 'Blog',
      url: 'https://yer1k.com/',
    },
    {
      name: 'About',
      url: 'https://liveterm.yer1k.com/',
    },
  ],
};

export default data;
