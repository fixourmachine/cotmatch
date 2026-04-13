// UI Controls
function toggleSidebar() { document.getElementById('sidebar').classList.toggle('-translate-x-full'); }

// Postcode Geolocation
let homeCoords = { lat: 51.499842, lon: -0.124638 }; // Default: SW1A 0AA
let lastPostcode = "";

async function fetchLocation() {
    const input = document.getElementById('postcode').value.trim();
    const status = document.getElementById('postcode-status');
    const locWarning = document.getElementById('location-warning-banner');

    if (!input) { 
        homeCoords = { lat: 51.499842, lon: -0.124638 }; 
        status.classList.add('hidden'); 
        if (locWarning) locWarning.classList.add('hidden');
        filterData(); 
        return; 
    }
    
    status.innerText = "Finding coordinates..."; 
    status.classList.remove('hidden'); 
    status.className = "text-xs mt-1 text-blue-500 block";
    
    try {
        let encoded = encodeURIComponent(input);
        let response = await fetch(`https://api.postcodes.io/postcodes/${encoded}`);
        let data = await response.json();
        
        if (data.status === 200) {
            homeCoords = { lat: data.result.latitude, lon: data.result.longitude };
            lastPostcode = input;
            status.innerText = "Ordering by proximity."; 
            status.className = "text-xs mt-1 text-emerald-600 block";
            if (locWarning) locWarning.classList.add('hidden');
            filterData();
        } else {
            // Fallback to outcode
            response = await fetch(`https://api.postcodes.io/outcodes/${encoded}`);
            data = await response.json();
            
            if (data.status === 200) {
                homeCoords = { lat: data.result.latitude, lon: data.result.longitude };
                lastPostcode = input;
                status.innerText = "Ordering by regional proximity."; 
                status.className = "text-xs mt-1 text-emerald-600 block";
                if (locWarning) locWarning.classList.add('hidden');
                filterData();
            } else {
                throw new Error();
            }
        }
    } catch (e) { 
        homeCoords = { lat: 51.499842, lon: -0.124638 }; 
        status.innerText = "Invalid postcode. Try format: SW1A 1AA or SW1A"; 
        status.className = "text-xs mt-1 text-red-500 block"; 
        if (locWarning) locWarning.classList.remove('hidden');
        filterData(); 
    }
}

// Haversine Distance Calculator
function calculateMiles(lat1, lon1, lat2, lon2) {
    const R = 3958.8; 
    const dLat = (lat2 - lat1) * Math.PI / 180; 
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon/2) * Math.sin(dLon/2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}

// NATIONAL DATASET (Dynamic)
let units = [];
let filterByName = "";

// Core Filtering Engine
function filterData() {
    const wIn = parseInt(document.getElementById('weight').value);
    const gIn = parseInt(document.getElementById('gestation').value);
    const lSl = document.getElementById('level').value;
    const oSl = document.getElementById('odn').value;
    
    const req = {
        cpap: document.getElementById('req-cpap').checked, pn: document.getElementById('req-pn').checked,
        long: document.getElementById('req-long').checked, vent: document.getElementById('req-vent').checked,
        stoma: document.getElementById('req-stoma').checked, trachy: document.getElementById('req-trachy').checked,
        ino: document.getElementById('req-ino').checked, ecmo: document.getElementById('req-ecmo').checked,
        cooling: document.getElementById('req-cooling').checked, laser: document.getElementById('req-laser').checked,
        picu: document.getElementById('req-picu').checked, gen: document.getElementById('req-gen').checked,
        neurosurg: document.getElementById('req-neurosurg').checked, cardio: document.getElementById('req-cardio').checked,
        ent: document.getElementById('req-ent').checked, paed_anaes: document.getElementById('req-paed_anaes').checked,
        ltv: document.getElementById('req-ltv').checked, ngt: document.getElementById('req-ngt').checked,
        njt: document.getElementById('req-njt').checked, cont: document.getElementById('req-cont').checked,
        brov: document.getElementById('req-brov').checked, conv: document.getElementById('req-conv').checked,
        pall: document.getElementById('req-pall').checked
    };

    const results = units.filter(u => {
        if (filterByName && u.name !== filterByName) return false;
        if (!isNaN(wIn) && u.wt > 0 && u.wt > wIn) return false;
        if (!isNaN(gIn) && u.gest > 0 && u.gest > gIn) return false;
        if (lSl !== 'all' && u.level < parseInt(lSl)) return false;
        if (oSl !== 'all' && u.odn !== oSl) return false;
        for (let k in req) if (req[k] && u[k] === 0) return false;
        return true;
    });

    if (homeCoords) {
        results.forEach(u => u.dist = calculateMiles(homeCoords.lat, homeCoords.lon, u.lat, u.lon));
        results.sort((a, b) => a.dist - b.dist);
    } else {
        results.sort((a, b) => a.name.localeCompare(b.name));
    }
    
    render(results, req, wIn, gIn, lSl, oSl);
}

