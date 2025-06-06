// Simulate loading uploaded files from sessionStorage (or use a placeholder array for now)
let uploadedFiles = JSON.parse(sessionStorage.getItem('uploadedFiles')) || [
  // Example placeholder data
  { name: 'bird1.jpg', src: 'https://via.placeholder.com/48', status: 'Ready', ai: '' },
  { name: 'bird2.png', src: 'https://via.placeholder.com/48', status: 'Ready', ai: '' },
  { name: 'bird3.jpg', src: 'https://via.placeholder.com/48', status: 'Ready', ai: '' },
];

const summaryDiv = document.getElementById('summary');
const fileListBody = document.getElementById('file-list-body');
const uploadMoreBtn = document.getElementById('uploadMoreBtn');
const startProcessingBtn = document.getElementById('startProcessingBtn');
const batchProgressContainer = document.getElementById('batch-progress-container');
const batchProgressBarInner = document.getElementById('batch-progress-bar-inner');
const batchProgressText = document.getElementById('batch-progress-text');
const reviewDashboardBtn = document.getElementById('reviewDashboardBtn');
const modal = document.getElementById('modal');
const modalImage = document.getElementById('modalImage');
const modalClose = document.getElementById('modalClose');
const filterBar = document.getElementById('filter-bar');
const retryAllBtn = document.getElementById('retryAllBtn');
const pagination = document.getElementById('pagination');
const aiModal = document.getElementById('aiModal');
const aiModalClose = document.getElementById('aiModalClose');
const aiModalContent = document.getElementById('aiModalContent');
let currentFilter = 'all';
let currentPage = 1;
const pageSize = 10;

function renderSummary() {
  summaryDiv.textContent = `You uploaded ${uploadedFiles.length} image${uploadedFiles.length !== 1 ? 's' : ''}. All are ready for processing.`;
}

function updateBatchProgress() {
  let completed = 0, processing = 0;
  uploadedFiles.forEach(f => {
    if (f.status === 'Completed') completed++;
    else if (f.status === 'Processing') processing++;
  });
  batchProgressText.textContent = `${completed}/${uploadedFiles.length}`;
  const percent = uploadedFiles.length ? (completed / uploadedFiles.length) * 100 : 0;
  batchProgressBarInner.style.width = percent + '%';
  batchProgressContainer.style.display = uploadedFiles.length ? 'flex' : 'none';
}

function renderTable() {
  fileListBody.innerHTML = '';
  // Filtered files
  const filtered = uploadedFiles.filter(file => currentFilter === 'all' || file.status.toLowerCase() === currentFilter);
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  if (currentPage > totalPages) currentPage = totalPages;
  const startIdx = (currentPage - 1) * pageSize;
  const pageFiles = filtered.slice(startIdx, startIdx + pageSize);
  pageFiles.forEach((file, idx) => {
    const realIdx = uploadedFiles.indexOf(file);
    const row = document.createElement('tr');
    // Thumbnail
    const thumbTd = document.createElement('td');
    const img = document.createElement('img');
    img.alt = file.name;
    img.src = file.src || 'https://via.placeholder.com/48';
    img.style.cursor = 'pointer';
    img.onclick = () => {
      modalImage.src = img.src;
      modal.style.display = 'block';
    };
    thumbTd.appendChild(img);
    // Filename
    const nameTd = document.createElement('td');
    nameTd.textContent = file.name;
    // Status
    const statusTd = document.createElement('td');
    let icon = '';
    if (file.status === 'Processing') icon = '<i class="fas fa-spinner status-icon"></i>';
    else if (file.status === 'Completed') icon = '<i class="fas fa-check-circle status-icon"></i>';
    else if (file.status === 'Error') icon = '<i class="fas fa-times-circle status-icon"></i>';
    statusTd.innerHTML = `<span class="status ${file.status.toLowerCase()}">${icon}${file.status}</span>`;
    // AI Results
    const aiTd = document.createElement('td');
    if (file.status === 'Completed' && file.ai) {
      const aiSpan = document.createElement('span');
      aiSpan.className = 'ai-results clickable';
      aiSpan.textContent = file.ai;
      aiSpan.onclick = () => showAIModal(file);
      aiTd.appendChild(aiSpan);
    } else {
      aiTd.innerHTML = `<span class="ai-results">${file.ai || '-'}</span>`;
    }
    // Action
    const actionTd = document.createElement('td');
    if (file.status === 'Error') {
      const retryBtn = document.createElement('button');
      retryBtn.className = 'retry-btn';
      retryBtn.textContent = 'Retry';
      retryBtn.onclick = () => retryProcessing(realIdx);
      actionTd.appendChild(retryBtn);
    } else {
      actionTd.innerHTML = '-';
    }
    // Append all tds
    row.appendChild(thumbTd);
    row.appendChild(nameTd);
    row.appendChild(statusTd);
    row.appendChild(aiTd);
    row.appendChild(actionTd);
    fileListBody.appendChild(row);
  });
  updateBatchProgress();
  renderPagination(filtered.length, totalPages);
}

