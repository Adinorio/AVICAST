console.log("image_processing.js loaded successfully.");

document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.getElementById('drop-area');
    const fileElemFiles = document.getElementById('fileElemFiles');
    const fileElemFolder = document.getElementById('fileElemFolder');
    const selectFilesBtn = document.getElementById('selectFilesBtn');
    const selectFolderBtn = document.getElementById('selectFolderBtn');
    const fileListSection = document.getElementById('file-list-section');
    const fileListBody = document.getElementById('file-list-body');
    const folderListBody = document.getElementById('folder-list-body');
    const uploadBtn = document.getElementById('uploadBtn');
    const addMoreBtn = document.getElementById('addMoreBtn');
    const startProcessingBtn = document.getElementById('startProcessingBtn');
    const continueBtn = document.getElementById('continueBtn');
    const batchProgressContainer = document.getElementById('batch-progress-container');
    const batchProgressBarInner = document.getElementById('batch-progress-bar-inner');
    const batchProgressText = document.getElementById('batch-progress-text');

    let selectedFiles = [];
    let folderFiles = [];

    // --- Event Listeners ---

    // Prevent default drag behaviors on drop area and body
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.classList.add('highlight');
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.classList.remove('highlight');
    });

    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false);

    // Explicitly link visible buttons to hidden file inputs
    selectFilesBtn.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent event from bubbling
        e.preventDefault(); // Prevent default label behavior
        fileElemFiles.click();
    });
    selectFolderBtn.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent event from bubbling
        e.preventDefault(); // Prevent default label behavior
        fileElemFolder.click();
    });

    // Handle file input changes (when user selects or cancels)
    fileElemFiles.addEventListener('change', handleFileSelect);
    fileElemFolder.addEventListener('change', handleFolderSelect);

    // Upload button click handler
    uploadBtn.addEventListener('click', handleUpload);

    // --- Core Functions ---

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight() {
        dropArea.classList.add('highlight');
    }

    function unhighlight() {
        dropArea.classList.remove('highlight');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        // Check if it's likely a folder drop based on dataTransfer items
        // This is a heuristic; direct folder read is complex in browsers.
        const hasFolder = Array.from(dt.items).some(item => item.webkitGetAsEntry && item.webkitGetAsEntry().isDirectory);

        if (hasFolder) {
            handleFolderFiles(files);
        } else {
            handleFiles(files);
        }
    }

    function handleFileSelect(e) {
        const files = e.target.files;
        handleFiles(files);
        e.target.value = ''; // Crucial: Clear the input value to allow re-selection and prevent re-opening on cancel
    }

    function handleFolderSelect(e) {
        const files = e.target.files;
        handleFolderFiles(files);
        e.target.value = ''; // Crucial: Clear the input value to allow re-selection and prevent re-opening on cancel
    }

    function handleFiles(files) {
        const validFiles = Array.from(files).filter(file => {
            const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
            return validTypes.includes(file.type);
        });

        if (validFiles.length > 0) {
            selectedFiles = [...selectedFiles, ...validFiles];
            updateFileList();
            fileListSection.style.display = 'block';
            uploadBtn.disabled = false;
        }
        checkOverallFileStatus();
    }

    function handleFolderFiles(files) {
        const validFiles = Array.from(files).filter(file => {
            const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
            return validTypes.includes(file.type);
        });

        if (validFiles.length > 0) {
            folderFiles = [...folderFiles, ...validFiles];
            updateFolderList();
            fileListSection.style.display = 'block';
            uploadBtn.disabled = false;
        }
        checkOverallFileStatus();
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function createFileRow(file, isFolder = false) {
        const row = document.createElement('tr');
        row.dataset.fileName = file.name; // Store filename for easy lookup
        row.dataset.isFolder = isFolder;

        const thumbnailCell = document.createElement('td');
        const filenameCell = document.createElement('td');
        const typeCell = document.createElement('td');
        const sizeCell = document.createElement('td');
        const statusCell = document.createElement('td');
        const progressCell = document.createElement('td');
        const actionCell = document.createElement('td');

        // Thumbnail
        const thumbnail = document.createElement('img');
        thumbnail.className = 'file-thumbnail';
        thumbnail.src = URL.createObjectURL(file);
        thumbnailCell.appendChild(thumbnail);

        // Filename (include relative path for folder files)
        filenameCell.textContent = isFolder && file.webkitRelativePath ? file.webkitRelativePath : file.name;

        // File type
        typeCell.textContent = file.type.split('/')[1]?.toUpperCase() || 'FILE';

        // File size
        sizeCell.textContent = formatFileSize(file.size);

        // Status
        statusCell.textContent = 'Pending';
        statusCell.className = 'status-pending';

        // Progress
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar';
        const progressInner = document.createElement('div');
        progressInner.className = 'progress-bar-inner';
        progressBar.appendChild(progressInner);
        progressCell.appendChild(progressBar);

        // Action
        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-btn';
        removeBtn.innerHTML = '<i class="fas fa-times"></i>';
        removeBtn.title = 'Remove file';
        removeBtn.onclick = () => removeFile(file, isFolder);
        actionCell.appendChild(removeBtn);

        row.append(thumbnailCell, filenameCell, typeCell, sizeCell, statusCell, progressCell, actionCell);
        return row;
    }

    function updateFileList() {
        fileListBody.innerHTML = '';
        selectedFiles.forEach(file => {
            fileListBody.appendChild(createFileRow(file));
        });
    }

    function updateFolderList() {
        folderListBody.innerHTML = '';
        folderFiles.forEach(file => {
            folderListBody.appendChild(createFileRow(file, true));
        });
    }

    function removeFile(fileToRemove, isFolder) {
        if (isFolder) {
            folderFiles = folderFiles.filter(f => f !== fileToRemove);
            updateFolderList();
        } else {
            selectedFiles = selectedFiles.filter(f => f !== fileToRemove);
            updateFileList();
        }
        URL.revokeObjectURL(fileToRemove.src); // Clean up memory
        checkOverallFileStatus();
    }

    function checkOverallFileStatus() {
        if (selectedFiles.length === 0 && folderFiles.length === 0) {
            fileListSection.style.display = 'none';
            uploadBtn.disabled = true;
            addMoreBtn.style.display = 'none';
            startProcessingBtn.style.display = 'none';
            continueBtn.disabled = true;
            batchProgressContainer.style.display = 'none';
        } else {
            addMoreBtn.style.display = 'inline-block';
        }
    }

    async function handleUpload() {
        const allFiles = [...selectedFiles, ...folderFiles];
        if (allFiles.length === 0) return;

        uploadBtn.disabled = true;
        batchProgressContainer.style.display = 'flex';
        let uploadedCount = 0;

        for (let i = 0; i < allFiles.length; i++) {
            const file = allFiles[i];
            const formData = new FormData();
            formData.append('file', file);

            // Determine if the file is from a folder and get the correct table body
            const isFileFromFolder = folderFiles.includes(file);
            const targetTableBody = isFileFromFolder ? folderListBody : fileListBody;

            // Find the corresponding row to update its status and progress
            const fileRow = targetTableBody.querySelector(`[data-file-name="${file.name}"]`);
            const statusCell = fileRow ? fileRow.querySelector('.status-pending') : null;
            const progressBarInner = fileRow ? fileRow.querySelector('.progress-bar-inner') : null;

            if (statusCell) {
                statusCell.textContent = 'Uploading...';
                statusCell.className = 'status-uploading';
            }
            if (progressBarInner) {
                progressBarInner.style.width = '0%'; // Reset for upload
            }

            try {
                // Simulate upload with progress
                await new Promise(resolve => {
                    let progress = 0;
                    const interval = setInterval(() => {
                        progress += 10;
                        if (progressBarInner) {
                            progressBarInner.style.width = `${progress}%`;
                        }
                        if (progress >= 100) {
                            clearInterval(interval);
                            resolve();
                        }
                    }, 100);
                });

                // Replace with your actual upload endpoint
                // const response = await fetch('/upload/', {
                //     method: 'POST',
                //     body: formData
                // });

                // if (response.ok) {
                    uploadedCount++;
                    updateBatchProgress(uploadedCount, allFiles.length);
                    if (statusCell) {
                        statusCell.textContent = 'Uploaded';
                        statusCell.className = 'status-success';
                    }
                    if (progressBarInner) {
                        progressBarInner.style.width = '100%';
                    }
                // } else {
                //     throw new Error('Upload failed');
                // }
            } catch (error) {
                console.error('Upload failed:', error);
                if (statusCell) {
                    statusCell.textContent = 'Failed';
                    statusCell.className = 'status-error';
                }
                if (progressBarInner) {
                    progressBarInner.style.width = '0%';
                }
            }
        }

        if (uploadedCount === allFiles.length) {
            startProcessingBtn.style.display = 'inline-block';
            continueBtn.disabled = false;
            addMoreBtn.style.display = 'none'; // Hide Add More after full upload
        }
    }

    function updateBatchProgress(current, total) {
        const percentage = (current / total) * 100;
        batchProgressBarInner.style.width = percentage + '%';
        batchProgressText.textContent = `${current}/${total}`;
    }

    // Initial state setup
    checkOverallFileStatus();
}); 