/**
 * CricPulse Developer Portal Client Interactions
 * Unbounded Postman-Style API Workbench & Utilities.
 */

// 1. One-click Copy to Clipboard with Tooltip
function copyToClipboard(text, buttonElement) {
  navigator.clipboard.writeText(text).then(() => {
    const originalText = buttonElement.innerHTML;
    buttonElement.innerHTML = `
      <svg class="w-4 h-4 text-emerald-600 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
      </svg> Copied!
    `;
    buttonElement.classList.add("bg-emerald-50", "border-emerald-300", "text-emerald-700");

    setTimeout(() => {
      buttonElement.innerHTML = originalText;
      buttonElement.classList.remove("bg-emerald-50", "border-emerald-300", "text-emerald-700");
    }, 2000);
  }).catch(err => {
    console.error("Could not copy text: ", err);
  });
}

// 2. Toggle API Key Visibility (Reveal / Mask)
function toggleKeyVisibility(elementId, fullKey, maskedKey, toggleBtn) {
  const target = document.getElementById(elementId);
  if (!target) return;

  if (target.getAttribute("data-masked") === "true") {
    target.textContent = fullKey;
    target.setAttribute("data-masked", "false");
    toggleBtn.innerHTML = `
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18"></path>
      </svg>
      <span>Hide</span>
    `;
  } else {
    target.textContent = maskedKey;
    target.setAttribute("data-masked", "true");
    toggleBtn.innerHTML = `
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
      </svg>
      <span>Reveal</span>
    `;
  }
}

// 3. Mobile Navigation Menu Toggle & Auto Dismiss Alerts
document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.getElementById("mobile-menu-btn");
  const mobileMenu = document.getElementById("mobile-menu");

  if (menuToggle && mobileMenu) {
    menuToggle.addEventListener("click", () => {
      mobileMenu.classList.toggle("hidden");
    });
  }

  const alerts = document.querySelectorAll(".alert-auto-dismiss");
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = "opacity 0.4s ease";
      alert.style.opacity = "0";
      setTimeout(() => alert.remove(), 400);
    }, 5000);
  });

  // Initialize Workbench parameter rows if workbench input exists
  const urlInput = document.getElementById("workbench-url-input");
  if (urlInput) {
    syncParamsFromUrl();
    updateLiveCurl();
  }
});


/* =========================================================================
   4. UNBOUNDED API WORKBENCH (Postman/RapidAPI Style)
   ========================================================================= */

// Load a preset template into the editable URL bar
function loadPresetUrl(presetUrl) {
  const urlInput = document.getElementById("workbench-url-input");
  if (!urlInput) return;
  urlInput.value = presetUrl;
  syncParamsFromUrl();
  updateLiveCurl();
}

// Clear the entire URL input
function clearWorkbenchUrl() {
  const urlInput = document.getElementById("workbench-url-input");
  if (!urlInput) return;
  urlInput.value = "/api/v1/";
  syncParamsFromUrl();
  updateLiveCurl();
}

// Parse query parameters from the URL bar into editable Key-Value rows
function syncParamsFromUrl() {
  const urlInput = document.getElementById("workbench-url-input");
  const container = document.getElementById("workbench-params-container");
  if (!urlInput || !container) return;

  const fullUrl = urlInput.value.trim();
  const qIndex = fullUrl.indexOf("?");
  container.innerHTML = "";

  if (qIndex !== -1 && qIndex < fullUrl.length - 1) {
    const queryString = fullUrl.substring(qIndex + 1);
    const searchParams = new URLSearchParams(queryString);

    searchParams.forEach((val, key) => {
      addParamRow(key, val, false);
    });
  }

  updateParamCount();
  updateLiveCurl();
}

