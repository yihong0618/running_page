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
  siteUrl: 'https://run.licardo.cn/',
  logo: 'https://ghproxy.com/https://raw.githubusercontent.com/L1cardo/l1cardo.github.io/blog/themes/butterfly/source/img/avatar.png',
  description: '我的跑步页',
  navLinks: [
    {
      name: '博客',
      url: 'https://blog.licardo.cn',
    },
    {
      name: '关于',
      url: 'https://blog.licardo.cn/about',
    },
  ],
};

export default data;
