document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generateBtn');
    const publishBtn = document.getElementById('publishBtn');
    const topicInput = document.getElementById('topic');
    const resultSection = document.getElementById('resultSection');
    
    let currentPostId = null;

    // ── Progress Bar ────────────────────────────────────
    const stages = [
        { pct: 10, text: '🧠 جاري تحليل الموضوع...' },
        { pct: 30, text: '✍️ جاري كتابة المنشور...' },
        { pct: 55, text: '🌐 جاري الترجمة الاحترافية...' },
        { pct: 70, text: '🎨 جاري إنشاء وصف الصورة...' },
        { pct: 88, text: '🖼️ جاري تحميل الصورة...' },
        { pct: 95, text: '💾 جاري الحفظ في قاعدة البيانات...' },
    ];

    function setProgress(pct, text) {
        document.getElementById('progressBar').style.width = pct + '%';
        document.getElementById('progressPercent').innerText = pct + '%';
        if (text) document.getElementById('progressText').innerText = text;
    }

    function startProgressSimulation() {
        document.getElementById('progressContainer').classList.remove('hidden');
        setProgress(0, stages[0].text);
        let i = 0;
        const iv = setInterval(() => {
            if (i < stages.length) { setProgress(stages[i].pct, stages[i].text); i++; }
            else clearInterval(iv);
        }, 1800);
        return iv;
    }

    function finishProgress() {
        setProgress(100, '✅ تم الانتهاء!');
        setTimeout(() => {
            document.getElementById('progressContainer').classList.add('hidden');
            setProgress(0, '');
        }, 800);
    }

    const enableSchedule = document.getElementById('enableSchedule');
    const scheduleWrapper = document.getElementById('scheduleWrapper');
    const scheduleTimeInput = document.getElementById('scheduleTime');

    enableSchedule.addEventListener('change', () => {
        scheduleWrapper.classList.toggle('hidden', !enableSchedule.checked);
    });

    const API = ''; // Use relative paths since we serve from the same server

    // ── Trend Finder (Phase 3) ──────────────────────────
    const searchTrendBtn = document.getElementById('searchTrendBtn');
    const trendKeywordInput = document.getElementById('trendKeyword');
    const trendResultBox = document.getElementById('trendResultBox');
    const trendSummary = document.getElementById('trendSummary');
    const trendAngles = document.getElementById('trendAngles');

    searchTrendBtn.addEventListener('click', async () => {
        const keyword = trendKeywordInput.value.trim();
        if (!keyword) { alert('أدخل كلمة مفتاحية أولاً!'); return; }

        searchTrendBtn.disabled = true;
        searchTrendBtn.innerText = 'جاري التحليل...';
        trendResultBox.classList.add('hidden');

        try {
            const res = await fetch(`${API}/api/trends?keyword=${encodeURIComponent(keyword)}`);
            const data = await res.json();
            
            trendSummary.innerText = data.summary;
            trendAngles.innerHTML = '';
            
            data.angles.forEach((angle, idx) => {
                const angleBtn = document.createElement('button');
                angleBtn.className = 'btn btn-outline';
                angleBtn.style.cssText = 'text-align: right; white-space: normal; height: auto; padding: 0.8rem;';
                angleBtn.innerHTML = `<strong>زاوية ${idx + 1}:</strong> ${angle}`;
                angleBtn.onclick = () => {
                    topicInput.value = `${keyword} (الزاوية: ${angle})`;
                    topicInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    topicInput.focus();
                };
                trendAngles.appendChild(angleBtn);
            });
            
            trendResultBox.classList.remove('hidden');
        } catch (error) {
            alert('حدث خطأ أثناء جلب التريند: ' + error.message);
        } finally {
            searchTrendBtn.disabled = false;
            searchTrendBtn.innerText = '🔍 حلل التريند';
        }
    });

    // ── Recommendations (Phase 3) ───────────────────────
    const refreshIdeasBtn = document.getElementById('refreshIdeasBtn');
    const recommendationsList = document.getElementById('recommendationsList');

    async function loadRecommendations() {
        recommendationsList.innerHTML = `
            <div style="background: var(--bg); padding: 1rem; border-radius: var(--radius); border: 1px dashed var(--primary); text-align: center; grid-column: 1 / -1;">
                <span class="loader" style="width: 20px; height: 20px; border-width: 2px; border-top-color: var(--primary);"></span>
                <p style="margin-top: 0.5rem; font-size: 0.9rem;">جاري جلب أحدث التريندات والأفكار بالذكاء الاصطناعي...</p>
            </div>
        `;
        refreshIdeasBtn.disabled = true;

        try {
            const res = await fetch(`${API}/api/recommendations`);
            const data = await res.json();
            
            recommendationsList.innerHTML = '';
            data.recommendations.forEach(rec => {
                const card = document.createElement('div');
                card.style.cssText = `
                    background: var(--bg);
                    padding: 1rem;
                    border-radius: var(--radius);
                    border: 1px solid var(--border);
                    cursor: pointer;
                    transition: all 0.2s;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                `;
                card.onmouseover = () => { card.style.borderColor = 'var(--primary)'; card.style.transform = 'translateY(-2px)'; };
                card.onmouseout = () => { card.style.borderColor = 'var(--border)'; card.style.transform = 'translateY(0)'; };
                card.onclick = () => {
                    topicInput.value = `${rec.title} (الزاوية: ${rec.angle})`;
                    topicInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    topicInput.focus();
                };

                card.innerHTML = `
                    <div>
                        <h3 style="font-size: 1rem; margin-bottom: 0.5rem; color: var(--primary);">${rec.title}</h3>
                        <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">🎯 الزاوية: ${rec.angle}</p>
                    </div>
                    <button class="btn btn-outline" style="width: 100%; padding: 0.4rem; font-size: 0.8rem;">استخدم هذه الفكرة ✍️</button>
                `;
                recommendationsList.appendChild(card);
            });
        } catch (error) {
            recommendationsList.innerHTML = `<div style="grid-column: 1 / -1; color: var(--danger); text-align: center;">فشل جلب التوصيات: ${error.message}</div>`;
        } finally {
            refreshIdeasBtn.disabled = false;
        }
    }

    refreshIdeasBtn.addEventListener('click', loadRecommendations);
    
    // Set initial placeholder message
    recommendationsList.innerHTML = `
        <div style="background: var(--bg); padding: 1rem; border-radius: var(--radius); border: 1px dashed var(--border); text-align: center; grid-column: 1 / -1; color: var(--text-muted);">
            <p style="font-size: 0.95rem;">💡 اضغط على زر "تحديث الأفكار" لجلب أحدث 3 تريندات مخصصة لك (يستهلك من رصيد الذكاء الاصطناعي).</p>
        </div>
    `;

    // ── Generate ────────────────────────────────────────
    generateBtn.addEventListener('click', async () => {
        const topic = document.getElementById('topic').value;
        const platform = 'LinkedIn';
        let scheduled_at = null;

        if (enableSchedule.checked) {
            if (!scheduleTimeInput.value) { alert('رجاءً اختر موعد الجدولة!'); return; }
            scheduled_at = scheduleTimeInput.value.replace('T', ' ');
        }

        if (!topic.trim()) { alert('رجاءً أدخل موضوعاً أولاً!'); return; }

        const btnText = generateBtn.querySelector('.btn-text');
        const loader = generateBtn.querySelector('.loader');
        btnText.classList.add('hidden');
        loader.classList.remove('hidden');
        topicInput.disabled = true;
        generateBtn.disabled = true;
        resultSection.classList.add('hidden');

        const progressInterval = startProgressSimulation();

        try {
            const res = await fetch(`${API}/api/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic, platform, scheduled_at })
            });
            const data = await res.json();
            clearInterval(progressInterval);
            finishProgress();

            if (res.ok) {
                const badge = document.getElementById('platformBadge');
                badge.innerText = platform;
                badge.className = 'badge ' + (platform === 'LinkedIn' ? 'badge-linkedin' : 'badge-twitter');

                document.getElementById('generatedContent').value = data.content;
                
                const imgContainer = document.querySelector('.image-container');
                if (data.image_url) {
                    document.getElementById('generatedImage').src = data.image_url;
                    imgContainer.style.display = 'flex';
                } else {
                    imgContainer.style.display = 'none';
                }
                
                currentPostId = data.post_id;
                
                const statusMsg = document.getElementById('publishStatus');
                publishBtn.classList.remove('hidden'); // Always show the publish button
                
                if (data.status === 'Scheduled') {
                    statusMsg.innerHTML = `📅 تم جدولة المنشور لينشر تلقائياً في: <b>${scheduled_at}</b>`;
                } else {
                    statusMsg.innerText = '';
                }
                
                resultSection.classList.remove('hidden');
                resultSection.scrollIntoView({ behavior: 'smooth' });
            } else {
                let errorMsg = data.detail;
                if (Array.isArray(data.detail)) {
                    errorMsg = data.detail.map(d => `${d.loc.join('.')}: ${d.msg}`).join('\n');
                }
                alert('حدث خطأ: ' + (errorMsg || 'تعذر الاتصال بالخادم'));
            }
        } catch (error) {
            clearInterval(progressInterval);
            document.getElementById('progressContainer').classList.add('hidden');
            alert('حدث خطأ في الاتصال بالخادم: ' + error.message);
        } finally {
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
            generateBtn.disabled = false;
            topicInput.disabled = false; // Re-enable the topic input
        }
    });

    // ── Publish ─────────────────────────────────────────
    publishBtn.addEventListener('click', async () => {
        if (!currentPostId) return;
        const originalText = publishBtn.innerText;
        publishBtn.innerText = '⏳ جاري النشر...';
        publishBtn.disabled = true;

        try {
            const editedContent = document.getElementById('generatedContent').value;
            const res = await fetch(`${API}/api/publish/${currentPostId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: editedContent })
            });
            const data = await res.json();
            const statusMsg = document.getElementById('publishStatus');
            if (res.ok) {
                statusMsg.innerText = data.message;
                statusMsg.style.color = 'var(--accent)';
            } else {
                alert('خطأ: ' + (data.detail || 'فشل النشر'));
            }
        } catch (error) {
            alert('حدث خطأ في الاتصال بالخادم.');
        } finally {
            publishBtn.innerText = originalText;
            publishBtn.disabled = false;
        }
    });
});
