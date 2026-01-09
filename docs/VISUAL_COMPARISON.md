# Visual Comparison: Mapbox vs MapCN

## Overview

This document helps you understand the visual differences between Mapbox and MapCN (Carto Basemaps).

## Map Styles

### Light Theme

**Mapbox (`light-v10`):**
- Cool gray color palette
- Bright blue water
- High contrast labels
- Modern, sleek appearance
- Proprietary Mapbox styling

**MapCN/Carto (`osm-bright`):**
- Warm tan/beige color palette
- Blue-green water
- Standard OpenStreetMap labels
- Clean, natural appearance
- OSM-based styling

### Dark Theme

**Mapbox (`dark-v10`):**
- Charcoal gray background
- Subtle blue water
- White labels
- Professional, corporate feel

**MapCN/Carto (`dark-matter`):**
- Deep blue-gray background
- Darker water
- Light gray labels
- Elegant, modern feel

## Running Route Visibility

**Both providers:**
- ✅ Excellent route visibility
- ✅ Clear polyline rendering
- ✅ Good contrast against background
- ✅ Supports custom route colors

**The most important aspect (route visualization) works equally well on both!**

## Feature Comparison

| Feature | Mapbox | MapCN (Carto) |
| :--- | :--- | :--- |
| **Vector Tiles** | ✅ Yes | ✅ Yes |
| **Zoom Levels** | 0-22 | 0-20 |
| **Label Quality** | Excellent | Very Good |
| **Typography** | Custom fonts | Standard fonts |
| **Color Palette** | Proprietary | OSM-standard |
| **3D Buildings** | ✅ Yes | ⚠️ Limited |
| **Terrain** | ✅ Yes | ❌ No |
| **Route Clarity** | ✅ Excellent | ✅ Excellent |

## What Matters for Running Page

For a running visualization app, the key requirements are:
1. ✅ **Route visibility** - Both providers: Excellent
2. ✅ **Performance** - Both providers: Fast
3. ✅ **Light/dark themes** - Both providers: Supported
4. ✅ **Geographic accuracy** - Both providers: Equal (OSM data)
5. ✅ **Labels** - Both providers: Clear

**Conclusion:** MapCN is an excellent choice for running_page use case.

## Subjective Assessment

**Mapbox** - 9/10
- Slightly more polished
- Better for professional/commercial apps
- Costs money

**MapCN (Carto)** - 8/10
- Very clean and professional
- Perfect for personal/open-source
- Free!

**For running_page users:** MapCN is a fantastic free alternative that doesn't compromise the core visualization experience.

## Screenshots

*Note: Add actual screenshots when testing:*
- [ ] Light theme with routes (Mapbox)
- [ ] Light theme with routes (MapCN)
- [ ] Dark theme with routes (Mapbox)
- [ ] Dark theme with routes (MapCN)

## User Feedback

*Collect feedback from community:*
- Visual quality ratings
- Performance comparisons
- Regional accessibility
- Personal preferences
