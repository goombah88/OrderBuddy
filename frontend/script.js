// frontend/script.js

const recordButton = document.getElementById('recordButton');
const statusDisplay = document.getElementById('status');
const transcribedTextDisplay = document.getElementById('transcribedText');
const menuDisplay = document.getElementById('menu-display');
const orderDisplay = document.getElementById('order-display');
const orderTotalDisplay = document.getElementById('order-total');
const clearOrderButton = document.getElementById('clearOrderButton');
const finalizeOrderButton = document.getElementById('finalizeOrderButton');

let mediaRecorder;
let audioChunks = [];
let isRecording = false;

// --- Configuration ---
// IMPORTANT: Replace with your server's IP (e.g., 192.168.1.100) and port (8000)
// If running on the same machine and accessing via localhost, use 'http://localhost:8000'
const BACKEND_URL = 'http://YOUR_SERVER_IP:8000'; // <<< ADJUST THIS

// --- UI Update Functions ---
async function updateMenuDisplay() {
    try {
        const response = await fetch(`${BACKEND_URL}/menu`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const menu = await response.json();

        menuDisplay.innerHTML = ''; // Clear previous menu
        menu.categories.forEach(category => {
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'mb-4';
            categoryDiv.innerHTML = `<h3 class="text-xl font-semibold text-blue-700">${category.name}</h3>`;
            const itemList = document.createElement('ul');
            itemList.className = 'list-disc list-inside ml-4';
            category.items.forEach(item => {
                const itemLi = document.createElement('li');
                itemLi.className = 'text-gray-700';
                let itemText = `${item.name} ($${item.price.toFixed(2)})`;
                if (item.description) itemText += `: ${item.description}`;
                if (Object.keys(item.options).length > 0) {
                    itemText += ` (Options: ${Object.keys(item.options).map(opt => `${opt}: ${item.options[opt].join(', ')}`).join('; ')})`;
                }
                if (item.available_sides && item.available_sides.length > 0) {
                    itemText += ` [Sides: ${item.available_sides.join(', ')}]`;
                }
                itemLi.textContent = itemText;
                itemList.appendChild(itemLi);
            });
            categoryDiv.appendChild(itemList);
            menuDisplay.appendChild(categoryDiv);
        });
    } catch (error) {
        console.error('Error fetching menu:', error);
        menuDisplay.innerHTML = '<p class="text-red-500">Failed to load menu. Please check server connection.</p>';
    }
}

function updateOrderDisplay(orderSummary) {
    if (!orderSummary || orderSummary.items.length === 0) {
        orderDisplay.innerHTML = '<p>No items in order.</p>';
        orderTotalDisplay.textContent = '0.00';
        return;
    }

    orderDisplay.innerHTML = '';
    orderSummary.items.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'flex justify-between items-center bg-gray-100 p-2 rounded-md';
        let itemDetails = `${item.quantity}x ${item.name}`;
        if (Object.keys(item.options).length > 0) {
            itemDetails += ` (${Object.keys(item.options).map(opt => `${opt}: ${item.options[opt]}`).join(', ')})`;
        }
        if (item.sides && item.sides.length > 0) {
            itemDetails += ` [${item.sides.join(', ')}]`;
        }
        itemDiv.innerHTML = `
            <span>${itemDetails}</span>
            <span>$${(item.price * item.quantity).toFixed(2)}</span>
        `;
        orderDisplay.appendChild(itemDiv);
    });
    orderTotalDisplay.textContent = orderSummary.total.toFixed(2);
}

// --- Voice Recording Logic ---
recordButton.onclick = async () => {
    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' }); // Use webm for broader browser support
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                statusDisplay.textContent = 'Sending to server...';
                transcribedTextDisplay.textContent = 'Transcribed: ...';
                recordButton.textContent = 'Start Recording';
                recordButton.classList.remove('bg-red-600', 'hover:bg-red-700');
                recordButton.classList.add('bg-blue-600', 'hover:bg-blue-700');
                isRecording = false;

                try {
                    const formData = new FormData();
                    formData.append('audio_file', audioBlob, 'audio.webm');

                    const response = await fetch(`${BACKEND_URL}/process_voice_command`, {
                        method: 'POST',
                        body: formData,
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(`Server error: ${response.status} - ${errorData.message || response.statusText}`);
                    }

                    const result = await response.json();
                    statusDisplay.textContent = result.message || 'Command processed.';
                    transcribedTextDisplay.textContent = `Transcribed: "${result.transcribed_text || 'N/A'}"`;
                    updateOrderDisplay(result.order);

                } catch (error) {
                    console.error('Error processing voice command:', error);
                    statusDisplay.textContent = `Error: ${error.message}`;
                    transcribedTextDisplay.textContent = 'Transcribed: (Error)';
                }
            };

            mediaRecorder.start();
            statusDisplay.textContent = 'Recording... Speak now!';
            recordButton.textContent = 'Stop Recording';
            recordButton.classList.remove('bg-blue-600', 'hover:bg-blue-700');
            recordButton.classList.add('bg-red-600', 'hover:bg-red-700');
            isRecording = true;

        } catch (err) {
            console.error('Error accessing microphone:', err);
            statusDisplay.textContent = 'Error: Microphone access denied or not available.';
        }
    } else {
        mediaRecorder.stop();
    }
};

// --- Button Actions ---
// These buttons directly send an intent override to the backend, bypassing ASR/NLU for simplicity
clearOrderButton.onclick = async () => {
    statusDisplay.textContent = 'Clearing order...';
    try {
        const response = await fetch(`${BACKEND_URL}/process_voice_command`, {
            method: 'POST',
            body: new FormData(), // Empty body as no audio is sent
            headers: { 'X-Intent-Override': 'clear_order' }
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Server error: ${response.status} - ${errorData.message || response.statusText}`);
        }
        const result = await response.json();
        statusDisplay.textContent = result.message;
        updateOrderDisplay(result.order);
    } catch (error) {
        console.error('Error clearing order:', error);
        statusDisplay.textContent = `Error: ${error.message}`;
    }
};

finalizeOrderButton.onclick = async () => {
    statusDisplay.textContent = 'Finalizing order...';
    try {
        const response = await fetch(`${BACKEND_URL}/process_voice_command`, {
            method: 'POST',
            body: new FormData(), // Empty body
            headers: { 'X-Intent-Override': 'finalize_order' }
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Server error: ${response.status} - ${errorData.message || response.statusText}`);
        }
        const result = await response.json();
        statusDisplay.textContent = result.message;
        updateOrderDisplay(result.order); // Order should be cleared after finalization
    } catch (error) {
        console.error('Error finalizing order:', error);
        statusDisplay.textContent = `Error: ${error.message}`;
    }
};


// --- Initial Load ---
document.addEventListener('DOMContentLoaded', () => {
    updateMenuDisplay();
    updateOrderDisplay({ items: [], total: 0 }); // Initialize empty order display
});
