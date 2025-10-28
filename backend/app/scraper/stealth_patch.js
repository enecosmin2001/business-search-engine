// stealth_patch.js
// Injected into each new document to reduce fingerprinting and headless detection.
// Keep this file alongside your Python code and load it with add_script_to_evaluate_on_new_document.
//
// NOTE: This attempts to be defensive; avoid making it more aggressive than needed
// so you don't accidentally change page behavior in subtle ways.

(function () {
  'use strict';

  // Helpers
  const safeDefine = (obj, prop, value, configurable = true) => {
    try {
      Object.defineProperty(obj, prop, { get: () => value, configurable });
    } catch (e) {
      // ignore
    }
  };

  // --- navigator properties ---
  try {
    safeDefine(navigator, 'languages', ['en-US', 'en']);
    safeDefine(navigator, 'platform', 'Win32');
    safeDefine(navigator, 'hardwareConcurrency', 8);
    safeDefine(navigator, 'deviceMemory', 8);

    // Remove webdriver flag
    try {
      Object.defineProperty(navigator, 'webdriver', { get: () => undefined, configurable: true });
    } catch (e) {}

    // Try to cover prototype too
    try {
      if (navigator.__proto__) {
        Object.defineProperty(navigator.__proto__, 'webdriver', { get: () => undefined, configurable: true });
      }
    } catch (e) {}
  } catch (e) {}

  // --- userAgentData fallback (some sites probe this) ---
  try {
    if (navigator.userAgentData === undefined) {
      safeDefine(navigator, 'userAgentData', {
        getBrands: () => [{ brand: 'Chromium', version: '120' }, { brand: 'Google Chrome', version: '120' }],
        mobile: false,
        platform: 'Windows',
      }, true);
    }
  } catch (e) {}

  // --- Canvas fingerprint mitigation ---
  try {
    const orig_toDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function () {
      try {
        const ctx = this.getContext && this.getContext('2d');
        if (ctx) {
          try {
            ctx.fillStyle = 'rgba(0,0,0,0)';
            ctx.fillRect(0, 0, 1, 1);
          } catch (e) {}
        }
      } catch (e) {}
      return orig_toDataURL.apply(this, arguments);
    };

    const orig_getImageData = CanvasRenderingContext2D.prototype.getImageData;
    CanvasRenderingContext2D.prototype.getImageData = function (x, y, w, h) {
      const data = orig_getImageData.apply(this, arguments);
      try {
        // Slight, deterministic noise every Nth pixel to alter fingerprint but keep visuals intact.
        for (let i = 0; i < data.data.length; i += 10) {
          data.data[i] = data.data[i] ^ 0x11;
        }
      } catch (e) {}
      return data;
    };
  } catch (e) {}

  // --- WebGL fingerprint mitigation ---
  try {
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function (param) {
      // 37445 = UNMASKED_VENDOR_WEBGL, 37446 = UNMASKED_RENDERER_WEBGL
      try {
        if (param === 37445) return 'Intel Inc.';
        if (param === 37446) return 'Intel Iris OpenGL Engine';
      } catch (e) {}
      return getParameter.apply(this, arguments);
    };
  } catch (e) {}

  // --- Audio fingerprint mitigation ---
  try {
    const orig_getChannelData = AudioBuffer.prototype.getChannelData;
    AudioBuffer.prototype.getChannelData = function () {
      const data = orig_getChannelData.apply(this, arguments);
      try {
        // tiny deterministic perturbation
        for (let i = 0; i < data.length; i += 100) {
          data[i] = data[i] + 1e-7;
        }
      } catch (e) {}
      return data;
    };
  } catch (e) {}

  // --- Clear common automation artifacts from window ---
  try {
    try {
      delete window.__webdriver;
    } catch (e) {}
    try {
      delete window._webdriver;
    } catch (e) {}

    const names = Object.getOwnPropertyNames(window);
    for (const k of names) {
      try {
        if (/^__?cdc_|webdriver|__driver|selenium|driver/i.test(k)) {
          try { delete window[k]; } catch (e) {}
        }
      } catch (e) {}
    }
  } catch (e) {}

  // --- navigator.permissions.query patch (used by some detection scripts) ---
  try {
    if (navigator.permissions && navigator.permissions.query) {
      const origQuery = navigator.permissions.query;
      navigator.permissions.query = function (parameters) {
        // some sites probe 'notifications' permission and expect 'denied' in headless.
        try {
          if (parameters && parameters.name === 'notifications') {
            return Promise.resolve({ state: Notification.permission });
          }
        } catch (e) {}
        return origQuery.apply(this, arguments);
      };
    }
  } catch (e) {}

  // --- Fake plugins and mimeTypes (non-invasive) ---
  try {
    // Minimal faux plugin list to satisfy simple checks
    const fakePlugins = [
      { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: '' },
      { name: 'Chromium PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
    ];

    if (navigator.plugins && navigator.plugins.length === 0) {
      // create a faux PluginArray-like object
      const pluginArray = fakePlugins.map((p, i) => ({
        name: p.name,
        filename: p.filename,
        description: p.description,
        length: 0,
        0: undefined,
      }));
      safeDefine(navigator, 'plugins', pluginArray, true);
    }

    if (navigator.mimeTypes && navigator.mimeTypes.length === 0) {
      safeDefine(navigator, 'mimeTypes', [], true);
    }
  } catch (e) {}

  // --- Defensive: mark script as applied (useful for debugging) ---
  try {
    Object.defineProperty(window, '__stealth_patch_applied__', { value: true, configurable: true });
  } catch (e) {}

})();
