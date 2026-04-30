<script lang="ts">
    import { onMount } from 'svelte';

    let sessions = $state([]);
    let currentSessionId = $state(null);
    let messages = $state([]);
    let inputMessage = $state('');
    let loading = $state(false);
    let chatContainer;

    onMount(async () => {
        await fetchSessions();
    });

    async function fetchSessions() {
        const res = await fetch('/api/coach/sessions');
        sessions = await res.json();
        if (sessions.length > 0) {
            if (!currentSessionId || !sessions.find(s => s.id === currentSessionId)) {
                currentSessionId = sessions[0].id;
            }
            await loadMessages(currentSessionId);
        } else {
            await createSession();
        }
    }

    async function createSession() {
        const res = await fetch('/api/coach/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: 'New Chat' })
        });
        const newSession = await res.json();
        sessions = [newSession, ...sessions];
        currentSessionId = newSession.id;
        await loadMessages(currentSessionId);
    }

    async function renameSession() {
        if (currentSessionId === null) return;
        const currentSession = sessions.find(s => s.id === currentSessionId);
        const newTitle = prompt("Enter new chat title:", currentSession.title);
        if (newTitle && newTitle.trim() !== "") {
            await fetch(`/api/coach/sessions/${currentSessionId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: newTitle.trim() })
            });
            await fetchSessions();
        }
    }

    async function deleteSession() {
        if (currentSessionId === null) return;
        if (confirm("Are you sure you want to delete this chat?")) {
            await fetch(`/api/coach/sessions/${currentSessionId}`, {
                method: 'DELETE'
            });
            currentSessionId = null;
            await fetchSessions();
        }
    }

    async function loadMessages(sessionId) {
        if (sessionId === null) return;
        const res = await fetch(`/api/coach/sessions/${sessionId}/messages`);
        const data = await res.json();
        if (data.messages && data.messages.length > 0) {
            messages = data.messages;
        } else {
            messages = [{ role: 'assistant', text: 'Ahlan. I\'ve seen your numbers. They are... interesting' }];
        }
        setTimeout(() => { if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight; }, 100);
    }

    function handleSessionChange(e) {
        currentSessionId = parseInt(e.target.value);
        loadMessages(currentSessionId);
    }

    async function sendMessage() {
        if (!inputMessage.trim() || currentSessionId === null) return;
        
        const userText = inputMessage;
        messages = [...messages, { role: 'user', text: userText }];
        inputMessage = '';
        loading = true;

        setTimeout(() => { if(chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight }, 100);

        try {
            const res = await fetch('/api/coach', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userText, session_id: String(currentSessionId) })
            });
            const data = await res.json();
            
            messages = [...messages, { role: 'assistant', text: data.reply || "API Error: No response." }];
        } catch (e) {
            messages = [...messages, { role: 'assistant', text: `API Error: ${e.message}` }];
        } finally {
            loading = false;
            setTimeout(() => { if(chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight }, 100);
        }
    }

    function handleKeydown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    }
</script>

<svelte:head>
    <title>Cornea Coach | Cornea</title>
</svelte:head>

<div class="page-header">
    <div class="header-content">
        <div>
            <h1>Coach</h1>
            <p class="subtitle">Your honest AI financial coach ...</p>
        </div>
        <div class="session-controls">
            <select class="session-select rounded-md" value={currentSessionId} onchange={handleSessionChange}>
                {#each sessions as session}
                    <option value={session.id}>{session.title}</option>
                {/each}
            </select>
            <button class="session-btn rounded-lg" onclick={createSession}>New</button>
            <button class="session-btn rounded-lg" onclick={renameSession}>Rename</button>
            <button class="session-btn rounded-lg" onclick={deleteSession}>Delete</button>
        </div>
    </div>
</div>

<div class="chat-interface rounded-md" >
    <div class="chat-history" bind:this={chatContainer}>
        {#each messages as msg}
            <div class="message-wrapper {msg.role}">
                <div class="message-bubble" dir="auto">
                    {msg.text}
                </div>
            </div>
        {/each}
        {#if loading}
            <div class="message-wrapper assistant">
                <div class="message-bubble typing">Cornea is typing...</div>
            </div>
        {/if}
    </div>

    <div class="chat-input-area">
        <textarea 
            bind:value={inputMessage} 
            onkeydown={handleKeydown}
            dir="auto"
            placeholder="Ask Cornea about your progress and next steps ..."
            rows="2"
        ></textarea>
        <button class="send-btn" onclick={sendMessage} disabled={loading || !inputMessage.trim()}>
            Send ↗
        </button>
    </div>
</div>

<style>
    .page-header {
        margin-bottom: 2rem;
    }
    .header-content {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
    }
    .session-controls {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    .session-select {
        padding: 0.5rem;
        border: 3px solid #2b1e16;
        background: #fff3e8;
        font-family: inherit;
        font-size: 1rem;
        outline: none;
        box-shadow: 2px 2px 0 #2b1e16;
        min-width: 150px;
    }
    .session-btn {
        padding: 0.5rem 1rem;
        border: 3px solid #2b1e16;
        background: #e2e3e5;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 2px 2px 0 #2b1e16;
        transition: all 0.2s;
    }
    .session-btn:hover {
        background: #ff6e32;
        color: #1f1108;
    }
    h1 {
        font-size: 3rem;
        margin: 0;
        text-transform: lowercase;
    }
    .subtitle {
        color: #7f523c;
        font-size: 1.2rem;
        margin-top: 0.5rem;
    }
    
    .chat-interface {
        display: flex;
        flex-direction: column;
        height: 600px;
        border: 4px solid #2b1e16;
        background: #fff3e8;
        box-shadow: 8px 8px 0 #2b1e16;
    }

    .chat-history {
        flex: 1;
        overflow-y: auto;
        padding: 2rem;
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }

    .message-wrapper {
        display: flex;
        width: 100%;
    }

    .message-wrapper.user {
        justify-content: flex-end;
    }

    .message-bubble {
        max-width: 70%;
        padding: 1rem 1.5rem;
        font-size: 1.1rem;
        line-height: 1.6;
        border: 3px solid #2b1e16;
        box-shadow: 4px 4px 0 #2b1e16;
        white-space: pre-wrap;
    }

    .user .message-bubble {
        background: #ff6e32;
        color: #1f1108;
        border-radius: 20px 20px 0 20px;
    }

    .assistant .message-bubble {
        background: #e2e3e5;
        color: #2b1e16;
        border-radius: 20px 20px 20px 0;
    }

    .typing {
        font-style: italic;
        color: #7f523c;
        background: transparent !important;
        box-shadow: none !important;
        border: none !important;
    }

    .chat-input-area {
        display: flex;
        border-top: 4px solid #2b1e16;
        background: #f0e0d0;
    }

    textarea {
        flex: 1;
        padding: 1.5rem;
        background: transparent;
        border: none;
        resize: none;
        font-family: inherit;
        font-size: 1.1rem;
        outline: none;
        transition: all 0.2s ease;
        line-height: 1.6;
    }

    .send-btn {
        background: #ff6e32;
        border: none;
        border-left: 4px solid #2b1e16;
        padding: 0 2rem;
        font-weight: 900;
        font-size: 1.2rem;
        cursor: pointer;
        transition: background 0.2s;
    }

    .send-btn:hover:not(:disabled) {
        background: #e55a20;
    }

    .send-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
</style>
