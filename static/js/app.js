// API Base URL
const API_BASE = '/api';

// State
let currentTab = 'bots';
let bots = {};
let channels = {};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadData();
    setInterval(loadData, 5000); // Refresh every 5 seconds
    setInterval(updateStatus, 2000); // Update status every 2 seconds
});

// Load data
async function loadData() {
    try {
        await Promise.all([
            loadBots(),
            loadChannels(),
            updateStats()
        ]);
    } catch (error) {
        console.error('Error loading data:', error);
        showToast('Error loading data', 'error');
    }
}

// Load bots
async function loadBots() {
    try {
        const response = await fetch(`${API_BASE}/bots`);
        const data = await response.json();
        
        if (data.success) {
            bots = data.bots || {};
            renderBots();
        }
    } catch (error) {
        console.error('Error loading bots:', error);
    }
}

// Load channels
async function loadChannels() {
    try {
        const response = await fetch(`${API_BASE}/channels`);
        const data = await response.json();
        
        if (data.success) {
            channels = data.channels || {};
            renderChannels();
        }
    } catch (error) {
        console.error('Error loading channels:', error);
    }
}

// Update stats
async function updateStats() {
    try {
        const response = await fetch(`${API_BASE}/status`);
        const data = await response.json();
        
        if (data.success) {
            const status = data.status;
            document.getElementById('totalBots').textContent = status.total_bots;
            document.getElementById('runningBots').textContent = status.running_bots;
            document.getElementById('stoppedBots').textContent = status.stopped_bots;
            document.getElementById('totalChannels').textContent = status.total_channels;
            
            // Update server status badge
            const statusBadge = document.getElementById('serverStatus');
            if (status.server_running) {
                statusBadge.className = 'status-badge online';
                statusBadge.innerHTML = '<i class="fas fa-circle"></i> <span>Server Running</span>';
            } else {
                statusBadge.className = 'status-badge offline';
                statusBadge.innerHTML = '<i class="fas fa-circle"></i> <span>Server Stopped</span>';
            }
        }
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// Update status
async function updateStatus() {
    await updateStats();
}

// Render bots
function renderBots() {
    const tbody = document.getElementById('botsTableBody');
    
    if (Object.keys(bots).length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No bots added yet. Click "Add Bot" to get started.</td></tr>';
        return;
    }
    
    tbody.innerHTML = Object.entries(bots).map(([id, bot]) => `
        <tr>
            <td data-label="Name"><strong>${escapeHtml(bot.name)}</strong></td>
            <td data-label="Status">
                <span class="status-badge-table ${bot.is_running ? 'running' : 'stopped'}">
                    <i class="fas fa-circle"></i>
                    ${bot.is_running ? 'Running' : 'Stopped'}
                </span>
            </td>
            <td data-label="Token"><code>${escapeHtml(bot.token)}</code></td>
            <td data-label="Actions">
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    ${bot.is_running 
                        ? `<button class="btn btn-warning btn-sm" onclick="stopBot('${id}')">
                            <i class="fas fa-stop"></i> Stop
                           </button>`
                        : `<button class="btn btn-primary btn-sm" onclick="startBot('${id}')">
                            <i class="fas fa-play"></i> Start
                           </button>`
                    }
                    <button class="btn btn-danger btn-sm" onclick="removeBot('${id}')">
                        <i class="fas fa-trash"></i> Remove
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Render channels
function renderChannels() {
    const tbody = document.getElementById('channelsTableBody');
    
    if (Object.keys(channels).length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="empty-state">No channels added yet. Click "Add Channel" to get started.</td></tr>';
        return;
    }
    
    tbody.innerHTML = Object.entries(channels).map(([id, channel]) => `
        <tr>
            <td data-label="Name"><strong>${escapeHtml(channel.name)}</strong></td>
            <td data-label="Channel ID"><code>${escapeHtml(channel.channel_id)}</code></td>
            <td data-label="Actions">
                <button class="btn btn-danger btn-sm" onclick="removeChannel('${id}')">
                    <i class="fas fa-trash"></i> Remove
                </button>
            </td>
        </tr>
    `).join('');
}

// Switch tab
function switchTab(tab) {
    currentTab = tab;
    
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById(`${tab}Tab`).classList.add('active');
}

// Modal functions
function openAddBotModal() {
    document.getElementById('addBotModal').classList.add('active');
    document.getElementById('botName').value = '';
    document.getElementById('botToken').value = '';
}

function openAddChannelModal() {
    document.getElementById('addChannelModal').classList.add('active');
    document.getElementById('channelName').value = '';
    document.getElementById('channelId').value = '';
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Add bot
async function addBot() {
    const name = document.getElementById('botName').value.trim();
    const token = document.getElementById('botToken').value.trim();
    
    if (!token) {
        showToast('Please enter a bot token', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/bots`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, token })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Bot added successfully!', 'success');
            closeModal('addBotModal');
            await loadBots();
            await updateStats();
        } else {
            showToast(data.error || 'Failed to add bot', 'error');
        }
    } catch (error) {
        showToast('Error adding bot', 'error');
        console.error(error);
    }
}

