const API = 'http://127.0.0.1:8000';
let editingPostId = null;
let allPosts = []; // Store posts globally to access them by ID

async function loadPosts() {
    const list = document.getElementById('historyList');
    list.innerHTML = `<div class="empty-state"><div class="empty-icon">⏳</div><h3>جاري التحميل...</h3></div>`;

    try {
        const res = await fetch(`${API}/api/posts`);
        allPosts = await res.json();

        // Stats
        document.getElementById('statTotal').innerText = allPosts.length;
        document.getElementById('statPublished').innerText = allPosts.filter(p => p.status === 'Published').length;
        document.getElementById('statScheduled').innerText = allPosts.filter(p => p.status !== 'Published').length;

        if (!allPosts.length) {
            list.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📭</div>
                    <h3>لا توجد منشورات بعد</h3>
                    <p>اذهب إلى صفحة التوليد وأنشئ أول منشور!</p>
                </div>`;
            return;
        }

        list.innerHTML = '';
        allPosts.forEach(post => list.appendChild(buildCard(post)));

    } catch (e) {
        list.innerHTML = `<div class="empty-state"><div class="empty-icon">❌</div><h3>تعذر الاتصال بالخادم</h3></div>`;
    }
}

function formatDate(str) {
    if (!str) return '';
    const d = new Date(str);
    return d.toLocaleDateString('ar-EG', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function buildCard(post) {
    const card = document.createElement('div');
    card.className = 'history-card';
    card.id = `post-card-${post.id}`;

    const isPublished = post.status === 'Published';
    const platformBadgeClass = post.platform?.toLowerCase() === 'linkedin' ? 'badge-linkedin' : 'badge-twitter';
    const imageUrl = post.image_url ? `${API}${post.image_url}` : null;

    card.innerHTML = `
        ${imageUrl
            ? `<img class="history-thumb" src="${imageUrl}" alt="صورة المنشور" onerror="this.style.display='none'">`
            : `<div class="history-thumb-placeholder">🖼️</div>`
        }

        <div class="history-body">
            <div class="history-meta">
                <span class="history-topic">${escapeHtml(post.topic)}</span>
                <span class="badge ${platformBadgeClass}">${post.platform}</span>
                <span class="badge badge-status ${isPublished ? 'badge-published' : 'badge-scheduled'}">
                    ${isPublished ? '✅ منشور' : '🕐 مجدول'}
                </span>
            </div>
            <div class="history-date">🗓 ${formatDate(post.created_at)}</div>
            <div class="history-content-preview">${escapeHtml(post.content)}</div>
        </div>

        <div class="history-actions">
            ${post.post_url ? `<button class="btn btn-outline" style="border-color: var(--linkedin); color: var(--linkedin);" onclick="navigator.clipboard.writeText('${post.post_url}'); alert('تم نسخ رابط المنشور! 🎉\\nتفضل بلصقه في صفحة التفاعل لسحب تعليقاته.')">🔗 نسخ الرابط</button>` : ''}
            <button class="btn btn-outline" onclick="openEditModal(${post.id})">✏️ تعديل</button>
            <button class="btn btn-danger" onclick="deletePost(${post.id})">🗑️ حذف</button>
        </div>
    `;
    return card;
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

let deletingPostId = null;

function deletePost(id) {
    deletingPostId = id;
    document.getElementById('deleteModal').classList.remove('hidden');
}

document.getElementById('cancelDelete').addEventListener('click', () => {
    deletingPostId = null;
    document.getElementById('deleteModal').classList.add('hidden');
});

document.getElementById('confirmDelete').addEventListener('click', async () => {
    if (!deletingPostId) return;
    const btn = document.getElementById('confirmDelete');
    btn.innerText = 'جاري الحذف...';
    btn.disabled = true;

    try {
        const res = await fetch(`${API}/api/posts/${deletingPostId}`, { method: 'DELETE' });
        if (res.ok) {
            const card = document.getElementById(`post-card-${deletingPostId}`);
            card.style.opacity = '0';
            card.style.transform = 'translateX(30px)';
            card.style.transition = 'all 0.3s ease';
            setTimeout(() => { 
                card.remove(); 
                loadPosts(); 
                document.getElementById('deleteModal').classList.add('hidden');
            }, 300);
        } else {
            alert('فشل الحذف!');
        }
    } catch (e) {
        alert('خطأ في الاتصال بالخادم');
    } finally {
        btn.innerText = '🗑️ نعم، احذف المنشور';
        btn.disabled = false;
        deletingPostId = null;
    }
});

// ── EDIT MODAL ─────────────────────────────────────────
function openEditModal(id) {
    const post = allPosts.find(p => p.id === id);
    if (!post) return;
    
    editingPostId = id;
    document.getElementById('modalContent').value = post.content;
    document.getElementById('editModal').classList.remove('hidden');
}

function closeModal() {
    editingPostId = null;
    document.getElementById('editModal').classList.add('hidden');
}

document.getElementById('modalClose').addEventListener('click', closeModal);
document.getElementById('modalCancel').addEventListener('click', closeModal);
document.getElementById('editModal').addEventListener('click', (e) => {
    if (e.target === document.getElementById('editModal')) closeModal();
});

document.getElementById('modalSave').addEventListener('click', async () => {
    if (!editingPostId) return;
    const newContent = document.getElementById('modalContent').value;
    const btn = document.getElementById('modalSave');
    btn.innerText = 'جاري الحفظ...';
    btn.disabled = true;

    try {
        const res = await fetch(`${API}/api/posts/${editingPostId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: newContent })
        });
        if (res.ok) {
            closeModal();
            loadPosts();
        } else {
            alert('فشل الحفظ!');
        }
    } catch (e) {
        alert('خطأ في الاتصال بالخادم');
    } finally {
        btn.innerText = '💾 حفظ التعديلات';
        btn.disabled = false;
    }
});

// ── INIT ───────────────────────────────────────────────
loadPosts();
