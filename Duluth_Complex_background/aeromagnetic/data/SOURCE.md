# Minnesota aeromagnetic data provenance

- Publisher: Minnesota Geological Survey, University of Minnesota
- Compilation: 2007 statewide aeromagnetic database
- Survey dates: mainly 1979–1991, with contributing data from 1961–1991
- Source web map: `4cf7ad547c10492081697080f7ae9bf0`
- Source map service: `https://gis4.uspatial.umn.edu/arcgis/rest/services/mgs/Aeromagnetic/MapServer`
- Export extent: EPSG:3857 `-10828131.217914617,5378447.130396378,-9950692.605766904,6343886.506468261`
- Export size: 800 × 930 pixels at 96 dpi

Included service layers:

- `0` — total-field magnetic anomaly
- `5` — reduced-to-pole amplitude with tilt enhancement
- `9` — first vertical derivative
- `6` — county boundaries, overlaid on each raster export

The standalone HTML embeds the exported raster views and their official MGS
legends as data URLs, so it does not call external services at presentation
time. For display, the total-field and tilt-enhanced rainbow rasters are
recolored with Fabio Crameri's perceptually uniform `vik` diverging palette;
the original MGS exports remain alongside the derived images. The retained JSON
files record the web-map and service definitions used to build the visualization.
