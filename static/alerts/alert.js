function showAlert(message) {
    const alertBox = document.getElementById('customAlert');
    const alertMessage = document.getElementById('alertMessage');
    if (alertBox && alertMessage) {
        alertMessage.textContent = message;
        alertBox.classList.remove('hidden');
    }
}

function closeAlert() {
    const alertBox = document.getElementById('customAlert');
    if (alertBox) {
        alertBox.classList.add('hidden');
    }
}