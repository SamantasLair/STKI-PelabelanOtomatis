// _UIUX/stki/js/app.js
const App = {
    async init() {
        UIHelpers.initTabs();
        UIHelpers.initDatabaseSelector();
        
        SearchVM.init();
        RecommendVM.init();
        IngestVM.init();

        await this.updateGlobalStatus();
    },

    async updateGlobalStatus() {
        await UIHelpers.updateGlobalStatus();
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
