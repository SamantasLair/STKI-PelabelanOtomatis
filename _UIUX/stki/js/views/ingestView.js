// _UIUX/stki/js/views/ingestView.js
const IngestView = {
    appendLog(msg, type = 'info') {
        const terminal = document.getElementById('ingest-terminal');
        const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
        
        let color = 'var(--color-ink)';
        if (type === 'error') color = 'var(--color-danger)';
        if (type === 'success') color = 'var(--color-safe)';
        if (type === 'warn') color = 'var(--color-warn)';
        
        terminal.innerHTML += `<div style="color: ${color}; margin-bottom: 2px;">[${timestamp}] ${msg}</div>`;
        terminal.scrollTop = terminal.scrollHeight;
    },

    clearLog() {
        document.getElementById('ingest-terminal').innerHTML = '';
    },

    resetInput() {
        document.getElementById('input-file-ingest').value = '';
    }
};
