// DOM elements
const dropArea = document.getElementById('drop-area');
const fileInputFiles = document.getElementById('fileElemFiles');
const fileInputFolder = document.getElementById('fileElemFolder');
const fileListSection = document.getElementById('file-list-section');
const fileListBody = document.getElementById('file-list-body');
const uploadBtn = document.getElementById('uploadBtn');
const addMoreBtn = document.getElementById('addMoreBtn');
const startProcessingBtn = document.getElementById('startProcessingBtn');
const batchProgressContainer = document.getElementById('batch-progress-container');
const batchProgressBarInner = document.getElementById('batch-progress-bar-inner');
const batchProgressText = document.getElementById('batch-progress-text');
const continueBtn = document.getElementById('continueBtn');

let selectedFiles = [];

// Prevent default drag behaviors
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
  dropArea.addEventListener(eventName, preventDefaults, false);
  document.body.addEventListener(eventName, preventDefaults, false);
});
function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

// Highlight drop area
['dragenter', 'dragover'].forEach(eventName => {
  dropArea.addEventListener(eventName, () => dropArea.classList.add('highlight'), false);
});
['dragleave', 'drop'].forEach(eventName => {
  dropArea.addEventListener(eventName, () => dropArea.classList.remove('highlight'), false);
});

dropArea.addEventListener('drop', handleDrop, false);
function handleDrop(e) {
  const dt = e.dataTransfer;
  const files = dt.files;
  handleFiles(files);
}

dropArea.addEventListener('click', () => fileInputFiles.click());
dropArea.addEventListener('click', () => fileInputFolder.click());
fileInputFiles.addEventListener('change', (e) => {
  handleFiles(e.target.files);
});
fileInputFolder.addEventListener('change', (e) => {
  handleFiles(e.target.files);
});

function handleFiles(files) {
  // Convert FileList to Array and filter out duplicates
  const newFiles = Array.from(files).filter(f => !selectedFiles.some(sf => sf.name === f.name && sf.size === f.size));
  selectedFiles = selectedFiles.concat(newFiles);
  updateFileList();
}

function updateFileList() {
  fileListBody.innerHTML = '';
  if (selectedFiles.length === 0) {
    fileListSection.style.display = 'none';
    uploadBtn.disabled = true;
    batchProgressContainer.style.display = 'none';
    continueBtn.disabled = true;
    return;
  }
  fileListSection.style.display = 'block';
  uploadBtn.disabled = false;
  batchProgressContainer.style.display = 'block';
  updateBatchProgress();
  selectedFiles.forEach((file, idx) => {
    const row = document.createElement('tr');
    // Thumbnail
    const thumbTd = document.createElement('td');
    const img = document.createElement('img');
    img.alt = file.name;
    img.src = '';
    thumbTd.appendChild(img);
    // Use FileReader for image preview
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = e => { img.src = e.target.result; };
      reader.readAsDataURL(file);
    } else {
      img.src = 'https://via.placeholder.com/48?text=File';
    }
    // Filename
    const nameTd = document.createElement('td');
    nameTd.textContent = file.name;
    // Status
    const statusTd = document.createElement('td');
    statusTd.innerHTML = '<span class="status">Ready</span>';
    // Progress
    const progressTd = document.createElement('td');
    progressTd.innerHTML = '<div class="progress-bar"><div class="progress-bar-inner" style="width:0%"></div></div>';
    // Action
    const actionTd = document.createElement('td');
    const removeBtn = document.createElement('button');
    removeBtn.className = 'action-btn';
    removeBtn.textContent = 'Remove';
    removeBtn.onclick = () => {
      selectedFiles.splice(idx, 1);
      updateFileList();
    };
    actionTd.appendChild(removeBtn);
    // Append all tds
    row.appendChild(thumbTd);
    row.appendChild(nameTd);
    row.appendChild(statusTd);
    row.appendChild(progressTd);
    row.appendChild(actionTd);
    fileListBody.appendChild(row);
  });
}

function updateBatchProgress() {
  const rows = fileListBody.querySelectorAll('tr');
  let uploaded = 0;
  selectedFiles.forEach((file, idx) => {
    const row = rows[idx];
    const statusSpan = row.querySelector('.status');
    if (statusSpan && (statusSpan.textContent === 'Uploaded' || statusSpan.textContent === '100% ✓, PendingAI')) {
      uploaded++;
    }
  });
  batchProgressText.textContent = `${uploaded}/${selectedFiles.length}`;
  const percent = selectedFiles.length ? (uploaded / selectedFiles.length) * 100 : 0;
  batchProgressBarInner.style.width = percent + '%';
  continueBtn.disabled = uploaded !== selectedFiles.length;
}

