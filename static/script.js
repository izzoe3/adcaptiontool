document.addEventListener("DOMContentLoaded", function () {
    // Main caption generator logic (for index.html)
    const adForm = document.getElementById("adForm");
    if (adForm) {
        const platformSelect = document.getElementById("platform");
        const campaignTypeSelect = document.getElementById("campaign_type");
        const intakeSelect = document.getElementById("intake");
        const toneSelect = document.getElementById("tone");
        const minWordsContainer = document.getElementById("minWordsContainer");
        const minWordsInput = document.getElementById("min_words");
        const foundationContainer = document.getElementById("foundationContainer");
        const foundationPrograms = document.getElementById("programs");
        const addOnTextContainer = document.getElementById("addOnTextContainer");
        const addOnTextInput = document.getElementById("add_on_text");
        const adPreviewContainer = document.getElementById("adPreviewContainer");
        const regenerateBtn = document.getElementById("regenerateBtn");

        function updateMinWordsVisibility() {
            if (minWordsContainer) {
                minWordsContainer.style.display = platformSelect.value === "Meta" ? "block" : "none";
            }
        }

        function updateFoundationVisibility() {
            if (foundationContainer) {
                foundationContainer.style.display = campaignTypeSelect.value === "Foundation" ? "block" : "none";
            }
        }

        function updateAddOnTextVisibility() {
            if (addOnTextContainer) {
                addOnTextContainer.style.display = platformSelect.value === "Meta" ? "block" : "none";
            }
        }

        setTimeout(() => {
            updateMinWordsVisibility();
            updateFoundationVisibility();
            updateAddOnTextVisibility();
        }, 100);

        platformSelect.addEventListener("change", () => {
            updateMinWordsVisibility();
            updateAddOnTextVisibility();
        });

        campaignTypeSelect.addEventListener("change", updateFoundationVisibility);

        adForm.addEventListener("submit", function (e) {
            e.preventDefault();

            const platform = platformSelect.value;
            const campaignType = campaignTypeSelect.value;
            const intake = intakeSelect.value;
            const tone = toneSelect.value;
            const minWords = platform === "Meta" ? minWordsInput.value : 10;
            const addOnText = platform === "Meta" ? addOnTextInput.value.trim() : "";

            const programs = (foundationPrograms && campaignType === "Foundation")
                ? Array.from(foundationPrograms.selectedOptions).map(opt => opt.value)
                : [];

            const requestData = { 
                platform, 
                campaign_type: campaignType, 
                intake, 
                tone, 
                min_words: minWords, 
                add_on_text: addOnText,
                programs 
            };

            fetch("/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestData),
            })
            .then(response => response.json())
            .then(data => {
                displayResult(data);
                if (regenerateBtn) regenerateBtn.style.display = "block";
            })
            .catch(error => console.error("❌ Error:", error));
        });

        if (regenerateBtn) {
            regenerateBtn.addEventListener("click", function () {
                adForm.dispatchEvent(new Event("submit"));
            });
        }

        function displayResult(result) {
            adPreviewContainer.innerHTML = "";

            if (result.captions.length) {
                result.captions.forEach((caption, index) => {
                    const card = document.createElement("div");
                    card.classList.add("ad-card");
                    card.innerHTML = `<div class="ad-header">Ad Preview ${index + 1}</div><div class="ad-content">${caption}</div>`;
                    adPreviewContainer.appendChild(card);
                });
            }

            if (result.headlines.length) {
                const headlinesCard = document.createElement("div");
                headlinesCard.classList.add("ad-card");
                headlinesCard.innerHTML = `<div class="ad-header">Ad Headlines</div><ul class="ad-list">${result.headlines.map(h => `<li>${h}</li>`).join("")}</ul>`;
                adPreviewContainer.appendChild(headlinesCard);
            }

            if (result.descriptions.length) {
                const descriptionsCard = document.createElement("div");
                descriptionsCard.classList.add("ad-card");
                descriptionsCard.innerHTML = `<div class="ad-header">Ad Descriptions</div><ul class="ad-list">${result.descriptions.map(d => `<li>${d}</li>`).join("")}</ul>`;
                adPreviewContainer.appendChild(descriptionsCard);
            }
        }
    }

    // History page logic (for history.html)
    const historyList = document.getElementById('historyList'); // Updated to check for #historyList
    if (historyList) {
        const copyHistoryBtn = document.getElementById('copyHistory');
        const clearHistoryBtn = document.getElementById('clearHistory');
        const exportCSVBtn = document.getElementById('exportCSV');

        if (copyHistoryBtn) {
            copyHistoryBtn.addEventListener('click', function () {
                const text = Array.from(historyList.getElementsByTagName('li'))
                    .map(item => item.textContent.trim())
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
                            historyList.innerHTML = '<li>No history available.</li>';
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
    }
});