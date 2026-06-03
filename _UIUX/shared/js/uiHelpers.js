// _UIUX/shared/js/uiHelpers.js
const UIHelpers = {
    initTabs(onTabChangeCallback = null) {
        const navItems = document.querySelectorAll('.nav-item[data-target]');
        const tabPanes = document.querySelectorAll('.tab-pane');

        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const target = item.getAttribute('data-target');
                
                navItems.forEach(nav => nav.classList.remove('active'));
                tabPanes.forEach(tab => tab.classList.remove('active'));
                
                item.classList.add('active');
                const targetPane = document.getElementById(target);
                if (targetPane) targetPane.classList.add('active');

                if (onTabChangeCallback) onTabChangeCallback(target);
            });
        });
    },

    initDatabaseSelector(onDbSwitchCallback = null) {
        const selector = document.getElementById('select-db');
        if (!selector) return;
        
        selector.addEventListener('change', async (e) => {
            const dbType = e.target.value;
            try {
                await ApiService.switchDb(dbType);
                await this.updateGlobalStatus();
                if (onDbSwitchCallback) onDbSwitchCallback(dbType);
            } catch (err) {
                console.error("Gagal berpindah database:", err);
            }
        });
    },

    async updateGlobalStatus(callback = null) {
        try {
            const status = await ApiService.getStatus();
            const engineLabel = document.getElementById('status-engine');
            if (engineLabel) engineLabel.textContent = `ENGINE: ${status.db_type.toUpperCase()}`;
            
            // Simpan state taxonomy ke window agar bisa diakses oleh komponen lain (seperti tag styling)
            if (status.taxonomy) {
                window._globalTaxonomy = status.taxonomy;
            }
            
            const dbSelector = document.getElementById('select-db');
            if (dbSelector) {
                try {
                    const ledgersRes = await ApiService.getLedgers();
                    if (ledgersRes.status === 'success') {
                        dbSelector.innerHTML = ledgersRes.ledgers.map(l => `<option value="${l}">${l}</option>`).join('');
                        dbSelector.value = status.db_type;
                    }
                } catch (e) {
                    console.error("Failed to load ledgers", e);
                }
            }
            
            if (callback) callback(status);
        } catch (err) {
            const engineLabel = document.getElementById('status-engine');
            if (engineLabel) engineLabel.textContent = `ENGINE: DISCONNECTED`;
            console.error("Gagal getStatus:", err);
        }
    },

    showCustomModal(message, onConfirm) {
        const overlay = document.getElementById('neo-modal-overlay');
        const msgEl = document.getElementById('neo-modal-message');
        const btnCancel = document.getElementById('neo-modal-btn-cancel');
        const btnConfirm = document.getElementById('neo-modal-btn-confirm');

        if (!overlay) {
            console.warn("neo-modal-overlay not found. Falling back to native confirm.");
            if (confirm(message)) onConfirm();
            return;
        }

        msgEl.textContent = message;
        overlay.style.display = 'flex';

        // Cleanup function to remove event listeners
        const closeAndClean = () => {
            overlay.style.display = 'none';
            btnCancel.onclick = null;
            btnConfirm.onclick = null;
        };

        btnCancel.onclick = () => {
            closeAndClean();
        };

        btnConfirm.onclick = () => {
            closeAndClean();
            onConfirm();
        };
    },

    initFloatingTooltip() {
        const tooltipBox = document.getElementById('neo-floating-tooltip');
        if (!tooltipBox) return;

        document.addEventListener('mouseover', (e) => {
            const trigger = e.target.closest('[data-tooltip]');
            if (trigger) {
                tooltipBox.textContent = trigger.getAttribute('data-tooltip');
                tooltipBox.style.display = 'block';
                tooltipBox.style.opacity = '1';
            }
        });

        document.addEventListener('mousemove', (e) => {
            if (tooltipBox.style.display === 'block') {
                // Offset slightly from cursor to not block clicking
                let x = e.clientX + 15;
                let y = e.clientY + 15;
                
                // Keep it within screen bounds
                const boxRect = tooltipBox.getBoundingClientRect();
                if (x + boxRect.width > window.innerWidth) {
                    x = e.clientX - boxRect.width - 10;
                }
                if (y + boxRect.height > window.innerHeight) {
                    y = e.clientY - boxRect.height - 10;
                }

                tooltipBox.style.left = `${x}px`;
                tooltipBox.style.top = `${y}px`;
            }
        });

        document.addEventListener('mouseout', (e) => {
            const trigger = e.target.closest('[data-tooltip]');
            if (trigger) {
                tooltipBox.style.opacity = '0';
                tooltipBox.style.display = 'none';
            }
        });
    },

    currentGuidePage: 1,

    openCalibrationGuide(page) {
        this.currentGuidePage = page;
        this.updateCalibrationGuideUI();
        document.getElementById('calibration-guide-modal').style.display = 'flex';
    },

    navCalibrationGuide(dir) {
        this.currentGuidePage += dir;
        if (this.currentGuidePage < 1) this.currentGuidePage = 1;
        if (this.currentGuidePage > 3) this.currentGuidePage = 3;
        this.updateCalibrationGuideUI();
    },

    updateCalibrationGuideUI() {
        // Hide all pages
        for (let i = 1; i <= 3; i++) {
            const pageEl = document.getElementById(`guide-page-${i}`);
            if (pageEl) pageEl.style.display = 'none';
        }
        
        // Show current
        const currentEl = document.getElementById(`guide-page-${this.currentGuidePage}`);
        if (currentEl) currentEl.style.display = 'block';
        
        // Update indicator
        const indicator = document.getElementById('guide-page-indicator');
        if (indicator) indicator.textContent = `PAGE ${this.currentGuidePage}/3`;
        
        // Update buttons
        const btnPrev = document.getElementById('guide-btn-prev');
        const btnNext = document.getElementById('guide-btn-next');
        const btnClose = document.getElementById('guide-btn-close');
        
        if (btnPrev) btnPrev.style.visibility = this.currentGuidePage === 1 ? 'hidden' : 'visible';
        
        if (btnNext) {
            if (this.currentGuidePage === 3) {
                btnNext.style.display = 'none';
                if (btnClose) btnClose.style.display = 'block';
            } else {
                btnNext.style.display = 'block';
                if (btnClose) btnClose.style.display = 'none';
            }
        }
    },

    currentOutlierPage: 1,

    openOutlierGuide(page) {
        this.currentOutlierPage = page;
        this.updateOutlierGuideUI();
        document.getElementById('outlier-guide-modal').style.display = 'flex';
    },

    navOutlierGuide(dir) {
        this.currentOutlierPage += dir;
        if (this.currentOutlierPage < 1) this.currentOutlierPage = 1;
        if (this.currentOutlierPage > 2) this.currentOutlierPage = 2;
        this.updateOutlierGuideUI();
    },

    updateOutlierGuideUI() {
        for (let i = 1; i <= 2; i++) {
            const pageEl = document.getElementById(`outlier-page-${i}`);
            if (pageEl) pageEl.style.display = 'none';
        }
        
        const currentEl = document.getElementById(`outlier-page-${this.currentOutlierPage}`);
        if (currentEl) currentEl.style.display = 'block';
        
        const indicator = document.getElementById('outlier-page-indicator');
        if (indicator) indicator.textContent = `${this.currentOutlierPage} / 2`;
        
        const btnPrev = document.getElementById('outlier-btn-prev');
        const btnNext = document.getElementById('outlier-btn-next');
        
        if (btnPrev) btnPrev.style.visibility = this.currentOutlierPage === 1 ? 'hidden' : 'visible';
        if (btnNext) btnNext.style.visibility = this.currentOutlierPage === 2 ? 'hidden' : 'visible';
    },

    openOverlapGuide(page) {
        document.getElementById('overlap-guide-modal').style.display = 'flex';
    }
};

// Initialize common UI components
document.addEventListener('DOMContentLoaded', () => {
    UIHelpers.initFloatingTooltip();
});