function renderPagination(total, totalPages) {
  pagination.innerHTML = '';
  if (totalPages <= 1) return;
  for (let i = 1; i <= totalPages; i++) {
    const btn = document.createElement('button');
    btn.className = 'page-btn' + (i === currentPage ? ' active' : '');
    btn.textContent = i;
    btn.onclick = () => {
      currentPage = i;
      renderTable();
    };
    pagination.appendChild(btn);
  }
}

uploadMoreBtn.addEventListener('click', () => {
  window.location.href = '/admindashboard/image-processing/';
});

let pollingInterval = null;

startProcessingBtn.addEventListener('click', () => {
  // Simulate processing: update status to 'Processing', then poll for completion
  uploadedFiles.forEach((file, idx) => {
    file.status = 'Processing';
    file.ai = '';
  });
  renderTable();
  summaryDiv.textContent = `Processing ${uploadedFiles.length} images...`;
  if (pollingInterval) clearInterval(pollingInterval);
  pollingInterval = setInterval(simulatePolling, 3000);
  simulatePolling();
});

function simulatePolling() {
  let allDone = true;
  uploadedFiles.forEach((file, idx) => {
    if (file.status === 'Processing') {
      // 60% chance to complete each poll
      if (Math.random() < 0.6) {
        file.status = 'Completed';
        file.ai = 'Birds: ' + (Math.floor(Math.random() * 10) + 1) + ', Confidence: ' + (80 + Math.random() * 20).toFixed(1) + '%';
      } else if (Math.random() < 0.1) {
        file.status = 'Error';
        file.ai = 'Processing failed';
      } else {
        allDone = false;
      }
    } else if (file.status === 'Error') {
      allDone = false;
    }
  });
  renderTable();
  if (allDone) {
    summaryDiv.textContent = `All ${uploadedFiles.length} images have been processed.`;
    clearInterval(pollingInterval);
  }
}

reviewDashboardBtn.addEventListener('click', () => {
  window.location.href = '/admindashboard/review-dashboard/';
});

modalClose.onclick = function() {
  modal.style.display = 'none';
};
window.onclick = function(e) {
  if (e.target == modal) {
    modal.style.display = 'none';
  }
};

function retryProcessing(idx) {
  uploadedFiles[idx].status = 'Processing';
  uploadedFiles[idx].ai = '';
  renderTable();
  if (!pollingInterval) {
    pollingInterval = setInterval(simulatePolling, 3000);
  }
}

filterBar.addEventListener('click', (e) => {
  if (e.target.classList.contains('filter-btn')) {
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');
    currentFilter = e.target.getAttribute('data-filter');
    renderTable();
  }
});

retryAllBtn.addEventListener('click', () => {
  uploadedFiles.forEach((file, idx) => {
    if (file.status === 'Error') {
      file.status = 'Processing';
      file.ai = '';
    }
  });
  renderTable();
  if (!pollingInterval) {
    pollingInterval = setInterval(simulatePolling, 3000);
  }
});

function showAIModal(file) {
  aiModalContent.innerHTML = `<h2>AI Details for ${file.name}</h2><p>${file.ai}</p><p><em>Bounding boxes and more details coming soon.</em></p>`;
  aiModal.style.display = 'block';
}
aiModalClose.onclick = function() {
  aiModal.style.display = 'none';
};
window.addEventListener('click', function(e) {
  if (e.target == aiModal) {
    aiModal.style.display = 'none';
  }
});

// Initial render
renderSummary();
renderTable(); 