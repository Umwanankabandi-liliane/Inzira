/* Rwanda administrative map — districts with opportunity counts */
const RwandaMap = (() => {
  const PROVINCE_OF = {
    Musanze: 'Northern', Burera: 'Northern', Gakenke: 'Northern', Rulindo: 'Northern', Gicumbi: 'Northern',
    Rubavu: 'Western', Nyabihu: 'Western', Rutsiro: 'Western', Ngororero: 'Western', Rusizi: 'Western', Karongi: 'Western',
    Huye: 'Southern', Gisagara: 'Southern', Nyamagabe: 'Southern', Nyanza: 'Southern', Nyaruguru: 'Southern',
    Ruhango: 'Southern', Kamonyi: 'Southern', Muhanga: 'Southern',
    Nyagatare: 'Eastern', Gatsibo: 'Eastern', Kayonza: 'Eastern', Rwamagana: 'Eastern', Bugesera: 'Eastern', Kirehe: 'Eastern', Ngoma: 'Eastern',
    Gasabo: 'Kigali', Kicukiro: 'Kigali', Nyarugenge: 'Kigali',
  };

  const PROVINCE_BASE = {
    Northern: '#d4edda',
    Western: '#cce5e5',
    Southern: '#fde8d4',
    Eastern: '#fff3cd',
    Kigali: '#f8d7e8',
  };

  const HEAT = {
    very_low: '#f4f4f5',
    low: '#fef9c3',
    medium: '#fde047',
    high: '#f5c518',
    very_high: '#ca8a04',
  };

  let geoCache = null;
  let geoPromise = null;

  function loadGeo() {
    if (geoCache) return Promise.resolve(geoCache);
    if (!geoPromise) {
      geoPromise = fetch('/assets/data/rwanda-districts-simple.geojson')
        .then((r) => r.json())
        .then((data) => { geoCache = data; return data; })
        .catch(() => ({ type: 'FeatureCollection', features: [] }));
    }
    return geoPromise;
  }

  function eachCoord(geom, fn) {
    const t = geom.type;
    if (t === 'Polygon') geom.coordinates.forEach((ring) => ring.forEach(fn));
    else if (t === 'MultiPolygon') geom.coordinates.forEach((poly) => poly.forEach((ring) => ring.forEach(fn)));
  }

  function boundsOf(features) {
    let minLon = Infinity; let maxLon = -Infinity; let minLat = Infinity; let maxLat = -Infinity;
    features.forEach((f) => {
      eachCoord(f.geometry, ([lon, lat]) => {
        if (lon < minLon) minLon = lon;
        if (lon > maxLon) maxLon = lon;
        if (lat < minLat) minLat = lat;
        if (lat > maxLat) maxLat = lat;
      });
    });
    const padLon = (maxLon - minLon) * 0.03;
    const padLat = (maxLat - minLat) * 0.03;
    return { minLon: minLon - padLon, maxLon: maxLon + padLon, minLat: minLat - padLat, maxLat: maxLat + padLat };
  }

  function centroidOf(geom) {
    let sumLon = 0;
    let sumLat = 0;
    let n = 0;
    eachCoord(geom, ([lon, lat]) => {
      sumLon += lon;
      sumLat += lat;
      n += 1;
    });
    return n ? [sumLon / n, sumLat / n] : [0, 0];
  }

  function ringPath(ring, b, w, h) {
    const sx = (lon) => ((lon - b.minLon) / (b.maxLon - b.minLon)) * w;
    const sy = (lat) => ((b.maxLat - lat) / (b.maxLat - b.minLat)) * h;
    if (!ring.length) return '';
    let d = `M${sx(ring[0][0])},${sy(ring[0][1])}`;
    for (let i = 1; i < ring.length; i++) d += `L${sx(ring[i][0])},${sy(ring[i][1])}`;
    return `${d}Z`;
  }

  function geomPaths(geom, b, w, h) {
    if (geom.type === 'Polygon') return geom.coordinates.map((ring) => ringPath(ring, b, w, h));
    if (geom.type === 'MultiPolygon') {
      const paths = [];
      geom.coordinates.forEach((poly) => poly.forEach((ring) => paths.push(ringPath(ring, b, w, h))));
      return paths;
    }
    return [];
  }

  function project(lon, lat, b, w, h) {
    const x = ((lon - b.minLon) / (b.maxLon - b.minLon)) * w;
    const y = ((b.maxLat - lat) / (b.maxLat - b.minLat)) * h;
    return [x, y];
  }

  const GAP_HEAT = {
    critical: '#fca5a5',
    high_demand: '#fdba74',
    moderate_gap: '#fde047',
    balanced: '#fef08a',
    well_served: '#86efac',
  };

  function gapLevelFor(name, radarList) {
    const row = (radarList || []).find((d) => d.district === name);
    return row?.gap_level || 'balanced';
  }

  function levelFor(name, radarList) {
    const row = (radarList || []).find((d) => d.district === name);
    return row?.level || 'very_low';
  }

  function countFor(name, radarList) {
    const row = (radarList || []).find((d) => d.district === name);
    return row?.total ?? 0;
  }

  function fillFor(name, radarList, gapMode) {
    if (gapMode && radarList?.length) {
      return GAP_HEAT[gapLevelFor(name, radarList)] || GAP_HEAT.balanced;
    }
    const level = levelFor(name, radarList);
    if (radarList?.length) return HEAT[level] || HEAT.very_low;
    const prov = PROVINCE_OF[name] || 'Eastern';
    return PROVINCE_BASE[prov] || '#f4f4f5';
  }

  async function mount(host, opts = {}) {
    if (!host) return;
    host.innerHTML = '<div class="rwanda-map-loading">Loading map…</div>';
    const geo = await loadGeo();
    const features = geo.features || [];
    if (!features.length) {
      host.innerHTML = '<div class="rwanda-map-loading">Map unavailable</div>';
      return;
    }

    const gapMode = !!opts.gapMode;
    const radar = opts.radar || [];
    const selected = opts.selected || '';
    const onSelect = typeof opts.onSelect === 'function' ? opts.onSelect : () => {};
    const showLabels = opts.showLabels !== false;

    const b = boundsOf(features);
    const lonSpan = b.maxLon - b.minLon;
    const latSpan = b.maxLat - b.minLat;
    const W = 420;
    const H = Math.round(W * (latSpan / lonSpan));

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.setAttribute('class', 'rwanda-map-svg');
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', 'Rwanda districts map with opportunity counts');

    const country = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    country.setAttribute('class', 'rwanda-map-districts');

    const labels = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    labels.setAttribute('class', 'rwanda-map-labels');

    features.forEach((feat) => {
      const name = feat.properties?.name;
      if (!name) return;
      const paths = geomPaths(feat.geometry, b, W, H);
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.dataset.district = name;

      paths.forEach((d) => {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', d);
        path.setAttribute('class', `rwanda-district level-${levelFor(name, radar)}${name === selected ? ' selected' : ''}`);
        path.setAttribute('fill', fillFor(name, radar, gapMode));
        path.setAttribute('stroke', '#ffffff');
        path.setAttribute('stroke-width', '0.55');
        path.setAttribute('vector-effect', 'non-scaling-stroke');
        path.dataset.district = name;
        path.setAttribute('aria-label', `${name}: ${countFor(name, radar)} opportunities`);
        const click = () => onSelect(name);
        path.addEventListener('click', click);
        path.style.cursor = 'pointer';
        g.appendChild(path);
      });

      if (name === selected) {
        paths.forEach((d) => {
          const outline = document.createElementNS('http://www.w3.org/2000/svg', 'path');
          outline.setAttribute('d', d);
          outline.setAttribute('fill', 'none');
          outline.setAttribute('stroke', '#0a0a0a');
          outline.setAttribute('stroke-width', '1.6');
          outline.setAttribute('vector-effect', 'non-scaling-stroke');
          outline.setAttribute('pointer-events', 'none');
          g.appendChild(outline);
        });
      }

      country.appendChild(g);

      if (showLabels) {
        const [lon, lat] = centroidOf(feat.geometry);
        const [cx, cy] = project(lon, lat, b, W, H);
        const total = countFor(name, radar);
        const isSmall = ['Gasabo', 'Kicukiro', 'Nyarugenge'].includes(name);
        const labelG = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        labelG.setAttribute('class', `rwanda-district-label${isSmall ? ' rwanda-district-label--sm' : ''}`);
        labelG.setAttribute('pointer-events', 'none');

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', cx);
        circle.setAttribute('cy', cy);
        circle.setAttribute('r', isSmall ? 7 : 9);
        circle.setAttribute('class', 'rwanda-district-label__bg');

        const countText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        countText.setAttribute('x', cx);
        countText.setAttribute('y', cy + (isSmall ? 3 : 3.5));
        countText.setAttribute('text-anchor', 'middle');
        countText.setAttribute('class', 'rwanda-district-label__count');
        countText.textContent = String(total);

        labelG.appendChild(circle);
        labelG.appendChild(countText);

        if (!isSmall) {
          const nameText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          nameText.setAttribute('x', cx);
          nameText.setAttribute('y', cy + 16);
          nameText.setAttribute('text-anchor', 'middle');
          nameText.setAttribute('class', 'rwanda-district-label__name');
          const short = name.length > 9 ? `${name.slice(0, 8)}…` : name;
          nameText.textContent = short;
          labelG.appendChild(nameText);
        }

        labels.appendChild(labelG);
      }
    });

    svg.appendChild(country);
    svg.appendChild(labels);
    host.innerHTML = '';
    host.appendChild(svg);
  }

  return { mount, loadGeo, PROVINCE_OF };
})();
