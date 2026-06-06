import re
import os
import numpy as np
import streamlit as st

def clean_html(text):
    return "\n".join([line.strip() for line in text.split("\n")])

# Setup page config
st.set_page_config(page_title="HarvestDash | Solar Harvesting Dashboard", page_icon="⚡", layout="wide")

# CSS Styling Injection
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Courier+Prime&family=Outfit:wght@300;400;500;600;700;800&display=swap');

/* Main Body background and typography */
.stApp {
    background-color: #0b0f19 !important;
    font-family: 'Outfit', sans-serif !important;
    background-image: 
        radial-gradient(circle at 10% 20%, rgba(0, 210, 255, 0.05) 0%, transparent 40%),
        radial-gradient(circle at 90% 80%, rgba(79, 172, 254, 0.05) 0%, transparent 40%) !important;
    background-attachment: fixed !important;
}

/* Custom dark theming for Streamlit selectbox inputs */
div[data-baseweb="select"] {
    background-color: rgba(0, 0, 0, 0.4) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 10px !important;
}
div[role="listbox"] {
    background-color: #0b0f19 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
}
span[data-baseweb="select"] {
    color: #f3f4f6 !important;
}

/* Stats Grid & Cards */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    margin-bottom: 1.5rem;
    width: 100%;
}

