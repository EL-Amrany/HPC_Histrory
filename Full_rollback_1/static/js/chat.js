document.getElementById('send-btn').addEventListener('click', sendMessage);

function sendMessage() {
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();
    if (!message) return;

    appendToChat("You", message);
    userInput.value = "";

    fetch('/chat/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        appendToChat("Bot", data.answer);
    })
    .catch(err => console.error(err));
}

function appendToChat(sender, text) {
    const chatBox = document.getElementById('chat-box');
    const p = document.createElement('p');
    p.innerHTML = `<strong>${sender}:</strong> ${text}`;
    chatBox.appendChild(p);
    chatBox.scrollTop = chatBox.scrollHeight;
}
