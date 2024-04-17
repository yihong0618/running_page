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
  siteTitle: 'Cigar\'s Running Page',
  siteUrl: 'https://running.cigar.design',
  logo: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQTtc69JxHNcmN1ETpMUX4dozAgAN6iPjWalQ&usqp=CAU',
  description: 'Cigar\'s personal site and blog',
  navLinks: [
    {
      name: 'Home',
      url: 'https://cigar.design',
    },
    {
      name: 'Photos',
      url: 'https://lens.cigar.design',
    },
    {
      name: 'About',
      url: 'https://https://cigar.design/about/',
    },
  ],
};

export default data;
