document.addEventListener('DOMContentLoaded', function () {
    const platformSelect = document.getElementById('platform');
    const campaignTypeSelect = document.getElementById('campaign_type');
    const programsContainer = document.getElementById('programsContainer');
    const minWordsContainer = document.getElementById('minWordsContainer');
    const minWordsInput = document.getElementById('min_words');

    // Hide or show the programs field based on campaign type selection
    campaignTypeSelect.addEventListener('change', function() {
        if (campaignTypeSelect.value === 'Foundation') {
            programsContainer.style.display = 'block';  // Show programs dropdown
        } else {
            programsContainer.style.display = 'none';  // Hide programs dropdown
        }
    });

    // Show or hide Minimum Words input for Meta platform
    platformSelect.addEventListener('change', function() {
        if (platformSelect.value === 'Meta') {
            minWordsContainer.style.display = 'block';  // Show min words input for Meta
        } else {
            minWordsContainer.style.display = 'none';  // Hide min words input
        }
    });

    // Event listener for ad form submission
    document.getElementById('adForm').addEventListener('submit', function(e) {
        e.preventDefault();

        // Gather form data
        const platform = platformSelect.value;
        const campaignType = campaignTypeSelect.value;
        const intake = document.getElementById('intake').value;
        const tone = document.getElementById('tone').value;
        const customMessage = document.getElementById('custom_message').value;

        // Only include selected programs if Foundation campaign type is selected
        const programs = campaignType === 'Foundation' ? 
            Array.from(document.getElementById('programs').selectedOptions).map(option => option.value) : [];

        // Get the minimum words if Meta platform is selected
        const minWords = platform === 'Meta' ? minWordsInput.value : 10;

        // Prepare data for POST request
        const data = {
            platform: platform,
            campaign_type: campaignType,
            intake: intake,
            tone: tone,
            custom_message: customMessage,
            min_words: minWords,
            programs: programs
        };

        fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            // Display the result
            displayResult(result);
        })
        .catch(error => console.error('Error generating ad copy:', error));
    });

    function displayResult(result) {
        // Clear any previous result
        document.getElementById('captions').innerHTML = '';
        document.getElementById('headlines').innerHTML = '';
        document.getElementById('descriptions').innerHTML = '';

        // Display captions
        if (result.captions) {
            const captionsContainer = document.getElementById('captions');
            result.captions.forEach(caption => {
                const captionDiv = document.createElement('div');
                captionDiv.textContent = caption;
                captionsContainer.appendChild(captionDiv);
            });
        }

        // Display headlines
        if (result.headlines) {
            const headlinesContainer = document.getElementById('headlines');
            result.headlines.forEach(headline => {
                const headlineDiv = document.createElement('div');
                headlineDiv.textContent = headline;
                headlinesContainer.appendChild(headlineDiv);
            });
        }

        // Display descriptions
        if (result.descriptions) {
            const descriptionsContainer = document.getElementById('descriptions');
            result.descriptions.forEach(description => {
                const descriptionDiv = document.createElement('div');
                descriptionDiv.textContent = description;
                descriptionsContainer.appendChild(descriptionDiv);
            });
        }
    }
});