.stat-card {
    background: rgba(22, 30, 46, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
    opacity: 1;
}

.stat-content {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    flex: 1;
}

.stat-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

.stat-value {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -1px;
    color: #fff;
    line-height: 1;
}

.stat-unit {
    font-size: 1rem;
    font-weight: 500;
    color: #00d2ff;
    margin-left: 2px;
}

.stat-desc {
    font-size: 0.75rem;
    color: #9ca3af;
    font-weight: 400;
}

/* Gauge Progress */
.gauge-container {
    position: relative;
    width: 70px;
    height: 70px;
    margin-left: 10px;
    flex-shrink: 0;
}

.gauge-svg {
    transform: rotate(-90deg);
    width: 100%;
    height: 100%;
}

.gauge-track {
    fill: none;
    stroke: rgba(255, 255, 255, 0.05);
    stroke-width: 6;
}

.gauge-fill {
    fill: none;
    stroke: #00d2ff;
    stroke-width: 6;
    stroke-linecap: round;
    stroke-dasharray: 201; /* 2 * pi * r (r=32) */
    transition: stroke-dashoffset 0.8s ease-out;
}

.gauge-text {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 0.9rem;
    font-weight: 700;
    color: #fff;
}

/* Terminal Console Styling */
.terminal-container {
    background-color: #05070b;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    font-family: 'Courier Prime', 'Courier New', monospace;
    font-size: 0.9rem;
    line-height: 1.5;
    padding: 1.5rem;
    max-height: 500px;
    overflow-y: auto;
    width: 100%;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
}

.terminal-lines {
    padding: 0;
    margin: 0;
    list-style: none;
    display: flex;
    flex-direction: column;
}

.log-line {
    display: flex;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    white-space: pre-wrap;
    word-break: break-all;
    color: #38bdf8;
    border: 1px solid transparent;
}

.log-line:hover {
    background-color: rgba(255, 255, 255, 0.02);
}

.log-line.charging {
    color: #4ade80;
    background-color: rgba(74, 222, 128, 0.08);
}

.log-line.charging:hover {
    background-color: rgba(74, 222, 128, 0.12);
}

.log-line.cycle-summary {
    color: #fb7185;
    background-color: rgba(251, 113, 133, 0.06);
    border: 1px solid rgba(251, 113, 133, 0.15);
    margin: 0.15rem 0;
    font-weight: 600;
}

.log-line.header-line {
    color: #d8b4fe;
    font-weight: bold;
    border-bottom: 1px dashed rgba(216, 180, 254, 0.15);
    padding-bottom: 0.5rem;
    margin-bottom: 0.5rem;
}

.line-num {
    color: #4b5563;
    width: 4.5rem;
    flex-shrink: 0;
    user-select: none;
    text-align: right;
    padding-right: 1.25rem;
    border-right: 1px solid rgba(255, 255, 255, 0.04);
    margin-right: 1rem;
}

.line-text {
    flex: 1;
}
</style>
""", unsafe_allow_html=True)


# --- Core Logic Functions ---

def calculate_cycle_stats(cyc, summary=None, avg_esr_fallback=1.5):
    t_start = cyc[0]['t']
    t_end = cyc[-1]['t']
    duration = t_end - t_start
    if duration <= 0:
        duration = len(cyc) * 5.0
        
    q_panel = 0.0
    q_battery = 0.0
    e_panel = 0.0
    e_battery = 0.0
    active_charging_time = 0.0
    total_time = 0.0
    
    bv1_vals = []
    bv2_vals = []
    
    for i in range(len(cyc)):
        d_curr = cyc[i]
        if i > 0:
            dt = d_curr['t'] - cyc[i-1]['t']
            if dt <= 0 or dt > 100:
                dt = 5.0
        else:
            dt = 5.0
            
        total_time += dt
        
        i_panel = abs(d_curr['cur2'])
        v_panel = d_curr['bv2']
        q_panel += i_panel * dt
        e_panel += i_panel * v_panel * dt
        
        i_bat = d_curr['cur1']
        v_bat = d_curr['bv1']
        
        bv1_vals.append(v_bat)
        bv2_vals.append(v_panel)
        
        if abs(i_bat) > 2.0:
            i_bat_abs = abs(i_bat)
            q_battery += i_bat_abs * dt
            e_battery += i_bat_abs * v_bat * dt
            active_charging_time += dt
            
    esr_estimates = []
    for i in range(len(cyc)):
        d_curr = cyc[i]
        if i > 0:
            d_prev = cyc[i-1]
            dt_trans = d_curr['t'] - d_prev['t']
            if 0 < dt_trans < 20:
                is_on_curr = abs(d_curr['cur1']) > 2.0
                is_on_prev = abs(d_prev['cur1']) > 2.0
                if is_on_curr != is_on_prev:
                    delta_i_bat = abs(abs(d_curr['cur1']) - abs(d_prev['cur1']))
                    delta_v_cap = abs(d_curr['bv2'] - d_prev['bv2'])
                    if delta_i_bat > 10.0:
                        esr_estimates.append(delta_v_cap / (delta_i_bat / 1000.0))
                        
    avg_esr = np.median(esr_estimates) if esr_estimates else None
    if avg_esr is None or avg_esr < 0.05 or avg_esr > 20.0:
        avg_esr = avg_esr_fallback
        
    e_lost_esr = 0.0
    for i in range(len(cyc)):
        d_curr = cyc[i]
        if i > 0:
            dt = d_curr['t'] - cyc[i-1]['t']
            if dt <= 0 or dt > 100:
                dt = 5.0
        else:
            dt = 5.0
        i_panel = abs(d_curr['cur2'])
        i_bat = d_curr['cur1']
        i_cap = abs(i_bat) - i_panel if abs(i_bat) > 2.0 else i_panel
        p_loss_mw = (i_cap ** 2) * avg_esr / 1000.0
        e_lost_esr += p_loss_mw * dt
        
    if summary:
        avg_i_panel = summary['panel_avg']
        avg_i_bat = summary['total_chrg_cyc']
        avg_chrg_on = summary['chrg_cur']
        q_eff = (avg_i_bat / avg_i_panel * 100.0) if avg_i_panel > 0 else 0
        duty_cycle = (avg_i_bat / avg_chrg_on * 100.0) if avg_chrg_on > 0 else 0
    else:
        avg_i_panel = q_panel / total_time if total_time > 0 else 0
        avg_i_bat = q_battery / total_time if total_time > 0 else 0
        q_eff = (q_battery / q_panel * 100.0) if q_panel > 0 else 0
        avg_chrg_on = (q_battery / active_charging_time) if active_charging_time > 0 else 0
        duty_cycle = (active_charging_time / total_time * 100.0) if total_time > 0 else 0
        
    mean_bv1 = np.mean(bv1_vals) if bv1_vals else 3.65
    mean_bv2 = np.mean(bv2_vals) if bv2_vals else 3.95
    e_eff_consistent = q_eff * (mean_bv1 / mean_bv2)
    
    esr_loss_ratio = (e_lost_esr / e_panel * 100.0) if e_panel > 0 else 0
    charger_eff = (e_battery / (e_panel - e_lost_esr) * 100.0) if (e_panel - e_lost_esr) > 0 else 0
    
    return {
        'avg_panel': round(avg_i_panel, 3),
        'avg_battery': round(avg_i_bat, 3),
        'q_efficiency': round(q_eff, 2),
        'e_efficiency': round(e_eff_consistent, 2),
        'esr': round(avg_esr, 3),
        'esr_loss_ratio': round(esr_loss_ratio, 2),
        'charger_efficiency': round(charger_eff, 2),
        'duty_cycle': round(duty_cycle, 2),
        'cycle_period': round(duration, 1)
    }

def get_cycle_summary(cycles, k):
    if k + 1 < len(cycles):
        first_line_next = cycles[k+1][0]['line_str']
        match_panel = re.search(r'Panel_avg:\s*([-\d\.]+)', first_line_next)
        match_total = re.search(r'Total_chrg_cyc:\s*([-\d\.]+)', first_line_next)
        match_chrg = re.search(r'CHRG_cur:\s*([-\d\.]+)', first_line_next)
        if match_panel and match_total and match_chrg:
            return {
                'panel_avg': abs(float(match_panel.group(1))),
                'total_chrg_cyc': abs(float(match_total.group(1))),
                'chrg_cur': abs(float(match_chrg.group(1)))
            }
    return None

@st.cache_data
def parse_and_process_log_file(filename):
    all_lines = []
    if not os.path.exists(filename):
        return None, None
        
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f):
            stripped = line.strip()
            if '&CS' in stripped:
                match_time = re.search(r'(\d+)\s*ms', stripped)
                match_cur1 = re.search(r'Curch1:\s*([-\d\.]+)', stripped)
                match_bv1 = re.search(r'BVCh1:\s*([-\d\.]+)', stripped)
                match_cur2 = re.search(r'CurCh2:\s*([-\d\.]+)', stripped)
                match_bv2 = re.search(r'BVCh2:\s*([-\d\.]+)', stripped)
                
                if match_time and match_cur1 and match_bv1 and match_cur2 and match_bv2:
                    all_lines.append({
                        'line_num': idx + 1,
                        'line_str': stripped,
                        't': int(match_time.group(1)),
                        'cur1': float(match_cur1.group(1)),
                        'bv1': float(match_bv1.group(1)),
                        'cur2': float(match_cur2.group(1)),
                        'bv2': float(match_bv2.group(1))
                    })
                    
    # Segment into cycles
    cycles = []
    current_cycle = []
    for d in all_lines:
        has_summary = ('CHRG_cur:' in d['line_str'] and 
                       'Total_chrg_cyc:' in d['line_str'] and 
                       'Panel_avg:' in d['line_str'])
        if has_summary:
            if current_cycle:
                cycles.append(current_cycle)
            current_cycle = []
        if current_cycle or has_summary:
            current_cycle.append(d)
            
    # Calculate fallback ESR
    global_esr_estimates = []
    for i in range(1, len(all_lines)):
        d_curr = all_lines[i]
        d_prev = all_lines[i-1]
        dt = d_curr['t'] - d_prev['t']
        if 0 < dt < 20:
            is_on_curr = abs(d_curr['cur1']) > 2.0
            is_on_prev = abs(d_prev['cur1']) > 2.0
            if is_on_curr != is_on_prev:
                delta_i_bat = abs(abs(d_curr['cur1']) - abs(d_prev['cur1']))
                delta_v_cap = abs(d_curr['bv2'] - d_prev['bv2'])
                if delta_i_bat > 10.0:
                    global_esr_estimates.append(delta_v_cap / (delta_i_bat / 1000.0))
    fallback_esr = np.median(global_esr_estimates) if global_esr_estimates else 1.5
    
    return cycles, fallback_esr


# --- Load & Parse Data ---

files = {
    '1880uF': '1880uF_5ma_10ma_15ma_20ma_25ma_data.txt',
    '1F': '1F_5ma_10ma_15ma_20ma_25ma_data.txt'
}

sectors = {
    '5mA': (3.0, 7.0),
    '10mA': (8.0, 12.0),
    '15mA': (13.0, 17.0),
    '20mA': (18.0, 22.0),
    '25mA': (23.0, 27.0)
}

# Preprocess all cycles on load
@st.cache_data
def get_all_sector_data():
    db = {}
    for cap_name, filename in files.items():
        db[cap_name] = {}
        for s in sectors:
            db[cap_name][s] = []
            
        cycles, fallback_esr = parse_and_process_log_file(filename)
        if not cycles:
            continue
            
        temp_sector_cycles = {s: [] for s in sectors}
        for k, cyc in enumerate(cycles):
            summary = get_cycle_summary(cycles, k)
            if summary:
                avg_panel_current = summary['panel_avg']
            else:
                cur2s = [abs(d['cur2']) for d in cyc]
                avg_panel_current = np.mean(cur2s) if cur2s else 0.0
                
            matched_sector = None
            for sector_name, (low, high) in sectors.items():
                if low <= avg_panel_current <= high:
                    matched_sector = sector_name
                    break
                    
            if matched_sector:
                temp_sector_cycles[matched_sector].append((cyc, summary))
                
        # Apply outlier filtering
        for sector_name in sectors:
            cycles_in_sector = temp_sector_cycles[sector_name]
            if not cycles_in_sector:
                continue
                
            lengths = [len(cyc) for cyc, _ in cycles_in_sector]
            median_len = np.median(lengths)
            
            filtered_cycles = []
            for cyc, summary in cycles_in_sector:
                if median_len - 2 <= len(cyc) <= median_len + 2:
                    stats = calculate_cycle_stats(cyc, summary, fallback_esr)
                    filtered_cycles.append({
                        'stats': stats,
                        'lines': [{'num': d['line_num'], 'str': d['line_str']} for d in cyc],
                        'line_count': len(cyc)
                    })
            db[cap_name][sector_name] = filtered_cycles
            
    return db

db = get_all_sector_data()


# --- Streamlit Layout & Controls ---

# Header Section
col_logo, col_status = st.columns([4, 1])
with col_logo:
    st.markdown(clean_html("""
    <div style="display: flex; align-items: center; gap: 0.75rem;">
        <div style="width: 38px; height: 38px; background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.25rem; color: #fff; box-shadow: 0 0 20px rgba(0, 210, 255, 0.3);">⚡</div>
        <div>
            <h1 style="font-size: 1.5rem; font-weight: 800; margin: 0; background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">HarvestDash</h1>
            <p style="font-size: 0.75rem; color: #9ca3af; font-weight: 500; text-transform: uppercase; margin: 0; letter-spacing: 1px;">Solar Charging Energy Analyser</p>
        </div>
    </div>
    """), unsafe_allow_html=True)

with col_status:
    st.markdown(clean_html("""
    <div style="display: flex; justify-content: flex-end; padding-top: 5px;">
        <div style="display: flex; align-items: center; gap: 0.5rem; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); padding: 0.5rem 0.85rem; border-radius: 20px; font-size: 0.85rem; font-weight: 500; color: #f3f4f6;">
            <div style="width: 8px; height: 8px; background-color: #10b981; border-radius: 50%; box-shadow: 0 0 10px #10b981;"></div>
            <span>Cloud Connected</span>
        </div>
    </div>
    """), unsafe_allow_html=True)

st.markdown("<hr style='border: none; border-top: 1px solid rgba(255, 255, 255, 0.08); margin: 1.5rem 0 1rem 0;'>", unsafe_allow_html=True)

# Selectors Row
col1, col2, col3 = st.columns(3)

with col1:
    cap_choice = st.selectbox(
        "Select Capacitor Buffer",
        options=["1880uF", "1F"],
        format_func=lambda x: "1880uF (Electrolytic)" if x == "1880uF" else "1F (Supercapacitor)"
    )

with col2:
    sector_choice = st.selectbox(
        "Select Current Sector",
        options=["5mA", "10mA", "15mA", "20mA", "25mA"]
    )

# Retrieve data for selection
sector_cycles = db.get(cap_choice, {}).get(sector_choice, [])

with col3:
    cycle_options = ["all"] + [str(c['stats']['cycle_period']) + f" ms (Cycle {idx+1})" for idx, c in enumerate(sector_cycles)]
    cycle_choice_raw = st.selectbox(
        "Select Cycle",
        options=["all"] + list(range(1, len(sector_cycles) + 1)),
        format_func=lambda x: "All Cycles (Average)" if x == "all" else f"Cycle {x} ({sector_cycles[x-1]['line_count']} samples)"
    )

# Compute average sector stats if "all" is selected
if cycle_choice_raw == "all":
    if sector_cycles:
        avg_panel = np.mean([c['stats']['avg_panel'] for c in sector_cycles])
        avg_battery = np.mean([c['stats']['avg_battery'] for c in sector_cycles])
        q_eff = np.mean([c['stats']['q_efficiency'] for c in sector_cycles])
        e_eff = np.mean([c['stats']['e_efficiency'] for c in sector_cycles])
        esr = np.median([c['stats']['esr'] for c in sector_cycles])
        esr_loss = np.mean([c['stats']['esr_loss_ratio'] for c in sector_cycles])
        charger_eff = np.mean([c['stats']['charger_efficiency'] for c in sector_cycles])
        period = np.mean([c['stats']['cycle_period'] for c in sector_cycles])
        
        display_stats = {
            'avg_panel': round(avg_panel, 3),
            'avg_battery': round(avg_battery, 3),
            'q_efficiency': round(q_eff, 2),
            'e_efficiency': round(e_eff, 2),
            'esr': round(esr, 3),
            'esr_loss_ratio': round(esr_loss, 2),
            'charger_efficiency': round(charger_eff, 2),
            'cycle_period': round(period, 1)
        }
    else:
        display_stats = None
else:
    display_stats = sector_cycles[cycle_choice_raw - 1]['stats']

st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)


# --- Display Stats Cards ---

if display_stats:
    # Circle gauge circumference calculation (r = 32 -> 201)
    stroke_offset = 201 - (display_stats['e_efficiency'] / 100) * 201
    
    st.markdown(clean_html(f"""
    <div class="stats-grid">
        <!-- Card 1: Solar Input -->
        <div class="stat-card">
            <div class="stat-content">
                <div class="stat-label">Avg. Solar Current</div>
                <div class="stat-value">{display_stats['avg_panel']}<span class="stat-unit">mA</span></div>
                <div class="stat-desc">Harvested input from solar panel</div>
            </div>
        </div>
        
        <!-- Card 2: Battery Delivery -->
        <div class="stat-card">
            <div class="stat-content">
                <div class="stat-label">Avg. Battery Current</div>
                <div class="stat-value">{display_stats['avg_battery']}<span class="stat-unit">mA</span></div>
                <div class="stat-desc">Delivered net current to battery</div>
            </div>
        </div>
        
        <!-- Card 3: Energy Efficiency Progress Circle -->
        <div class="stat-card">
            <div class="stat-content">
                <div class="stat-label">Energy Efficiency</div>
                <div class="stat-value">{display_stats['e_efficiency']}<span class="stat-unit">%</span></div>
                <div class="stat-desc">Coulombic: {display_stats['q_efficiency']}% | Charger: {display_stats['charger_efficiency']}%</div>
            </div>
            <div class="gauge-container">
                <svg class="gauge-svg">
                    <circle class="gauge-track" cx="35" cy="35" r="32"></circle>
                    <circle class="gauge-fill" cx="35" cy="35" r="32" style="stroke-dashoffset: {stroke_offset}px;"></circle>
                </svg>
                <div class="gauge-text">{round(display_stats['e_efficiency'])}%</div>
            </div>
        </div>
        
        <!-- Card 4: Cycle Period & ESR -->
        <div class="stat-card">
            <div class="stat-content">
                <div class="stat-label">Cycle & ESR</div>
                <div class="stat-value">{display_stats['cycle_period']}<span class="stat-unit">ms</span></div>
                <div class="stat-desc">Est. ESR: {display_stats['esr']} Ω | Loss: {display_stats['esr_loss_ratio']}%</div>
            </div>
        </div>
    </div>
    """), unsafe_allow_html=True)
else:
    st.markdown("<p style='color: #9ca3af;'>No cycles matching selection.</p>", unsafe_allow_html=True)


# --- Console Logs Section ---

st.markdown("<hr style='border: none; border-top: 1px solid rgba(255, 255, 255, 0.08); margin: 1.5rem 0;'>", unsafe_allow_html=True)

# Build search controls
col_title, col_search = st.columns([2, 1])
with col_title:
    selected_name = f"Cycle {cycle_choice_raw}" if cycle_choice_raw != "all" else "All Cycles"
    st.markdown(f"<h3 style='margin: 0; font-size: 1.25rem; font-weight: 700; color: #fff;'>System Console Logs ({selected_name})</h3>", unsafe_allow_html=True)

with col_search:
    search_query = st.text_input("Search Logs", placeholder="Filter logs...", label_visibility="collapsed").lower()

# Gather logs
if cycle_choice_raw == "all":
    all_log_lines = []
    for c in sector_cycles:
        all_log_lines.extend(c['lines'])
else:
    if sector_cycles and cycle_choice_raw - 1 < len(sector_cycles):
        all_log_lines = sector_cycles[cycle_choice_raw - 1]['lines']
    else:
        all_log_lines = []

# Filter logs
if search_query:
    filtered_log_lines = [line for line in all_log_lines if search_query in line['str'].lower()]
else:
    filtered_log_lines = all_log_lines

# Pagination logic to prevent slow HTML rendering
PAGE_SIZE = 200
total_lines = len(filtered_log_lines)
total_pages = max(1, int(np.ceil(total_lines / PAGE_SIZE)))

if total_lines > PAGE_SIZE:
    col_stat_info, col_page_slider = st.columns([2, 1])
    with col_stat_info:
        st.markdown(f"<span style='color: #9ca3af; font-size: 0.9rem;'>Showing {total_lines} lines total. Use controls on right to paginate.</span>", unsafe_allow_html=True)
    with col_page_slider:
        page_num = st.number_input("Select Page", min_value=1, max_value=total_pages, value=1, step=1)
else:
    page_num = 1
    st.markdown(f"<span style='color: #9ca3af; font-size: 0.9rem;'>Showing {total_lines} / {total_lines} lines.</span>", unsafe_allow_html=True)

# Slicing lines for the current page
start_idx = (page_num - 1) * PAGE_SIZE
end_idx = min(start_idx + PAGE_SIZE, total_lines)
paginated_lines = filtered_log_lines[start_idx:end_idx]

# Render Console lines in a styled container
if paginated_lines:
    html_lines = []
    for line in paginated_lines:
        line_num = line['num']
        line_text = line['str']
        
        # Apply specific styling class based on contents
        classes = "log-line"
        if "Curch1: -" in line_text and "Total_chrg_cyc:" not in line_text:
            match = re.search(r'Curch1:\s*-([\d\.]+)', line_text)
            if match and float(match.group(1)) > 2.0:
                classes += " charging"
        elif "Total_chrg_cyc:" in line_text:
            classes += " cycle-summary"
        elif "<Current Sense" in line_text or "Log File" in line_text:
            classes += " header-line"
            
        html_item = clean_html(f"""
        <li class="{classes}">
            <span class="line-num">{line_num}</span>
            <span class="line-text">{line_text}</span>
        </li>
        """)
        html_lines.append(html_item)
        
    st.markdown(clean_html(f"""
    <div class="terminal-container">
        <ul class="terminal-lines">
            {"".join(html_lines)}
        </ul>
    </div>
    """), unsafe_allow_html=True)
else:
    st.markdown(clean_html("""
    <div class="terminal-container" style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem; text-align: center; color: #9ca3af;">
        <svg style="width: 48px; height: 48px; stroke: #4b5563; opacity: 0.6; margin-bottom: 1rem;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="8" y1="12" x2="16" y2="12"></line>
        </svg>
        <p>No log records match your filter criteria.</p>
    </div>
    """), unsafe_allow_html=True)