uploadBtn.addEventListener('click', () => {
  uploadBtn.disabled = true;
  // Simulate upload for each file
  const rows = fileListBody.querySelectorAll('tr');
  let completed = 0;
  selectedFiles.forEach((file, idx) => {
    const row = rows[idx];
    const statusSpan = row.querySelector('.status');
    const progressBar = row.querySelector('.progress-bar-inner');
    statusSpan.textContent = 'Uploading...';
    statusSpan.classList.remove('success', 'error');
    progressBar.style.width = '0%';
    // Simulate upload with setInterval
    let progress = 0;
    const fail = Math.random() < 0.2; // 20% chance to fail
    const interval = setInterval(() => {
      progress += Math.random() * 20 + 10; // Random progress increment
      if (progress >= 100) progress = 100;
      progressBar.style.width = progress + '%';
      if (progress >= 100) {
        clearInterval(interval);
        if (fail) {
          statusSpan.textContent = 'Error';
          statusSpan.classList.add('error');
          progressBar.style.width = '0%';
          // Add retry button
          let retryBtn = row.querySelector('.retry-btn');
          if (!retryBtn) {
            retryBtn = document.createElement('button');
            retryBtn.className = 'retry-btn';
            retryBtn.textContent = 'Retry';
            retryBtn.onclick = () => retryUpload(idx, row);
            row.querySelector('td:last-child').appendChild(retryBtn);
          }
        } else {
          statusSpan.textContent = 'Uploaded';
          statusSpan.classList.add('success');
          progressBar.style.width = '100%';
          // Remove retry button if present
          const retryBtn = row.querySelector('.retry-btn');
          if (retryBtn) retryBtn.remove();
          completed++;
        }
        updateBatchProgress();
        if (completed === selectedFiles.length) {
          addMoreBtn.style.display = '';
          startProcessingBtn.style.display = '';
        }
      }
    }, 300 + Math.random() * 400);
  });
});

function retryUpload(idx, row) {
  const statusSpan = row.querySelector('.status');
  const progressBar = row.querySelector('.progress-bar-inner');
  statusSpan.textContent = 'Uploading...';
  statusSpan.classList.remove('error');
  progressBar.style.width = '0%';
  let progress = 0;
  const interval = setInterval(() => {
    progress += Math.random() * 20 + 10;
    if (progress >= 100) progress = 100;
    progressBar.style.width = progress + '%';
    if (progress >= 100) {
      clearInterval(interval);
      statusSpan.textContent = 'Uploaded';
      statusSpan.classList.add('success');
      progressBar.style.width = '100%';
      // Remove retry button if present
      const retryBtn = row.querySelector('.retry-btn');
      if (retryBtn) retryBtn.remove();
      updateBatchProgress();
    }
  }, 300 + Math.random() * 400);
}

continueBtn.addEventListener('click', () => {
  // Save uploaded file info to sessionStorage and go to next steps page
  const rows = fileListBody.querySelectorAll('tr');
  const uploadedFiles = [];
  selectedFiles.forEach((file, idx) => {
    const row = rows[idx];
    const statusSpan = row.querySelector('.status');
    if (statusSpan && statusSpan.textContent === 'Uploaded') {
      // Save name and thumbnail src
      const img = row.querySelector('img');
      uploadedFiles.push({
        name: file.name,
        src: img ? img.src : '',
        status: 'Ready',
        ai: ''
      });
    }
  });
  sessionStorage.setItem('uploadedFiles', JSON.stringify(uploadedFiles));
  window.location.href = '/admindashboard/image-processing-next/';
});

// Reset UI for Add More
addMoreBtn.addEventListener('click', () => {
  fileInputFiles.value = '';
  fileInputFolder.value = '';
  addMoreBtn.style.display = 'none';
  startProcessingBtn.style.display = 'none';
  uploadBtn.disabled = false;
});

// Placeholder for Start Processing
startProcessingBtn.addEventListener('click', () => {
  window.location.href = '/admindashboard/image-processing-next/';
}); 