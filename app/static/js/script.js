document.addEventListener('DOMContentLoaded', function () {
    // Input type toggle with smooth transitions
    document.querySelectorAll('input[name="inputType"]').forEach(radio => {
        radio.addEventListener('change', function () {
            const groups = ['textInputGroup', 'urlInputGroup', 'fileInputGroup'];
            groups.forEach(id => {
                const el = document.getElementById(id);
                el.classList.add('d-none');
                el.classList.remove('animate__fadeIn');
            });

            let targetId = 'textInputGroup';
            if (this.value === 'url') targetId = 'urlInputGroup';
            if (this.value === 'pdf') targetId = 'fileInputGroup';

            const targetEl = document.getElementById(targetId);
            targetEl.classList.remove('d-none');
            targetEl.classList.add('animate__fadeIn');
        });
    });

    // Clear file input
    document.getElementById('clearFile').addEventListener('click', function () {
        document.getElementById('fileUpload').value = '';
    });

    // Form submission
    document.getElementById('analysisForm').addEventListener('submit', async function (e) {
        e.preventDefault();

        const inputType = document.querySelector('input[name="inputType"]:checked').value;
        let content = '';

        if (inputType === 'text') {
            content = document.getElementById('content').value.trim();
            if (!content) {
                showAlert('Please enter some text to analyze', 'warning');
                return;
            }
        }
        else if (inputType === 'url') {
            content = document.getElementById('urlContent').value.trim();
            if (!content) {
                showAlert('Please enter a URL to analyze', 'warning');
                return;
            }
            if (!isValidUrl(content)) {
                showAlert('Please enter a valid URL', 'warning');
                return;
            }
        }
        else {
            const file = document.getElementById('fileUpload').files[0];
            if (!file) {
                showAlert('Please select a PDF file to upload', 'warning');
                return;
            }
            content = await extractTextFromPDF(file);
        }

        analyzeContent(inputType, content);
    });
});

function showAlert(message, type) {
    const alert = document.createElement('div');
    alert.className = `alert glass-panel border-${type} text-white animate__animated animate__headShake position-fixed top-0 start-50 translate-middle-x mt-4`;
    alert.style.zIndex = '9999';
    alert.style.backgroundColor = 'rgba(15, 23, 42, 0.9)';
    alert.innerHTML = `<i class="bi bi-info-circle me-2 text-${type}"></i>${message}`;

    document.body.appendChild(alert);

    setTimeout(() => {
        alert.classList.replace('animate__headShake', 'animate__fadeOutUp');
        setTimeout(() => alert.remove(), 500);
    }, 3000);
}

function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

async function extractTextFromPDF(file) {
    return file.name;
}

function analyzeContent(inputType, content) {
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultsContainer = document.getElementById('resultsContainer');
    const submitBtn = document.querySelector('.btn-premium');

    submitBtn.disabled = true;
    loadingSpinner.classList.remove('d-none');
    resultsContainer.innerHTML = '';

    createLoadingParticles();

    fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ inputType, content })
    })
        .then(response => response.json())
        .then(data => {
            submitBtn.disabled = false;
            loadingSpinner.classList.add('d-none');
            removeLoadingParticles();
            showResults(data);
        })
        .catch(error => {
            submitBtn.disabled = false;
            loadingSpinner.classList.add('d-none');
            removeLoadingParticles();
            resultsContainer.innerHTML = `
            <div class="glass-panel p-4 border-danger animate__animated animate__shakeX">
                <i class="bi bi-exclamation-octagon-fill me-2 text-danger"></i>
                Error: ${error.message}
            </div>
        `;
        });
}

