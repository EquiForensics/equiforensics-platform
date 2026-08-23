// NOTE: Make sure this URL matches your live Render.com backend URL!
const API_BASE = 'https://equiforensics-api.onrender.com'; 
let dbClient = null;
let currentUser = null;
let currentTab = 'experts';
let viewMode = 'card'; 
let jitsiApi = null;

async function initApp() {
    try {
        const res = await fetch(`${API_BASE}/config`);
        const config = await res.json();
        dbClient = window.supabase.createClient(config.supabase_url, config.supabase_key);
        await checkSession();
        switchTab('experts');
    } catch (err) {
        document.getElementById('results-grid').innerHTML = `<p class="text-red-400 text-center mt-10">Cannot connect to backend server. Ensure Docker is running.</p>`;
    }
}

async function checkSession() {
    if (!dbClient) return;
    const { data: { session } } = await dbClient.auth.getSession();
    updateAuthUI(session?.user);
}

function updateAuthUI(user) {
    currentUser = user;
    const nav = document.getElementById('auth-nav-section');
    const dashTab = document.getElementById('tab-dashboard');
    
    if (user) {
        nav.innerHTML = `<span class="text-sm text-efGray mr-4 hidden md:inline-block">${user.email}</span>
                         <button onclick="handleLogout()" class="text-sm font-semibold hover:text-white text-gray-300">Sign Out</button>`;
        dashTab.classList.remove('hidden');
    } else {
        nav.innerHTML = `<button onclick="openAuthModal()" class="text-sm font-semibold hover:text-white text-gray-300 transition">Sign In</button>
                         <button onclick="openAuthModal()" class="text-sm font-bold bg-white text-black px-4 py-2 rounded hover:bg-gray-200 transition">Join Network</button>`;
        dashTab.classList.add('hidden');
        if(currentTab === 'dashboard') switchTab('experts');
    }
}

async function handleSignup() {
    const email = document.getElementById('auth-email').value;
    const pass = document.getElementById('auth-password').value;
    showAuthMsg("Processing registration...", "text-efYellow");
    const { error } = await dbClient.auth.signUp({ email, password: pass });
    if (error) showAuthMsg(error.message, "text-red-500");
    else showAuthMsg("Success! Account created.", "text-green-500");
}

async function handleLogin() {
    const email = document.getElementById('auth-email').value;
    const pass = document.getElementById('auth-password').value;
    const { data, error } = await dbClient.auth.signInWithPassword({ email, password: pass });
    if (error) showAuthMsg(error.message, "text-red-500");
    else { closeAuthModal(); updateAuthUI(data.user); }
}

async function handleLogout() {
    await dbClient.auth.signOut();
    updateAuthUI(null);
}

function showAuthMsg(text, color) {
    const msg = document.getElementById('auth-message');
    msg.className = `text-center text-sm font-semibold mt-4 block ${color}`;
    msg.innerText = text;
}

function openAuthModal() { document.getElementById('auth-modal').classList.add('modal-active'); }
function closeAuthModal() { document.getElementById('auth-modal').classList.remove('modal-active'); }

function toggleViewMode() {
    viewMode = viewMode === 'card' ? 'list' : 'card';
    const btnText = document.getElementById('view-icon-text');
    const icon = document.getElementById('view-icon');
    
    if (viewMode === 'list') {
        btnText.innerText = "List";
        icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>`;
    } else {
        btnText.innerText = "Grid";
        icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path>`;
    }
    runSearch(); 
}

