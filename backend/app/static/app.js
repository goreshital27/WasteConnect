// WasteConnect Pune SPA Application Logic

let token = localStorage.getItem("wasteconnect_token") || null;
let currentUser = null;
let categories = [];
let listings = [];
let currentTab = "browse";

// API Request Helper
async function api(endpoint, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(endpoint, {
      ...options,
      headers
    });
    const body = await res.json();
    if (!res.ok) {
      const msg = body.detail?.detail || body.detail || body.message || "Request failed";
      throw new Error(msg);
    }
    return body;
  } catch (err) {
    showToast(err.message || "Network error", "error");
    throw err;
  }
}

// Toast Notifications
function showToast(message, type = "success") {
  const toast = document.getElementById("toast");
  const title = document.getElementById("toastTitle");
  const msg = document.getElementById("toastMessage");
  const icon = document.getElementById("toastIcon");

  title.innerText = type === "success" ? "Success" : "Error";
  msg.innerText = message;
  icon.innerHTML = type === "success"
    ? '<i class="fa-solid fa-circle-check text-lg text-emerald-600"></i>'
    : '<i class="fa-solid fa-circle-exclamation text-lg text-rose-600"></i>';

  toast.classList.remove("hidden");
  setTimeout(() => {
    toast.classList.add("hidden");
  }, 4000);
}

function hideToast() {
  document.getElementById("toast").classList.add("hidden");
}

// Dropdown toggle
function toggleDropdown(id) {
  const el = document.getElementById(id);
  el.classList.toggle("hidden");
}

// Close dropdown on outside click
window.addEventListener("click", (e) => {
  if (!e.target.closest("#quickLoginBtn") && !e.target.closest("#quickLoginDropdown")) {
    document.getElementById("quickLoginDropdown")?.classList.add("hidden");
  }
});

// Modal helpers
function openModal(id) {
  document.getElementById(id).classList.remove("hidden");
}

function closeModal(id) {
  document.getElementById(id).classList.add("hidden");
}

// Navigation Tab Switcher
function switchTab(tab) {
  currentTab = tab;
  const sections = ["browse", "create", "myListings", "myOrders", "rateCard"];
  sections.forEach((s) => {
    const secEl = document.getElementById(`section-${s}`);
    const tabEl = document.getElementById(`tab-${s}`);
    if (s === tab) {
      secEl.classList.remove("hidden");
      tabEl?.classList.add("active");
    } else {
      secEl.classList.add("hidden");
      tabEl?.classList.remove("active");
    }
  });

  if (tab === "browse") loadListings();
  if (tab === "myListings") loadMyListingsAndOffers();
  if (tab === "myOrders") loadOrders();
  if (tab === "rateCard") loadRateCardAndImpact();
}

// Initialize Application
async function initApp() {
  await loadCategories();
  if (token) {
    try {
      const res = await api("/me");
      currentUser = res.data;
      updateAuthUI();
    } catch {
      logout();
    }
  } else {
    updateAuthUI();
  }
  loadListings();
}

// Load Categories
async function loadCategories() {
  try {
    const res = await api("/categories");
    categories = res.data;

    // Populate filter dropdown
    const filterCat = document.getElementById("filterCategory");
    filterCat.innerHTML = '<option value="">All Categories</option>';
    categories.forEach((c) => {
      filterCat.innerHTML += `<option value="${c.code}">${c.name}</option>`;
    });

    // Populate create listing dropdown
    const postCat = document.getElementById("postCategory");
    postCat.innerHTML = "";
    categories.forEach((c) => {
      postCat.innerHTML += `<option value="${c.id}">${c.name} (${c.unit})</option>`;
    });
  } catch (err) {
    console.error("Failed to load categories:", err);
  }
}