function createLoadingParticles() {
    const container = document.createElement('div');
    container.id = 'premium-particles';
    container.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:900;';

    for (let i = 0; i < 15; i++) {
        const p = document.createElement('div');
        const size = Math.random() * 4 + 2;
        p.style.cssText = `
            position:absolute;
            width:${size}px;
            height:${size}px;
            background:${i % 2 === 0 ? 'var(--primary)' : 'var(--secondary)'};
            border-radius:50%;
            filter:blur(1px);
            left:${Math.random() * 100}%;
            top:${Math.random() * 100}%;
            opacity:0.6;
            animation: float ${Math.random() * 4 + 3}s infinite linear;
        `;
        container.appendChild(p);
    }
    document.body.appendChild(container);
}

function removeLoadingParticles() {
    const c = document.getElementById('premium-particles');
    if (c) c.remove();
}

function showResults(data) {
    const resultsContainer = document.getElementById('resultsContainer');
    const isReal = data.label === 'Real';
    const confidencePercent = Math.round(parseFloat(data.confidence) * 100);
    const accentColor = isReal ? 'var(--real)' : 'var(--fake)';

    resultsContainer.innerHTML = `
        <div class="glass-panel result-card ${isReal ? 'real-border' : 'fake-border'} animate__animated animate__fadeInUp p-4 p-md-5">
            <div class="row align-items-center">
                <div class="col-md-7">
                    <div class="d-flex align-items-center mb-4">
                        <div class="icon-box me-3 p-3 rounded-circle" style="background: ${accentColor}20;">
                            <i class="bi ${isReal ? 'bi-patch-check-fill' : 'bi-shield-exclamation'} fs-1" style="color: ${accentColor};"></i>
                        </div>
                        <div>
                            <h6 class="text-secondary text-uppercase small fw-bold mb-1">AI Verdict</h6>
                            <h2 class="fw-bold mb-0">${data.label} Content</h2>
                        </div>
                    </div>
                    
                    <div class="mb-4">
                        <div class="d-flex justify-content-between mb-2">
                            <span class="text-secondary small fw-medium">Confidence Score</span>
                            <span class="fw-bold" style="color: ${accentColor};">${confidencePercent}%</span>
                        </div>
                        <div class="progress bg-white bg-opacity-10" style="height: 8px; border-radius: 4px;">
                            <div class="progress-bar" style="width: ${confidencePercent}%; background: ${accentColor}; border-radius: 4px; box-shadow: 0 0 10px ${accentColor}60;"></div>
                        </div>
                    </div>

                    <div class="mb-4">
                        <h6 class="text-secondary text-uppercase small fw-bold mb-3">AI Explanation</h6>
                        <div class="p-3 rounded-4" style="background: rgba(255,255,255,0.5); border: 1px solid rgba(255,255,255,0.1);">
                            <p class="mb-0 text-secondary-emphasis" style="line-height: 1.6;">${data.explanation}</p>
                        </div>
                    </div>
                </div>

                <div class="col-md-5 d-flex justify-content-center">
                    <div class="position-relative">
                        <canvas id="confidenceChart" width="200" height="200"></canvas>
                        <div class="position-absolute top-50 start-50 translate-middle text-center">
                            <h3 class="fw-bold mb-0">${confidencePercent}%</h3>
                            <span class="text-secondary small">Match</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="mt-4 border-top border-secondary border-opacity-10 pt-4 d-flex justify-content-between align-items-center">
                <span class="text-secondary small"><i class="bi bi-clock-history me-1"></i> Analysis complete</span>
                <button class="btn btn-outline-secondary btn-sm px-4" onclick="window.location.reload()">Reset Analyzer</button>
            </div>
        </div>
    `;

    createConfidenceChart(confidencePercent, isReal);
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function createConfidenceChart(confidence, isReal) {
    const ctx = document.getElementById('confidenceChart').getContext('2d');
    const color = isReal ? '#10b981' : '#ef4444';

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [confidence, 100 - confidence],
                backgroundColor: [color, 'rgba(255,255,255,0.05)'],
                borderWidth: 0,
                borderRadius: 10,
            }]
        },
        options: {
            cutout: '85%',
            events: [],
            plugins: { legend: { display: false }, tooltip: { enabled: false } }
        }
    });
}