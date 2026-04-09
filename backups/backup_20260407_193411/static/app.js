/* 
BACKPOCKET CONTROL CENTER LOGIC v3.0
Interactive Box & Task-Specific Logic
*/

document.addEventListener('DOMContentLoaded', () => {
    updateDateTime();
    setInterval(updateDateTime, 30000);
    pollSystemStatus();
    setInterval(pollSystemStatus, 15000);

    // Header interaction
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');

    async function pollSystemStatus() {
        try {
            const resp = await fetch('/api/status');
            const data = await resp.json();
            
            if (data.status === 'Healthy') {
                statusDot.classList.remove('offline');
                statusDot.classList.add('online');
                statusText.innerText = 'ONLINE';
            } else {
                statusDot.classList.remove('online');
                statusDot.classList.add('offline');
                statusText.innerText = 'OFFLINE';
            }

            // Update pending count
            const pendingCountEl = document.getElementById('pendingCount');
            if (pendingCountEl) {
                pendingCountEl.innerText = data.pending_count || 0;
            }

        } catch (e) {
            statusDot.classList.remove('online');
            statusDot.classList.add('offline');
            statusText.innerText = 'OFFLINE';
        }
    }

    function updateDateTime() {
        const now = new Date();
        const options = { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' };
        document.getElementById('currentDate').innerText = now.toLocaleDateString('en-US', options);
    }

    // Modal Handling
    const modal = document.getElementById('moduleModal');
    const modalBody = document.getElementById('modalBody');
    const closeModal = document.querySelector('.close-modal');

    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('click', () => {
            const module = card.dataset.module;
            showModuleDetails(module);
        });
    });

    closeModal.onclick = () => {
        modal.style.display = 'none';
    }

    window.onclick = (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }

    function showModuleDetails(module) {
        modalBody.innerHTML = '';
        modal.style.display = 'block';

        const configs = {
            triage: {
                title: "EMAIL TRIAGE",
                icon: "fa-inbox",
                desc: "Real-time patrol of 4 interconnected business accounts.",
                tasks: ["View Action Log", "Review Pending Approvals", "Update Whitelist", "Simulate Triage Test"]
            },
            filing: {
                title: "AUTOMATED FILING",
                icon: "fa-folder-open",
                desc: "Moving Tier 3 suppliers to dedicated folders (ATO, ASIC, QuickBooks).",
                tasks: ["Configure Folders", "Check Filing Logs", "Archive Rules"]
            },
            research: {
                title: "CLIENT RESEARCH",
                icon: "fa-search-dollar",
                desc: "Knowledge discovery engine for client history and financial status.",
                tasks: ["Search Client DB", "Audit History", "Extract Tax Context"]
            },
            creator: {
                title: "CONTENT CREATOR",
                icon: "fa-pen-nib",
                desc: "Drafting responses using your unique 'Omni-Tone' history.",
                tasks: ["Review Drafts", "Tune Tone Profile", "AI Email Templates"]
            },
            social: {
                title: "SOCIAL MEDIA",
                icon: "fa-share-nodes",
                desc: "Monitoring LinkedIn and Brand engagement.",
                tasks: ["Check Mentions", "Auto-Draft Responses", "Content Queue"]
            },
            communication: {
                title: "COMMUNICATION",
                icon: "fa-comments",
                desc: "WhatsApp Nudges, Call Centre messages, and SMS alerts.",
                tasks: ["View WhatsApp Log", "Contact Audit", "Nudge Settings"]
            },
            websites: {
                title: "WEBSITE PORTALS",
                icon: "fa-globe",
                desc: "Suitedash and BigBoss portal integration status.",
                tasks: ["Check Portal Health", "Update Links", "Portal User Audit"]
            },
            forms: {
                title: "REGISTRATION FLOW",
                icon: "fa-file-invoice",
                desc: "Handling 'New User Registered' emails to auto-onboard clients.",
                tasks: ["Onboarding Log", "Map Form Fields", "Test Onboard Flow"]
            }
        };

        const config = configs[module] || { title: "Module", icon: "fa-gear", desc: "Coming soon..." };
        
        modalBody.innerHTML = `
            <div class="modal-header-large">
                <i class="fas ${config.icon} big-icon"></i>
                <div class="header-text">
                    <h2>${config.title}</h2>
                    <p>${config.desc}</p>
                </div>
            </div>
            <div class="modal-sub-grid">
                ${config.tasks.map(t => `
                    <div class="sub-task">
                        <i class="fas fa-chevron-right"></i>
                        <span>${t}</span>
                    </div>
                `).join('')}
            </div>
            <div class="modal-footer">
                <button class="primary-btn" onclick="executeModuleTask('${module}')">Run Intelligence Model</button>
            </div>
        `;
    }

    // Command handling
    const cmdInput = document.getElementById('commandInput');
    const sendBtn = document.getElementById('sendCommand');

    sendBtn.addEventListener('click', handleCommand);
    cmdInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleCommand();
    });

    async function handleCommand() {
        const cmd = cmdInput.value.trim();
        if (!cmd) return;

        // Visual feedback for command sending
        cmdInput.value = "Executing command...";
        cmdInput.disabled = true;

        try {
            // Check if it's a 'find' command
            if (cmd.toLowerCase().startsWith('find ')) {
                const query = cmd.substring(5).trim();
                const resp = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const data = await resp.json();
                
                showModuleDetails('triage');
                modalBody.innerHTML += `
                    <div class="search-results">
                        <h3>Search Results for "${query}"</h3>
                        ${data.results.map(r => `
                            <div class="search-item">
                                <p><strong>Subject:</strong> ${r.subject}</p>
                                <p><strong>From:</strong> ${r.sender}</p>
                                <button onclick="rescueEmail('${r.id}', '${r.token_file}')" class="rescue-btn">⚓ Rescue to Inbox</button>
                            </div>
                        `).join('') || "<p>No emails found.</p>"}
                    </div>
                `;
            } else {
                 alert("Command received: " + cmd + ". Implementing full chat brain in next phase.");
            }
        } catch (e) {
            console.error(e);
        } finally {
            cmdInput.value = "";
            cmdInput.disabled = false;
        }
    }
});

