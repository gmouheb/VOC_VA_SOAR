// Main JavaScript file for the Vulnerability Management System

// Function to handle dismissing alerts
document.addEventListener('DOMContentLoaded', function() {
    // Get all elements with class 'alert'
    const alerts = document.querySelectorAll('.alert');
    
    // Add click event listener to each alert
    alerts.forEach(function(alert) {
        // Create a close button
        const closeButton = document.createElement('button');
        closeButton.className = 'close';
        closeButton.innerHTML = '&times;';
        closeButton.style.float = 'right';
        closeButton.style.cursor = 'pointer';
        closeButton.style.border = 'none';
        closeButton.style.background = 'none';
        closeButton.style.fontSize = '1.25rem';
        closeButton.style.fontWeight = 'bold';
        closeButton.style.lineHeight = '1';
        
        // Add click event to close button
        closeButton.addEventListener('click', function() {
            alert.style.display = 'none';
        });
        
        // Add close button to alert
        alert.insertBefore(closeButton, alert.firstChild);
    });
});

// Function to confirm deletion
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}

// Function to toggle password visibility
function togglePasswordVisibility(inputId) {
    const passwordInput = document.getElementById(inputId);
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
    } else {
        passwordInput.type = 'password';
    }
}

// Function to validate file upload
function validateFileUpload(formId, maxSizeMB) {
    const form = document.getElementById(formId);
    const fileInput = form.querySelector('input[type="file"]');
    const maxSize = maxSizeMB * 1024 * 1024; // Convert MB to bytes
    
    if (fileInput.files.length > 0) {
        const fileSize = fileInput.files[0].size;
        if (fileSize > maxSize) {
            alert(`File size exceeds the ${maxSizeMB}MB limit.`);
            return false;
        }
    }
    
    return true;
}

// Add event listener to file inputs to show selected filename
document.addEventListener('DOMContentLoaded', function() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const fileName = this.files[0]?.name || 'No file selected';
            const fileNameDisplay = document.createElement('span');
            fileNameDisplay.className = 'selected-file';
            fileNameDisplay.textContent = fileName;
            
            // Remove any existing filename display
            const existingDisplay = this.parentNode.querySelector('.selected-file');
            if (existingDisplay) {
                existingDisplay.remove();
            }
            
            // Add new filename display
            this.parentNode.appendChild(fileNameDisplay);
        });
    });
});