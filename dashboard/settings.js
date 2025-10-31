// Get DOM elements
const changePasswordBtn = document.querySelector('.change-password-btn');
const passwordModal = document.getElementById('passwordModal');
const cancelBtn = document.querySelector('.cancel-btn');
const changePasswordForm = document.getElementById('changePasswordForm');

// Application Settings Elements
const languageSelect = document.getElementById('languageSelect');
const timezoneSelect = document.getElementById('timezoneSelect');
const darkModeToggle = document.getElementById('darkModeToggle');
const compactLayoutToggle = document.getElementById('compactLayoutToggle');
const saveSettingsBtn = document.querySelector('.save-settings-btn');
const cancelSettingsBtn = document.querySelector('.cancel-settings-btn');

// Load saved settings
function loadSavedSettings() {
    const savedSettings = JSON.parse(localStorage.getItem('appSettings') || '{}');
    
    if (savedSettings.language) {
        languageSelect.value = savedSettings.language;
    }
    if (savedSettings.timezone) {
        timezoneSelect.value = savedSettings.timezone;
    }
    if (savedSettings.darkMode !== undefined) {
        darkModeToggle.checked = savedSettings.darkMode;
        document.body.classList.toggle('light-mode', !savedSettings.darkMode);
    }
    if (savedSettings.compactLayout !== undefined) {
        compactLayoutToggle.checked = savedSettings.compactLayout;
        document.body.classList.toggle('compact-layout', savedSettings.compactLayout);
    }
}

// Save settings
function saveSettings() {
    const settings = {
        language: languageSelect.value,
        timezone: timezoneSelect.value,
        darkMode: darkModeToggle.checked,
        compactLayout: compactLayoutToggle.checked
    };
    
    localStorage.setItem('appSettings', JSON.stringify(settings));
    
    // Show success message
    const toast = document.createElement('div');
    toast.className = 'toast success';
    toast.textContent = 'Settings saved successfully!';
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Cancel changes
function cancelSettings() {
    loadSavedSettings();
}

// Event listeners
saveSettingsBtn.addEventListener('click', saveSettings);
cancelSettingsBtn.addEventListener('click', cancelSettings);

// Dark mode toggle
darkModeToggle.addEventListener('change', function() {
    document.body.classList.toggle('light-mode', !this.checked);
});

// Compact layout toggle
compactLayoutToggle.addEventListener('change', function() {
    document.body.classList.toggle('compact-layout', this.checked);
});

// Load settings on page load
document.addEventListener('DOMContentLoaded', () => {
    loadSavedSettings();
    initDataManagement();
});

// Data Management Functions
function initDataManagement() {
    const autoBackupToggle = document.getElementById('autoBackupToggle');
    const dataRetentionSelect = document.getElementById('dataRetentionSelect');
    const exportDataBtn = document.querySelector('.export-data-btn');
    const deleteDataBtn = document.querySelector('.delete-data-btn');

    // Load saved data management settings
    const savedDataSettings = JSON.parse(localStorage.getItem('dataSettings') || '{}');
    
    if (savedDataSettings.autoBackup !== undefined) {
        autoBackupToggle.checked = savedDataSettings.autoBackup;
    }
    if (savedDataSettings.retention) {
        dataRetentionSelect.value = savedDataSettings.retention;
    }

    // Auto-backup toggle handler
    autoBackupToggle.addEventListener('change', () => {
        const settings = JSON.parse(localStorage.getItem('dataSettings') || '{}');
        settings.autoBackup = autoBackupToggle.checked;
        localStorage.setItem('dataSettings', JSON.stringify(settings));
        
        showToast(autoBackupToggle.checked ? 'Auto-backup enabled' : 'Auto-backup disabled');
    });

    // Data retention handler
    dataRetentionSelect.addEventListener('change', () => {
        const settings = JSON.parse(localStorage.getItem('dataSettings') || '{}');
        settings.retention = dataRetentionSelect.value;
        localStorage.setItem('dataSettings', JSON.stringify(settings));
        
        showToast(`Data retention period set to ${dataRetentionSelect.value} months`);
    });

    // Export data handler
    exportDataBtn.addEventListener('click', () => {
        // Simulating data export
        showToast('Preparing data export...');
        setTimeout(() => {
            const dummyData = {
                transactions: [],
                settings: JSON.parse(localStorage.getItem('dataSettings') || '{}'),
                exportDate: new Date().toISOString()
            };
            
            const dataStr = JSON.stringify(dummyData, null, 2);
            const blob = new Blob([dataStr], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'fraud-detection-data.json';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
            
            showToast('Data exported successfully');
        }, 1000);
    });

    // Delete data handler
    deleteDataBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to delete all data? This action cannot be undone.')) {
            // Simulating data deletion
            showToast('Deleting all data...');
            setTimeout(() => {
                localStorage.removeItem('dataSettings');
                autoBackupToggle.checked = false;
                dataRetentionSelect.value = '6';
                showToast('All data has been deleted');
            }, 1000);
        }
    });
}

// Toast notification helper
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Show password modal
changePasswordBtn.addEventListener('click', () => {
    passwordModal.style.display = 'block';
});

// Hide password modal
cancelBtn.addEventListener('click', () => {
    passwordModal.style.display = 'none';
    changePasswordForm.reset();
});

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target === passwordModal) {
        passwordModal.style.display = 'none';
        changePasswordForm.reset();
    }
});

// Handle password change
changePasswordForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (newPassword !== confirmPassword) {
        alert('New passwords do not match!');
        return;
    }

    try {
        const user = firebase.auth().currentUser;
        
        // Reauthenticate user
        const credential = firebase.auth.EmailAuthProvider.credential(
            user.email,
            currentPassword
        );
        
        await user.reauthenticateWithCredential(credential);
        
        // Update password
        await user.updatePassword(newPassword);
        
        alert('Password updated successfully!');
        passwordModal.style.display = 'none';
        changePasswordForm.reset();
    } catch (error) {
        alert(error.message);
    }
});

// Save settings changes
document.querySelectorAll('.toggle input, .dropdown').forEach(input => {
    input.addEventListener('change', async (e) => {
        const settingName = e.target.closest('.settings-item').querySelector('h4').textContent;
        const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
        
        try {
            // Here you would typically save to your backend
            console.log(`Setting "${settingName}" updated to:`, value);
            
            // Show success message
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.textContent = 'Settings saved successfully!';
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.remove();
            }, 3000);
        } catch (error) {
            console.error('Error saving settings:', error);
            alert('Failed to save settings. Please try again.');
        }
    });
});