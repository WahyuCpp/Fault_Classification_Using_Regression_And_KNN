/**
 * MONTREAL-VT Dashboard Real-Time Visualizer
 * Plotly.js + WebSocket Client
 */

// Plotly layout configuration with dark engineering palette
const darkLayoutBase = {
    paper_bgcolor: 'rgba(30, 41, 59, 0.4)',
    plot_bgcolor: 'rgba(15, 23, 42, 0.8)',
    font: { family: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto', color: '#94a3b8', size: 10 },
    margin: { l: 45, r: 20, t: 25, b: 35 },
    xaxis: { gridcolor: '#334155', zerolinecolor: '#475569' },
    yaxis: { gridcolor: '#334155', zerolinecolor: '#475569' },
    legend: { orientation: 'h', y: 1.15, x: 0.1, font: { color: '#f8fafc', size: 10 } },
    showlegend: true
};

// Rolling trend history buffers
const maxTrendPoints = 60;
const historyTime = [];
const historyRms = [];
const historyCurrent = [];
const historyTemp = [];

let isPaused = false;
let ws = null;
let reconnectTimer = null;

// Initialize Plotly Charts
function initPlots() {
    // 1. Time-Domain Plot
    const traceX = { x: [], y: [], name: 'Acc X', mode: 'lines', line: { color: '#38bdf8', width: 1.2 } };
    const traceY = { x: [], y: [], name: 'Acc Y', mode: 'lines', line: { color: '#4ade80', width: 1.2 } };
    const traceZ = { x: [], y: [], name: 'Acc Z', mode: 'lines', line: { color: '#f43f5e', width: 1.2 } };

    const layoutTime = {
        ...darkLayoutBase,
        xaxis: { ...darkLayoutBase.xaxis, title: { text: 'Time (s)', font: { size: 10 } } },
        yaxis: { ...darkLayoutBase.yaxis, title: { text: 'Acceleration (m/s²)', font: { size: 10 } } }
    };
    Plotly.newPlot('plotTimeDomain', [traceX, traceY, traceZ], layoutTime, { responsive: true, displayModeBar: false });

    // 2. Frequency Spectrum Plot
    const traceFftX = { x: [], y: [], name: 'FFT X', mode: 'lines', line: { color: '#38bdf8', width: 1.2 } };
    const traceFftY = { x: [], y: [], name: 'FFT Y', mode: 'lines', line: { color: '#4ade80', width: 1.2 } };
    const traceFftZ = { x: [], y: [], name: 'FFT Z', mode: 'lines', line: { color: '#f43f5e', width: 1.2 } };

    const layoutFFT = {
        ...darkLayoutBase,
        xaxis: { ...darkLayoutBase.xaxis, range: [0, 500], title: { text: 'Frequency (Hz)', font: { size: 10 } } },
        yaxis: { ...darkLayoutBase.yaxis, title: { text: 'Amplitude (m/s²)', font: { size: 10 } } }
    };
    Plotly.newPlot('plotFFT', [traceFftX, traceFftY, traceFftZ], layoutFFT, { responsive: true, displayModeBar: false });

    // 3. Severity Trend Plot
    const traceSev = { x: [], y: [], name: 'RMS Total', mode: 'lines+markers', line: { color: '#38bdf8', width: 2 } };
    const layoutSev = {
        ...darkLayoutBase,
        margin: { l: 40, r: 15, t: 15, b: 25 },
        showlegend: false,
        shapes: [
            { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 1.12, y1: 1.12, line: { color: '#22c55e', dash: 'dot', width: 1 } },
            { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 2.80, y1: 2.80, line: { color: '#f59e0b', dash: 'dot', width: 1 } },
            { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 4.50, y1: 4.50, line: { color: '#ef4444', dash: 'dot', width: 1 } },
        ]
    };
    Plotly.newPlot('plotSeverity', [traceSev], layoutSev, { responsive: true, displayModeBar: false });

    // 4. Current Trend Plot
    const traceCurr = { x: [], y: [], name: 'Current', mode: 'lines', line: { color: '#fbbf24', width: 2 } };
    const layoutCurr = {
        ...darkLayoutBase,
        margin: { l: 40, r: 15, t: 15, b: 25 },
        showlegend: false,
        shapes: [
            { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 0.5, y1: 0.5, line: { color: '#ef4444', dash: 'dot', width: 1 } }
        ]
    };
    Plotly.newPlot('plotCurrent', [traceCurr], layoutCurr, { responsive: true, displayModeBar: false });

    // 5. Temperature Trend Plot
    const traceTemp = { x: [], y: [], name: 'Temp', mode: 'lines', line: { color: '#f87171', width: 2 } };
    const layoutTemp = {
        ...darkLayoutBase,
        margin: { l: 40, r: 15, t: 15, b: 25 },
        showlegend: false,
        shapes: [
            { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 70.0, y1: 70.0, line: { color: '#ef4444', dash: 'dot', width: 1 } }
        ]
    };
    Plotly.newPlot('plotTemperature', [traceTemp], layoutTemp, { responsive: true, displayModeBar: false });
}

// WebSocket Connection & Packet Processing
function connectWebSocket() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
        return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/live`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('[WebSocket] Connected to Montreal-VT monitoring stream.');
        const dbBadge = document.getElementById('navDbBadge');
        if (dbBadge && dbBadge.innerText.includes('Connecting')) {
            dbBadge.innerText = 'Stream: Live';
            dbBadge.style.color = '#38bdf8';
        }
        if (reconnectTimer) clearInterval(reconnectTimer);
    };

    ws.onmessage = (event) => {
        if (isPaused) return;
        try {
            const data = JSON.parse(event.data);
            handleDataPacket(data);
        } catch (e) {
            console.error('Failed to parse monitoring packet:', e);
        }
    };

    ws.onclose = () => {
        console.warn('[WebSocket] Closed. Fallback to polling and reconnecting in 2s...');
        scheduleReconnect();
    };

    ws.onerror = (err) => {
        console.error('[WebSocket] Error:', err);
        ws.close();
    };
}

function scheduleReconnect() {
    if (!reconnectTimer) {
        reconnectTimer = setInterval(() => {
            connectWebSocket();
            // Fallback REST polling while disconnected
            fetchLatestData();
        }, 1000);
    }
}

// REST Fallback fetch
async function fetchLatestData() {
    if (isPaused) return;
    try {
        const res = await fetch('/api/data/latest');
        if (res.ok) {
            const data = await res.json();
            handleDataPacket(data);
        }
    } catch (e) {
        // quiet
    }
}

// Update UI with Data Packet
function handleDataPacket(data) {
    if (!data || data.status === 'Buffering') return;

    // 1. Update KPI Values
    const lr = data.latest_readings || {};
    document.getElementById('valAccX').innerText = (lr.x !== undefined) ? lr.x.toFixed(3) : '0.00';
    document.getElementById('valAccY').innerText = (lr.y !== undefined) ? lr.y.toFixed(3) : '0.00';
    document.getElementById('valAccZ').innerText = (lr.z !== undefined) ? lr.z.toFixed(3) : '9.81';

    const rms = data.rms || {};
    const totalRms = rms.a_rms_total !== undefined ? rms.a_rms_total : 0.0;
    document.getElementById('valRmsTotal').innerText = totalRms.toFixed(3);

    // Vibration Severity
    const cond = data.condition || {};
    const vibEval = cond.vibration_eval || {};
    const sevBadge = document.getElementById('severityBadge');
    if (sevBadge && vibEval.zone) {
        sevBadge.innerText = `${vibEval.zone}: ${vibEval.severity}`;
        sevBadge.style.background = `${vibEval.color}33`;
        sevBadge.style.color = vibEval.color;
        sevBadge.style.borderColor = vibEval.color;
    }

    // Current & Temp
    const currVal = (lr.current !== undefined) ? lr.current : 0.42;
    document.getElementById('valCurrent').innerText = currVal.toFixed(2);
    document.getElementById('valCurrentRms').innerText = (rms.a_rms_x !== undefined) ? currVal.toFixed(2) : '0.42';

    const tempVal = (lr.temperature !== undefined) ? lr.temperature : 43.2;
    document.getElementById('valTemp').innerText = tempVal.toFixed(1);

    // RPM & 1x
    const rpmVal = (lr.rpm !== undefined) ? lr.rpm : 1450;
    document.getElementById('valRpm').innerText = Math.round(rpmVal);
    document.getElementById('valShaftFreq').innerText = (rpmVal / 60.0).toFixed(2);

    // Header Badges
    const navFsBadge = document.getElementById('navFsBadge');
    if (navFsBadge && data.sampling_rate) {
        navFsBadge.innerText = `fs: ${Math.round(data.sampling_rate)} Hz`;
    }
    const navStateBadge = document.getElementById('navStateBadge');
    if (navStateBadge && cond.machine_state) {
        navStateBadge.innerText = cond.machine_state;
        if (cond.machine_state === 'WARNING') {
            navStateBadge.className = 'badge-custom badge-danger';
        } else if (cond.machine_state === 'STARTING') {
            navStateBadge.className = 'badge-custom badge-warning';
        } else {
            navStateBadge.className = 'badge-custom badge-healthy';
        }
    }

    // Header Info for plots
    const timeInfo = document.getElementById('timeDomainInfo');
    if (timeInfo) {
        timeInfo.innerText = `N: ${data.window_size || 1024} samples | fs: ${Math.round(data.sampling_rate || 1500)} Hz`;
    }
    const fftInfo = document.getElementById('fftInfo');
    if (fftInfo) {
        fftInfo.innerText = `Δf: ${data.frequency_resolution || 1.46} Hz | Nyquist: ${data.nyquist_frequency || 750} Hz | Window: ${data.fft_window_function || 'Hann'}`;
    }

    // 2. ML Prediction Badge
    const ml = data.ml_prediction || {};
    const mlBadge = document.getElementById('mlPredictionBadge');
    if (mlBadge) {
        const condName = ml.condition_name || 'Normal';
        const predCode = ml.predicted_label || 'A';
        mlBadge.innerText = `${condName} (${predCode})`;
        if (predCode === 'A' || condName.toLowerCase() === 'healthy') {
            mlBadge.className = 'badge-custom badge-healthy';
        } else {
            mlBadge.className = 'badge-custom badge-warning';
        }
    }
    document.getElementById('mlConfidence').innerText = `${((ml.confidence || 0.95) * 100).toFixed(1)}%`;
    document.getElementById('activeModelLabel').innerText = (ml.model_used || 'KNN').toUpperCase();

    // ML Probabilities breakdown bars
    renderMLProbabilities(ml.probabilities || {});

    // 3. Update Plots
    updatePlots(data, totalRms, currVal, tempVal);

    // 4. Update Diagnostic Tables
    updateCharacteristicFrequencies(data.bearing_frequencies, data.electrical_frequencies);
    updatePotentialFaults(data.fault_analysis);
}

// Render ML class probabilities
function renderMLProbabilities(probs) {
    const container = document.getElementById('mlProbBars');
    if (!container) return;

    const entries = Object.entries(probs);
    if (entries.length === 0) {
        container.innerHTML = '<div class="small text-muted">Awaiting probability estimates...</div>';
        return;
    }

    let html = '';
    for (const [cls, prob] of entries) {
        const pct = Math.round(prob * 100);
        const color = cls.toLowerCase() === 'healthy' ? '#22c55e' : '#f59e0b';
        html += `
            <div class="mb-1">
                <div class="d-flex justify-content-between small text-muted">
                    <span>${cls}</span>
                    <span>${pct}%</span>
                </div>
                <div class="progress" style="height: 5px; background: #0f172a;">
                    <div class="progress-bar" role="progressbar" style="width: ${pct}%; background-color: ${color};"></div>
                </div>
            </div>
        `;
    }
    container.innerHTML = html;
}

// Fast plot updating using Plotly.react
function updatePlots(data, totalRms, currVal, tempVal) {
    const wf = data.waveform || {};
    const fft = data.fft || {};

    const showX = document.getElementById('axisXToggle').checked;
    const showY = document.getElementById('axisYToggle').checked;
    const showZ = document.getElementById('axisZToggle').checked;

    // Time indices (0 to N-1) converted to milliseconds
    const fs = data.sampling_rate || 1500;
    const dtMs = 1000.0 / fs;
    const timeX = (wf.x || []).map((_, i) => (i * dtMs).toFixed(1));

    // 1. Time-Domain update
    Plotly.react('plotTimeDomain', [
        { x: timeX, y: showX ? (wf.x || []) : [], name: 'Acc X', mode: 'lines', line: { color: '#38bdf8', width: 1.2 }, visible: showX },
        { x: timeX, y: showY ? (wf.y || []) : [], name: 'Acc Y', mode: 'lines', line: { color: '#4ade80', width: 1.2 }, visible: showY },
        { x: timeX, y: showZ ? (wf.z || []) : [], name: 'Acc Z', mode: 'lines', line: { color: '#f43f5e', width: 1.2 }, visible: showZ }
    ], {
        ...darkLayoutBase,
        xaxis: { ...darkLayoutBase.xaxis, title: { text: 'Time (ms)', font: { size: 10 } } },
        yaxis: { ...darkLayoutBase.yaxis, title: { text: 'Acceleration (m/s²)', font: { size: 10 } } }
    }, { responsive: true, displayModeBar: false });

    // 2. Frequency Spectrum update
    Plotly.react('plotFFT', [
        { x: fft.frequency || [], y: showX ? (fft.magnitude_x || []) : [], name: 'FFT X', mode: 'lines', line: { color: '#38bdf8', width: 1.2 }, visible: showX },
        { x: fft.frequency || [], y: showY ? (fft.magnitude_y || []) : [], name: 'FFT Y', mode: 'lines', line: { color: '#4ade80', width: 1.2 }, visible: showY },
        { x: fft.frequency || [], y: showZ ? (fft.magnitude_z || []) : [], name: 'FFT Z', mode: 'lines', line: { color: '#f43f5e', width: 1.2 }, visible: showZ }
    ], {
        ...darkLayoutBase,
        xaxis: { ...darkLayoutBase.xaxis, range: [0, Math.min(500, (data.nyquist_frequency || 750))], title: { text: 'Frequency (Hz)', font: { size: 10 } } },
        yaxis: { ...darkLayoutBase.yaxis, title: { text: 'Amplitude (m/s²)', font: { size: 10 } } }
    }, { responsive: true, displayModeBar: false });

    // Append to rolling trend buffers
    const nowStr = new Date().toLocaleTimeString();
    historyTime.push(nowStr);
    historyRms.push(totalRms);
    historyCurrent.push(currVal);
    historyTemp.push(tempVal);

    if (historyTime.length > maxTrendPoints) {
        historyTime.shift();
        historyRms.shift();
        historyCurrent.shift();
        historyTemp.shift();
    }

    // 3. Severity Trend
    Plotly.react('plotSeverity', [
        { x: historyTime, y: historyRms, name: 'RMS Total', mode: 'lines+markers', line: { color: '#38bdf8', width: 2 } }
    ], {
        ...darkLayoutBase,
        margin: { l: 40, r: 15, t: 15, b: 25 },
        showlegend: false,
        shapes: [
            { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 1.12, y1: 1.12, line: { color: '#22c55e', dash: 'dot', width: 1 } },
            { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 2.80, y1: 2.80, line: { color: '#f59e0b', dash: 'dot', width: 1 } },
            { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 4.50, y1: 4.50, line: { color: '#ef4444', dash: 'dot', width: 1 } },
        ]
    }, { responsive: true, displayModeBar: false });

    // 4. Current Trend
    Plotly.react('plotCurrent', [
        { x: historyTime, y: historyCurrent, name: 'Current', mode: 'lines', line: { color: '#fbbf24', width: 2 } }
    ], {
        ...darkLayoutBase,
        margin: { l: 40, r: 15, t: 15, b: 25 },
        showlegend: false,
        shapes: [
            { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 0.5, y1: 0.5, line: { color: '#ef4444', dash: 'dot', width: 1 } }
        ]
    }, { responsive: true, displayModeBar: false });

    // 5. Temperature Trend
    Plotly.react('plotTemperature', [
        { x: historyTime, y: historyTemp, name: 'Temp', mode: 'lines', line: { color: '#f87171', width: 2 } }
    ], {
        ...darkLayoutBase,
        margin: { l: 40, r: 15, t: 15, b: 25 },
        showlegend: false,
        shapes: [
            { type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 70.0, y1: 70.0, line: { color: '#ef4444', dash: 'dot', width: 1 } }
        ]
    }, { responsive: true, displayModeBar: false });
}

// Characteristic Frequencies Update
function updateCharacteristicFrequencies(bf, ef) {
    if (!bf) return;
    if (bf.fr !== undefined) document.getElementById('freq1x').innerText = bf.fr.toFixed(2);
    if (bf.harmonics && bf.harmonics['2x'] !== undefined) document.getElementById('freq2x').innerText = bf.harmonics['2x'].toFixed(2);
    if (bf.bpfo !== undefined) document.getElementById('freqBPFO').innerText = bf.bpfo ? bf.bpfo.toFixed(2) : 'N/A';
    if (bf.bpfi !== undefined) document.getElementById('freqBPFI').innerText = bf.bpfi ? bf.bpfi.toFixed(2) : 'N/A';
    if (bf.bsf !== undefined) document.getElementById('freqBSF').innerText = bf.bsf ? bf.bsf.toFixed(2) : 'N/A';
    if (bf.ftf !== undefined) document.getElementById('freqFTF').innerText = bf.ftf ? bf.ftf.toFixed(2) : 'N/A';

    if (ef && ef.pole_pass_frequency !== undefined) {
        document.getElementById('freqPP').innerText = ef.pole_pass_frequency ? ef.pole_pass_frequency.toFixed(2) : 'N/A';
    }
}

// Potential Faults Table Update
function updatePotentialFaults(fa) {
    if (!fa) return;
    const tableBody = document.getElementById('potentialFaultsTable');
    if (!tableBody) return;

    const faults = fa.potential_faults || [];
    if (faults.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td>None Detected</td>
                <td>Baseline spectral vibration levels within acceptable tolerances</td>
                <td><span class="badge-custom badge-healthy">Nominal</span></td>
            </tr>
        `;
        return;
    }

    let html = '';
    for (const f of faults) {
        let badgeClass = 'badge-info';
        if (f.status === 'High' || f.status === 'Strong indication') badgeClass = 'badge-danger';
        else if (f.status === 'Moderate' || f.status === 'Moderate indication') badgeClass = 'badge-warning';
        else if (f.status === 'Nominal') badgeClass = 'badge-healthy';

        html += `
            <tr>
                <td><strong>${f.fault}</strong></td>
                <td>${f.evidence}</td>
                <td><span class="badge-custom ${badgeClass}">${f.status}</span></td>
            </tr>
        `;
    }
    tableBody.innerHTML = html;
}