// Rebuild the URL string from the base path and current Key-Value rows
function syncUrlFromParams() {
  const urlInput = document.getElementById("workbench-url-input");
  const container = document.getElementById("workbench-params-container");
  if (!urlInput || !container) return;

  const currentVal = urlInput.value.trim();
  const qIndex = currentVal.indexOf("?");
  const basePath = qIndex !== -1 ? currentVal.substring(0, qIndex) : currentVal;

  const rows = container.querySelectorAll(".param-row");
  const params = new URLSearchParams();

  rows.forEach(row => {
    const keyInput = row.querySelector(".param-key");
    const valInput = row.querySelector(".param-val");
    const key = keyInput ? keyInput.value.trim() : "";
    const val = valInput ? valInput.value.trim() : "";
    if (key) {
      params.append(key, val);
    }
  });

  const queryString = params.toString();
  urlInput.value = queryString ? `${basePath}?${queryString}` : basePath;
  updateParamCount();
  updateLiveCurl();
}

// Add a single parameter row
function addParamRow(key = "", val = "", autoSync = true) {
  const container = document.getElementById("workbench-params-container");
  if (!container) return;

  const row = document.createElement("div");
  row.className = "param-row grid grid-cols-12 gap-2 items-center";
  row.innerHTML = `
    <div class="col-span-5">
      <input type="text" value="${escapeHtml(key)}" placeholder="Parameter name (e.g. team1)" class="param-key w-full px-3 py-1.5 text-xs font-mono rounded-lg border border-slate-300 focus:ring-1 focus:ring-emerald-500 outline-none">
    </div>
    <div class="col-span-6">
      <input type="text" value="${escapeHtml(val)}" placeholder="Value (e.g. CSK)" class="param-val w-full px-3 py-1.5 text-xs font-mono rounded-lg border border-slate-300 focus:ring-1 focus:ring-emerald-500 outline-none">
    </div>
    <div class="col-span-1 text-right">
      <button type="button" onclick="this.closest('.param-row').remove(); syncUrlFromParams();" class="p-1 rounded text-slate-400 hover:text-rose-600 transition" title="Delete parameter">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
      </button>
    </div>
  `;

  // Attach live input listeners to trigger URL update
  row.querySelectorAll("input").forEach(input => {
    input.addEventListener("input", syncUrlFromParams);
  });

  container.appendChild(row);
  if (autoSync) {
    syncUrlFromParams();
  }
}

function updateParamCount() {
  const container = document.getElementById("workbench-params-container");
  const countBadge = document.getElementById("params-count-badge");
  if (container && countBadge) {
    const count = container.querySelectorAll(".param-row").length;
    countBadge.textContent = count;
  }
}

// Toggle parameter table collapse
function toggleParamsSection() {
  const section = document.getElementById("workbench-params-section");
  const icon = document.getElementById("params-toggle-icon");
  if (!section) return;

  const isHidden = section.classList.contains("hidden");
  if (isHidden) {
    section.classList.remove("hidden");
    if (icon) icon.style.transform = "rotate(180deg)";
  } else {
    section.classList.add("hidden");
    if (icon) icon.style.transform = "rotate(0deg)";
  }
}

// Update the live cURL preview tab
function updateLiveCurl() {
  const urlInput = document.getElementById("workbench-url-input");
  const curlBox = document.getElementById("workbench-curl-display");
  const engineBase = document.getElementById("workbench-engine-base");
  const keyInput = document.getElementById("workbench-active-key");

  if (!urlInput || !curlBox) return;

  const base = engineBase ? engineBase.value : "https://cricpulse-engine.onrender.com";
  const endpoint = urlInput.value.trim();
  const apiKey = keyInput ? keyInput.value : "cric_live_YOUR_KEY";

  const curlCommand = `curl -X GET "${base}${endpoint}" \\\n     -H "X-API-Key: ${apiKey}" \\\n     -H "Accept: application/json"`;
  curlBox.textContent = curlCommand;
}

// Switch Response Tabs (JSON Payload vs Captured Headers vs cURL)
function switchResponseTab(tabName) {
  const tabs = ["json", "headers", "curl"];
  tabs.forEach(t => {
    const btn = document.getElementById(`tab-btn-${t}`);
    const panel = document.getElementById(`tab-panel-${t}`);
    if (t === tabName) {
      if (btn) btn.className = "px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 text-white transition";
      if (panel) panel.classList.remove("hidden");
    } else {
      if (btn) btn.className = "px-3 py-1.5 text-xs font-semibold rounded-lg text-slate-400 hover:text-slate-200 transition";
      if (panel) panel.classList.add("hidden");
    }
  });
}

