const API = '';
let currentMode = 'engagement'; // 'engagement' or 'reply'

const modeEngagementBtn = document.getElementById('modeEngagement');
const modeReplyBtn = document.getElementById('modeReply');
const inputTitle = document.getElementById('inputTitle');
const inputHint = document.getElementById('inputHint');
const inputLabel = document.getElementById('inputLabel');
const postInput = document.getElementById('postInput');
const generateRepliesBtn = document.getElementById('generateRepliesBtn');
const repliesSection = document.getElementById('repliesSection');
const repliesList = document.getElementById('repliesList');

// ── Mode Switcher ─────────────────────────────────────────
modeEngagementBtn.addEventListener('click', () => {
    currentMode = 'engagement';
    modeEngagementBtn.classList.add('mode-btn-active');
    modeReplyBtn.classList.remove('mode-btn-active');
    inputTitle.innerText = '⚔️ التفاعل الاستباقي مع المؤثرين';
    inputHint.innerText = 'انسخ نص منشور أي مؤثر في مجالك والصقه هنا، وسيكتب لك الذكاء الاصطناعي 3 تعليقات مختلفة تجذب متابعيه.';
    inputLabel.innerText = '📋 نص المنشور (الصق هنا)';
    postInput.placeholder = 'الصق هنا نص منشور المؤثر...';
    repliesSection.classList.add('hidden');
    postInput.value = '';
});

modeReplyBtn.addEventListener('click', () => {
    currentMode = 'reply';
    modeReplyBtn.classList.add('mode-btn-active');
    modeEngagementBtn.classList.remove('mode-btn-active');
    inputTitle.innerText = '💌 الرد على تعليق جمهورك';
    inputHint.innerText = 'انسخ التعليق الذي جاءك على أحد منشوراتك، وسيكتب لك الذكاء الاصطناعي 3 ردود احترافية ودافئة.';
    inputLabel.innerText = '💬 نص التعليق الوارد (الصق هنا)';
    postInput.placeholder = 'الصق هنا نص التعليق الذي تلقيته...';
    repliesSection.classList.add('hidden');
    postInput.value = '';
});

// ── Scrape Comments ───────────────────────────────────────
const scrapeBtn = document.getElementById('scrapeBtn');
const urlInput = document.getElementById('urlInput');

if(scrapeBtn) {
    scrapeBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url || !url.startsWith('http')) {
            alert('يرجى إدخال رابط لينكدإن صحيح!');
            return;
        }

        const btnText = scrapeBtn.querySelector('.btn-text');
        const loader = scrapeBtn.querySelector('.loader');
        btnText.classList.add('hidden');
        loader.classList.remove('hidden');
        scrapeBtn.disabled = true;

        try {
            const res = await fetch(`${API}/api/scrape-comments`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            });
            const data = await res.json();

            if (!res.ok) {
                alert('حدث خطأ أثناء السحب: ' + (data.detail || 'تعذر سحب التعليقات'));
                return;
            }

            if(data.comments && data.comments.length > 0) {
                // Combine comments into the text area
                postInput.value = "التعليقات المسحوبة:\n\n" + data.comments.map((c, i) => `${i+1}. ${c}`).join('\n\n---\n\n');
                postInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else {
                alert('لم يتم العثور على تعليقات في هذا الرابط.');
            }

        } catch (error) {
            alert('حدث خطأ في الاتصال: ' + error.message);
        } finally {
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
            scrapeBtn.disabled = false;
        }
    });
}

// ── Generate Replies ──────────────────────────────────────
generateRepliesBtn.addEventListener('click', async () => {
    const postText = postInput.value.trim();
    if (!postText) {
        alert('يرجى لصق النص أولاً!');
        return;
    }

    const btnText = generateRepliesBtn.querySelector('.btn-text');
    const loader = generateRepliesBtn.querySelector('.loader');
    btnText.classList.add('hidden');
    loader.classList.remove('hidden');
    generateRepliesBtn.disabled = true;
    repliesSection.classList.add('hidden');
    repliesList.innerHTML = '';

    try {
        const res = await fetch(`${API}/api/smart-reply`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ post_text: postText, context: currentMode })
        });
        const data = await res.json();

        if (!res.ok) {
            alert('حدث خطأ: ' + (data.detail || 'تعذر توليد الردود'));
            return;
        }

        const colors = ['var(--primary)', 'var(--accent)', 'var(--warning)'];
        const icons = ['🏆', '💡', '🎯'];

        data.replies.forEach((reply, idx) => {
            const card = document.createElement('div');
            card.className = 'reply-card';
            card.innerHTML = `
                <div class="reply-card-header" style="border-right-color: ${colors[idx]};">
                    <span class="reply-type-icon">${icons[idx]}</span>
                    <span class="reply-type-label" style="color: ${colors[idx]};">${reply.type}</span>
                </div>
                <p class="reply-text">${reply.text}</p>
                <div class="reply-actions">
                    <button class="btn btn-outline copy-btn" id="copy-btn-${idx}" 
                            onclick="copyReply(${idx}, \`${escapeForJs(reply.text)}\`)">
                        📋 نسخ النص
                    </button>
                    <button class="btn btn-primary use-btn"
                            onclick="useReply(${idx}, \`${escapeForJs(reply.text)}\`)">
                        ✍️ استخدم هذا الرد
                    </button>
                </div>
            `;
            repliesList.appendChild(card);
        });

        repliesSection.classList.remove('hidden');
        repliesSection.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        alert('حدث خطأ في الاتصال: ' + error.message);
    } finally {
        btnText.classList.remove('hidden');
        loader.classList.add('hidden');
        generateRepliesBtn.disabled = false;
    }
});

function escapeForJs(str) {
    return str.replace(/`/g, '\\`').replace(/\$/g, '\\$').replace(/\\/g, '\\\\');
}

function copyReply(idx, text) {
    navigator.clipboard.writeText(text).then(() => {
        const btn = document.getElementById(`copy-btn-${idx}`);
        const original = btn.innerText;
        btn.innerText = '✅ تم النسخ!';
        btn.style.color = 'var(--accent)';
        setTimeout(() => { btn.innerText = original; btn.style.color = ''; }, 2000);
    });
}

function useReply(idx, text) {
    // Open LinkedIn in a new tab & copy to clipboard for easy paste
    copyReply(idx, text);
    window.open('https://www.linkedin.com/feed/', '_blank');
}
