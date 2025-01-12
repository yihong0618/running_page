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
  siteUrl: 'https://gthjtjj.github.io/snail_running_page/',
  logo: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQTtc69JxHNcmN1ETpMUX4dozAgAN6iPjWalQ&usqp=CAU',
  description: 'Personal site and blog',
  navLinks: [
    {
      name: '小红书',
      url: 'https://www.xiaohongshu.com/user/profile/5b3b2a25f7e8b91a5561c4d8?xsec_token=YBSTvVlqAmEu-lZkFUYfEPD_uU0v6VaJExdJbT6KrdaxM=&xsec_source=app_share&xhsshare=CopyLink&appuid=5b3b2a25f7e8b91a5561c4d8&apptime=1736653918&share_id=245e0b668f664cfa9aa2831d59e0ebd7',
    },
    {
      name: 'About',
      url: 'https://github.com/yihong0618/running_page/blob/master/README-CN.md',
    },
  ],
};

export default data;