function switchTab(tab) {
    currentTab = tab;
    ['experts', 'papers', 'labs', 'dashboard'].forEach(t => {
        const btn = document.getElementById(`tab-${t}`);
        if(!btn) return;
        btn.className = (t === tab) ? "px-6 py-2.5 rounded-lg font-bold bg-efYellow text-black transition" : "px-6 py-2.5 rounded-lg font-bold bg-efDark text-efGray hover:text-white border border-gray-800 transition";
    });

    const searchSection = document.getElementById('search-section');
    const heroSection = document.getElementById('hero-section');
    const grid = document.getElementById('results-grid');
    const dashboard = document.getElementById('dashboard-section');
    const yearFilter = document.getElementById('year-filter');
    const viewToggle = document.getElementById('view-toggle-btn');
    const searchInput = document.getElementById('search-input');

    searchInput.value = "";
    yearFilter.value = "2000";
    grid.innerHTML = ""; 
    
    if (tab === 'dashboard') {
        searchSection.classList.add('hidden');
        heroSection.classList.add('hidden');
        grid.classList.add('hidden');
        dashboard.classList.remove('hidden');
        loadDashboard();
    } else {
        dashboard.classList.add('hidden');
        grid.classList.remove('hidden');
        heroSection.classList.remove('hidden');
        
        if (tab === 'papers') {
            searchSection.classList.remove('hidden');
            yearFilter.classList.remove('hidden');
            viewToggle.classList.remove('hidden');
            searchInput.placeholder = "Search methods, keywords, authors...";
            runSearch(); 
        } else if (tab === 'labs') {
            searchSection.classList.remove('hidden');
            yearFilter.classList.add('hidden');
            viewToggle.classList.add('hidden');
            searchInput.placeholder = "Search labs by location or name...";
            runSearch(); 
        } else {
            searchSection.classList.add('hidden');
            runSearch(); 
        }
    }
}

async function runSearch() {
    const query = document.getElementById('search-input').value.trim() || "*";
    const grid = document.getElementById('results-grid');
    grid.innerHTML = `<p class="text-efYellow text-center py-8 animate-pulse">Querying global infrastructure...</p>`;

    try {
        let endpoint = '';
        if(currentTab === 'experts') {
            grid.className = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 scrollable-container pr-2";
            endpoint = `/search-experts`;
        }
        if(currentTab === 'labs') {
            grid.className = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 scrollable-container pr-2";
            endpoint = `/search-labs?query=${encodeURIComponent(query)}`;
        }
        if(currentTab === 'papers') {
            const minYear = document.getElementById('year-filter').value;
            endpoint = `/search-papers?query=${encodeURIComponent(query)}&min_year=${minYear}`;
        }

        const res = await fetch(`${API_BASE}${endpoint}`);
        const data = await res.json();
        
        grid.innerHTML = "";
        if(!data.results || data.results.length === 0) {
            grid.innerHTML = `<p class="text-efGray text-center py-8">No results found.</p>`;
            return;
        }

        if(currentTab === 'experts') renderExperts(data.results);
        if(currentTab === 'papers') renderPapers(data.results, grid);
        if(currentTab === 'labs') renderLabs(data.results);

    } catch(e) {
        grid.innerHTML = `<p class="text-red-400 text-center py-8">Failed to fetch data.</p>`;
    }
}

function renderExperts(experts) {
    const grid = document.getElementById('results-grid');
    grid.innerHTML = experts.map(exp => `
        <div class="bg-efDark p-6 rounded-xl border border-gray-800 flex flex-col justify-between hover:border-gray-600 transition h-full">
            <div>
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h3 class="text-white font-bold text-lg">${exp.full_name || 'Anonymous Expert'}</h3>
                        <p class="text-efYellow text-sm font-semibold">${exp.city || 'Global Network'}</p>
                    </div>
                    <span class="bg-green-900/50 text-green-400 border border-green-800 text-[10px] uppercase font-bold px-2 py-1 rounded">Available</span>
                </div>
                <p class="text-sm text-efGray mb-6 line-clamp-3">${exp.bio || 'Professional forensic expert.'}</p>
            </div>
            <button onclick="launchConsultation('${exp.id}')" class="w-full bg-white text-black font-bold py-2.5 rounded-lg hover:bg-gray-200 transition text-sm mt-auto">
                Request Secure Consultation
            </button>
        </div>
    `).join('');
}

