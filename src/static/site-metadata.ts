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
  siteTitle: `Let's fxxking run`,
  siteUrl: 'https://www.madcodelife.com',
  logo: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQTtc69JxHNcmN1ETpMUX4dozAgAN6iPjWalQ&usqp=CAU',
  description: `Floyd Wang's running page`,
  navLinks: [
    {
      name: 'Blog',
      url: 'https://www.madcodelife.com/blog',
    },
    {
      name: 'About',
      url: 'https://www.madcodelife.com',
    },
  ],
};

export default data;