// Add channel
async function addChannel() {
    const name = document.getElementById('channelName').value.trim();
    const channelId = document.getElementById('channelId').value.trim();
    
    if (!channelId) {
        showToast('Please enter a channel ID', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/channels`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, channel_id: channelId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Channel added successfully!', 'success');
            closeModal('addChannelModal');
            await loadChannels();
            await updateStats();
        } else {
            showToast(data.error || 'Failed to add channel', 'error');
        }
    } catch (error) {
        showToast('Error adding channel', 'error');
        console.error(error);
    }
}

// Start bot
async function startBot(botId) {
    try {
        const response = await fetch(`${API_BASE}/bots/${botId}/start`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Bot started successfully!', 'success');
            await loadBots();
            await updateStats();
        } else {
            showToast(data.error || 'Failed to start bot', 'error');
        }
    } catch (error) {
        showToast('Error starting bot', 'error');
        console.error(error);
    }
}

// Stop bot
async function stopBot(botId) {
    try {
        const response = await fetch(`${API_BASE}/bots/${botId}/stop`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Bot stopped successfully!', 'success');
            await loadBots();
            await updateStats();
        } else {
            showToast(data.error || 'Failed to stop bot', 'error');
        }
    } catch (error) {
        showToast('Error stopping bot', 'error');
        console.error(error);
    }
}

// Remove bot
async function removeBot(botId) {
    if (!confirm('Are you sure you want to remove this bot?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/bots/${botId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Bot removed successfully!', 'success');
            await loadBots();
            await updateStats();
        } else {
            showToast(data.error || 'Failed to remove bot', 'error');
        }
    } catch (error) {
        showToast('Error removing bot', 'error');
        console.error(error);
    }
}

// Remove channel
async function removeChannel(channelId) {
    if (!confirm('Are you sure you want to remove this channel?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/channels/${channelId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Channel removed successfully!', 'success');
            await loadChannels();
            await updateStats();
        } else {
            showToast(data.error || 'Failed to remove channel', 'error');
        }
    } catch (error) {
        showToast('Error removing channel', 'error');
        console.error(error);
    }
}

// Start all bots
async function startAllBots() {
    try {
        const response = await fetch(`${API_BASE}/bots/start-all`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`Started ${data.count} bots!`, 'success');
            await loadBots();
            await updateStats();
        } else {
            showToast(data.error || 'Failed to start bots', 'error');
        }
    } catch (error) {
        showToast('Error starting bots', 'error');
        console.error(error);
    }
}

// Stop all bots
async function stopAllBots() {
    try {
        const response = await fetch(`${API_BASE}/bots/stop-all`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`Stopped ${data.count} bots!`, 'success');
            await loadBots();
            await updateStats();
        } else {
            showToast(data.error || 'Failed to stop bots', 'error');
        }
    } catch (error) {
        showToast('Error stopping bots', 'error');
        console.error(error);
    }
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modal on outside click
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
}

