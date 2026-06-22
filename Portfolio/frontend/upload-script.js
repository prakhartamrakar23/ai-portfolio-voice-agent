const BACKEND_URL = "http://localhost:8000"; // Change to your Render URL after deployment

const uploadBox = document.getElementById("uploadBox");
const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");
const statusSection = document.getElementById("statusSection");
const statusContent = document.getElementById("statusContent");
const refreshBtn = document.getElementById("refreshBtn");
const rebuildBtn = document.getElementById("rebuildBtn");
const kbStats = document.getElementById("kbStats");
const pdfList = document.getElementById("pdfList");

let selectedFiles = [];

// File selection handling
uploadBox.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", (e) => {
    selectedFiles = Array.from(e.target.files);
    updateUploadButton();
});

// Drag and drop
uploadBox.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadBox.classList.add("drag-over");
});

uploadBox.addEventListener("dragleave", () => {
    uploadBox.classList.remove("drag-over");
});

uploadBox.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadBox.classList.remove("drag-over");
    
    const files = Array.from(e.dataTransfer.files).filter(f => 
        f.name.toLowerCase().endsWith('.pdf')
    );
    
    if (files.length > 0) {
        selectedFiles = files;
        fileInput.files = e.dataTransfer.files;
        updateUploadButton();
    }
});

function updateUploadButton() {
    if (selectedFiles.length > 0) {
        uploadBtn.disabled = false;
        uploadBtn.textContent = `Upload & Process ${selectedFiles.length} PDF${selectedFiles.length > 1 ? 's' : ''}`;
    } else {
        uploadBtn.disabled = true;
        uploadBtn.textContent = "Upload & Process";
    }
}

// Upload PDFs
uploadBtn.addEventListener("click", async () => {
    if (selectedFiles.length === 0) return;
    
    uploadBtn.disabled = true;
    showStatus("Uploading and processing PDFs...");
    
    const chunkSize = document.getElementById("chunkSize").value;
    const overlap = document.getElementById("overlap").value;
    const smartChunking = document.getElementById("smartChunking").checked;
    
    try {
        const formData = new FormData();
        selectedFiles.forEach(file => formData.append("files", file));
        formData.append("chunk_size", chunkSize);
        formData.append("overlap", overlap);
        formData.append("use_smart_chunking", smartChunking);
        
        const response = await fetch(`${BACKEND_URL}/upload-multiple-pdfs`, {
            method: "POST",
            body: formData
        });
        
        const result = await response.json();
        
        if (result.successful > 0) {
            showStatus(
                `✅ Successfully processed ${result.successful}/${result.total_files} PDFs\n\n` +
                result.details.map(d => 
                    `${d.filename}: ${d.status === 'success' ? 
                        `✓ ${d.chunks_created} chunks created` : 
                        `✗ ${d.message}`}`
                ).join('\n'),
                "success"
            );
            
            // Reset
            selectedFiles = [];
            fileInput.value = "";
            updateUploadButton();
            
            // Refresh list
            await loadKnowledgeBase();
        } else {
            showStatus(`❌ All uploads failed. Check the details below.`, "error");
        }
        
    } catch (error) {
        showStatus(`❌ Error: ${error.message}`, "error");
    } finally {
        uploadBtn.disabled = false;
    }
});

function showStatus(message, type = "info") {
    statusSection.style.display = "block";
    statusContent.textContent = message;
    statusContent.className = type === "success" ? "success-message" : 
                              type === "error" ? "error-message" : "";
}

// Load knowledge base stats and PDF list
async function loadKnowledgeBase() {
    try {
        // Get stats
        const statsResponse = await fetch(`${BACKEND_URL}/kb-stats`);
        const stats = await statsResponse.json();
        
        kbStats.innerHTML = `
            <strong>📊 Knowledge Base Statistics</strong><br>
            Total Chunks: ${stats.total_chunks}<br>
            Total Documents: ${stats.total_documents}<br>
            Status: ${stats.status}
        `;
        
        // Get PDF list
        const listResponse = await fetch(`${BACKEND_URL}/list-pdfs`);
        const pdfData = await listResponse.json();
        
        if (pdfData.pdfs.length === 0) {
            pdfList.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #999;">
                    No PDFs uploaded yet. Upload your resume, portfolio, or project docs above!
                </div>
            `;
        } else {
            pdfList.innerHTML = pdfData.pdfs.map(pdf => `
                <div class="pdf-item">
                    <div class="pdf-info">
                        <div class="pdf-name">📄 ${pdf.filename}</div>
                        <div class="pdf-meta">
                            ${pdf.chunk_count} chunks • Last updated: ${new Date(pdf.last_updated).toLocaleString()}
                        </div>
                    </div>
                    <div class="pdf-actions">
                        <button class="btn-delete" onclick="deletePDF('${pdf.filename}')">
                            🗑️ Delete
                        </button>
                    </div>
                </div>
            `).join('');
        }
        
    } catch (error) {
        kbStats.innerHTML = `<span style="color: #c00;">Error loading stats: ${error.message}</span>`;
        pdfList.innerHTML = `<div style="color: #c00;">Error loading PDF list</div>`;
    }
}

// Delete PDF
async function deletePDF(filename) {
    if (!confirm(`Are you sure you want to delete "${filename}" from the knowledge base?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${BACKEND_URL}/delete-pdf/${encodeURIComponent(filename)}`, {
            method: "DELETE"
        });
        
        const result = await response.json();
        
        if (result.status === "success") {
            showStatus(`✅ Deleted ${filename}`, "success");
            await loadKnowledgeBase();
        } else {
            showStatus(`❌ ${result.message}`, "error");
        }
    } catch (error) {
        showStatus(`❌ Error deleting PDF: ${error.message}`, "error");
    }
}

// Rebuild entire knowledge base
rebuildBtn.addEventListener("click", async () => {
    if (!confirm(
        "⚠️ WARNING: This will DELETE the entire knowledge base and rebuild from all PDFs.\n\n" +
        "This action cannot be undone. Continue?"
    )) {
        return;
    }
    
    rebuildBtn.disabled = true;
    rebuildBtn.textContent = "Rebuilding...";
    showStatus("🔄 Rebuilding knowledge base from all PDFs. This may take a few minutes...");
    
    try {
        const response = await fetch(`${BACKEND_URL}/rebuild-kb`, {
            method: "POST"
        });
        
        const result = await response.json();
        
        if (result.status === "success") {
            showStatus(
                `✅ Knowledge base rebuilt!\n\n` +
                `Processed: ${result.successful}/${result.total_pdfs} PDFs\n` +
                result.details.map(d => 
                    `${d.filename}: ${d.status === 'success' ? 
                        `${d.chunks_created} chunks` : 
                        d.message}`
                ).join('\n'),
                "success"
            );
            await loadKnowledgeBase();
        } else {
            showStatus(`❌ Rebuild failed: ${result.message}`, "error");
        }
    } catch (error) {
        showStatus(`❌ Error: ${error.message}`, "error");
    } finally {
        rebuildBtn.disabled = false;
        rebuildBtn.textContent = "Rebuild Entire Knowledge Base";
    }
});

// Refresh button
refreshBtn.addEventListener("click", loadKnowledgeBase);

// Load on page load
window.addEventListener("load", loadKnowledgeBase);
