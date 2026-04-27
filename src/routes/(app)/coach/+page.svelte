<script lang="ts">
    let messages = $state([
        { role: 'assistant', text: 'Ahlan. I\'ve seen your numbers. They are... interesting' }
    ]);
    let inputMessage = $state('');
    let loading = $state(false);
    let chatContainer;

    async function sendMessage() {
        if (!inputMessage.trim()) return;
        
        const userText = inputMessage;
        messages = [...messages, { role: 'user', text: userText }];
        inputMessage = '';
        loading = true;

        setTimeout(() => chatContainer.scrollTop = chatContainer.scrollHeight, 100);

        try {
            const res = await fetch('/api/coach', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userText })
            });
            const data = await res.json();
            
            messages = [...messages, { role: 'assistant', text: data.reply || "API Error: No response." }];
        } catch (e) {
            messages = [...messages, { role: 'assistant', text: `API Error: ${e.message}` }];
        } finally {
            loading = false;
            setTimeout(() => chatContainer.scrollTop = chatContainer.scrollHeight, 100);
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
    <h1>Coach</h1>
    <p class="subtitle">Your brutally honest AI financial coach.</p>
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
            placeholder="Ask about your client revenue or income..."
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
