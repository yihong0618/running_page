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
  siteTitle: "Echo's Running Page",
  siteUrl: 'https://donghao526.github.io/running/',
  logo: 'https://media.istockphoto.com/id/1158723576/vector/running-man-icon-sign-flat.jpg?s=612x612&w=0&k=20&c=Nfj6k5NvsAdx9nS5JeqrK_tkpVvJ1pDHZfe7mqSvMOU=',
  description: 'Personal site and blog',
  navLinks: [
    {
      name: 'Summary',
      url: `${getBasePath()}/summary`,
    },
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