function renderPapers(papers, container) {
    container.className = viewMode === 'card' 
        ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 scrollable-container pr-2"
        : "flex flex-col gap-4 scrollable-container pr-2";

    container.innerHTML = papers.map(p => {
        const authors = (p.authors && p.authors.length) ? p.authors.slice(0, 2).join(", ") : "Unknown Author";
        const mockDescription = `A scientific analysis evaluating methodologies and peer-reviewed standards within ${p.discipline || 'forensic science'}. Published in ${p.publication_year}.`;
        
        if (viewMode === 'list') {
            return `
            <div class="bg-efDark p-5 rounded-xl border border-gray-800 hover:border-efYellow transition shadow flex flex-col md:flex-row justify-between items-start md:items-center group">
                <div class="flex-1 pr-6 mb-4 md:mb-0">
                    <span class="text-efYellow text-[10px] font-bold uppercase tracking-wider mb-1 block">${p.discipline || 'Forensics'}</span>
                    <h3 class="text-white font-bold text-lg mb-1 leading-snug">${p.title}</h3>
                    <p class="text-sm text-efGray mb-2 line-clamp-2">${mockDescription}</p>
                    <p class="text-xs text-gray-500">👥 ${authors} • Year: ${p.publication_year} • Citations: ${p.citation_count}</p>
                </div>
                <div class="flex items-center gap-3 w-full md:w-auto justify-end border-t border-gray-800 md:border-none pt-4 md:pt-0">
                    <button onclick="savePaper('${p.id}')" title="Save to Dashboard" class="text-gray-500 hover:text-efYellow p-2 bg-black rounded-lg border border-gray-800 transition">
                        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z"></path></svg>
                    </button>
                    ${p.pdf_url ? `<a href="${p.pdf_url}" target="_blank" class="bg-white text-black px-4 py-2 rounded-lg font-bold hover:bg-gray-200 transition text-sm">Read PDF</a>` : ''}
                </div>
            </div>`;
        } else {
            return `
            <div class="bg-efDark p-6 rounded-xl border border-gray-800 hover:border-efYellow transition shadow-lg flex flex-col justify-between relative group h-full">
                <button onclick="savePaper('${p.id}')" title="Save to Dashboard" class="absolute top-4 right-4 text-gray-500 hover:text-efYellow transition z-10 bg-black/50 p-1.5 rounded">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z"></path></svg>
                </button>
                <div>
                    <div class="mb-3 pr-8">
                        <span class="bg-gray-800 text-gray-300 text-[10px] font-bold px-2 py-1 rounded uppercase tracking-wider">${p.discipline || 'Forensics'}</span>
                    </div>
                    <h3 class="text-white font-bold text-base mb-2 leading-snug">${p.title}</h3>
                    <p class="text-sm text-efGray mb-4 line-clamp-3">${mockDescription}</p>
                </div>
                <div class="mt-auto pt-4 border-t border-gray-800">
                    <p class="text-xs text-gray-400 mb-2">👥 ${authors} • ${p.publication_year}</p>
                    <div class="flex justify-between items-center">
                        <span class="text-xs text-gray-500">Citations: ${p.citation_count || 0}</span>
                        ${p.pdf_url ? `<a href="${p.pdf_url}" target="_blank" class="text-efYellow hover:underline text-xs font-bold">PDF ↗</a>` : ''}
                    </div>
                </div>
            </div>`;
        }
    }).join('');
}

function renderLabs(labs) {
    const grid = document.getElementById('results-grid');
    grid.innerHTML = labs.map(lab => `
        <div class="bg-efDark p-6 rounded-xl border border-gray-800 flex flex-col justify-between h-full">
            <div>
                <div class="flex justify-between items-start mb-2">
                    <h3 class="text-white font-bold text-lg">${lab.lab_name}</h3>
                    ${lab.is_iso_17025 ? `<span class="bg-efYellow text-black text-[10px] font-bold px-2 py-1 rounded">ISO 17025</span>` : ''}
                </div>
                <p class="text-sm text-efGray mb-4">📍 ${lab.city}, ${lab.country}</p>
            </div>
        </div>
    `).join('');
}

