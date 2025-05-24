function showAlert(message, onClose) {
    let alertBox = document.getElementById('customAlert');
    if (!alertBox) {
        alertBox = document.createElement('div');
        alertBox.id = 'customAlert';
        alertBox.classList.add('hidden');

        const alertContent = document.createElement('div');
        alertContent.classList.add('bg-white');

        const alertMessage = document.createElement('p');
        alertMessage.id = 'alertMessage';
        alertMessage.classList.add('text-palette6', 'text-xl');

        const closeButton = document.createElement('button');
        closeButton.textContent = 'Tutup';
        closeButton.classList.add('bg-palette3', 'hover:bg-palette4', 'text-white', 'px-4', 'py-2', 'rounded-2xl');
        closeButton.onclick = () => {
            closeAlert(alertBox);
            if (typeof onClose === 'function') {
                onClose();
            }
        };

        alertContent.appendChild(alertMessage);
        alertContent.appendChild(closeButton);
        alertBox.appendChild(alertContent);
        document.body.appendChild(alertBox);
    }

    let alertOverlay = document.getElementById('alert-overlay');
    if (!alertOverlay) {
        alertOverlay = document.createElement('div');
        alertOverlay.id = 'alert-overlay';
        document.body.appendChild(alertOverlay);
    }

    const alertMessage = document.getElementById('alertMessage');
    alertMessage.textContent = message;
    alertBox.classList.add('show');
    alertOverlay.classList.add('show');
    document.body.classList.add('no-scroll');
}

function closeAlert(alertBox) {
    alertBox.classList.remove('show');
    let alertOverlay = document.getElementById('alert-overlay');
    if (alertOverlay) {
        alertOverlay.classList.remove('show');
    }
    document.body.classList.remove('no-scroll');
}