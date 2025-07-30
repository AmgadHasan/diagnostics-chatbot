document.addEventListener('DOMContentLoaded', () => {
    const chatDisplay = document.getElementById('chat-display');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const fileInput = document.getElementById('file-input');
    const uploadButton = document.getElementById('upload-button');
    const filesList = document.getElementById('files-list');
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'loading-indicator';
    loadingIndicator.textContent = 'Processing...';
    loadingIndicator.style.display = 'none';
    document.body.appendChild(loadingIndicator);

    let isLoading = false;

    const API_BASE_URL = 'http://localhost:8000'; // FastAPI server URL

    // Load initial data
    loadChatHistory();
    loadFilesList();

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    uploadButton.addEventListener('click', uploadFile);
    document.getElementById('clear-button').addEventListener('click', clearChat);

    async function loadChatHistory() {
        try {
            // Show loading state
            chatDisplay.innerHTML = '<div class="loading">Loading messages...</div>';
            
            const response = await fetch(`${API_BASE_URL}/chat/`);
            if (!response.ok) throw new Error('Failed to load chat history');
            
            const messages = await response.json();
            chatDisplay.innerHTML = '';
            
            const emptyChat = document.getElementById('empty-chat');
            if (messages.length === 0) {
                if (emptyChat) emptyChat.style.display = 'block';
                return;
            }
            
            messages.forEach(message => {
                const messageElement = document.createElement('div');
                messageElement.classList.add('message', message.role === 'user' ? 'user' : 'model');
                // Convert markdown to HTML and sanitize
                const sanitized = DOMPurify.sanitize(marked.parse(message.content));
                messageElement.innerHTML = sanitized;
                chatDisplay.appendChild(messageElement);
            });
            
            chatDisplay.scrollTop = chatDisplay.scrollHeight;
        } catch (error) {
            console.error('Error loading chat history:', error);
            chatDisplay.innerHTML = '<div class="error-message">Failed to load chat history</div>';
        }
    }

    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        try {
            // Add user message to chat immediately
            addMessageToChat('user', message);
            messageInput.value = '';

            const response = await fetch(`${API_BASE_URL}/chat/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });

            if (!response.ok) throw new Error('Failed to send message');
            
            const { response: botResponse } = await response.json();
            addMessageToChat('model', botResponse);
        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message');
        }
    }

    function addMessageToChat(role, content) {
        // Hide empty state if visible
        const emptyChat = document.getElementById('empty-chat');
        if (emptyChat) emptyChat.style.display = 'none';
        
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', role);
        // Convert markdown to HTML and sanitize
        const sanitized = DOMPurify.sanitize(marked.parse(content));
        messageElement.innerHTML = sanitized;
        chatDisplay.appendChild(messageElement);
        chatDisplay.scrollTop = chatDisplay.scrollHeight;
    }

    async function uploadFile() {
        const file = fileInput.files[0];
        if (!file) {
            alert('Please select a file first');
            return;
        }

        // Check file type and set MIME type
        let fileType, mimeType;
        if (file.name.endsWith('.pdf')) {
            fileType = 'pdf';  // Backend expects lowercase
            mimeType = 'application/pdf';
        } else if (file.name.endsWith('.docx')) {
            fileType = 'docx';  // Backend expects lowercase
            mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
        } else {
            alert('Only PDF and DOCX files are allowed');
            return;
        }

        try {
            const formData = new FormData();
            // Create new File object with proper MIME type
            const typedFile = new File([file], file.name, { type: mimeType });
            formData.append('file', typedFile);

            const response = await fetch(`${API_BASE_URL}/upload/?type=${fileType}`, {
                method: 'POST',
                headers: {
                    'accept': 'application/json'
                },
                body: formData
            });

            if (!response.ok) throw new Error('Failed to upload file');
            
            const result = await response.json();
            alert(`File uploaded successfully: ${result.filename}`);
            fileInput.value = ''; // Clear file input
            loadFilesList(); // Refresh files list
        } catch (error) {
            console.error('Error uploading file:', error);
            alert('Failed to upload file');
        }
    }

    async function loadFilesList() {
        try {
            filesList.innerHTML = '<li class="loading">Loading files...</li>';
            
            const response = await fetch(`${API_BASE_URL}/files/`);
            if (!response.ok) throw new Error('Failed to load files list');
            
            const { files } = await response.json();
            filesList.innerHTML = '';
            
            const emptyFiles = document.getElementById('empty-files');
            if (files.length === 0) {
                if (emptyFiles) emptyFiles.style.display = 'block';
                return;
            }
            
            files.forEach(file => {
                const listItem = document.createElement('li');
                listItem.textContent = `${file.filename} (${file.content_type}, ${formatFileSize(file.size)})`;
                filesList.appendChild(listItem);
            });
        } catch (error) {
            console.error('Error loading files list:', error);
            filesList.innerHTML = '<li class="error-message">Failed to load files list</li>';
        } finally {
            isLoading = false;
            loadingIndicator.style.display = 'none';
            sendButton.disabled = false;
            uploadButton.disabled = false;
        }
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async function clearChat() {
        try {
            const response = await fetch(`${API_BASE_URL}/chat/`, {
                method: 'DELETE'
            });
            
            if (!response.ok) throw new Error('Failed to clear chat');
            
            // Reload chat after clearing
            loadChatHistory();
        } catch (error) {
            console.error('Error clearing chat:', error);
            alert('Failed to clear chat');
        }
    }
});
