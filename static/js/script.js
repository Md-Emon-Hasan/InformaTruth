document.addEventListener('DOMContentLoaded', function() {
    // Input type toggle
    document.querySelectorAll('input[name="inputType"]').forEach(radio => {
        radio.addEventListener('change', function() {
            document.getElementById('textInputGroup').classList.add('d-none');
            document.getElementById('urlInputGroup').classList.add('d-none');
            document.getElementById('fileInputGroup').classList.add('d-none');
            
            if (this.value === 'text') {
                document.getElementById('textInputGroup').classList.remove('d-none');
            } else if (this.value === 'url') {
                document.getElementById('urlInputGroup').classList.remove('d-none');
            } else {
                document.getElementById('fileInputGroup').classList.remove('d-none');
            }
        });
    });

    // Clear file input
    document.getElementById('clearFile').addEventListener('click', function() {
        document.getElementById('fileUpload').value = '';
    });

    // Form submission
    document.getElementById('analysisForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const inputType = document.querySelector('input[name="inputType"]:checked').value;
        let content = '';
        
        // Validate input
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
                showAlert('Please enter a valid URL (starting with http:// or https://)', 'warning');
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
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const form = document.getElementById('analysisForm');
    form.prepend(alert);
    
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 150);
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
    // In a real implementation, you would use PDF.js or similar
    // This is a placeholder that just returns the filename
    return file.name;
}

function analyzeContent(inputType, content) {
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultsContainer = document.getElementById('resultsContainer');
    
    // Show loading state
    loadingSpinner.classList.remove('d-none');
    resultsContainer.innerHTML = '';
    
    // Create floating particles during loading
    createLoadingParticles();
    
    fetch('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            inputType: inputType,
            content: content
        })
    })
    .then(response => response.json())
    .then(data => {
        loadingSpinner.classList.add('d-none');
        removeLoadingParticles();
        showResults(data);
    })
    .catch(error => {
        loadingSpinner.classList.add('d-none');
        removeLoadingParticles();
        resultsContainer.innerHTML = `
            <div class="alert alert-danger animate__animated animate__shakeX">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                Error analyzing content: ${error.message}
            </div>
        `;
    });
}

function createLoadingParticles() {
    const container = document.createElement('div');
    container.id = 'particles-container';
    container.style.position = 'fixed';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '100%';
    container.style.height = '100%';
    container.style.pointerEvents = 'none';
    container.style.zIndex = '1000';
    
    for (let i = 0; i < 20; i++) {
        const particle = document.createElement('div');
        particle.style.position = 'absolute';
        particle.style.width = '10px';
        particle.style.height = '10px';
        particle.style.backgroundColor = '#6a11cb';
        particle.style.borderRadius = '50%';
        particle.style.opacity = '0.6';
        
        // Random position
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;
        
        // Animation
        particle.style.animation = `float ${2 + Math.random() * 3}s infinite ease-in-out`;
        
        container.appendChild(particle);
    }
    
    document.body.appendChild(container);
    
    // Add CSS animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes float {
            0%, 100% { transform: translateY(0) translateX(0); }
            25% { transform: translateY(-20px) translateX(10px); }
            50% { transform: translateY(-40px) translateX(0); }
            75% { transform: translateY(-20px) translateX(-10px); }
        }
    `;
    document.head.appendChild(style);
}

function removeLoadingParticles() {
    const container = document.getElementById('particles-container');
    if (container) container.remove();
}

function showResults(data) {
    const resultsContainer = document.getElementById('resultsContainer');
    const isReal = data.label === 'Real';
    const confidencePercent = Math.round(parseFloat(data.confidence) * 100);
    
    resultsContainer.innerHTML = `
        <div class="card animate__animated animate__fadeInUp">
            <div class="card-header ${isReal ? 'real-bg' : 'fake-bg'} text-white">
                <h4 class="mb-0">
                    <i class="bi ${isReal ? 'bi-check-circle' : 'bi-exclamation-triangle'} me-2"></i>
                    Analysis Result: ${data.label}
                </h4>
            </div>
            <div class="card-body">
                <div class="row mb-4">
                    <div class="col-md-6 mb-3 mb-md-0">
                        <h5 class="d-flex align-items-center">
                            <span class="badge ${isReal ? 'bg-success' : 'bg-danger'} me-2">
                                ${isReal ? 'Authentic' : 'Fake'}
                            </span>
                            Confidence: ${confidencePercent}%
                        </h5>
                        <div class="confidence-meter mt-2">
                            <div class="confidence-fill ${isReal ? 'bg-success' : 'bg-danger'}" 
                                 style="width: ${confidencePercent}%"></div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <canvas id="confidenceChart" height="100"></canvas>
                    </div>
                </div>
                
                <div class="mb-3">
                    <h5><i class="bi bi-chat-square-text me-2"></i>AI Explanation</h5>
                    <div class="p-3 bg-light rounded">
                        <p class="mb-0">${data.explanation}</p>
                    </div>
                </div>
                
                <div class="d-grid mt-4">
                    <button class="btn ${isReal ? 'btn-success' : 'btn-danger'} animate__animated animate__pulse animate__infinite" 
                            onclick="window.location.reload()">
                        <i class="bi bi-arrow-repeat me-2"></i>Analyze Another
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Create confidence chart
    createConfidenceChart(confidencePercent, isReal);
}

function createConfidenceChart(confidence, isReal) {
    const ctx = document.getElementById('confidenceChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Confidence', 'Uncertainty'],
            datasets: [{
                data: [confidence, 100 - confidence],
                backgroundColor: [
                    isReal ? '#00b09b' : '#ff416c',
                    '#e9ecef'
                ],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '70%',
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}