// Main execution runner: Sends request via Django proxy with custom endpoint
async function executeWorkbench(proxyUrl) {
  const urlInput = document.getElementById("workbench-url-input");
  const resultBox = document.getElementById("workbench-result");
  const statusBadge = document.getElementById("workbench-status");
  const latencyBadge = document.getElementById("workbench-latency");
  const sizeBadge = document.getElementById("workbench-size");
  const runBtn = document.getElementById("workbench-run-btn");
  const headersTableBody = document.getElementById("workbench-headers-body");

  if (!urlInput || !resultBox) return;

  const endpoint = urlInput.value.trim();
  if (!endpoint) {
    alert("Please enter a valid endpoint path.");
    return;
  }

  // Set running state
  runBtn.disabled = true;
  runBtn.innerHTML = `
    <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
    Sending...
  `;
  resultBox.textContent = `// Contacting CricPulse-Engine...\n// Path: ${endpoint}`;

  // Switch to JSON view on run
  switchResponseTab("json");

  try {
    const fetchUrl = `${proxyUrl}?endpoint=${encodeURIComponent(endpoint)}`;
    const startTime = performance.now();
    const res = await fetch(fetchUrl);
    const duration = (performance.now() - startTime).toFixed(1);
    const json = await res.json();

    runBtn.disabled = false;
    runBtn.innerHTML = `
      <span>Send Request</span>
      <svg class="w-4 h-4 ml-1.5 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
      </svg>
    `;

    // Status badge formatting
    const statusCode = json.status_code || res.status;
    const isSuccess = statusCode >= 200 && statusCode < 300;
    const isClientErr = statusCode >= 400 && statusCode < 500;

    if (statusBadge) {
      statusBadge.textContent = `${statusCode} ${json.status_text || (isSuccess ? "OK" : "Error")}`;
      if (isSuccess) {
        statusBadge.className = "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200";
      } else if (isClientErr) {
        statusBadge.className = "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200";
      } else {
        statusBadge.className = "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200";
      }
    }

    // Latency & size badges
    if (latencyBadge) {
      latencyBadge.textContent = json.process_time || `${duration}ms`;
    }
    if (sizeBadge) {
      const sizeBytes = json.size_bytes || JSON.stringify(json.data || json).length;
      sizeBadge.textContent = formatBytes(sizeBytes);
    }

    // Populate Headers Tab
    if (headersTableBody && json.headers) {
      headersTableBody.innerHTML = "";
      Object.entries(json.headers).forEach(([k, v]) => {
        const tr = document.createElement("tr");
        tr.className = "border-b border-slate-800/80 font-mono text-xs";
        tr.innerHTML = `
          <td class="py-2 px-3 text-sky-400 font-medium">${escapeHtml(k)}</td>
          <td class="py-2 px-3 text-slate-300 select-all">${escapeHtml(String(v))}</td>
        `;
        headersTableBody.appendChild(tr);
      });
    }

    // Display formatted JSON
    resultBox.textContent = JSON.stringify(json.data || json, null, 2);
  } catch (err) {
    runBtn.disabled = false;
    runBtn.innerHTML = `<span>Send Request</span>`;
    resultBox.textContent = `// Error executing request:\n${err.message}`;
    if (statusBadge) {
      statusBadge.textContent = "Error";
      statusBadge.className = "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800";
    }
  }
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

// 5. Multi-Language Code Snippet Tab Switcher (Dashboard & Docs)
function switchSnippetTab(lang, prefix = "snippet") {
  const languages = ["python", "javascript", "java", "go", "csharp", "curl"];
  languages.forEach(l => {
    const btn = document.getElementById(`${prefix}-tab-${l}`);
    const panel = document.getElementById(`${prefix}-panel-${l}`);
    if (l === lang) {
      if (btn) {
        btn.className = "px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 text-white shadow-sm transition";
      }
      if (panel) panel.classList.remove("hidden");
    } else {
      if (btn) {
        btn.className = "px-3.5 py-1.5 text-xs font-semibold rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition";
      }
      if (panel) panel.classList.add("hidden");
    }
  });
}