// Render Engine
function render(filtered, reqs, wIn, gIn, lSl, oSl) {
    const container = document.getElementById('results-container');
    document.getElementById('result-count').innerText = filtered.length;
    container.innerHTML = '';

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="h-full flex flex-col items-center justify-center text-center p-8">
                <svg class="w-16 h-16 text-slate-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                <h3 class="text-lg font-bold text-slate-800">No matching units found</h3>
                <p class="text-sm text-slate-500 mt-2 max-w-md">Try loosening your criteria. Ensure you aren't selecting advanced surgical features for a Level 1 or 2 search.</p>
                <button onclick="resetFilters()" class="mt-6 px-4 py-2 bg-slate-800 text-white rounded-md text-sm font-medium hover:bg-slate-900 transition-colors">Clear all filters</button>
            </div>
        `;
        return;
    }
    
    const tick = `<svg class="w-3.5 h-3.5 ml-1 text-emerald-600 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"></path></svg>`;
    const grid = document.createElement('div');
    grid.className = 'grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 items-start';

    const styles = {
        ecmo: {l:'ECMO', c:'bg-red-100 text-red-800 border-red-200'}, 
        cooling: {l:'Cooling', c:'bg-cyan-100 text-cyan-800 border-cyan-200'}, 
        ino: {l:'iNO', c:'bg-sky-100 text-sky-800 border-sky-200'}, 
        neurosurg: {l:'Neurosurg', c:'bg-pink-100 text-pink-800 border-pink-200'},
        picu: {l:'PICU', c:'bg-indigo-100 text-indigo-800 border-indigo-200'}, 
        cardio: {l:'Cardiac', c:'bg-rose-100 text-rose-800 border-rose-200'},
        gen: {l:'Gen Surg', c:'bg-blue-50 text-blue-700 border-blue-100'}, 
        laser: {l:'Laser', c:'bg-blue-50 text-blue-700 border-blue-100'},
        ent: {l:'Paed ENT', c:'bg-blue-50 text-blue-700 border-blue-100'}, 
        paed_anaes: {l:'Paed Anaes', c:'bg-blue-50 text-blue-700 border-blue-100'},
        ltv: {l:'LTV', c:'bg-blue-50 text-blue-700 border-blue-100'}
    };

    filtered.forEach(u => {
        let badges = '';
        const rendered = new Set();

        // 1. Render specifically requested badges with tick marks
        for(let k in reqs) {
            if(reqs[k] && u[k] === 1 && styles[k]) {
                badges += `<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border mr-1 mb-1 bg-emerald-50 text-emerald-800 border-emerald-200 ring-1 ring-emerald-400">${styles[k].l} ${tick}</span>`;
                rendered.add(k);
            }
        }

        // 2. Render remaining default badges
        for(let k in styles) {
            if(u[k] === 1 && !rendered.has(k)) {
                badges += `<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border mr-1 mb-1 shadow-sm ${styles[k].c}">${styles[k].l}</span>`;
            }
        }

        let wtD = !isNaN(wIn) ? `<span class="text-emerald-700 font-bold">${u.wt===0?'No Limit':'>'+u.wt+'g'}${tick}</span>` : u.wt===0?'No Limit':'>'+u.wt+'g';
        let gsD = !isNaN(gIn) ? `<span class="text-emerald-700 font-bold">${u.gest===0?'No Limit':'>'+u.gest+'w'}${tick}</span>` : u.gest===0?'No Limit':'>'+u.gest+'w';
        const odnLinks = {
            "London": "https://londonneonatalnetwork.org.uk/",
            "Thames Valley & Wessex": "https://neonatalnetworkssoutheast.nhs.uk/",
            "Kent, Surrey & Sussex": "https://neonatalnetworkssoutheast.nhs.uk/",
            "North West": "https://www.neonatalnetwork.co.uk/",
            "East of England": "https://eoeneonatalpccsicnetwork.nhs.uk/",
            "Northern Ireland": "https://online.hscni.net/partnerships/neonatalni/",
            "Scotland": "https://www.perinatalnetwork.nhs.scot/"
        };
        let odnUrl = odnLinks[u.odn] || `https://www.google.com/search?q=${encodeURIComponent(u.odn + ' UK')}`;
        let odnHtml = `<a href="${odnUrl}" target="_blank" rel="noopener noreferrer" class="hover:text-blue-600 hover:underline inline-block w-full align-top" title="${u.odn}">${u.odn}</a>`;
        let odnD = (oSl !== 'all' && u.odn === oSl) ? `<span class="text-emerald-700 font-bold inline-flex items-start gap-1 w-full"><span class="block w-full">${odnHtml}</span> <span class="flex-shrink-0 mt-0.5">${tick}</span></span>` : odnHtml;
        let levelBg = (lSl!=='all' && u.level >= parseInt(lSl)) ? 'bg-emerald-100 text-emerald-800 ring-1 ring-emerald-400' : (u.level===3?'bg-purple-100 text-purple-700':'bg-teal-100 text-teal-700');
        
        let phone_link_str = u.phone.replace(/\s+/g,'');
        let trphone_link_str = u.transport_phone.replace(/\s+/g,'');
        
        let destStr = encodeURIComponent(u.name + ' ' + u.address + ' ' + u.postcode);
        let gmapsLink = `https://www.google.com/maps/dir/?api=1&destination=${destStr}`;
        if (lastPostcode) {
            gmapsLink += `&origin=${encodeURIComponent(lastPostcode)}`;
        }
        
        let displayAddr = u.address;
        if (!displayAddr.includes(u.postcode)) {
            displayAddr += ", " + u.postcode;
        }
        
        let address_html = `<a href="${gmapsLink}" target="_blank" rel="noopener noreferrer" class="hover:text-blue-600 hover:underline flex items-center gap-1">${displayAddr} <svg class="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg></a>`;

        grid.innerHTML += `
            <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col hover:shadow-md transition-all relative">
                <div class="flex justify-between items-start mb-2 gap-2">
                    <h3 class="text-base font-bold text-slate-900 leading-tight">${u.name}</h3>
                    <div class="flex items-center gap-1 flex-shrink-0">
                        <span class="px-2 py-1 rounded text-xs font-bold ${levelBg}">L${u.level}</span>
                        ${u.dist?`<span class="px-2.5 py-1 rounded-full bg-slate-800 text-white text-xs font-bold flex items-center shadow-sm"><svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path></svg>${u.dist.toFixed(1)}m</span>`:''}
                    </div>
                </div>
                <p class="text-xs text-slate-400 mb-1"><a href="https://www.google.com/search?q=${encodeURIComponent(u.trust + ' UK')}" target="_blank" rel="noopener noreferrer" class="hover:text-blue-600 hover:underline" title="Search ${u.trust}">${u.trust}</a></p>
                <p class="text-xs text-slate-500 mb-4 w-full">${address_html}</p>
                
                <div class="grid grid-cols-2 gap-3 mb-4 bg-slate-50 p-3 rounded-lg text-xs border border-slate-100">
                    <div class="min-w-0 break-words"><span class="block text-slate-400 mb-0.5">Network</span><span class="font-semibold block w-full leading-tight pr-1">${odnD}</span></div>
                    <div class="min-w-0 break-words">
                        <span class="block text-slate-400 mb-0.5">Transport</span>
                        <a href="tel:${trphone_link_str}" class="font-semibold text-slate-900 hover:text-blue-600 hover:underline block w-full leading-tight" title="${u.transport}">${u.transport}</a>
                    </div>
                    <div class="col-span-2 flex items-center pt-2 mt-2 border-t border-slate-200 group">
                        <a href="tel:${phone_link_str}" class="flex items-center group-hover:text-blue-600 hover:underline">
                            <svg class="w-4 h-4 text-slate-400 group-hover:text-blue-600 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path></svg>
                            <span class="font-semibold text-slate-900 text-sm tracking-wide group-hover:text-blue-600">${u.phone}</span>
                        </a>
                    </div>
                </div>

                <div class="mt-auto">
                    <div class="flex justify-between text-xs mb-3 pb-3 border-b border-slate-100">
                        <div class="pr-2"><span class="text-slate-400">Accepts from Wt:</span><br> ${wtD}</div>
                        <div><span class="text-slate-400">Accepts from Gest:</span><br> ${gsD}</div>
                    </div>
                    <div class="flex flex-wrap gap-y-1">${badges}</div>
                </div>
            </div>`;
    });

    container.appendChild(grid);
}

