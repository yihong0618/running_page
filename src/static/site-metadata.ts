import { SITE_METADATA } from '../core/config';

// Add Summary link for classic theme
const siteMetadata = {
  ...SITE_METADATA,
  navLinks: [
    {
      name: 'Summary',
      url: '/summary',
    },
    ...SITE_METADATA.navLinks,
  ],
};

export default siteMetadata;
