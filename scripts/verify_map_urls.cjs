#!/usr/bin/env node

/**
 * Verify that all map tile URLs are accessible
 * Run with: node scripts/verify_map_urls.js
 */

const https = require('https');
const http = require('http');

const MAP_TILE_STYLES = {
  mapcn: {
    'osm-bright': 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json',
    'osm-liberty': 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
    'dark-matter': 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
  },
  mapcn_openfreemap: {
    'osm-bright': 'https://tiles.openfreemap.org/styles/bright',
    'dark-matter': 'https://tiles.openfreemap.org/styles/dark',
  },
};

function checkUrl(url) {
  return new Promise((resolve) => {
    const protocol = url.startsWith('https') ? https : http;

    const req = protocol.get(url, { timeout: 5000 }, (res) => {
      const success = res.statusCode >= 200 && res.statusCode < 400;
      resolve({
        url,
        status: res.statusCode,
        success,
        message: success ? '✅ OK' : `❌ Failed (${res.statusCode})`,
      });
    });

    req.on('error', (err) => {
      resolve({
        url,
        status: 0,
        success: false,
        message: `❌ Error: ${err.message}`,
      });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({
        url,
        status: 0,
        success: false,
        message: '❌ Timeout (>5s)',
      });
    });
  });
}

async function verifyAllUrls() {
  console.log('🔍 Verifying Map Tile URLs...\n');

  let allSuccess = true;

  for (const [vendor, styles] of Object.entries(MAP_TILE_STYLES)) {
    console.log(`\n📦 Vendor: ${vendor}`);

    for (const [styleName, url] of Object.entries(styles)) {
      const result = await checkUrl(url);
      console.log(`  ${styleName}: ${result.message}`);

      if (!result.success) {
        allSuccess = false;
        console.log(`     URL: ${result.url}`);
      }
    }
  }

  console.log('\n' + '='.repeat(50));
  if (allSuccess) {
    console.log('✅ All map tile URLs are accessible!');
    process.exit(0);
  } else {
    console.log('❌ Some URLs failed verification');
    console.log('💡 Check your network connection or firewall');
    process.exit(1);
  }
}

verifyAllUrls();
