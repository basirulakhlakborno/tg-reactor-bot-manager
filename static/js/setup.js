// Setup page JavaScript

let moduleStatus = {};
let setupStarted = false;
let modulesToInstall = [];
let currentModuleIndex = 0;

// Don't check modules on load - wait for Start Setup button
document.addEventListener('DOMContentLoaded', () => {
    // Hide modules initially
    const modulesList = document.getElementById('modulesList');
    if (modulesList) {
        modulesList.style.display = 'none';
    }
    
    // Add click handler to start setup button
    const startBtn = document.getElementById('startSetupBtn');
    if (startBtn) {
        startBtn.addEventListener('click', startSetup);
    }
});

async function startSetup() {
    if (setupStarted) return;
    
    setupStarted = true;
    const startContainer = document.getElementById('startSetupContainer');
    const modulesList = document.getElementById('modulesList');
    const setupActions = document.getElementById('setupActions');
    const errorMsg = document.getElementById('setupErrorMessage');
    
    // Hide error message if visible
    if (errorMsg) {
        errorMsg.style.display = 'none';
        errorMsg.textContent = '';
    }
    
    // Hide start container (header and button) and show modules
    if (startContainer) {
        startContainer.style.display = 'none';
    }
    if (modulesList) {
        modulesList.style.display = 'block';
    }
    if (setupActions) {
        setupActions.style.display = 'flex';
    }
    
    // Check modules first
    await checkModules();
    
    // Get list of modules that need installation
    modulesToInstall = Object.keys(moduleStatus).filter(m => !moduleStatus[m]);
    currentModuleIndex = 0;
    
    // Start installing modules one at a time
    if (modulesToInstall.length > 0) {
        installNextModule();
    } else {
        // All modules already installed
        document.getElementById('nextStepBtn').style.display = 'inline-flex';
    }
}

async function checkModules() {
    try {
        const response = await fetch('/setup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ action: 'check_modules' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            moduleStatus = result.modules;
            updateModuleStatus();
        }
    } catch (error) {
        console.error('Error checking modules:', error);
    }
}

function updateModuleStatus() {
    for (const [module, installed] of Object.entries(moduleStatus)) {
        const statusEl = document.getElementById(`status-${module}`);
        const btnEl = document.getElementById(`btn-${module}`);
        const itemEl = statusEl ? statusEl.closest('.module-item') : null;
        
        if (installed) {
            if (statusEl) {
                statusEl.innerHTML = '<i class="fas fa-check-circle"></i> Installed';
                statusEl.className = 'module-status installed';
            }
            if (btnEl) btnEl.style.display = 'none';
            if (itemEl) itemEl.classList.add('installed');
        } else {
            if (statusEl) {
                statusEl.innerHTML = '<i class="fas fa-times-circle"></i> Not Installed';
                statusEl.className = 'module-status';
            }
            if (btnEl) btnEl.style.display = 'none'; // Hide individual install buttons
            if (itemEl) itemEl.classList.remove('installed');
        }
    }
}

async function installModule(moduleName) {
    const statusEl = document.getElementById(`status-${moduleName}`);
    const btnEl = document.getElementById(`btn-${moduleName}`);
    const itemEl = statusEl ? statusEl.closest('.module-item') : null;
    
    // Update UI
    if (statusEl) {
        statusEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Installing...';
        statusEl.className = 'module-status installing';
    }
    if (btnEl) btnEl.disabled = true;
    if (itemEl) {
        itemEl.classList.add('installing');
        itemEl.classList.remove('error');
    }
    
    try {
        const response = await fetch('/setup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ action: 'install_module', module: moduleName })
        });
        
        const result = await response.json();
        
        if (result.success) {
            moduleStatus[moduleName] = true;
            if (statusEl) {
                statusEl.innerHTML = '<i class="fas fa-check-circle"></i> Installed';
                statusEl.className = 'module-status installed';
            }
            if (btnEl) btnEl.style.display = 'none';
            if (itemEl) {
                itemEl.classList.remove('installing');
                itemEl.classList.add('installed');
            }
            
            return true;
        } else {
            if (statusEl) {
                statusEl.innerHTML = `<i class="fas fa-exclamation-circle"></i> Error: ${result.message || 'Installation failed'}`;
                statusEl.className = 'module-status error';
            }
            if (btnEl) btnEl.disabled = false;
            if (itemEl) {
                itemEl.classList.remove('installing');
                itemEl.classList.add('error');
            }
            return false;
        }
    } catch (error) {
        if (statusEl) {
            statusEl.innerHTML = '<i class="fas fa-exclamation-circle"></i> Error: Network error';
            statusEl.className = 'module-status error';
        }
        if (btnEl) btnEl.disabled = false;
        if (itemEl) {
            itemEl.classList.remove('installing');
            itemEl.classList.add('error');
        }
        return false;
    }
}

async function installNextModule() {
    if (currentModuleIndex >= modulesToInstall.length) {
        // All modules installed
        const allInstalled = Object.values(moduleStatus).every(v => v);
        if (allInstalled) {
            document.getElementById('nextStepBtn').style.display = 'inline-flex';
        }
        return;
    }
    
    const moduleName = modulesToInstall[currentModuleIndex];
    const success = await installModule(moduleName);
    
    // Move to next module
    currentModuleIndex++;
    
    // Install next module after a short delay
    if (currentModuleIndex < modulesToInstall.length) {
        setTimeout(() => {
            installNextModule();
        }, 500);
    } else {
        // All modules processed
        const allInstalled = Object.values(moduleStatus).every(v => v);
        if (allInstalled) {
            document.getElementById('nextStepBtn').style.display = 'inline-flex';
        }
    }
}

function nextStep() {
    document.getElementById('step1').classList.remove('active');
    document.getElementById('step2').classList.add('active');
    document.getElementById('setupUsername').focus();
}

// Setup form handler
document.getElementById('setupForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoader = submitBtn.querySelector('.btn-loader');
    const errorMsg = document.getElementById('setupErrorMessage');
    
    // Show loading state
    submitBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-block';
    errorMsg.style.display = 'none';
    
    const formData = new FormData(form);
    const data = {
        action: 'complete_setup',
        username: formData.get('username'),
        password: formData.get('password'),
        confirm_password: formData.get('confirm_password')
    };
    
    try {
        const response = await fetch('/setup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            window.location.href = result.redirect || '/';
        } else {
            errorMsg.textContent = result.error || 'Setup failed';
            errorMsg.style.display = 'block';
            submitBtn.disabled = false;
            btnText.style.display = 'inline-block';
            btnLoader.style.display = 'none';
        }
    } catch (error) {
        errorMsg.textContent = 'An error occurred. Please try again.';
        errorMsg.style.display = 'block';
        submitBtn.disabled = false;
        btnText.style.display = 'inline-block';
        btnLoader.style.display = 'none';
    }
});
