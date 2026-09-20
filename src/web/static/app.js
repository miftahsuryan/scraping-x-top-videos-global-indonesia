"use strict";

// Dashboard interaction behavior for X Video Scraper

(function() {
    'use strict';

    const CATEGORIES = [
        'engagement', 'news', 'economic', 'social',
        'technology', 'research', 'business', 'social_media'
    ];
    const PERIODS = ['1day', '3days', 'weekly', 'monthly'];
    const CATEGORY_LABELS = {
        engagement: 'Engagement',
        news: 'News',
        economic: 'Economic',
        social: 'Social',
        technology: 'Technology',
        research: 'Research',
        business: 'Business',
        social_media: 'Social Media'
    };

    let pollInterval = null;

    function init() {
        renderCheckboxes('periods-group', PERIODS, p => p);
        renderCheckboxes('categories-group', CATEGORIES, c => CATEGORY_LABELS[c] || c);
        populateCategoryFilter();
        setupForm();
        setupFilters();
        setupCloseDetail();
        setupModeToggle();
        loadReports();
        pollStatus();
    }

    function renderCheckboxes(containerId, values, labelFn) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const selectAll = document.createElement('label');
        const selectAllCb = document.createElement('input');
        selectAllCb.type = 'checkbox';
        selectAllCb.checked = true;
        selectAllCb.classList.add('select-all');
        selectAllCb.addEventListener('change', function() {
            const cbs = container.querySelectorAll('input[type="checkbox"]:not(.select-all)');
            cbs.forEach(cb => cb.checked = this.checked);
        });
        selectAll.appendChild(selectAllCb);
        selectAll.appendChild(document.createTextNode(' All'));
        container.appendChild(selectAll);

        values.forEach(val => {
            const label = document.createElement('label');
            const cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.value = val;
            cb.checked = true;
            label.appendChild(cb);
            label.appendChild(document.createTextNode(' ' + labelFn(val)));
            container.appendChild(label);
        });
    }

    function populateCategoryFilter() {
        const select = document.getElementById('filter-category');
        if (!select) return;
        CATEGORIES.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c;
            opt.textContent = CATEGORY_LABELS[c] || c;
            select.appendChild(opt);
        });
    }

    function getSelectedValues(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return [];
        const cbs = container.querySelectorAll('input[type="checkbox"]:not(.select-all):checked');
        return Array.from(cbs).map(cb => cb.value);
    }

    function setupModeToggle() {
        const modeRadios = document.querySelectorAll('input[name="mode"]');
        const categoriesSection = document.getElementById('categories-section');
        const keywordsSection = document.getElementById('keywords-section');
        const periodsSection = document.getElementById('periods-section');
        
        function toggleSections() {
            const selectedMode = document.querySelector('input[name="mode"]:checked')?.value;
            if (selectedMode === 'explore') {
                categoriesSection.style.display = 'none';
                keywordsSection.style.display = 'none';
                periodsSection.style.display = 'none';
            } else {
                categoriesSection.style.display = 'block';
                keywordsSection.style.display = 'flex';
                periodsSection.style.display = 'block';
            }
        }
        
        modeRadios.forEach(radio => {
            radio.addEventListener('change', toggleSections);
        });
        
        // Initialize on load
        toggleSections();
    }

    function setupForm() {
        const form = document.getElementById('run-form');
        if (!form) return;

        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            const errorEl = document.getElementById('form-error');
            const startBtn = document.getElementById('start-btn');
            errorEl.classList.add('hidden');

            const mode = document.querySelector('input[name="mode"]:checked')?.value || 'explore';
            const periods = mode === 'explore' ? ['explore'] : getSelectedValues('periods-group');
            const categories = mode === 'search' ? getSelectedValues('categories-group') : ['explore'];
            const keywordsId = mode === 'search' ? (document.getElementById('keywords-id').value.trim() || null) : null;
            const keywordsGl = mode === 'search' ? (document.getElementById('keywords-gl').value.trim() || null) : null;
            const headless = document.getElementById('headless').checked;

            if (mode !== 'explore' && !periods.length) {
                errorEl.textContent = 'Select at least one period.';
                errorEl.classList.remove('hidden');
                return;
            }

            if (mode === 'search' && !categories.length) {
                errorEl.textContent = 'Select at least one category for search mode.';
                errorEl.classList.remove('hidden');
                return;
            }

            startBtn.disabled = true;
            startBtn.textContent = 'Starting...';

            try {
                const res = await fetch('/api/jobs', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        mode,
                        periods,
                        categories,
                        keywords_id: keywordsId,
                        keywords_gl: keywordsGl,
                        headless
                    })
                });

                const data = await res.json();

                if (!res.ok) {
                    const msg = data.detail || 'Request failed.';
                    const fields = (data.fields || []).map(f => f.message).join('; ');
                    errorEl.textContent = fields ? msg + ' ' + fields : msg;
                    errorEl.classList.remove('hidden');
                    return;
                }

                pollStatus();
            } catch (err) {
                errorEl.textContent = 'Network error: ' + err.message;
                errorEl.classList.remove('hidden');
            } finally {
                startBtn.disabled = false;
                startBtn.textContent = 'Start Scraping';
            }
        });
    }

    function setupFilters() {
        ['filter-locale', 'filter-category', 'filter-period'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('change', loadReports);
        });
    }

    function setupCloseDetail() {
        const btn = document.getElementById('close-detail');
        if (btn) {
            btn.addEventListener('click', function() {
                document.getElementById('detail-panel').classList.add('hidden');
            });
        }
    }

    async function pollStatus() {
        if (pollInterval) { clearInterval(pollInterval); pollInterval = null; }

        await fetchStatus();

        pollInterval = setInterval(async () => {
            const snapshot = await fetchStatus();
            if (snapshot && ['completed', 'failed', 'idle'].includes(snapshot.state)) {
                clearInterval(pollInterval);
                pollInterval = null;
                if (snapshot.state === 'completed') loadReports();
            }
        }, 2000);
    }

    async function fetchStatus() {
        try {
            const res = await fetch('/api/jobs/current');
            const snapshot = await res.json();
            renderStatus(snapshot);
            return snapshot;
        } catch (err) {
            console.error('Status fetch error:', err);
            return null;
        }
    }

    function renderStatus(snapshot) {
        const container = document.getElementById('status-content');
        if (!container) return;

        if (snapshot.state === 'idle') {
            container.innerHTML = '<p class="idle-text">No active job.</p>';
            return;
        }

        const stateColors = {
            queued: '#f9ab00',
            running: 'var(--primary)',
            completed: 'var(--success)',
            failed: 'var(--danger)'
        };

        container.innerHTML = `
            <div class="progress-bar ${['queued', 'running'].includes(snapshot.state) ? 'active' : ''}"
                 style="background: ${stateColors[snapshot.state] || 'var(--border)'}"></div>
            <div class="status-grid">
                <span class="status-label">State:</span>
                <span class="status-value" style="color: ${stateColors[snapshot.state]}">${snapshot.state}</span>
                <span class="status-label">Message:</span>
                <span class="status-value">${escapeHtml(snapshot.message)}</span>
                ${snapshot.job_id ? `<span class="status-label">Job ID:</span><span class="status-value">${escapeHtml(snapshot.job_id)}</span>` : ''}
                ${snapshot.total_tweets ? `<span class="status-label">Tweets:</span><span class="status-value">${snapshot.total_tweets}</span>` : ''}
            </div>
        `;
    }

    async function loadReports() {
        const locale = document.getElementById('filter-locale')?.value || '';
        const category = document.getElementById('filter-category')?.value || '';
        const period = document.getElementById('filter-period')?.value || '';

        const params = new URLSearchParams();
        if (locale) params.set('locale', locale);
        if (category) params.set('category', category);
        if (period) params.set('period', period);

        try {
            const res = await fetch('/api/reports?' + params.toString());
            const reports = await res.json();
            renderReports(reports);
        } catch (err) {
            console.error('Reports fetch error:', err);
        }
    }

    function renderReports(reports) {
        const container = document.getElementById('reports-list');
        if (!container) return;

        if (!reports.length) {
            container.innerHTML = '<p class="empty-text">No reports available.</p>';
            return;
        }

        container.innerHTML = reports.map(r => `
            <div class="report-item" data-id="${escapeHtml(r.report_id)}">
                <div>
                    <strong>${escapeHtml(r.category)}</strong> - ${escapeHtml(r.period)}
                </div>
                <div class="report-meta">
                    <span class="tag">${escapeHtml(r.locale)}</span>
                    <span class="tag">${r.total_items} tweets</span>
                    <span class="tag">${escapeHtml(r.scraped_at?.slice(0, 10) || '')}</span>
                </div>
            </div>
        `).join('');

        container.querySelectorAll('.report-item').forEach(item => {
            item.addEventListener('click', () => loadReportDetail(item.dataset.id));
        });
    }

    async function loadReportDetail(reportId) {
        try {
            const res = await fetch('/api/reports/' + reportId);
            if (!res.ok) {
                alert('Report not found.');
                return;
            }
            const report = await res.json();
            renderReportDetail(report);
        } catch (err) {
            console.error('Report detail error:', err);
        }
    }

    function renderReportDetail(report) {
        const panel = document.getElementById('detail-panel');
        const container = document.getElementById('report-detail');
        if (!panel || !container) return;

        panel.classList.remove('hidden');

        let html = `
            <div class="status-grid" style="margin-bottom:16px">
                <span class="status-label">Locale:</span><span class="status-value">${escapeHtml(report.locale)}</span>
                <span class="status-label">Category:</span><span class="status-value">${escapeHtml(report.category)}</span>
                <span class="status-label">Period:</span><span class="status-value">${escapeHtml(report.period)}</span>
                <span class="status-label">Scraped:</span><span class="status-value">${escapeHtml(report.scraped_at?.slice(0, 19) || '')}</span>
                <span class="status-label">Total:</span><span class="status-value">${report.total_items} items</span>
                <span class="status-label">Formula:</span><span class="status-value">${escapeHtml(report.formula)}</span>
            </div>
        `;

        if (!report.tweets || !report.tweets.length) {
            html += '<p class="empty-text">No tweets in this report.</p>';
        } else {
            report.tweets.forEach((tweet, i) => {
                html += `
                    <div class="tweet-card">
                        <span class="rank">#${i + 1}</span>
                        <span class="author">${escapeHtml(tweet.username)}</span>
                        <span class="handle">${escapeHtml(tweet.handle)}</span>
                        <div class="caption">${escapeHtml(tweet.caption)}</div>
                        ${tweet.screenshot_path ? `
                            <div class="screenshot-container" style="margin: 12px 0;">
                                ${(() => {
                                    const parts = tweet.screenshot_path.split('/');
                                    const date = parts[parts.length - 2] || '';
                                    const file = parts[parts.length - 1] || '';
                                    const url = '/api/screenshots/' + date + '/' + file;
                                    return '<a href="' + url + '" target="_blank" rel="noopener noreferrer"><img src="' + url + '" alt="Tweet Screenshot" style="max-width: 100%; border-radius: 8px; border: 1px solid var(--border);" /></a>';
                                })()}
                            </div>
                        ` : ''}
                        <div class="metrics">
                            <span>Likes: ${tweet.engagement.likes.toLocaleString()}</span>
                            <span>Reposts: ${tweet.engagement.reposts.toLocaleString()}</span>
                            <span>Views: ${tweet.engagement.views.toLocaleString()}</span>
                            <span>Replies: ${tweet.engagement.replies.toLocaleString()}</span>
                            <span><strong>Score: ${tweet.engagement.total_score.toLocaleString()}</strong></span>
                        </div>
                        <div class="links">
                            <a href="${escapeHtml(tweet.tweet_url)}" target="_blank" rel="noopener noreferrer">View Tweet</a>
                            ${tweet.video_url ? `<a href="${escapeHtml(tweet.video_url)}" target="_blank" rel="noopener noreferrer">View Video</a>` : ''}
                        </div>
                    </div>
                `;
            });
        }

        container.innerHTML = html;
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = String(str);
        return div.innerHTML;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
