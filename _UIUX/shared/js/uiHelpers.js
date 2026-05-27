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
            
            const dbSelector = document.getElementById('select-db');
            if (dbSelector) dbSelector.value = status.db_type;
            
            if (callback) callback(status);
        } catch (err) {
            const engineLabel = document.getElementById('status-engine');
            if (engineLabel) engineLabel.textContent = `ENGINE: OFFLINE`;
            console.error("Gagal memuat status:", err);
        }
    }
};
