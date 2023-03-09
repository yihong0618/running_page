interface siteMetadata {
  siteTitle: string;
  siteUrl: string;
  logo: string;
  description: string;
  author: string;
  navLinks: NavLink[];
}
interface NavLink {
  name: string;
  url: string;
}

const siteMetadata: siteMetadata = {
  siteTitle: `Running_page`,
  siteUrl: `https://yihong.run`,
  logo: `/images/favicon.png`,
  description: `This is my awesome website!`,
  author: `John Doe`,
  navLinks: [
    {
      name: `Blog`,
      url: `https://yihong.run/running`,
    },
    {
      name: `About`,
      url: `https://github.com/yihong0618/running_page/blob/master/README-CN.md`,
    },
  ],
};

export default siteMetadata;
