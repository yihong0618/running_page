interface ISiteMetadataResult {
  siteTitle: string;
  siteUrl: string;
  description: string;
  keywords: string;
  logo: string;
  navLinks: {
    name: string;
    url: string;
  }[];
}

const data: ISiteMetadataResult = {
  siteTitle: 'Daniel Yu的跑步地图',
  siteUrl: 'https://danielyu316.github.io/running_page/',
  logo: 'https://himg.bdimg.com/sys/portrait/item/pp.1.3668f5f3.hau1M2vJz1JAREz-mN-lyQ.jpg',
  description: 'Personal site and blog',
  keywords: 'workouts, running, fitness',
  navLinks: [
    // {
    //   name: 'Blog',
    //   url: 'https://ben29.xyz',
    // },
    // {
    //   name: 'About',
    //   url: 'https://github.com/ben-29/workouts_page/blob/master/README-CN.md',
    // },
  ],
};

export default data;
