interface ISiteMetadataResult {
  siteTitle: string;
  siteUrl: string;
  description: string;
  logo: string;
  repoUrl: string | undefined;
  
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
  siteTitle: 'Sports Page',
  siteUrl: 'https://sports-page.lczhuigz.cn',
  logo: 'https://blog.lczhuigz.cn/images/fav-icon/fav-icon.jpg',
  description: 'Personal site and blog',
  repoUrl: 'https://github.com/lczhuigz/running_page',
  
  navLinks: [
    {
      name: 'Blog',
      url: 'https://blog.lczhuigz.cn',
    },
    {
      name: 'About',
      url: 'https://blog.lczhuigz.cn/about',
    },
  ],
};

export default data;