// State Management
function resetFilters() {
    document.getElementById('postcode').value = ''; 
    document.getElementById('postcode-status').classList.add('hidden');
    
    const locWarning = document.getElementById('location-warning-banner');
    if (locWarning) locWarning.classList.add('hidden');

    homeCoords = { lat: 51.499842, lon: -0.124638 }; 
    document.querySelectorAll('input[type="number"]').forEach(e => e.value = '');
    document.querySelectorAll('input[type="checkbox"]').forEach(e => e.checked = false);
    document.getElementById('level').value = 'all'; 
    document.getElementById('odn').value = 'all';
    document.getElementById('unitSearch').value = '';
    const clearBtn = document.getElementById('clearSearchBtn');
    if (clearBtn) clearBtn.classList.add('hidden');
    document.getElementById('searchSuggestions').classList.add('hidden');
    filterByName = "";
    filterData();
}

// Fuzzy Search Implementation
function handleSearchInput() {
    const searchEl = document.getElementById('unitSearch');
    const queryWords = searchEl.value.toLowerCase().split(/\s+/).filter(w => w.length > 0);
    const queryRaw = searchEl.value.toLowerCase().replace(/[^a-z0-9]/g, '');
    const suggestionsDiv = document.getElementById('searchSuggestions');
    const clearBtn = document.getElementById('clearSearchBtn');
    
    if (searchEl.value.length > 0) {
        if (clearBtn) clearBtn.classList.remove('hidden');
    } else {
        if (clearBtn) clearBtn.classList.add('hidden');
    }
    
    if (searchEl.value.length < 2) {
        suggestionsDiv.classList.add('hidden');
        if (filterByName) {
            filterByName = "";
            filterData();
        }
        return;
    }
    
    filterByName = "";

    const matches = units.filter(u => {
        const fullText = [
            u.name, u.name_full, u.trust, u.trust_full,
            u.address, u.postcode, u.odn, u.odn_full,
            u.transport, u.transport_full
        ].join(" ").toLowerCase();
        
        if (queryWords.every(w => fullText.includes(w))) return true;

        let qIdx = 0;
        const normName = u.name_full.toLowerCase().replace(/[^a-z0-9]/g, '');
        for (let i = 0; i < normName.length && qIdx < queryRaw.length; i++) { if (normName[i] === queryRaw[qIdx]) qIdx++; }
        return qIdx === queryRaw.length;
    }).slice(0, 10); 

    if (matches.length > 0) {
        suggestionsDiv.innerHTML = matches.map(m => `
            <div class="cursor-pointer select-none relative py-2 pl-3 pr-9 hover:bg-blue-50 text-slate-900 border-b border-slate-100 last:border-0" onclick="selectHospital('${m.name.replace(/'/g, "\\'")}')">
                <span class="block truncate font-medium">${m.name}</span>
                <span class="block truncate text-xs text-slate-500">${m.trust}</span>
            </div>
        `).join('');
        suggestionsDiv.classList.remove('hidden');
    } else {
        suggestionsDiv.innerHTML = `<div class="py-2 pl-3 text-slate-500 text-sm italic">No matches found...</div>`;
        suggestionsDiv.classList.remove('hidden');
    }
}