// Update Header User UI
function updateAuthUI() {
  const container = document.getElementById("authContainer");
  if (currentUser) {
    const roleColors = {
      individual: "bg-slate-100 text-slate-800",
      reseller: "bg-blue-100 text-blue-800",
      aggregator: "bg-emerald-100 text-emerald-800",
      recycler: "bg-purple-100 text-purple-800"
    };
    const roleBadge = roleColors[currentUser.role] || "bg-slate-100 text-slate-800";

    container.innerHTML = `
      <div class="flex items-center space-x-3">
        <div class="text-right hidden sm:block">
          <div class="text-xs font-bold text-slate-900">${currentUser.name}</div>
          <div class="text-[10px] text-slate-500">${currentUser.area} &bull; <span class="capitalize">${currentUser.role}</span></div>
        </div>
        <span class="px-2 py-0.5 text-xs font-semibold rounded-full capitalize ${roleBadge}">${currentUser.role}</span>
        <button onclick="logout()" title="Logout" class="w-8 h-8 rounded-lg border border-slate-200 text-slate-500 hover:text-rose-600 hover:border-rose-200 flex items-center justify-center transition">
          <i class="fa-solid fa-arrow-right-from-bracket text-xs"></i>
        </button>
      </div>
    `;

    // Pre-fill create listing location
    document.getElementById("postArea").value = currentUser.area || "";
    document.getElementById("postPincode").value = currentUser.pincode || "";
  } else {
    container.innerHTML = `
      <button onclick="openModal('loginModal')" class="px-3.5 py-1.5 text-xs sm:text-sm font-medium text-slate-700 hover:text-emerald-600 transition">Log In</button>
      <button onclick="openModal('registerModal')" class="px-3.5 py-1.5 text-xs sm:text-sm font-medium bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 shadow-sm transition">Sign Up</button>
    `;
  }
}

// Authentication Handlers
async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById("loginEmail").value;
  const password = document.getElementById("loginPassword").value;

  try {
    const res = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
    token = res.data.access_token;
    localStorage.setItem("wasteconnect_token", token);
    currentUser = res.data.user;
    updateAuthUI();
    closeModal("loginModal");
    showToast(`Welcome back, ${currentUser.name}!`);
    switchTab("browse");
  } catch (err) {
    // Error handled in api()
  }
}

