document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded");

    // Ad Generator Page Logic
    const adForm = document.getElementById("adForm");
    if (adForm) {
        console.log("Main generator page detected");

        const resultSection = document.getElementById("resultSection");
        const captionsTbody = document.getElementById("captions");
        const headlinesTbody = document.getElementById("headlines");
        const descriptionsTbody = document.getElementById("descriptions");
        const regenerateBtn = document.getElementById("regenerateBtn");
        const platformSelect = document.getElementById("platform");
        const campaignTypeSelect = document.getElementById("campaign_type");
        const foundationOptions = document.getElementById("foundation_options");
        const metaFields = document.getElementById("meta_fields");

        if (!resultSection || !captionsTbody || !headlinesTbody || !descriptionsTbody || !regenerateBtn || !platformSelect || !campaignTypeSelect || !foundationOptions || !metaFields) {
            console.error("Missing DOM elements:", { resultSection, captionsTbody, headlinesTbody, descriptionsTbody, regenerateBtn, platformSelect, campaignTypeSelect, foundationOptions, metaFields });
            return;
        }

        let formData = {};

        function togglePlatformFields() {
            const platform = platformSelect.value;
            metaFields.style.display = platform === "Meta" ? "block" : "none";
        }

        platformSelect.addEventListener("change", togglePlatformFields);
        togglePlatformFields();

        campaignTypeSelect.addEventListener("change", function () {
            foundationOptions.style.display = this.value === "Foundation" ? "block" : "none";
        });

        adForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const programs = Array.from(document.querySelectorAll('input[name="programs"]:checked')).map(input => input.value);
            formData = {
                platform: platformSelect.value,
                campaign_type: campaignTypeSelect.value,
                intake: document.getElementById("intake").value,
                tone: document.getElementById("tone").value,
                min_words: platformSelect.value === "Meta" ? document.getElementById("min_words").value : undefined,
                add_on_text: platformSelect.value === "Meta" ? document.getElementById("add_on_text").value : undefined,
                programs: programs,
                target_audience: document.getElementById("target_audience").value,
                ad_goal: document.getElementById("ad_goal").value || ""
            };
            console.log("Form data:", formData);
            generateCaptions(formData);
        });

        regenerateBtn.addEventListener("click", function () {
            generateCaptions(formData);
        });

        function generateCaptions(data) {
            fetch("/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            })
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                return response.json();
            })
            .then(result => {
                console.log("Raw result:", result);

                if (result.error) {
                    alert(result.error);
                    return;
                }

                const latestId = result.id;
                const platform = data.platform;
                const captions = result.result.captions || [];
                const headlines = result.result.headlines || [];
                const descriptions = result.result.descriptions || [];

                console.log("Processed captions:", captions);
                console.log("Processed headlines:", headlines);
                console.log("Processed descriptions:", descriptions);

                if (platform === "Meta") {
                    captionsTbody.innerHTML = captions.length ? captions.map(caption => `
                        <tr>
                            <td>${caption}</td>
                            <td><button class="btn btn-copy" data-caption="${caption}" data-id="${latestId}">Copy</button></td>
                        </tr>
                    `).join('') : '<tr><td colspan="2">No captions generated.</td></tr>';
                    headlinesTbody.innerHTML = headlines.length ? headlines.map(headline => `
                        <tr>
                            <td>${headline}</td>
                            <td><button class="btn btn-copy" data-caption="${headline}" data-id="${latestId}">Copy</button></td>
                        </tr>
                    `).join('') : '<tr><td colspan="2">No headlines generated.</td></tr>';
                    descriptionsTbody.innerHTML = '';
                } else {
                    captionsTbody.innerHTML = '';
                    headlinesTbody.innerHTML = headlines.length ? headlines.map(headline => `
                        <tr>
                            <td>${headline}</td>
                            <td><button class="btn btn-copy" data-caption="${headline}" data-id="${latestId}">Copy</button></td>
                        </tr>
                    `).join('') : '<tr><td colspan="2">No headlines generated.</td></tr>';
                    descriptionsTbody.innerHTML = descriptions.length ? descriptions.map(desc => `
                        <tr>
                            <td>${desc}</td>
                            <td><button class="btn btn-copy" data-caption="${desc}" data-id="${latestId}">Copy</button></td>
                        </tr>
                    `).join('') : '<tr><td colspan="2">No descriptions generated.</td></tr>';
                }

                resultSection.style.display = "block";
                regenerateBtn.style.display = "inline-block";

                document.querySelectorAll('.btn-copy').forEach(btn => {
                    btn.addEventListener('click', function () {
                        const caption = this.dataset.caption;
                        const itemId = this.dataset.id;
                        navigator.clipboard.writeText(caption)
                            .then(() => {
                                alert('Copied to clipboard!');
                                markAsUsed(itemId, caption);
                            })
                            .catch(err => console.error('Error copying:', err));
                    });
                });
            })
            .catch(error => console.error("Error generating captions:", error));
        }

        function markAsUsed(itemId, caption) {
            fetch('/mark_used', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: itemId, caption: caption, used: true })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Marked as used:', caption);
                }
            })
            .catch(error => console.error('Error marking as used:', error));
        }
    }

    // History Page Logic
    const historyPage = document.querySelector('.history-section');
    if (historyPage) {
        console.log("History page detected");

        const copyHistoryBtn = document.getElementById('copyHistory');
        const clearHistoryBtn = document.getElementById('clearHistory');
        const exportCSVBtn = document.getElementById('exportCSV');
        const dateFilter = document.getElementById('dateFilter');

        document.querySelectorAll('.section-toggle').forEach(toggle => {
            toggle.addEventListener('click', function () {
                const content = this.nextElementSibling;
                const icon = this.querySelector('.toggle-icon');
                content.style.display = content.style.display === 'none' ? 'block' : 'none';
                icon.textContent = content.style.display === 'none' ? '+' : '−';
            });
        });

        document.querySelectorAll('.date-toggle').forEach(toggle => {
            toggle.addEventListener('click', function () {
                const content = this.nextElementSibling;
                const icon = this.querySelector('.toggle-icon');
                content.style.display = content.style.display === 'none' ? 'block' : 'none';
                icon.textContent = content.style.display === 'none' ? '+' : '−';
            });
        });

        dateFilter.addEventListener('change', function () {
            const selectedDate = this.value;
            document.querySelectorAll('.date-group').forEach(group => {
                const date = group.querySelector('.date-toggle').textContent.trim().split(' ')[0];
                group.style.display = (selectedDate && date !== selectedDate) ? 'none' : 'block';
            });
        });

        if (copyHistoryBtn) {
            copyHistoryBtn.addEventListener('click', function () {
                const text = Array.from(document.querySelectorAll('.history-row'))
                    .map(row => row.textContent.trim())
                    .join('\n\n');
                navigator.clipboard.writeText(text)
                    .then(() => alert('History copied to clipboard!'))
                    .catch(err => console.error('Error copying text:', err));
            });
        }

        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', function () {
                if (confirm('Are you sure you want to clear all history?')) {
                    fetch('/clear_history', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            document.querySelectorAll('.section-content').forEach(content => {
                                content.innerHTML = '<p>No campaigns available.</p>';
                            });
                            alert(data.message);
                        }
                    })
                    .catch(error => console.error('Error clearing history:', error));
                }
            });
        }

        if (exportCSVBtn) {
            exportCSVBtn.addEventListener('click', function () {
                window.location.href = '/export_history';
            });
        }

        document.querySelectorAll('.used-toggle').forEach(toggle => {
            toggle.addEventListener('change', function () {
                const caption = this.dataset.caption;
                const itemId = this.dataset.id;
                const isChecked = this.checked;

                fetch('/mark_used', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: itemId, caption: caption, used: isChecked })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const span = this.previousElementSibling;
                        if (span) {
                            span.classList.toggle('used', isChecked);
                        }
                    }
                })
                .catch(error => console.error('Error updating used status:', error));
            });
        });
    }

    // Link Shortener Logic (Updated)
    const shortenForm = document.getElementById("shortenForm");
    if (shortenForm) {
        shortenForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const url = document.getElementById("linkInput").value;
            fetch("/shorten", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) throw new Error(data.error);
                const resultDiv = document.getElementById("shortLinkResult");
                resultDiv.innerHTML = `
                    <p>Short URL: <a href="${data.short_url}" target="_blank">${data.short_url}</a></p>
                    <button class="btn btn-primary view-stats-btn" data-link-id="${data.id}">View Stats</button>
                    <div id="stats-${data.id}"></div>
                `;

                // Attach event listener to the "View Stats" button
                const statsBtn = resultDiv.querySelector('.view-stats-btn');
                statsBtn.addEventListener('click', function () {
                    const linkId = this.getAttribute('data-link-id');
                    getStats(linkId);
                });
            })
            .catch(error => alert("Error: " + error.message));
        });
    }

    function getStats(linkId) {
        fetch(`/link_stats/${linkId}`)
        .then(response => response.json())
        .then(data => {
            const statsDiv = document.getElementById(`stats-${linkId}`);
            statsDiv.innerHTML = `
                <p>Clicks: ${data.click_count}</p>
                <ul>${data.clicks.map(click => `<li>${click.timestamp} (IP: ${click.ip})</li>`).join('')}</ul>
            `;
        })
        .catch(error => console.error("Error fetching stats:", error));
    }
});