function selectHospital(name) {
    document.getElementById('unitSearch').value = name;
    const clearBtn = document.getElementById('clearSearchBtn');
    if (clearBtn) clearBtn.classList.remove('hidden');
    document.getElementById('searchSuggestions').classList.add('hidden');
    filterByName = name;
    filterData();
}

function clearSearch() {
    document.getElementById('unitSearch').value = '';
    const clearBtn = document.getElementById('clearSearchBtn');
    if (clearBtn) clearBtn.classList.add('hidden');
    document.getElementById('searchSuggestions').classList.add('hidden');
    filterByName = '';
    filterData();
}

// Hide dropdown
document.addEventListener('click', (e) => {
    const el = document.getElementById('unitSearch');
    const sug = document.getElementById('searchSuggestions');
    if (el && sug && !el.contains(e.target) && !sug.contains(e.target)) {
        sug.classList.add('hidden');
    }
});

// App Init & Data Ingestion
async function initApp() {
    try {
        const response = await fetch('./uk_neonatal_units.json');
        const rawData = await response.json();
        
        units = rawData.map(unit => ({
            name: unit.unit_name,
            name_full: unit.unit_name_full || unit.unit_name,
            trust: unit.trust,
            trust_full: unit.trust_full || unit.trust,
            address: unit.address,
            postcode: unit.unit_postcode,
            phone: unit.telephone_numbers && unit.telephone_numbers.length > 0 ? unit.telephone_numbers[0] : "Unlisted",
            transport: unit.regional_transport_team,
            transport_full: unit.regional_transport_team_full || unit.regional_transport_team,
            transport_phone: unit.transport_telephone || "000 000 000",
            level: unit.minimum_level_of_care ? parseInt(String(unit.minimum_level_of_care).replace('L', '')) : 1,
            odn: unit.network_odn || "Unknown",
            odn_full: unit.network_odn_full || unit.network_odn,
            wt: unit.accepts_weight_from || 0,
            gest: unit.accepts_gestation_from || 0,
            lat: unit.latitude,
            lon: unit.longitude,
            cpap: unit.nursing_capabilities.cpap_hhfnc ? 1 : 0,
            ngt: unit.nursing_capabilities.hourly_ngt_feeds ? 1 : 0,
            njt: unit.nursing_capabilities.njt_care ? 1 : 0,
            cont: unit.nursing_capabilities.continuous_pump_feeds ? 1 : 0,
            pn: unit.nursing_capabilities.parenteral_nutrition ? 1 : 0,
            long: unit.nursing_capabilities.long_line_picc ? 1 : 0,
            brov: unit.nursing_capabilities.broviac_hickman ? 1 : 0,
            vent: unit.nursing_capabilities.ventricular_taps ? 1 : 0,
            conv: unit.nursing_capabilities.convulsion_mgmt ? 1 : 0,
            stoma: unit.nursing_capabilities.stoma_care ? 1 : 0,
            trachy: unit.nursing_capabilities.tracheostomy_care ? 1 : 0,
            pall: unit.nursing_capabilities.palliative_care ? 1 : 0,
            ino: unit.advanced_facilities.ino ? 1 : 0,
            ecmo: unit.advanced_facilities.respiratory_ecmo ? 1 : 0,
            cooling: unit.advanced_facilities.active_cooling ? 1 : 0,
            laser: unit.advanced_facilities.laser_rop ? 1 : 0,
            picu: unit.advanced_facilities.on_site_picu ? 1 : 0,
            gen: unit.specialties.on_site_gen_surgery ? 1 : 0,
            neurosurg: unit.specialties.on_site_neurosurgery ? 1 : 0,
            cardio: unit.specialties.on_site_cardiology ? 1 : 0,
            ent: unit.specialties.paediatric_ent ? 1 : 0,
            paed_anaes: unit.specialties.paed_anaesthetic_support ? 1 : 0,
            ltv: unit.specialties.paed_resp_ltv ? 1 : 0
        }));

        const odns = [...new Set(units.map(u => u.odn))].filter(Boolean).sort();
        const select = document.getElementById('odn');
        select.innerHTML = '<option value="all">All Networks</option>';
        odns.forEach(odn => {
            select.innerHTML += `<option value="${odn}">${odn}</option>`;
        });

        const locWarning = document.getElementById('location-warning-banner');
        if (locWarning) {
             locWarning.classList.add('hidden');
        }

        filterData();
    } catch (err) {
        console.error("Failed to fetch unit data:", err);
        document.getElementById('results-container').innerHTML = `<div class="p-8 text-center text-red-500">Failed to load neonatal database. Ensure you have a connection or try refreshing.</div>`;
    }
}

// Init and Register Service Worker
window.onload = () => {
    initApp();
    
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('./sw.js').then(reg => {
            console.log('CotMatch PWA Service Worker registered:', reg.scope);
        }).catch(err => {
            console.error('Service Worker registration failed:', err);
        });
    }
};
