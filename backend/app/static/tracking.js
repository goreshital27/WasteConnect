// Order Tracking with Leaflet + OpenStreetMap
// File: backend/app/static/tracking.js

(function () {
  const PUNE_ROUTE_POINTS = [
    { lat: 18.598500, lng: 73.763500 }, // 1. Wakad Datta Mandir
    { lat: 18.595200, lng: 73.765100 }, // 2. Wakad Bridge
    { lat: 18.591000, lng: 73.767500 }, // 3. Bhumkar Chowk
    { lat: 18.587000, lng: 73.770200 }, // 4. Sayaji Underpass
    { lat: 18.582500, lng: 73.772500 }, // 5. Wakad Flyover
    { lat: 18.578000, lng: 73.774000 }, // 6. Tathawade Junction
    { lat: 18.574000, lng: 73.775800 }, // 7. Hinjawadi Bypass
    { lat: 18.570000, lng: 73.777000 }, // 8. Highway Corridor
    { lat: 18.566000, lng: 73.778200 }, // 9. Balewadi Stadium
    { lat: 18.563000, lng: 73.779500 }, // 10. Balewadi High Street
    { lat: 18.560500, lng: 73.781000 }, // 11. Baner-Balewadi Link Rd
    { lat: 18.558000, lng: 73.783000 }, // 12. Baner Phata
    { lat: 18.555500, lng: 73.785000 }, // 13. Baner Ganpati Chowk
    { lat: 18.553000, lng: 73.787500 }, // 14. Baner Main Road
    { lat: 18.550500, lng: 73.790000 }  // 15. Baner Recycler Hub
  ];

  let leafletMap = null;
  let mapMarker = null;
  let sellerPollTimer = null;
  let demoRouteTimer = null;
  let currentDemoIndex = 0;
  let selectedOrderId = null;
  let cachedOrders = [];

  function loadLeaflet(callback) {
    if (window.L) {
      callback();
      return;
    }
    if (!document.getElementById("leaflet-css")) {
      const link = document.createElement("link");
      link.id = "leaflet-css";
      link.rel = "stylesheet";
      link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      document.head.appendChild(link);
    }
    const existingScript = document.getElementById("leaflet-js");
    if (existingScript) {
      existingScript.addEventListener("load", callback);
    } else {
      const script = document.createElement("script");
      script.id = "leaflet-js";
      script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
      script.onload = callback;
      document.head.appendChild(script);
    }
  }

  function clearTimers() {
    if (sellerPollTimer) {
      clearInterval(sellerPollTimer);
      sellerPollTimer = null;
    }
    if (demoRouteTimer) {
      clearInterval(demoRouteTimer);
      demoRouteTimer = null;
    }
  }

  function initMap(containerId, initialLat = 18.57, initialLng = 73.77) {
    loadLeaflet(() => {
      const el = document.getElementById(containerId);
      if (!el) return;

      if (leafletMap) {
        try {
          leafletMap.remove();
        } catch {
          // ignore cleanup error
        }
        leafletMap = null;
        mapMarker = null;
      }

      leafletMap = window.L.map(containerId).setView([initialLat, initialLng], 13);
      window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
      }).addTo(leafletMap);

      setTimeout(() => {
        if (leafletMap) leafletMap.invalidateSize();
      }, 250);
    });
  }

  function updateMarker(lat, lng, popupHtml = "Position") {
    if (!leafletMap || !window.L) return;
    const numLat = Number(lat);
    const numLng = Number(lng);
    if (isNaN(numLat) || isNaN(numLng)) return;

    if (!mapMarker) {
      const truckIcon = window.L.divIcon({
        className: "custom-tracking-marker",
        html: `<div style="background:#059669; color:white; width:34px; height:34px; border-radius:50%; display:flex; align-items:center; justify-content:center; box-shadow:0 3px 10px rgba(0,0,0,0.35); border:2.5px solid white; font-size:14px;"><i class="fa-solid fa-truck"></i></div>`,
        iconSize: [34, 34],
        iconAnchor: [17, 17]
      });
      mapMarker = window.L.marker([numLat, numLng], { icon: truckIcon }).addTo(leafletMap);
    } else {
      mapMarker.setLatLng([numLat, numLng]);
    }
    mapMarker.bindPopup(popupHtml).openPopup();
    leafletMap.panTo([numLat, numLng], { animate: true });
  }

  async function pollSeller(orderId) {
    try {
      const res = await api(`/tracking/orders/${orderId}/position`);
      const statusEl = document.getElementById("tracking-status-text");
      if (res && res.data) {
        const pos = res.data;
        updateMarker(
          pos.lat,
          pos.lng,
          `<strong>Reseller Transit Location</strong><br><span style="font-size:11px;color:#64748b;">Updated: ${new Date(pos.updated_at).toLocaleTimeString()}</span>`
        );
        if (statusEl) {
          statusEl.innerHTML = `<span class="text-emerald-700 font-semibold"><i class="fa-solid fa-satellite-dish mr-1 text-emerald-600"></i> Location updated: [${Number(pos.lat).toFixed(4)}, ${Number(pos.lng).toFixed(4)}] at ${new Date(pos.updated_at).toLocaleTimeString()}</span>`;
        }
      } else {
        if (statusEl) {
          statusEl.innerHTML = `<span class="text-slate-500"><i class="fa-solid fa-clock mr-1"></i> Waiting for buyer to broadcast position...</span>`;
        }
      }
    } catch (err) {
      // If error (e.g. order not collected or permission issue), stop polling
      console.warn("Tracking poll stopped:", err);
      clearTimers();
    }
  }

  window.startTrackingDemoRoute = async function (orderId) {
    if (demoRouteTimer) {
      clearInterval(demoRouteTimer);
      demoRouteTimer = null;
    }
    currentDemoIndex = 0;
    const startBtn = document.getElementById("btn-start-demo");
    const stopBtn = document.getElementById("btn-stop-demo");
    if (startBtn) startBtn.classList.add("hidden");
    if (stopBtn) stopBtn.classList.remove("hidden");

    const statusEl = document.getElementById("tracking-status-text");

    async function postStep(idx) {
      const pt = PUNE_ROUTE_POINTS[idx];
      try {
        await api(`/tracking/orders/${orderId}/position`, {
          method: "POST",
          body: JSON.stringify({ lat: pt.lat, lng: pt.lng })
        });
        updateMarker(
          pt.lat,
          pt.lng,
          `<strong>Demo Route: Step ${idx + 1} of ${PUNE_ROUTE_POINTS.length}</strong><br><span style="font-size:11px;color:#64748b;">Wakad ➔ Baner Transit</span>`
        );
        if (statusEl) {
          statusEl.innerHTML = `<span class="text-emerald-700 font-semibold"><i class="fa-solid fa-truck-moving mr-1"></i> Broadcasting: Step ${idx + 1}/${PUNE_ROUTE_POINTS.length} (${pt.lat}, ${pt.lng})</span>`;
        }
      } catch (err) {
        console.error("Demo route error:", err);
        if (statusEl) statusEl.innerText = "Error broadcasting point: " + (err.message || err);
      }
    }

    await postStep(0);
    currentDemoIndex = 1;

    demoRouteTimer = setInterval(async () => {
      if (currentDemoIndex >= PUNE_ROUTE_POINTS.length) {
        clearInterval(demoRouteTimer);
        demoRouteTimer = null;
        if (startBtn) startBtn.classList.remove("hidden");
        if (stopBtn) stopBtn.classList.add("hidden");
        if (statusEl) {
          statusEl.innerHTML = `<span class="text-emerald-700 font-bold"><i class="fa-solid fa-flag-checkered mr-1"></i> Demo route completed: arrived at Baner destination!</span>`;
        }
        showToast("Demo route completed! Arrived at destination.");
        return;
      }
      await postStep(currentDemoIndex);
      currentDemoIndex++;
    }, 3000);
  };

  window.stopTrackingDemoRoute = function () {
    if (demoRouteTimer) {
      clearInterval(demoRouteTimer);
      demoRouteTimer = null;
    }
    const startBtn = document.getElementById("btn-start-demo");
    const stopBtn = document.getElementById("btn-stop-demo");
    if (startBtn) startBtn.classList.remove("hidden");
    if (stopBtn) stopBtn.classList.add("hidden");
    const statusEl = document.getElementById("tracking-status-text");
    if (statusEl) statusEl.innerText = "Demo route paused.";
  };

  window.shareTrackingLocation = async function (orderId) {
    const consent = window.confirm(
      `Allow WasteConnect to access and share your live browser GPS location with the seller for Order #${orderId.substring(0, 8)}?`
    );
    if (!consent) return;

    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }

    const statusEl = document.getElementById("tracking-status-text");
    if (statusEl) statusEl.innerText = "Requesting device coordinates...";

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = Number(pos.coords.latitude.toFixed(6));
        const lng = Number(pos.coords.longitude.toFixed(6));
        try {
          await api(`/tracking/orders/${orderId}/position`, {
            method: "POST",
            body: JSON.stringify({ lat, lng })
          });
          updateMarker(lat, lng, `<strong>My GPS Location</strong><br><span style="font-size:11px;color:#64748b;">Shared live</span>`);
          if (statusEl) {
            statusEl.innerHTML = `<span class="text-emerald-700 font-semibold"><i class="fa-solid fa-check mr-1"></i> Live location shared at ${new Date().toLocaleTimeString()} (${lat}, ${lng})</span>`;
          }
          showToast("Live location broadcasted successfully!");
        } catch (err) {
          if (statusEl) statusEl.innerText = "Failed to broadcast location: " + (err.message || err);
        }
      },
      (err) => {
        alert("Location error: " + err.message);
        if (statusEl) statusEl.innerText = "GPS permission denied or unavailable.";
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  };

  window.onTrackingOrderChanged = function (newOrderId) {
    selectedOrderId = newOrderId;
    renderTrackingUI();
  };

  async function renderTrackingUI() {
    clearTimers();
    const panel = document.getElementById("tracking-panel");
    if (!panel) return;

    if (!currentUser || !token) {
      panel.innerHTML = "";
      return;
    }

    // Load user orders if cachedOrders empty
    if (!cachedOrders || !cachedOrders.length) {
      try {
        const res = await api("/orders");
        cachedOrders = res.data || [];
      } catch {
        cachedOrders = [];
      }
    }

    if (!cachedOrders.length) {
      panel.innerHTML = "";
      return;
    }

    // Determine which order to track
    let activeOrder = cachedOrders.find((o) => o.id === selectedOrderId);
    if (!activeOrder) {
      // Default to first 'collected' order, or first order
      activeOrder = cachedOrders.find((o) => o.status === "collected") || cachedOrders[0];
      selectedOrderId = activeOrder ? activeOrder.id : null;
    }

    if (!activeOrder) {
      panel.innerHTML = "";
      return;
    }

    const isBuyer = activeOrder.buyer_id === currentUser.id;
    const isSeller = activeOrder.seller_id === currentUser.id;
    const orderTitle = activeOrder.offer?.listing?.title || `Order #${activeOrder.id.substring(0, 8)}`;
    const isCollected = activeOrder.status === "collected";
    const isDeliveredOrDone = activeOrder.status === "delivered" || activeOrder.status === "completed";

    // Order Selector Options
    const orderOptions = cachedOrders.map((o) => {
      const isSel = o.id === selectedOrderId ? "selected" : "";
      return `<option value="${o.id}" ${isSel}>#${o.id.substring(0, 8)} - ${o.offer?.listing?.title || "Scrap"} [${o.status.toUpperCase()}]</option>`;
    }).join("");

    // Message when order is not collected
    if (!isCollected) {
      let statusMessage = "";
      let iconClass = "fa-info-circle text-blue-500";
      if (isDeliveredOrDone) {
        statusMessage = `Order #${activeOrder.id.substring(0, 8)} is <strong>${activeOrder.status.toUpperCase()}</strong>. Live transit tracking has finished and is stopped.`;
        iconClass = "fa-circle-check text-emerald-500";
      } else {
        statusMessage = `Order #${activeOrder.id.substring(0, 8)} is in <strong>${activeOrder.status.toUpperCase()}</strong> stage. Live transit tracking is only available while the order status is <strong>Collected</strong>.`;
        iconClass = "fa-triangle-exclamation text-amber-500";
      }

      panel.innerHTML = `
        <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3">
          <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
            <div class="flex items-center space-x-2">
              <i class="fa-solid fa-map-location-dot text-emerald-600 text-lg"></i>
              <h3 class="font-bold text-slate-900 text-base">Live Order Transit Tracking</h3>
            </div>
            <div class="flex items-center space-x-2 text-xs">
              <label for="trackingOrderSelect" class="text-slate-500 font-medium">Select Order:</label>
              <select id="trackingOrderSelect" onchange="onTrackingOrderChanged(this.value)" class="border border-slate-300 rounded-lg px-2.5 py-1 text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                ${orderOptions}
              </select>
            </div>
          </div>
          <div class="bg-slate-50 rounded-xl p-4 flex items-center space-x-3 text-xs text-slate-700">
            <i class="fa-solid ${iconClass} text-xl"></i>
            <div>${statusMessage}</div>
          </div>
        </div>
      `;
      return;
    }

    // Order IS in "collected" stage: Render map and controls
    let controlsHtml = "";
    if (isBuyer) {
      controlsHtml = `
        <div class="flex flex-wrap items-center gap-2 pt-1">
          <button id="btn-start-demo" onclick="startTrackingDemoRoute('${activeOrder.id}')" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow-sm transition flex items-center">
            <i class="fa-solid fa-route mr-1.5"></i> Start demo route
          </button>
          <button id="btn-stop-demo" onclick="stopTrackingDemoRoute()" class="hidden px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-lg shadow-sm transition flex items-center">
            <i class="fa-solid fa-stop mr-1.5"></i> Stop demo route
          </button>
          <button id="btn-share-location" onclick="shareTrackingLocation('${activeOrder.id}')" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow-sm transition flex items-center">
            <i class="fa-solid fa-location-crosshairs mr-1.5"></i> Share my location
          </button>
          <span id="tracking-status-text" class="text-xs text-slate-500 ml-2">Click to broadcast location from Wakad to Baner (15 points).</span>
        </div>
      `;
    } else if (isSeller) {
      controlsHtml = `
        <div class="flex flex-wrap items-center justify-between gap-2 pt-1 text-xs">
          <div id="tracking-status-text" class="text-emerald-700 font-semibold flex items-center">
            <i class="fa-solid fa-satellite-dish mr-2 text-emerald-600 animate-pulse"></i>
            Monitoring reseller transit: polling every 5 seconds...
          </div>
          <div class="text-slate-400 text-[11px]">Auto-updates live as buyer moves</div>
        </div>
      `;
    } else {
      controlsHtml = `
        <div class="text-xs text-slate-400">Viewing tracking mode.</div>
      `;
    }

    panel.innerHTML = `
      <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3">
        <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div class="flex items-center space-x-2">
            <div class="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
              <i class="fa-solid fa-map-location-dot"></i>
            </div>
            <div>
              <div class="flex items-center space-x-2">
                <h3 class="font-bold text-slate-900 text-sm">Live Transit Tracking: ${orderTitle}</h3>
                <span class="px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wide bg-emerald-100 text-emerald-800 rounded-full">COLLECTED</span>
              </div>
              <div class="text-[11px] text-slate-500">
                ${isBuyer ? '<span class="text-blue-600 font-medium">Buyer Mode</span> &bull; Broadcast transit location to seller' : '<span class="text-emerald-600 font-medium">Seller Mode</span> &bull; Live position polled every 5s'}
              </div>
            </div>
          </div>
          <div class="flex items-center space-x-2 text-xs">
            <label for="trackingOrderSelect" class="text-slate-500 font-medium">Track Order:</label>
            <select id="trackingOrderSelect" onchange="onTrackingOrderChanged(this.value)" class="border border-slate-300 rounded-lg px-2.5 py-1 text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-none">
              ${orderOptions}
            </select>
          </div>
        </div>

        ${controlsHtml}

        <div id="tracking-leaflet-map" style="height: 380px; width: 100%; border-radius: 0.75rem; border: 1px solid #e2e8f0; margin-top: 0.5rem;" class="z-0"></div>
      </div>
    `;

    // Initialize Map on Pune
    initMap("tracking-leaflet-map", 18.57, 73.77);

    // If seller, poll immediately and schedule every 5 seconds
    if (isSeller) {
      pollSeller(activeOrder.id);
      sellerPollTimer = setInterval(() => {
        pollSeller(activeOrder.id);
      }, 5000);
    }
  }

  // Hook into WasteConnect app lifecycles
  function hookAppEvents() {
    if (window.loadOrders) {
      const origLoadOrders = window.loadOrders;
      window.loadOrders = async function () {
        await origLoadOrders.apply(this, arguments);
        try {
          const res = await api("/orders");
          cachedOrders = res.data || [];
        } catch {
          // ignore
        }
        renderTrackingUI();
      };
    }

    if (window.switchTab) {
      const origSwitchTab = window.switchTab;
      window.switchTab = function (tab) {
        origSwitchTab.apply(this, arguments);
        if (tab === "myOrders") {
          renderTrackingUI();
        } else {
          clearTimers();
        }
      };
    }

    if (window.demoLogin) {
      const origDemoLogin = window.demoLogin;
      window.demoLogin = async function (email) {
        clearTimers();
        selectedOrderId = null;
        cachedOrders = [];
        await origDemoLogin.apply(this, arguments);
        if (window.currentTab === "myOrders") {
          renderTrackingUI();
        }
      };
    }
  }

  // Initial setup on DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      hookAppEvents();
      loadLeaflet(() => {});
    });
  } else {
    hookAppEvents();
    loadLeaflet(() => {});
  }
})();