async function loadDashboard() {
    if(!currentUser) return;
    const { data: profile } = await dbClient.from('profiles').select('*').eq('id', currentUser.id).single();
    if(profile) {
        document.getElementById('prof-name').value = profile.full_name || '';
        document.getElementById('prof-city').value = profile.city || '';
        document.getElementById('prof-bio').value = profile.bio || '';
        document.getElementById('prof-available').checked = profile.is_available;
    }
    const { data: saved } = await dbClient.from('saved_papers').select(`paper_id, papers ( id, title, publication_year, discipline, authors, pdf_url )`).order('saved_at', { ascending: false });
    const grid = document.getElementById('saved-papers-grid');
    if(saved && saved.length > 0) {
        const paperObjects = saved.map(s => s.papers).filter(p => p != null);
        viewMode = 'card';
        renderPapers(paperObjects, grid);
    } else {
        grid.innerHTML = `<p class="text-efGray text-sm">You haven't saved any papers yet.</p>`;
    }
}

// NEW: Upload to Storage & Extract Text
async function uploadAndExtractPDF() {
    const fileInput = document.getElementById('pdf-upload');
    const msg = document.getElementById('pdf-msg');
    const btn = document.getElementById('pdf-btn');

    if (!fileInput.files[0]) return alert("Please select a PDF first.");
    const file = fileInput.files[0];

    // UI Loading state
    btn.innerText = "Processing...";
    btn.disabled = true;
    msg.classList.add('hidden');

    try {
        // 1. Upload to Supabase Storage 
        const fileExt = file.name.split('.').pop();
        const fileName = `${currentUser.id}-${Math.random().toString(36).substring(7)}.${fileExt}`;
        
        await dbClient.storage.from('resumes').upload(fileName, file, { upsert: true });

        // 2. Extract Text via FastAPI Backend
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch(`${API_BASE}/extract-pdf-text`, {
            method: 'POST',
            body: formData
        });
        
        const data = await res.json();

        if (data.status === 'success') {
            document.getElementById('prof-bio').value = data.text;
            msg.innerText = "PDF uploaded & text extracted into bio!";
            msg.className = "text-green-400 text-sm mt-3 block";
        } else {
            throw new Error(data.message);
        }
    } catch (err) {
        msg.innerText = "Error: " + err.message;
        msg.className = "text-red-400 text-sm mt-3 block";
    } finally {
        btn.innerText = "Extract Text";
        btn.disabled = false;
    }
}

async function saveProfile() {
    const msg = document.getElementById('prof-msg');
    const { error } = await dbClient.from('profiles').update({
        full_name: document.getElementById('prof-name').value,
        city: document.getElementById('prof-city').value,
        bio: document.getElementById('prof-bio').value,
        is_available: document.getElementById('prof-available').checked
    }).eq('id', currentUser.id);
    msg.classList.remove('hidden');
    if(error) { msg.innerText = error.message; msg.className = "text-red-400 text-sm mt-3"; }
    else { msg.innerText = "Profile updated successfully!"; msg.className = "text-green-400 text-sm mt-3"; }
    setTimeout(() => msg.classList.add('hidden'), 3000);
}

async function savePaper(paperId) {
    if (!currentUser) return openAuthModal();
    const { error } = await dbClient.from('saved_papers').insert({ user_id: currentUser.id, paper_id: paperId });
    if(error && error.code !== '23505') alert("Error saving paper: " + error.message);
    else alert("Paper saved to your Dashboard!");
}

async function launchConsultation(expertId) {
    if (!currentUser) return openAuthModal();
    document.getElementById('video-modal').classList.add('modal-active');
    const res = await fetch(`${API_BASE}/create-consultation`, { method: 'POST' });
    const data = await res.json();
    const roomCode = data.room_url.split('/').pop(); 
    jitsiApi = new JitsiMeetExternalAPI('meet.jit.si', {
        roomName: roomCode, width: '100%', height: '100%',
        parentNode: document.querySelector('#jitsi-container'),
        userInfo: { displayName: currentUser.email.split('@')[0] }
    });
}

function endConsultation() {
    if (jitsiApi) { jitsiApi.dispose(); jitsiApi = null; }
    document.getElementById('video-modal').classList.remove('modal-active');
}

async function handleSocialLogin(provider) {
    const { error } = await dbClient.auth.signInWithOAuth({
        provider: provider,
        options: {
            redirectTo: window.location.origin // Automatically redirects back to your live site
        }
    });
    if (error) {
        showAuthMsg(error.message, "text-red-500");
    }
}

window.onload = initApp;