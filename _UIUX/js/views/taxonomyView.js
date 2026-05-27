// _UIUX/js/views/taxonomyView.js
const TaxonomyView = {
    renderList(labels) {
        const container = document.getElementById('taxonomy-list');
        
        if (!labels || labels.length === 0) {
            container.innerHTML = `<div class="empty-state">TAKSONOMI KOSONG.</div>`;
            return;
        }

        let html = '<table style="width: 100%; border-collapse: collapse; font-family: var(--font-mono); font-size: 0.85rem;">';
        html += `
            <tr style="border-bottom: 1px solid var(--color-border); background: var(--color-bg);">
                <th style="text-align: left; padding: 4px;">LABEL KELAS</th>
                <th style="text-align: right; padding: 4px;">FREKUENSI (N)</th>
            </tr>
        `;

        labels.forEach(item => {
            html += `
                <tr style="border-bottom: 1px dashed var(--color-border-light);">
                    <td style="padding: 4px;">${item.label}</td>
                    <td style="text-align: right; padding: 4px;">${item.count}</td>
                </tr>
            `;
        });
        
        html += '</table>';
        container.innerHTML = html;
    },

    updateTelemetry(totalDocs, optimal, actual) {
        const span = document.getElementById('taxonomy-telemetry');
        span.textContent = `N: ${totalDocs} | TARGET RICE: ${optimal} | AKTIF: ${actual}`;
    },

    renderProgress(progress) {
        const term = document.getElementById('relabel-progress-terminal');
        term.style.display = 'block';
        
        if (progress.status === 'running') {
            const barLength = 20;
            const filled = Math.floor((progress.percentage / 100) * barLength);
            const empty = barLength - filled;
            const bar = '█'.repeat(filled) + '-'.repeat(empty);
            
            term.innerHTML = `[${bar}] ${progress.percentage}%<br>MEMPROSES ARSIP: ${progress.current} / ${progress.total}<br>STATUS: INFERENSI ONNX BERJALAN...`;
        } else if (progress.status === 'success') {
            const bar = '█'.repeat(20);
            term.innerHTML = `[${bar}] 100%<br>STATUS: BATCH RELABELING SELESAI.`;
        } else if (progress.status === 'failed') {
            term.innerHTML = `STATUS: KEGAGALAN SISTEM TERDETEKSI.`;
        }
    }
};