// Initialize Controls & Event Listeners
async function setupControls() {
    // Replay Buttons
    document.getElementById('btnStart').addEventListener('click', async () => {
        await fetch('/api/control/replay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'start' })
        });
        isPaused = false;
        document.getElementById('btnPause').style.display = 'inline-block';
        document.getElementById('btnResume').style.display = 'none';
    });

    document.getElementById('btnPause').addEventListener('click', async () => {
        await fetch('/api/control/replay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'pause' })
        });
        isPaused = true;
        document.getElementById('btnPause').style.display = 'none';
        document.getElementById('btnResume').style.display = 'inline-block';
    });

    document.getElementById('btnResume').addEventListener('click', async () => {
        await fetch('/api/control/replay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'resume' })
        });
        isPaused = false;
        document.getElementById('btnPause').style.display = 'inline-block';
        document.getElementById('btnResume').style.display = 'none';
    });

    document.getElementById('btnStop').addEventListener('click', async () => {
        await fetch('/api/control/replay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'stop' })
        });
    });

    document.getElementById('btnReset').addEventListener('click', async () => {
        await fetch('/api/control/replay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'reset' })
        });
        historyTime.length = 0;
        historyRms.length = 0;
        historyCurrent.length = 0;
        historyTemp.length = 0;
    });

    // Speed Selector
    document.getElementById('speedSelect').addEventListener('change', async (e) => {
        await fetch('/api/control/replay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'speed', speed: e.target.value })
        });
    });

    // Loop Toggle
    document.getElementById('loopCheckbox').addEventListener('change', async (e) => {
        await fetch('/api/control/replay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'loop', loop: e.target.checked })
        });
    });

    // Window Size Selector
    document.getElementById('windowSizeSelect').addEventListener('change', async (e) => {
        const sz = parseInt(e.target.value);
        await fetch('/api/control/dsp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ window_size: sz })
        });
        document.getElementById('mlInputSize').innerText = sz;
    });

    // FFT Window Selector
    document.getElementById('fftWindowSelect').addEventListener('change', async (e) => {
        await fetch('/api/control/dsp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fft_window: e.target.value })
        });
    });

    // ML Model Selector
    document.getElementById('mlModelSelect').addEventListener('change', async (e) => {
        await fetch('/api/control/dsp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ml_model: e.target.value })
        });
    });

    // Dataset Selector
    const datasetSelect = document.getElementById('datasetSelect');
    datasetSelect.addEventListener('change', async (e) => {
        if (!e.target.value) return;
        await fetch('/api/control/replay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'load_dataset', file_path: e.target.value })
        });
    });

    // Populate Datasets Dropdown
    try {
        const res = await fetch('/api/datasets');
        if (res.ok) {
            const datasets = await res.json();
            datasetSelect.innerHTML = '';
            for (const d of datasets) {
                const opt = document.createElement('option');
                opt.value = d.file_path;
                opt.innerText = `${d.condition}: ${d.file_name}`;
                if (d.is_active) opt.selected = true;
                datasetSelect.appendChild(opt);
            }
        }
    } catch (e) {
        console.error('Failed to load datasets list:', e);
    }

    // Fetch Database Status for Navbar
    try {
        const stRes = await fetch('/api/status');
        if (stRes.ok) {
            const st = await stRes.json();
            const dbBadge = document.getElementById('navDbBadge');
            if (dbBadge && st.database) {
                dbBadge.innerText = `DB: ${st.database.db_type}`;
                dbBadge.style.color = st.database.is_mysql ? '#22c55e' : '#fbbf24';
            }
        }
    } catch (e) {}
}

// On Page Load
document.addEventListener('DOMContentLoaded', () => {
    initPlots();
    setupControls();
    connectWebSocket();
});

