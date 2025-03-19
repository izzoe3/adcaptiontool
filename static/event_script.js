document.addEventListener("DOMContentLoaded", function () {
    const eventForm = document.getElementById("eventForm");
    if (eventForm) {
        console.log("Event caption page detected");

        const resultSection = document.getElementById("resultSection");
        const captionsTbody = document.getElementById("captions");
        const headlinesTbody = document.getElementById("headlines");
        const regenerateBtn = document.getElementById("regenerateBtn");

        if (!resultSection || !captionsTbody || !headlinesTbody || !regenerateBtn) {
            console.error("Missing DOM elements:", { resultSection, captionsTbody, headlinesTbody, regenerateBtn });
            return;
        }

        let formData = {};

        eventForm.addEventListener("submit", function (e) {
            e.preventDefault();
            formData = {
                event_name: document.getElementById("event_name").value,
                event_venue: document.getElementById("event_venue").value,
                event_date: document.getElementById("event_date").value,
                event_time: document.getElementById("event_time").value,
                tone: document.getElementById("tone").value,
                min_words: document.getElementById("min_words").value,
                add_on_text: document.getElementById("add_on_text").value,
                target_audience: document.getElementById("target_audience").value,
                ad_goal: document.getElementById("ad_goal").value || "" // Optional
            };
            console.log("Form data:", formData);
            generateCaptions(formData);
        });

        regenerateBtn.addEventListener("click", function () {
            generateCaptions(formData);
        });

        function generateCaptions(data) {
            fetch("/event_caption", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            })
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                return response.json();
            })
            .then(result => {
                console.log("Generated result:", result);
                if (result.error) {
                    alert(result.error);
                } else {
                    const latestId = result.id;
                    captionsTbody.innerHTML = result.result.captions.length ? result.result.captions.map(caption => `
                        <tr>
                            <td>${caption}</td>
                            <td><button class="btn btn-copy" data-caption="${caption}" data-id="${latestId}">Copy</button></td>
                        </tr>
                    `).join('') : '<tr><td colspan="2">No captions generated.</td></tr>';
        
                    headlinesTbody.innerHTML = result.result.headlines.length ? result.result.headlines.map(headline => `
                        <tr>
                            <td>${headline}</td>
                            <td><button class="btn btn-copy" data-caption="${headline}" data-id="${latestId}">Copy</button></td>
                        </tr>
                    `).join('') : '<tr><td colspan="2">No headlines generated.</td></tr>';
        
                    document.getElementById("visual_idea").textContent = result.result.visual_idea;
                    document.getElementById("cta").textContent = result.result.cta;
        
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
                }
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
});