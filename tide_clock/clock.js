/**
 * TideClock — single-file widget showing current time (analog face), sunrise/sunset,
 * and high/low tide predictions for a configured (or browser-detected) location.
 *
 * Usage:
 *   const clock = new TideClock({ configUrl: 'settings.json', container: 'clock' });
 *   await clock.init();
 *   clock.setDate('2026-07-04'); // recompute sun/tide sections for another date
 *
 * Settings JSON shape:
 *   {
 *     "location": { "lat": 40.7, "lon": -74.0, "name": "My Marina" },
 *     "timeZone": "America/New_York",
 *     "tideStationId": "8518750",   // optional; nearest NOAA station is used if omitted
 *     "events": []                   // reserved for a future version, ignored today
 *   }
 *
 * Must be served over http(s), not opened as a file:// URL, since it fetches
 * the settings JSON and the NOAA tide API.
 */
(function (global) {
  'use strict';

  const NOAA_STATIONS_URL =
    'https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json?type=tidepredictions';
  const NOAA_PREDICTIONS_URL = 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter';

  const DEG2RAD = Math.PI / 180;
  const DAY_MS = 1000 * 60 * 60 * 24;
  const J1970 = 2440588;
  const J2000 = 2451545;
  const OBLIQUITY = DEG2RAD * 23.4397;

  // ---- Low-precision solar position math (public-domain astronomical formulas) ----
  // Accurate to roughly a minute, which is plenty for a display widget.

  function toJulian(date) {
    return date.valueOf() / DAY_MS - 0.5 + J1970;
  }

  function fromJulian(j) {
    return new Date((j - J1970 + 0.5) * DAY_MS);
  }

  function toDays(date) {
    return toJulian(date) - J2000;
  }

  function solarMeanAnomaly(d) {
    return DEG2RAD * (357.5291 + 0.98560028 * d);
  }

  function eclipticLongitude(M) {
    const C = DEG2RAD * (1.9148 * Math.sin(M) + 0.02 * Math.sin(2 * M) + 0.0003 * Math.sin(3 * M));
    const P = DEG2RAD * 102.9372;
    return M + C + P + Math.PI;
  }

  function declination(l, b) {
    return Math.asin(Math.sin(b) * Math.cos(OBLIQUITY) + Math.cos(b) * Math.sin(OBLIQUITY) * Math.sin(l));
  }

  function solarTransitJ(ds, M, L) {
    return J2000 + ds + 0.0053 * Math.sin(M) - 0.0069 * Math.sin(2 * L);
  }

  function hourAngle(h, phi, d) {
    return Math.acos((Math.sin(h) - Math.sin(phi) * Math.sin(d)) / (Math.cos(phi) * Math.cos(d)));
  }

  /** Returns { sunrise, sunset } as UTC Date instants for the given day/location. */
  function getSunTimes(date, lat, lon) {
    const lw = DEG2RAD * -lon;
    const phi = DEG2RAD * lat;
    const d = toDays(date);
    const n = Math.round(d - 0.0009 - lw / (2 * Math.PI));
    const ds = 0.0009 + lw / (2 * Math.PI) + n;
    const M = solarMeanAnomaly(ds);
    const L = eclipticLongitude(M);
    const dec = declination(L, 0);
    const Jnoon = solarTransitJ(ds, M, L);

    const h0 = DEG2RAD * -0.833; // accounts for atmospheric refraction + sun's radius
    const w0 = hourAngle(h0, phi, dec);
    if (Number.isNaN(w0)) {
      throw new Error('sun does not rise or set at this location on this date');
    }
    const a = 0.0009 + (w0 + lw) / (2 * Math.PI) + n;
    const Jset = solarTransitJ(a, M, L);
    const Jrise = Jnoon - (Jset - Jnoon);

    return { sunrise: fromJulian(Jrise), sunset: fromJulian(Jset) };
  }

  // ---- Formatting helpers ----

  function isoDateInTz(date, timeZone) {
    return new Intl.DateTimeFormat('en-CA', {
      timeZone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(date);
  }

  function formatClockTime(date, timeZone) {
    return new Intl.DateTimeFormat('en-US', {
      timeZone,
      hour: 'numeric',
      minute: '2-digit',
    }).format(date);
  }

  /** Compact "5:45a" style label used on the analog face, where space is tight. */
  function formatCompactHM(hour24, minute) {
    const h12 = hour24 % 12 === 0 ? 12 : hour24 % 12;
    const mm = String(minute).padStart(2, '0');
    const suffix = hour24 < 12 ? 'a' : 'p';
    return `${h12}:${mm}${suffix}`;
  }

  /** NOAA times already come back as local "HH:MM" strings — no time zone conversion needed. */
  function fractionFromTimeStr(hhmm) {
    const [h, m] = hhmm.split(':').map(Number);
    return fraction12(h, m);
  }

  // ---- Analog clock geometry helpers ----

  const SVG_NS = 'http://www.w3.org/2000/svg';
  const CLOCK_CX = 170;
  const CLOCK_CY = 170;
  const CLOCK_R = 85;
  const CLOCK_HOUR_LEN = 48;
  const CLOCK_MINUTE_LEN = 72;
  const SUN_MOON_ICON_R = 100;
  const SUN_MOON_LABEL_R = 116;

  function svgEl(tag, attrs) {
    const el = document.createElementNS(SVG_NS, tag);
    for (const key in attrs) el.setAttribute(key, attrs[key]);
    return el;
  }

  /** Local hour (0-23) and minute for a Date instant in a given IANA time zone. */
  function getLocalHM(date, timeZone) {
    const parts = new Intl.DateTimeFormat('en-US', {
      timeZone,
      hourCycle: 'h23',
      hour: '2-digit',
      minute: '2-digit',
    }).formatToParts(date);
    let hour = 0;
    let minute = 0;
    for (const p of parts) {
      if (p.type === 'hour') hour = parseInt(p.value, 10);
      if (p.type === 'minute') minute = parseInt(p.value, 10);
    }
    return { hour, minute };
  }

  /** Position on a traditional 12-hour dial, as a fraction of a full turn (0 = 12 o'clock). */
  function fraction12(hour24, minute) {
    const h12 = hour24 % 12;
    return (h12 + minute / 60) / 12;
  }

  /** Point on a circle of radius r centered at (cx, cy), fraction 0 = top, increasing clockwise. */
  function pointOnCircle(cx, cy, r, fraction) {
    const theta = -Math.PI / 2 + fraction * 2 * Math.PI;
    return { x: cx + r * Math.cos(theta), y: cy + r * Math.sin(theta) };
  }

  function positionAt(el, r, fraction) {
    const p = pointOnCircle(CLOCK_CX, CLOCK_CY, r, fraction);
    el.setAttribute('x', p.x);
    el.setAttribute('y', p.y);
  }

  /** SVG path for the pie wedge swept clockwise from startFraction to endFraction. */
  function wedgePath(cx, cy, r, startFraction, endFraction) {
    let span = endFraction - startFraction;
    if (span < 0) span += 1;
    if (span <= 0) return '';
    const p1 = pointOnCircle(cx, cy, r, startFraction);
    const p2 = pointOnCircle(cx, cy, r, endFraction);
    const largeArc = span > 0.5 ? 1 : 0;
    return `M ${cx} ${cy} L ${p1.x} ${p1.y} A ${r} ${r} 0 ${largeArc} 1 ${p2.x} ${p2.y} Z`;
  }

  /** A plain radial hand reaching the face perimeter for one tide event — thick for high, thin for low. */
  function buildTideHandLine(fraction, type) {
    const p = pointOnCircle(CLOCK_CX, CLOCK_CY, CLOCK_R, fraction);
    return svgEl('line', {
      x1: CLOCK_CX,
      y1: CLOCK_CY,
      x2: p.x,
      y2: p.y,
      class: 'tideclock-tide-hand tideclock-tide-hand-' + (type === 'H' ? 'high' : 'low'),
    });
  }

  /** Builds the static SVG markup for the analog face and returns refs to its dynamic parts. */
  function buildAnalogFace() {
    const svg = svgEl('svg', { viewBox: '0 0 340 340', class: 'tideclock-analog-svg' });

    svg.appendChild(svgEl('circle', { cx: CLOCK_CX, cy: CLOCK_CY, r: CLOCK_R, class: 'tideclock-face' }));

    const wedge = svgEl('path', { class: 'tideclock-wedge', d: '' });
    svg.appendChild(wedge);

    svg.appendChild(svgEl('circle', { cx: CLOCK_CX, cy: CLOCK_CY, r: CLOCK_R, class: 'tideclock-rim' }));

    for (let i = 0; i < 12; i++) {
      const frac = i / 12;
      const outer = pointOnCircle(CLOCK_CX, CLOCK_CY, CLOCK_R, frac);
      const inner = pointOnCircle(CLOCK_CX, CLOCK_CY, CLOCK_R - 8, frac);
      svg.appendChild(
        svgEl('line', { x1: inner.x, y1: inner.y, x2: outer.x, y2: outer.y, class: 'tideclock-tick' })
      );
    }

    const numerals = { 0: '12', 0.25: '3', 0.5: '6', 0.75: '9' };
    Object.keys(numerals).forEach((frac) => {
      const p = pointOnCircle(CLOCK_CX, CLOCK_CY, CLOCK_R - 20, parseFloat(frac));
      const text = svgEl('text', {
        x: p.x,
        y: p.y,
        class: 'tideclock-numeral',
        'text-anchor': 'middle',
        'dominant-baseline': 'central',
      });
      text.textContent = numerals[frac];
      svg.appendChild(text);
    });

    // Tide hands sit below the sun/moon icons and the time hands so they never obscure them.
    const tideMarkersGroup = svgEl('g', { class: 'tideclock-tide-hand-group' });
    svg.appendChild(tideMarkersGroup);

    const sunriseIcon = svgEl('text', {
      class: 'tideclock-sunmoon-icon',
      'text-anchor': 'middle',
      'dominant-baseline': 'central',
    });
    sunriseIcon.textContent = '☀️';
    const sunriseLabel = svgEl('text', {
      class: 'tideclock-sunmoon-label',
      'text-anchor': 'middle',
      'dominant-baseline': 'central',
    });
    const sunsetIcon = svgEl('text', {
      class: 'tideclock-sunmoon-icon',
      'text-anchor': 'middle',
      'dominant-baseline': 'central',
    });
    sunsetIcon.textContent = '🌙';
    const sunsetLabel = svgEl('text', {
      class: 'tideclock-sunmoon-label',
      'text-anchor': 'middle',
      'dominant-baseline': 'central',
    });
    svg.appendChild(sunriseIcon);
    svg.appendChild(sunriseLabel);
    svg.appendChild(sunsetIcon);
    svg.appendChild(sunsetLabel);

    const hourHand = svgEl('line', { class: 'tideclock-hand tideclock-hand-hour', x1: CLOCK_CX, y1: CLOCK_CY });
    const minuteHand = svgEl('line', {
      class: 'tideclock-hand tideclock-hand-minute',
      x1: CLOCK_CX,
      y1: CLOCK_CY,
    });
    svg.appendChild(hourHand);
    svg.appendChild(minuteHand);

    svg.appendChild(svgEl('circle', { cx: CLOCK_CX, cy: CLOCK_CY, r: 4, class: 'tideclock-hub' }));

    return {
      svg,
      wedge,
      sunriseIcon,
      sunriseLabel,
      sunsetIcon,
      sunsetLabel,
      tideMarkersGroup,
      hourHand,
      minuteHand,
    };
  }

  // ---- Geo helpers ----

  function haversineKm(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = DEG2RAD * (lat2 - lat1);
    const dLon = DEG2RAD * (lon2 - lon1);
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(DEG2RAD * lat1) * Math.cos(DEG2RAD * lat2) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(a));
  }

  let stationListPromise = null;

  async function findNearestStation(lat, lon) {
    if (!stationListPromise) {
      stationListPromise = fetch(NOAA_STATIONS_URL)
        .then((res) => {
          if (!res.ok) throw new Error('HTTP ' + res.status);
          return res.json();
        })
        .then((data) => data.stations || []);
    }
    const stations = await stationListPromise;
    if (!stations.length) throw new Error('NOAA station list was empty');

    let best = null;
    let bestDist = Infinity;
    for (const s of stations) {
      const dist = haversineKm(lat, lon, s.lat, s.lng);
      if (dist < bestDist) {
        bestDist = dist;
        best = s;
      }
    }
    if (!best) throw new Error('no NOAA tide station found');
    return best.id;
  }

  async function fetchTidePredictions(isoDate, stationId) {
    const ymd = isoDate.replace(/-/g, '');
    const params = new URLSearchParams({
      product: 'predictions',
      datum: 'MLLW',
      station: stationId,
      begin_date: ymd,
      end_date: ymd,
      time_zone: 'lst_ldt',
      units: 'english',
      interval: 'hilo',
      format: 'json',
      application: 'nsyc-clocks',
    });
    const res = await fetch(NOAA_PREDICTIONS_URL + '?' + params.toString());
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    if (data.error) throw new Error(data.error.message || 'NOAA API error');
    const predictions = data.predictions || [];
    return predictions.map((p) => ({
      time: (p.t || '').split(' ')[1] || p.t,
      type: p.type,
      heightFt: parseFloat(p.v),
    }));
  }

  function configFromBrowser() {
    return new Promise((resolve, reject) => {
      if (!('geolocation' in navigator)) {
        reject(new Error('geolocation not available in this browser'));
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          resolve({
            location: {
              lat: pos.coords.latitude,
              lon: pos.coords.longitude,
              name: 'Current location',
            },
            timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            events: [],
          });
        },
        (err) => reject(new Error(err.message)),
        { timeout: 10000 }
      );
    });
  }

  async function loadConfig(configUrl) {
    const res = await fetch(configUrl, { cache: 'no-store' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const json = await res.json();
    if (!json.location || typeof json.location.lat !== 'number' || typeof json.location.lon !== 'number') {
      throw new Error('settings JSON is missing location.lat/location.lon');
    }
    if (!json.timeZone) throw new Error('settings JSON is missing timeZone');
    return json;
  }

  // ---- TideClock widget ----

  class TideClock {
    constructor({ configUrl, container }) {
      this.configUrl = configUrl;
      this.container = typeof container === 'string' ? document.getElementById(container) : container;
      if (!this.container) throw new Error('TideClock: container element not found');
      this.config = null;
      this.selectedDate = null;
      this._clockTimer = null;
      this._sunTimes = null;
      this._buildDom();
    }

    async init() {
      this._setStatus('Loading configuration…');
      try {
        this.config = await loadConfig(this.configUrl);
      } catch (err) {
        this._setStatus('Could not load settings (' + err.message + '); trying browser location…');
        try {
          this.config = await configFromBrowser();
        } catch (fallbackErr) {
          this._setStatus('Unable to determine location: ' + fallbackErr.message);
          return;
        }
      }

      this.titleEl.textContent = this.config.location.name || 'Time & Tide';

      if (!this.config.tideStationId) {
        this._setStatus('Looking up nearest NOAA tide station…');
        try {
          this.config.tideStationId = await findNearestStation(this.config.location.lat, this.config.location.lon);
        } catch (err) {
          this._setStatus('Could not find a nearby NOAA tide station: ' + err.message);
        }
      }

      this.selectedDate = isoDateInTz(new Date(), this.config.timeZone);
      this.dateInput.value = this.selectedDate;
      this._setStatus('');
      this._startClock();
      await this._refresh();
    }

    setDate(isoDateStr) {
      this.selectedDate = isoDateStr;
      this.dateInput.value = isoDateStr;
      this._refresh();
    }

    destroy() {
      if (this._clockTimer) clearTimeout(this._clockTimer);
    }

    async _refresh() {
      if (!this.config) return;
      this._renderSun();
      await this._renderTides();
    }

    _renderSun() {
      const { lat, lon } = this.config.location;
      const [y, m, d] = this.selectedDate.split('-').map(Number);
      const refInstant = new Date(Date.UTC(y, m - 1, d, 12, 0, 0));

      this.sunEl.innerHTML = '';
      try {
        const times = getSunTimes(refInstant, lat, lon);
        this._sunTimes = times;
        this.sunEl.appendChild(rowEl('Sunrise', formatClockTime(times.sunrise, this.config.timeZone)));
        this.sunEl.appendChild(rowEl('Sunset', formatClockTime(times.sunset, this.config.timeZone)));
      } catch (err) {
        this._sunTimes = null;
        this.sunEl.textContent = 'Sun times unavailable: ' + err.message;
      }
      this._renderAnalog();
    }

    async _renderTides() {
      if (!this.config.tideStationId) {
        this.tideEl.textContent = 'No tide station available for this location.';
        this._renderTideMarkers([]);
        return;
      }
      this.tideEl.textContent = 'Loading tide predictions…';
      try {
        const events = await fetchTidePredictions(this.selectedDate, this.config.tideStationId);
        this.tideEl.innerHTML = '';
        if (!events.length) {
          this.tideEl.textContent = 'No tide predictions returned for this date.';
          this._renderTideMarkers([]);
          return;
        }
        events.forEach((e) => {
          const label = (e.type === 'H' ? 'High' : 'Low') + ' tide';
          const detail = e.time + ' (' + e.heightFt.toFixed(2) + ' ft)';
          this.tideEl.appendChild(rowEl(label, detail));
        });
        this._renderTideMarkers(events);
      } catch (err) {
        this.tideEl.textContent = 'Tide predictions unavailable: ' + err.message;
        this._renderTideMarkers([]);
      }
    }

    /** Rebuilds the on-face tide hands: thick for high tide, thin for low tide, to the rim. */
    _renderTideMarkers(events) {
      if (!this._analog) return;
      this._analog.tideMarkersGroup.innerHTML = '';
      events.forEach((e) => {
        const fraction = fractionFromTimeStr(e.time);
        this._analog.tideMarkersGroup.appendChild(buildTideHandLine(fraction, e.type));
      });
    }

    _startClock() {
      const tick = () => {
        const now = new Date();
        this._renderAnalog();
        const msToNextMinute = 60000 - (now.getSeconds() * 1000 + now.getMilliseconds());
        this._clockTimer = setTimeout(tick, msToNextMinute);
      };
      tick();
    }

    /** Updates the analog face: hands (live "now"), sunrise/sunset icons, and the night wedge. */
    _renderAnalog() {
      if (!this.config || !this._analog) return;

      const now = new Date();
      const { hour, minute } = getLocalHM(now, this.config.timeZone);

      const hourP = pointOnCircle(CLOCK_CX, CLOCK_CY, CLOCK_HOUR_LEN, fraction12(hour, minute));
      const minuteP = pointOnCircle(CLOCK_CX, CLOCK_CY, CLOCK_MINUTE_LEN, minute / 60);
      this._analog.hourHand.setAttribute('x2', hourP.x);
      this._analog.hourHand.setAttribute('y2', hourP.y);
      this._analog.minuteHand.setAttribute('x2', minuteP.x);
      this._analog.minuteHand.setAttribute('y2', minuteP.y);

      if (this._sunTimes) {
        const sunriseHM = getLocalHM(this._sunTimes.sunrise, this.config.timeZone);
        const sunsetHM = getLocalHM(this._sunTimes.sunset, this.config.timeZone);
        const sunriseFraction = fraction12(sunriseHM.hour, sunriseHM.minute);
        const sunsetFraction = fraction12(sunsetHM.hour, sunsetHM.minute);

        positionAt(this._analog.sunriseIcon, SUN_MOON_ICON_R, sunriseFraction);
        positionAt(this._analog.sunriseLabel, SUN_MOON_LABEL_R, sunriseFraction);
        this._analog.sunriseLabel.textContent = formatCompactHM(sunriseHM.hour, sunriseHM.minute);
        this._analog.sunriseIcon.style.display = '';
        this._analog.sunriseLabel.style.display = '';

        positionAt(this._analog.sunsetIcon, SUN_MOON_ICON_R, sunsetFraction);
        positionAt(this._analog.sunsetLabel, SUN_MOON_LABEL_R, sunsetFraction);
        this._analog.sunsetLabel.textContent = formatCompactHM(sunsetHM.hour, sunsetHM.minute);
        this._analog.sunsetIcon.style.display = '';
        this._analog.sunsetLabel.style.display = '';

        // 00:00-11:59 -> shade midnight-to-sunrise (still dark before dawn).
        // 12:00-23:59 -> shade sunset-to-midnight (already dark after dusk).
        const wedgeD =
          hour < 12
            ? wedgePath(CLOCK_CX, CLOCK_CY, CLOCK_R, 0, sunriseFraction)
            : wedgePath(CLOCK_CX, CLOCK_CY, CLOCK_R, sunsetFraction, 1);
        this._analog.wedge.setAttribute('d', wedgeD);
      } else {
        this._analog.wedge.setAttribute('d', '');
        this._analog.sunriseIcon.style.display = 'none';
        this._analog.sunriseLabel.style.display = 'none';
        this._analog.sunsetIcon.style.display = 'none';
        this._analog.sunsetLabel.style.display = 'none';
      }
    }

    _buildDom() {
      this.container.innerHTML = '';
      this.container.classList.add('tideclock');

      this.titleEl = document.createElement('h2');
      this.titleEl.className = 'tideclock-title';
      this.container.appendChild(this.titleEl);

      this.statusEl = document.createElement('div');
      this.statusEl.className = 'tideclock-status';
      this.container.appendChild(this.statusEl);

      const controlsRow = document.createElement('div');
      controlsRow.className = 'tideclock-date-row';
      const label = document.createElement('label');
      label.textContent = 'Date: ';
      this.dateInput = document.createElement('input');
      this.dateInput.type = 'date';
      this.dateInput.addEventListener('change', () => {
        if (this.dateInput.value) this.setDate(this.dateInput.value);
      });
      label.appendChild(this.dateInput);
      controlsRow.appendChild(label);

      this.container.appendChild(controlsRow);

      this.analogViewEl = document.createElement('div');
      this.analogViewEl.className = 'tideclock-analog-view';
      this._analog = buildAnalogFace();
      this.analogViewEl.appendChild(this._analog.svg);
      this.container.appendChild(this.analogViewEl);

      // Flat data list: sunrise/sunset rows, followed by tide rows, no sub-headers.
      this.sunEl = document.createElement('div');
      this.sunEl.className = 'tideclock-sun';
      this.container.appendChild(this.sunEl);

      this.tideEl = document.createElement('div');
      this.tideEl.className = 'tideclock-tides';
      this.container.appendChild(this.tideEl);
    }

    _setStatus(msg) {
      this.statusEl.textContent = msg || '';
    }
  }

  function rowEl(label, value) {
    const row = document.createElement('div');
    row.className = 'tideclock-row';
    const l = document.createElement('span');
    l.className = 'tideclock-row-label';
    l.textContent = label + ': ';
    const v = document.createElement('span');
    v.className = 'tideclock-row-value';
    v.textContent = value;
    row.appendChild(l);
    row.appendChild(v);
    return row;
  }

  global.TideClock = TideClock;
})(window);