async function demoLogin(email) {
  try {
    const res = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password: "Password123!" })
    });
    token = res.data.access_token;
    localStorage.setItem("wasteconnect_token", token);
    currentUser = res.data.user;
    updateAuthUI();
    document.getElementById("quickLoginDropdown").classList.add("hidden");
    showToast(`Switched account to ${currentUser.name} (${currentUser.role})`);
    if (currentTab === "myListings") loadMyListingsAndOffers();
    else if (currentTab === "myOrders") loadOrders();
    else loadListings();
  } catch (err) {
    // Error handled
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const payload = {
    name: document.getElementById("regName").value,
    email: document.getElementById("regEmail").value,
    phone: document.getElementById("regPhone").value,
    role: document.getElementById("regRole").value,
    password: document.getElementById("regPassword").value,
    area: document.getElementById("regArea").value,
    pincode: document.getElementById("regPincode").value,
  };

  try {
    const res = await api("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    token = res.data.access_token;
    localStorage.setItem("wasteconnect_token", token);
    currentUser = res.data.user;
    updateAuthUI();
    closeModal("registerModal");
    showToast(`Account registered successfully! Welcome ${currentUser.name}`);
    switchTab("browse");
  } catch (err) {
    // Handled
  }
}

function logout() {
  token = null;
  currentUser = null;
  localStorage.removeItem("wasteconnect_token");
  updateAuthUI();
  showToast("Logged out successfully");
  switchTab("browse");
}

// Load Marketplace Listings
async function loadListings() {
  const cat = document.getElementById("filterCategory").value;
  const pin = document.getElementById("filterPincode").value;
  const minQty = document.getElementById("filterMinQty").value;

  const params = new URLSearchParams();
  if (cat) params.append("category", cat);
  if (pin) params.append("pincode", pin);
  if (minQty && Number(minQty) > 0) params.append("min_quantity", minQty);

  try {
    const res = await api(`/listings?${params.toString()}`);
    listings = res.data;
    document.getElementById("listingCount").innerText = listings.length;
    renderListings();
  } catch (err) {
    console.error(err);
  }
}

function resetFilters() {
  document.getElementById("filterCategory").value = "";
  document.getElementById("filterPincode").value = "";
  document.getElementById("filterMinQty").value = "";
  loadListings();
}

function renderListings() {
  const grid = document.getElementById("listingsGrid");
  if (!listings.length) {
    grid.innerHTML = `
      <div class="col-span-full py-12 text-center bg-white rounded-2xl border border-slate-200">
        <i class="fa-solid fa-boxes-packing text-4xl text-slate-300"></i>
        <h3 class="text-sm font-semibold text-slate-700 mt-2">No listings match your filter</h3>
        <p class="text-xs text-slate-500 mt-1">Try resetting the category, location, or minimum quantity.</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = listings.map((l) => {
    const isOwner = currentUser && l.seller_id === currentUser.id;
    const estTotal = (Number(l.quantity_kg) * Number(l.price_per_kg)).toFixed(2);
    const dateStr = new Date(l.created_at).toLocaleDateString("en-IN", { month: "short", day: "numeric" });

    return `
      <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between space-y-4">
        <div>
          <div class="flex items-center justify-between">
            <span class="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              ${l.category.name}
            </span>
            <span class="text-[11px] text-slate-400">${dateStr}</span>
          </div>

          <h3 class="text-base font-bold text-slate-900 mt-2.5 line-clamp-1">${l.title}</h3>

          <div class="mt-3 bg-slate-50 p-3 rounded-xl flex items-center justify-between text-xs">
            <div>
              <span class="text-slate-500 block">Lot Quantity</span>
              <span class="text-sm font-extrabold text-slate-900">${Number(l.quantity_kg).toFixed(2)} kg</span>
            </div>
            <div class="text-right">
              <span class="text-slate-500 block">Asking Rate</span>
              <span class="text-sm font-extrabold text-emerald-600">₹${Number(l.price_per_kg).toFixed(2)} <span class="text-[10px] font-normal text-slate-400">/kg</span></span>
            </div>
          </div>

          <div class="mt-3 flex items-center justify-between text-xs text-slate-500">
            <span><i class="fa-solid fa-location-dot text-slate-400 mr-1"></i> ${l.area} (${l.pincode})</span>
            <span class="font-medium ${l.is_negotiable ? 'text-amber-600' : 'text-slate-400'}">
              ${l.is_negotiable ? '<i class="fa-solid fa-comments-dollar mr-0.5"></i> Negotiable' : 'Fixed Price'}
            </span>
          </div>

          <div class="mt-2 text-[11px] text-slate-500 flex items-center space-x-1.5">
            <i class="fa-solid fa-user text-slate-400"></i>
            <span>${l.seller.name} &bull; <span class="capitalize text-slate-600 font-medium">${l.seller.role}</span></span>
          </div>
        </div>

        <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
          <div>
            <span class="text-[10px] text-slate-400 uppercase font-semibold">Est. Total</span>
            <div class="text-xs font-bold text-slate-800">₹${estTotal}</div>
          </div>
          ${
            isOwner
              ? `<span class="px-3 py-1.5 text-xs font-semibold bg-slate-100 text-slate-600 rounded-lg">Your Listing</span>`
              : `<button onclick="openOfferModal('${l.id}')" class="px-4 py-1.5 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition shadow-sm flex items-center space-x-1">
                   <span>Make Offer</span>
                   <i class="fa-solid fa-arrow-right text-[10px]"></i>
                 </button>`
          }
        </div>
      </div>
    `;
  }).join("");
}

// Make Offer Modal Flow
function openOfferModal(listingId) {
  if (!currentUser) {
    showToast("Please log in or select a demo account to make an offer", "error");
    openModal("loginModal");
    return;
  }

  const listing = listings.find((x) => x.id === listingId);
  if (!listing) return;

  if (listing.seller_id === currentUser.id) {
    showToast("You cannot make an offer on your own listing", "error");
    return;
  }

  document.getElementById("offerListingId").value = listing.id;
  document.getElementById("offerQuantity").value = Number(listing.quantity_kg);
  document.getElementById("offerPrice").value = Number(listing.price_per_kg);

  const summary = document.getElementById("offerModalListingSummary");
  summary.innerHTML = `
    <div class="font-semibold text-slate-900">${listing.title}</div>
    <div class="text-slate-600">${listing.category.name} &bull; Asking: ₹${Number(listing.price_per_kg).toFixed(2)}/kg for ${Number(listing.quantity_kg).toFixed(2)} kg</div>
    <div class="text-slate-500">Seller: ${listing.seller.name} (${listing.area})</div>
  `;

  updateOfferTotal();
  openModal("offerModal");
}

function updateOfferTotal() {
  const qty = Number(document.getElementById("offerQuantity").value) || 0;
  const price = Number(document.getElementById("offerPrice").value) || 0;
  document.getElementById("offerTotalValue").innerText = `₹${(qty * price).toFixed(2)}`;
}

document.getElementById("offerQuantity").addEventListener("input", updateOfferTotal);
document.getElementById("offerPrice").addEventListener("input", updateOfferTotal);

async function handleMakeOffer(e) {
  e.preventDefault();
  const listingId = document.getElementById("offerListingId").value;
  const quantity_kg = document.getElementById("offerQuantity").value;
  const price_per_kg = document.getElementById("offerPrice").value;

  try {
    await api(`/listings/${listingId}/offers`, {
      method: "POST",
      body: JSON.stringify({ quantity_kg, price_per_kg })
    });
    closeModal("offerModal");
    showToast("Offer submitted successfully! View status in 'My Listings & Offers'");
    switchTab("myListings");
  } catch (err) {
    // Handled
  }
}

// Create Listing Flow
async function handleCreateListing(e) {
  e.preventDefault();
  if (!currentUser) {
    showToast("Please log in first", "error");
    openModal("loginModal");
    return;
  }

  const payload = {
    title: document.getElementById("postTitle").value,
    category_id: document.getElementById("postCategory").value,
    quantity_kg: document.getElementById("postQuantity").value,
    price_per_kg: document.getElementById("postPrice").value,
    is_negotiable: document.getElementById("postNegotiable").checked,
    area: document.getElementById("postArea").value,
    pincode: document.getElementById("postPincode").value,
  };

  try {
    await api("/listings", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    showToast("Listing published successfully!");
    document.getElementById("createListingForm").reset();
    switchTab("myListings");
  } catch (err) {
    // Handled
  }
}

// Cancel Listing Flow
async function cancelListing(id) {
  if (!confirm("Are you sure you want to cancel this listing?")) return;
  try {
    await api(`/listings/${id}/cancel`, { method: "POST" });
    showToast("Listing cancelled");
    loadMyListingsAndOffers();
  } catch (err) {
    // Handled
  }
}

// My Listings & Offers
async function loadMyListingsAndOffers() {
  if (!currentUser) {
    document.getElementById("myListingsContainer").innerHTML = `
      <div class="col-span-full py-8 text-center text-slate-500 text-xs">
        Please log in to see your listings and incoming offers.
      </div>
    `;
    return;
  }

  try {
    const [mineRes, receivedRes, sentRes] = await Promise.all([
      api("/listings/mine"),
      api("/offers/received"),
      api("/offers/sent")
    ]);

    const myListings = mineRes.data;
    const receivedOffers = receivedRes.data;
    const sentOffers = sentRes.data;

    document.getElementById("myListingsCount").innerText = myListings.length;
    document.getElementById("receivedOffersCount").innerText = receivedOffers.length;
    document.getElementById("sentOffersCount").innerText = sentOffers.length;

    // Render my listings
    const lContainer = document.getElementById("myListingsContainer");
    if (!myListings.length) {
      lContainer.innerHTML = `<div class="col-span-full py-8 text-center text-slate-400 text-xs bg-white rounded-xl border border-slate-200">You haven't posted any listings yet.</div>`;
    } else {
      lContainer.innerHTML = myListings.map((l) => {
        const badgeColors = {
          open: "bg-emerald-100 text-emerald-800",
          sold: "bg-blue-100 text-blue-800",
          cancelled: "bg-slate-100 text-slate-600"
        };
        return `
          <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col justify-between space-y-3">
            <div>
              <div class="flex items-center justify-between">
                <span class="text-xs font-semibold text-emerald-700">${l.category.name}</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase ${badgeColors[l.status]}">${l.status}</span>
              </div>
              <h4 class="font-bold text-slate-900 text-sm mt-1">${l.title}</h4>
              <div class="mt-2 text-xs text-slate-600 flex justify-between">
                <span>${Number(l.quantity_kg).toFixed(2)} kg</span>
                <span class="font-bold text-emerald-600">₹${Number(l.price_per_kg).toFixed(2)}/kg</span>
              </div>
            </div>
            ${l.status === 'open' ? `
              <button onclick="cancelListing('${l.id}')" class="w-full text-xs py-1.5 border border-rose-200 text-rose-600 hover:bg-rose-50 rounded-lg transition font-medium">
                Cancel Listing
              </button>
            ` : ''}
          </div>
        `;
      }).join("");
    }

    // Render received offers
    const recContainer = document.getElementById("receivedOffersContainer");
    if (!receivedOffers.length) {
      recContainer.innerHTML = `<div class="py-6 text-center text-slate-400 text-xs bg-white rounded-xl border border-slate-200">No offers received yet on your listings.</div>`;
    } else {
      recContainer.innerHTML = receivedOffers.map((o) => {
        const isPending = o.status === "pending";
        const statusColors = {
          pending: "bg-amber-100 text-amber-800",
          accepted: "bg-emerald-100 text-emerald-800",
          rejected: "bg-rose-100 text-rose-800"
        };
        const total = (Number(o.quantity_kg) * Number(o.price_per_kg)).toFixed(2);

        return `
          <div class="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div class="space-y-1">
              <div class="flex items-center space-x-2">
                <span class="px-2 py-0.5 text-[10px] font-bold uppercase rounded ${statusColors[o.status]}">${o.status}</span>
                <span class="text-xs font-bold text-slate-900">Offer for: ${o.listing.title}</span>
              </div>
              <div class="text-xs text-slate-600">
                Buyer: <span class="font-semibold text-slate-800">${o.buyer.name}</span> (<span class="capitalize">${o.buyer.role}</span> &bull; ${o.buyer.phone})
              </div>
              <div class="text-xs text-slate-700">
                Offered <span class="font-bold">${Number(o.quantity_kg).toFixed(2)} kg</span> at <span class="font-bold text-emerald-600">₹${Number(o.price_per_kg).toFixed(2)}/kg</span> &bull; Total: <span class="font-bold">₹${total}</span>
              </div>
            </div>

            ${isPending ? `
              <div class="flex items-center space-x-2 self-end sm:self-center">
                <button onclick="rejectOffer('${o.id}')" class="px-3 py-1.5 text-xs font-medium border border-rose-200 text-rose-600 hover:bg-rose-50 rounded-lg transition">
                  Reject
                </button>
                <button onclick="acceptOffer('${o.id}')" class="px-3.5 py-1.5 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition shadow-sm flex items-center space-x-1">
                  <i class="fa-solid fa-check mr-1"></i> Accept & Create Order
                </button>
              </div>
            ` : `
              <div class="text-xs font-medium text-slate-400 capitalize self-end sm:self-center">
                ${o.status === 'accepted' ? '<span class="text-emerald-600 font-semibold"><i class="fa-solid fa-circle-check mr-1"></i> Order Created</span>' : 'Closed'}
              </div>
            `}
          </div>
        `;
      }).join("");
    }

    // Render sent offers
    const sentContainer = document.getElementById("sentOffersContainer");
    if (!sentOffers.length) {
      sentContainer.innerHTML = `<div class="py-6 text-center text-slate-400 text-xs bg-white rounded-xl border border-slate-200">You haven't made any offers yet.</div>`;
    } else {
      sentContainer.innerHTML = sentOffers.map((o) => {
        const total = (Number(o.quantity_kg) * Number(o.price_per_kg)).toFixed(2);
        return `
          <div class="bg-white rounded-xl border border-slate-200 p-3.5 text-xs flex items-center justify-between">
            <div>
              <span class="font-semibold text-slate-900">${o.listing.title}</span>
              <div class="text-slate-500 mt-0.5">Offered ${Number(o.quantity_kg).toFixed(2)} kg @ ₹${Number(o.price_per_kg).toFixed(2)}/kg (Total ₹${total})</div>
            </div>
            <span class="px-2 py-0.5 font-bold uppercase rounded text-[10px] ${o.status === 'accepted' ? 'bg-emerald-100 text-emerald-800' : o.status === 'pending' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600'}">
              ${o.status}
            </span>
          </div>
        `;
      }).join("");
    }
  } catch (err) {
    console.error(err);
  }
}

