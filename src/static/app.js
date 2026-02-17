document.addEventListener('DOMContentLoaded', function() {
    const statusDiv = document.getElementById('status');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const whitelistBox = document.getElementById('whitelistBox');
    const submitWhitelist = document.getElementById('submitWhitelist');
    const errorLogBox = document.getElementById('errorLogBox');
    const clearErrorsBtn = document.getElementById('clearErrorsBtn');

    function showStatus(msg, error) {
        statusDiv.textContent = msg;
        statusDiv.style.color = error ? 'red' : 'green';
    }

    function fetchWhitelist() {
        fetch('/whitelist')
            .then(r => r.json())
            .then(data => {
                whitelistBox.value = JSON.stringify(data, null, 2);
            });
    }

    function fetchStatus() {
        fetch('/status')
            .then(r => r.json())
            .then(data => {
                let msg = data.running ? `Server running. Users: ${data.users}` : 'Server stopped.';
                showStatus(msg, false);
            });
    }

    function fetchErrors() {
        fetch('/errors')
            .then(r => r.json())
            .then(data => {
                // Show newest first, with timestamp
                const formatted = data.slice().reverse().join('\n');
                errorLogBox.value = formatted;
                errorLogBox.scrollTop = 0; // stay at top for newest
            });
    }

    startBtn.onclick = function() {
        fetch('/start', {method: 'POST'})
            .then(r => r.json())
            .then(data => showStatus(data.message, !data.success));
    };

    stopBtn.onclick = function() {
        fetch('/stop', {method: 'POST'})
            .then(r => r.json())
            .then(data => showStatus(data.message, !data.success));
    };

    submitWhitelist.onclick = function() {
        let data;
        try {
            data = JSON.parse(whitelistBox.value);
        } catch (e) {
            showStatus('Invalid JSON in whitelist.', true);
            return;
        }
        fetch('/whitelist', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        })
        .then(r => r.json())
        .then(data => showStatus(data.message, !data.success));
    };

    clearErrorsBtn.onclick = function() {
        fetch('/errors/clear', {method: 'POST'})
            .then(r => r.json())
            .then(data => {
                showStatus(data.message, !data.success);
                fetchErrors();
            });
    };

    fetchWhitelist();
    fetchStatus();
    fetchErrors();
    setInterval(fetchStatus, 5000);
    setInterval(fetchErrors, 3000);
});
