import { SITE_METADATA } from '../../../core/config';

// Classic theme adds a Summary link that dashboard doesn't need
const classicSiteMetadata = {
  ...SITE_METADATA,
  navLinks: [
    {
      name: 'Summary',
      url: '/summary',
    },
    ...SITE_METADATA.navLinks,
  ],
};

export default classicSiteMetadata;
