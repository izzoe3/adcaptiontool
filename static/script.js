document.addEventListener("DOMContentLoaded", function () {
    const platformSelect = document.getElementById("platform");
    const campaignTypeSelect = document.getElementById("campaign_type");
    const intakeSelect = document.getElementById("intake");
    const toneSelect = document.getElementById("tone");
    const minWordsContainer = document.getElementById("minWordsContainer");
    const minWordsInput = document.getElementById("min_words");
    const foundationContainer = document.getElementById("foundationContainer");
    const foundationPrograms = document.getElementById("programs");
    const addOnTextContainer = document.getElementById("addOnTextContainer"); // ✅ Add-On Text Field
    const addOnTextInput = document.getElementById("add_on_text"); // ✅ Input Field

    const adForm = document.getElementById("adForm");
    const adPreviewContainer = document.getElementById("adPreviewContainer");
    const regenerateBtn = document.getElementById("regenerateBtn");

    // ✅ Function to show/hide Minimum Words input
    function updateMinWordsVisibility() {
        minWordsContainer.style.display = platformSelect.value === "Meta" ? "block" : "none";
    }

    // ✅ Function to show/hide Foundation dropdown
    function updateFoundationVisibility() {
        foundationContainer.style.display = campaignTypeSelect.value === "Foundation" ? "block" : "none";
    }

    // ✅ Function to show/hide Add-On Text field
    function updateAddOnTextVisibility() {
        addOnTextContainer.style.display = platformSelect.value === "Meta" ? "block" : "none";
    }

    // ✅ Ensure correct visibility on initial page load
    setTimeout(() => {
        updateMinWordsVisibility();
        updateFoundationVisibility();
        updateAddOnTextVisibility();
    }, 100);

    // ✅ Listen for platform selection changes
    platformSelect.addEventListener("change", () => {
        updateMinWordsVisibility();
        updateAddOnTextVisibility();
    });

    // ✅ Listen for campaign type selection changes
    campaignTypeSelect.addEventListener("change", updateFoundationVisibility);

    // ✅ Handle form submission
    adForm.addEventListener("submit", function (e) {
        e.preventDefault();

        const platform = platformSelect.value;
        const campaignType = campaignTypeSelect.value;
        const intake = intakeSelect.value;
        const tone = toneSelect.value;
        const minWords = platform === "Meta" ? minWordsInput.value : 10;
        const addOnText = platform === "Meta" ? addOnTextInput.value.trim() : ""; // ✅ Include Add-On Text

        const programs = (foundationPrograms && campaignType === "Foundation")
            ? Array.from(foundationPrograms.selectedOptions).map(opt => opt.value)
            : [];

        const requestData = { 
            platform, 
            campaign_type: campaignType, 
            intake, 
            tone, 
            min_words: minWords, 
            add_on_text: addOnText, // ✅ Send to backend
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
            regenerateBtn.style.display = "block"; // Show regenerate button
        })
        .catch(error => console.error("❌ Error:", error));
    });

    // ✅ Function to regenerate ad
    regenerateBtn.addEventListener("click", function () {
        adForm.dispatchEvent(new Event("submit"));
    });

    // ✅ Function to display generated results
    function displayResult(result) {
        adPreviewContainer.innerHTML = ""; // Clear previous results

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
});
