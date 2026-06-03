// _UIUX/ds/js/app.js
const App = {
    async init() {
        UIHelpers.initTabs((target) => {
            if (target === 'view-taxonomy') {
                TaxonomyVM.load();
            } else if (target === 'view-ledger') {
                this.loadLedgersList();
            }
        });
        UIHelpers.initDatabaseSelector(async (dbType) => {
            await App.updateGlobalStatus();
            if (document.getElementById('view-taxonomy').classList.contains('active')) {
                TaxonomyVM.load();
            }
        });
        
        TaxonomyVM.init();

        await this.updateGlobalStatus();
        TaxonomyVM.load();

        // Muat Looker URL
        const savedLooker = localStorage.getItem('stki_looker_url');
        if (savedLooker) {
            const input = document.getElementById('looker-url');
            if (input) input.value = savedLooker;
            this.renderLooker(savedLooker);
        }
    },

    async updateGlobalStatus() {
        await UIHelpers.updateGlobalStatus((status) => {
            TaxonomyVM.updateStats(status.total_docs, status.optimal_labels_count, status.taxonomy);
        });
    },

    loadLooker() {
        const url = document.getElementById('looker-url').value.trim();
        if (!url) return;
        localStorage.setItem('stki_looker_url', url);
        this.renderLooker(url);
    },

    renderLooker(url) {
        const container = document.getElementById('looker-container');
        if (!container) return;
        
        let finalUrl = url;
        // Jika user tidak sengaja paste seluruh tag <iframe> dari Looker Studio
        const iframeMatch = url.match(/src=["'](.*?)["']/);
        if (iframeMatch && iframeMatch[1]) {
            finalUrl = iframeMatch[1];
        }

        if (!finalUrl.startsWith('http')) {
            container.innerHTML = `<div style="color: var(--color-danger); font-family: var(--font-mono); text-align: center; padding: 20px;">URL TIDAK VALID. Masukkan URL Looker Studio yang benar.</div>`;
            return;
        }

        container.style.border = "2px solid var(--color-ink)";
        container.style.boxShadow = "4px 4px 0px var(--color-ink)";
        container.style.padding = "0";
        container.innerHTML = `<iframe src="${finalUrl}" width="100%" height="100%" frameborder="0" style="border:0" allowfullscreen></iframe>`;
    },

    async loadLedgersList() {
        const listDiv = document.getElementById('ledger-list');
        if (!listDiv) return;
        listDiv.innerHTML = '<div class="empty-state">MEMUAT LEDGER...</div>';
        
        try {
            const res = await ApiService.getLedgers();
            if (res.status === 'success') {
                if (res.ledgers.length === 0) {
                    listDiv.innerHTML = '<div class="empty-state">TIDAK ADA LEDGER AKTIF</div>';
                    return;
                }
                
                listDiv.innerHTML = res.ledgers.map(l => {
                    const isActive = l === res.active;
                    return `
                    <div class="ledger-row" style="display: flex; padding: var(--spacing-sm) var(--spacing-md); border-bottom: 1px dashed var(--color-border); align-items: center; transition: background 0.2s;" onmouseover="this.style.background='var(--color-bg)'" onmouseout="this.style.background='transparent'">
                        <div style="flex: 2; font-family: var(--font-mono); font-weight: bold; color: ${isActive ? 'var(--color-safe)' : 'var(--color-ink)'}">${l}</div>
                        <div style="flex: 1; font-family: var(--font-mono); font-size: 0.8rem;">
                            ${isActive ? '<span style="background: var(--color-safe); color: var(--color-paper); padding: 2px 6px;">[ACTIVE]</span>' : '<span style="color: var(--color-ink-muted);">[STANDBY]</span>'}
                        </div>
                        <div style="flex: 2; text-align: right; display: flex; gap: 5px; justify-content: flex-end;">
                            ${!isActive ? `<button class="btn btn-primary" style="padding: 2px 8px; font-size: 0.75rem;" onclick="App.switchLedger('${l}')">SWITCH</button>` : ''}
                            <button class="btn" style="padding: 2px 8px; font-size: 0.75rem;" onclick="App.renameLedger('${l}')">RENAME</button>
                            ${!isActive ? `<button class="btn btn-danger" style="padding: 2px 8px; font-size: 0.75rem;" onclick="App.deleteLedger('${l}')">DELETE</button>` : ''}
                        </div>
                    </div>`;
                }).join('');
            }
        } catch (e) {
            console.error(e);
            listDiv.innerHTML = '<div class="empty-state" style="color: var(--color-danger)">GAGAL MEMUAT LEDGER</div>';
        }
    },

    async createLedger() {
        const input = document.getElementById('new-ledger-name');
        const name = input.value.trim();
        if (!name) {
            alert("Nama ledger tidak boleh kosong!");
            return;
        }
        
        try {
            const res = await ApiService.createLedger(name);
            if (res.status === 'success') {
                input.value = '';
                await this.updateGlobalStatus();
                this.loadLedgersList();
            } else {
                alert(res.message);
            }
        } catch (e) {
            console.error(e);
        }
    },
    
    async switchLedger(name) {
        try {
            const res = await ApiService.switchDb(name);
            if (res.status === 'success') {
                await this.updateGlobalStatus();
                this.loadLedgersList();
            } else {
                alert(res.message);
            }
        } catch (e) {
            console.error(e);
        }
    },

    async renameLedger(oldName) {
        const newName = prompt(`Masukkan nama baru untuk ledger ${oldName}:`, oldName);
        if (!newName || newName === oldName) return;
        
        try {
            const res = await ApiService.renameLedger(oldName, newName);
            if (res.status === 'success') {
                await this.updateGlobalStatus();
                this.loadLedgersList();
            } else {
                alert(res.message);
            }
        } catch (e) {
            console.error(e);
        }
    },

    deleteLedger(name) {
        UIHelpers.showCustomModal(`PERINGATAN: Apakah Anda yakin ingin menghapus ledger ${name} secara permanen? Semua data vektor di dalamnya akan hilang.`, async () => {
            try {
                const res = await ApiService.deleteLedger(name);
                if (res.status === 'success') {
                    await this.updateGlobalStatus();
                    this.loadLedgersList();
                } else {
                    alert(res.message);
                }
            } catch (e) {
                console.error(e);
            }
        });
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