// Accept / Reject Offer
async function acceptOffer(offerId) {
  try {
    const res = await api(`/offers/${offerId}/accept`, { method: "POST" });
    showToast("Offer accepted! Order created in Confirmed status.");
    loadMyListingsAndOffers();
    // Switch to orders to view the new order
    setTimeout(() => {
      switchTab("myOrders");
    }, 600);
  } catch (err) {
    // Handled
  }
}

async function rejectOffer(offerId) {
  try {
    await api(`/offers/${offerId}/reject`, { method: "POST" });
    showToast("Offer rejected");
    loadMyListingsAndOffers();
  } catch (err) {
    // Handled
  }
}

// Orders Management
async function loadOrders() {
  if (!currentUser) {
    document.getElementById("ordersContainer").innerHTML = `
      <div class="py-12 text-center text-slate-500 text-xs bg-white rounded-xl border border-slate-200">
        Please log in to manage your orders.
      </div>
    `;
    return;
  }

  try {
    const res = await api("/orders");
    const orders = res.data;
    document.getElementById("ordersCount").innerText = orders.length;

    const container = document.getElementById("ordersContainer");
    if (!orders.length) {
      container.innerHTML = `
        <div class="py-12 text-center text-slate-400 text-xs bg-white rounded-2xl border border-slate-200">
          <i class="fa-solid fa-truck-ramp-box text-3xl text-slate-300"></i>
          <h3 class="text-sm font-semibold text-slate-700 mt-2">No orders found</h3>
          <p class="text-xs text-slate-500 mt-1">Accept an incoming offer or have a seller accept your offer to start fulfillment.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = orders.map((o) => {
      const isBuyer = o.buyer_id === currentUser.id;
      const isSeller = o.seller_id === currentUser.id;
      const roleTag = isBuyer
        ? `<span class="px-2.5 py-0.5 text-xs font-semibold bg-blue-100 text-blue-800 rounded-full">You are Buyer</span>`
        : `<span class="px-2.5 py-0.5 text-xs font-semibold bg-emerald-100 text-emerald-800 rounded-full">You are Seller</span>`;

      // Status Stepper active indicator
      const stages = ["confirmed", "collected", "delivered", "completed"];
      const isCancelled = o.status === "cancelled";
      const currentIdx = stages.indexOf(o.status);

      const stepperHtml = isCancelled ? `
        <div class="bg-rose-50 border border-rose-200 text-rose-800 px-3 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2">
          <i class="fa-solid fa-circle-xmark text-rose-600"></i>
          <span>Order Cancelled</span>
        </div>
      ` : `
        <div class="grid grid-cols-4 gap-2 py-3">
          ${stages.map((st, idx) => {
            const isDone = currentIdx >= idx;
            const isCurrent = currentIdx === idx;
            return `
              <div class="flex flex-col items-center">
                <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                  isCurrent ? 'bg-emerald-600 text-white ring-4 ring-emerald-100' : isDone ? 'bg-emerald-500 text-white' : 'bg-slate-200 text-slate-500'
                }">
                  ${isDone ? '<i class="fa-solid fa-check text-[10px]"></i>' : idx + 1}
                </div>
                <span class="text-[10px] mt-1 capitalize font-medium ${isCurrent ? 'text-emerald-700 font-bold' : isDone ? 'text-slate-800' : 'text-slate-400'}">${st}</span>
              </div>
            `;
          }).join("")}
        </div>
      `;

      // Weight card & difference calculation
      const hasCol = o.collection_weight_kg !== null;
      const hasDel = o.delivery_weight_kg !== null;
      const hasDiff = o.weight_difference_kg !== null;

      const diffVal = hasDiff ? Number(o.weight_difference_kg).toFixed(3) : null;
      const diffHtml = hasDiff ? `
        <div class="mt-2 text-xs bg-slate-100 p-2.5 rounded-lg flex items-center justify-between">
          <span class="text-slate-600 font-medium">Stage Weight Difference:</span>
          <span class="font-extrabold ${Number(diffVal) > 0 ? 'text-amber-700' : 'text-slate-800'}">
            ${diffVal} kg ${Number(diffVal) > 0 ? '(Handling Loss)' : ''}
          </span>
        </div>
      ` : '';

      return `
        <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
          <!-- Top Row -->
          <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
            <div class="flex items-center space-x-2">
              <span class="font-bold text-slate-900 text-sm">Order #${o.id.substring(0, 8)}</span>
              ${roleTag}
            </div>
            <div class="text-xs text-slate-500">
              Listing: <span class="font-semibold text-slate-800">${o.offer.listing.title}</span> (${o.offer.listing.category.name})
            </div>
          </div>

          <!-- Stepper -->
          ${stepperHtml}

          <!-- Transaction Parties & Price Details -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs bg-slate-50 p-3.5 rounded-xl">
            <div>
              <div class="text-slate-500">Seller: <span class="font-semibold text-slate-800">${o.seller.name}</span> (${o.seller.area}, ${o.seller.phone})</div>
              <div class="text-slate-500 mt-1">Buyer: <span class="font-semibold text-slate-800">${o.buyer.name}</span> (${o.buyer.area}, ${o.buyer.phone})</div>
            </div>
            <div class="md:text-right">
              <div>Contracted: <span class="font-bold text-slate-900">${Number(o.offer.quantity_kg).toFixed(2)} kg</span> @ <span class="font-bold text-emerald-600">₹${Number(o.offer.price_per_kg).toFixed(2)}/kg</span></div>
              <div class="font-extrabold text-sm text-slate-900 mt-1">Total: ₹${(Number(o.offer.quantity_kg) * Number(o.offer.price_per_kg)).toFixed(2)}</div>
            </div>
          </div>

          <!-- Weights Section -->
          <div class="border border-slate-200 rounded-xl p-3.5 space-y-2">
            <div class="text-xs font-bold text-slate-800 flex items-center justify-between">
              <span><i class="fa-solid fa-scale-balanced mr-1 text-slate-400"></i> Measured Weight Records</span>
              <span class="text-[11px] font-normal text-slate-400">Enforced by state machine</span>
            </div>
            <div class="grid grid-cols-2 gap-3 text-xs pt-1">
              <div class="bg-slate-50 p-2.5 rounded-lg">
                <span class="text-slate-400 block text-[10px] uppercase font-semibold">1. Collection Weight</span>
                <span class="font-bold text-slate-900 text-sm">
                  ${hasCol ? `${Number(o.collection_weight_kg).toFixed(3)} kg` : '<span class="text-slate-400 font-normal">Pending</span>'}
                </span>
              </div>
              <div class="bg-slate-50 p-2.5 rounded-lg">
                <span class="text-slate-400 block text-[10px] uppercase font-semibold">2. Delivery Weight</span>
                <span class="font-bold text-slate-900 text-sm">
                  ${hasDel ? `${Number(o.delivery_weight_kg).toFixed(3)} kg` : '<span class="text-slate-400 font-normal">Pending</span>'}
                </span>
              </div>
            </div>
            ${diffHtml}
          </div>

          <!-- Buyer Status Controls -->
          ${
            isBuyer && !isCancelled && o.status !== "completed" ? `
              <div class="pt-2 flex flex-wrap items-center justify-end gap-2 border-t border-slate-100">
                ${
                  o.status === "confirmed" ? `
                    <button onclick="openWeightModal('${o.id}', 'collection')" class="px-3 py-1.5 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition">
                      <i class="fa-solid fa-weight-scale mr-1"></i> Record Collection Weight
                    </button>
                    <button onclick="transitionOrder('${o.id}', 'collected')" class="px-3.5 py-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition shadow-sm">
                      Mark as Collected <i class="fa-solid fa-arrow-right ml-1"></i>
                    </button>
                    <button onclick="transitionOrder('${o.id}', 'cancelled')" class="px-3 py-1.5 text-xs font-medium text-rose-600 hover:bg-rose-50 rounded-lg transition">
                      Cancel
                    </button>
                  ` : ''
                }
                ${
                  o.status === "collected" ? `
                    <button onclick="openWeightModal('${o.id}', 'delivery')" class="px-3 py-1.5 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition">
                      <i class="fa-solid fa-weight-scale mr-1"></i> Record Delivery Weight
                    </button>
                    <button onclick="transitionOrder('${o.id}', 'delivered')" class="px-3.5 py-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition shadow-sm">
                      Mark as Delivered <i class="fa-solid fa-arrow-right ml-1"></i>
                    </button>
                  ` : ''
                }
                ${
                  o.status === "delivered" ? `
                    <button onclick="transitionOrder('${o.id}', 'completed')" class="px-4 py-1.5 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition shadow-sm">
                      <i class="fa-solid fa-circle-check mr-1"></i> Complete Order
                    </button>
                  ` : ''
                }
              </div>
            ` : `
              <div class="pt-2 text-right text-xs text-slate-400 border-t border-slate-100">
                ${isBuyer ? 'Order finalized.' : 'Status advances controlled by the buyer.'}
              </div>
            `
          }
        </div>
      `;
    }).join("");
  } catch (err) {
    console.error(err);
  }
}

// Weight Modal Flow
function openWeightModal(orderId, stage) {
  document.getElementById("weightOrderId").value = orderId;
  document.getElementById("weightStage").value = stage;
  document.getElementById("weightStageDisplay").value = stage;
  document.getElementById("weightModalTitle").innerText = `Record ${stage.toUpperCase()} Weight`;
  document.getElementById("weightValue").value = "";
  openModal("weightModal");
}

async function handleRecordWeight(e) {
  e.preventDefault();
  const orderId = document.getElementById("weightOrderId").value;
  const stage = document.getElementById("weightStage").value;
  const weight_kg = document.getElementById("weightValue").value;

  try {
    await api(`/orders/${orderId}/weights`, {
      method: "POST",
      body: JSON.stringify({ stage, weight_kg })
    });
    closeModal("weightModal");
    showToast(`Recorded ${stage} weight: ${weight_kg} kg`);
    loadOrders();
  } catch (err) {
    // Handled
  }
}

// Order Status Transition
async function transitionOrder(orderId, targetStatus) {
  try {
    await api(`/orders/${orderId}/transition`, {
      method: "POST",
      body: JSON.stringify({ target_status: targetStatus })
    });
    showToast(`Order updated to status: ${targetStatus.toUpperCase()}`);
    loadOrders();
  } catch (err) {
    // Handled
  }
}

// Rate Card & Impact Tab
async function loadRateCardAndImpact() {
  try {
    const [rateRes, impactRes] = await Promise.all([
      api("/stats/rate-card"),
      api("/stats/impact")
    ]);

    const cards = rateRes.data;
    const impact = impactRes.data;

    // Render Impact metrics
    document.getElementById("statTotalKg").innerText = `${Number(impact.total_diverted_kg).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} kg`;
    document.getElementById("statTotalOrders").innerText = impact.orders_diverted_count;
    document.getElementById("statCo2Saved").innerText = `${Number(impact.estimated_co2_saved_kg).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} kg`;

    const impactCategories = document.getElementById("impactCategoryBreakdown");
    if (impact.categories && impact.categories.length) {
      impactCategories.innerHTML = impact.categories.map((c) => `
        <div class="bg-white border border-slate-200 rounded-xl p-3 text-xs shadow-sm">
          <div class="text-slate-500 font-semibold truncate">${c.name}</div>
          <div class="text-emerald-600 font-extrabold text-sm mt-1">${Number(c.total_kg).toFixed(1)} kg</div>
          <div class="text-[10px] text-slate-400">${c.order_count} order(s)</div>
        </div>
      `).join("");
    } else {
      impactCategories.innerHTML = `<div class="col-span-full text-xs text-slate-400">Complete orders to see category breakdown.</div>`;
    }

    // Render Rate Card Table
    const tableBody = document.getElementById("rateCardTableBody");
    tableBody.innerHTML = cards.map((c) => {
      const minP = c.min_price_per_kg ? `₹${Number(c.min_price_per_kg).toFixed(2)}` : "-";
      const avgP = c.avg_price_per_kg ? `₹${Number(c.avg_price_per_kg).toFixed(2)}` : "-";
      const maxP = c.max_price_per_kg ? `₹${Number(c.max_price_per_kg).toFixed(2)}` : "-";
      const totQty = c.total_quantity_kg ? `${Number(c.total_quantity_kg).toFixed(1)} kg` : "0 kg";

      return `
        <tr class="hover:bg-slate-50 transition">
          <td class="py-3 px-4 font-semibold text-slate-900">${c.name}</td>
          <td class="py-3 px-4 text-slate-500 uppercase text-xs">${c.unit}</td>
          <td class="py-3 px-4 font-mono font-medium text-slate-700">${minP}</td>
          <td class="py-3 px-4 font-mono font-bold text-emerald-600">${avgP}</td>
          <td class="py-3 px-4 font-mono font-medium text-slate-700">${maxP}</td>
          <td class="py-3 px-4 text-slate-600">${c.listing_count}</td>
          <td class="py-3 px-4 font-medium text-slate-800">${totQty}</td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error(err);
  }
}

// Start
document.addEventListener("DOMContentLoaded", initApp);
