document.addEventListener("DOMContentLoaded", function () {
    const personaForm = document.getElementById("personaForm");
    if (personaForm) {
        console.log("Persona generator page detected");

        const resultSection = document.getElementById("resultSection");
        const personaTbody = document.getElementById("persona");
        const regenerateBtn = document.getElementById("regenerateBtn");

        if (!resultSection || !personaTbody || !regenerateBtn) {
            console.error("Missing DOM elements:", { resultSection, personaTbody, regenerateBtn });
            return;
        }

        let formData = {};

        personaForm.addEventListener("submit", function (e) {
            e.preventDefault();
            formData = {
                industry: document.getElementById("industry").value,
                product: document.getElementById("product").value,
                demographic: document.getElementById("demographic").value,
                tone: document.getElementById("tone").value
            };
            console.log("Form data:", formData);
            generatePersona(formData);
        });

        regenerateBtn.addEventListener("click", function () {
            generatePersona(formData);
        });

        function generatePersona(data) {
            fetch("/persona", {
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
                    const persona = result.result.persona || [];

                    personaTbody.innerHTML = persona.length ? persona.map(line => `
                        <tr>
                            <td>${line.split(':')[0]}</td>
                            <td>${line.split(':').slice(1).join(':') || line}</td>
                            <td><button class="btn btn-copy" data-caption="${line}" data-id="${latestId}">Copy</button></td>
                        </tr>
                    `).join('') : '<tr><td colspan="3">No persona generated.</td></tr>';

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
            .catch(error => console.error("Error generating persona:", error));
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