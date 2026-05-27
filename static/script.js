const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const loadingArea = document.getElementById('loading-area');
const resultArea = document.getElementById('result-area');
const jsonViewer = document.getElementById('json-viewer');
const btnPublish = document.getElementById('btn-publish');
const toast = document.getElementById('toast');

// Drag and drop handlers
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
});

dropZone.addEventListener('drop', (e) => {
    let dt = e.dataTransfer;
    let files = dt.files;
    handleFiles(files);
});

dropZone.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', function() {
    handleFiles(this.files);
});

function handleFiles(files) {
    if (files.length === 0) return;
    const file = files[0];
    
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
        showToast('Por favor, envie apenas arquivos PDF.', 'error');
        return;
    }

    uploadFile(file);
}

async function uploadFile(file) {
    dropZone.classList.add('hidden');
    loadingArea.classList.remove('hidden');
    resultArea.classList.add('hidden');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            loadingArea.classList.add('hidden');
            resultArea.classList.remove('hidden');
            jsonViewer.textContent = JSON.stringify(result.data, null, 2);
            showToast('Extração concluída com sucesso!', 'success');
        } else {
            throw new Error(result.error || 'Erro no upload.');
        }
    } catch (error) {
        loadingArea.classList.add('hidden');
        dropZone.classList.remove('hidden');
        showToast(error.message, 'error');
    }
}

btnPublish.addEventListener('click', async () => {
    btnPublish.disabled = true;
    btnPublish.textContent = 'Publicando...';

    try {
        const response = await fetch('/publicar', {
            method: 'POST'
        });

        const result = await response.json();

        if (response.ok) {
            showToast(result.message, 'success');
        } else {
            throw new Error(result.error || 'Erro ao publicar.');
        }
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        btnPublish.disabled = false;
        btnPublish.textContent = 'Publicar no Git';
    }
});

function showToast(message, type = 'success') {
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => {
        toast.classList.remove('show');
    }, 4000);
}