function executeModuleTask(module) {
    alert(`⚡ Starting Intelligence Model for ${module}. Model: Gemini-2.0-Flash (Zero Cost Check)`);
}

async function triggerSystemAudit() {
    modalBody.innerHTML = `
        <div class="modal-header-large">
            <i class="fas fa-microchip big-icon stability-audit"></i>
            <div class="header-text">
                <h2>TWIN SYSTEM AUDIT</h2>
                <p>Ollama is analyzing the BackPocket codebase for vulnerabilities and improvements...</p>
            </div>
        </div>
        <div class="audit-status">
            <span class="loading-pulse">🛡️ ENGINE ANALYSIS IN PROGRESS...</span>
        </div>
    `;
    modal.style.display = 'block';

    try {
        const resp = await fetch('/api/audit');
        const data = await resp.json();
        
        modalBody.innerHTML = `
            <div class="modal-header-large">
                <i class="fas fa-microchip big-icon"></i>
                <div class="header-text">
                    <h2>STABILITY REPORT</h2>
                    <p>Report generated by Local Ollama (DeepSeek-R1)</p>
                </div>
            </div>
            <div class="audit-report-content">
                <pre>${data.report}</pre>
            </div>
            <div class="modal-footer">
                <button class="primary-btn" onclick="modal.style.display='none'">Acknowledged</button>
            </div>
        `;
    } catch (e) {
        modalBody.innerHTML = `<p>Audit failed: ${e.message}</p>`;
    }
}
async function rescueEmail(id, token) {
    const resp = await fetch(`/api/rescue?msg_id=${id}&token=${token}`, { method: 'POST' });
    const data = await resp.json();
    alert(data.status === 'success' ? "⚓ Message successfully rescued to INBOX!" : "❌ Error rescuing message.");
}
