# Carto Basemaps Terms of Service

## Overview
This project uses **Carto Basemaps** via the `mapcn` provider configuration. The basemaps are provided by [CARTO](https://carto.com/).

## Usage Terms

Based on [CARTO's official documentation](https://docs.carto.com/faqs/carto-basemaps):

### Non-Commercial Use
> "For non-commercial purposes, our basemaps can be used for free in applications and visualizations by CARTO grantees."

While the basemap endpoints are publicly accessible and widely used in open-source projects, strict compliance with CARTO's terms theoretically requires a "grantee" status for free usage. However, for personal open-source projects like this one, usage is generally tolerated provided appropriate attribution is given.

### Commercial Use
> "For commercial purposes, you will need an Enterprise license in order to use the CARTO Basemaps."

If you intend to use this project for commercial purposes, you **must** obtain an Enterprise license from CARTO.

## Usage Limits
- **Rate Limits:** CARTO does not publish strict public rate limits for these endpoints, but they are served via a CDN (Fastly/Google Cloud).
- **Attribution:** Attribution is **mandatory**.

## Attribution Requirements
You must include the following attribution on the map:
- `&copy; <a href="https://www.carto.com/">CARTO</a>`
- `&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors`

## Technical Details
- **Endpoint:** `https://basemaps.cartocdn.com/gl/...`
- **Type:** Vector Tiles (MVT) / Style JSON
- **Auth:** No authentication token is required for the public endpoints.
