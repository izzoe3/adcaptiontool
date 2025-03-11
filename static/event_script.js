document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('eventForm');
    const captionsDiv = document.getElementById('captions');
    const headlinesDiv = document.getElementById('headlines');
    const dateFromInput = document.getElementById('date_from');
    const dateToInput = document.getElementById('date_to');
    const timeFromInput = document.getElementById('time_from');
    const timeToInput = document.getElementById('time_to');
    const minWordsInput = document.getElementById('min_words');

    form.addEventListener('submit', function (event) {
        event.preventDefault();

        // Format date as "10 March 2025"
        const formatDate = (dateStr) => {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-GB', {
                day: 'numeric',
                month: 'long',
                year: 'numeric'
            });
        };

        const dateFrom = formatDate(dateFromInput.value);
        const dateTo = formatDate(dateToInput.value);
        const eventDate = dateFrom === dateTo ? dateFrom : `${dateFrom} - ${dateTo}`;

        // Format time as "2:00pm - 5:00pm"
        const formatTime = (timeStr) => {
            const [hours, minutes] = timeStr.split(':');
            let hour = parseInt(hours, 10);
            const period = hour >= 12 ? 'pm' : 'am';
            hour = hour % 12 || 12; // Convert 0 or 12 to 12
            return `${hour}:${minutes}${period}`;
        };

        const timeFrom = formatTime(timeFromInput.value);
        const timeTo = formatTime(timeToInput.value);
        const eventTime = `${timeFrom} - ${timeTo}`;

        // Collect form data
        const data = {
            event_name: document.getElementById('event_name').value,
            event_venue: document.getElementById('event_venue').value,
            event_date: eventDate,
            event_time: eventTime,
            tone: document.getElementById('tone').value,
            min_words: parseInt(minWordsInput.value, 10), // Add min_words as an integer
            add_on_text: document.getElementById('add_on_text').value.trim()
        };

        // Send AJAX request to /event_caption
        fetch('/event_caption', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.error) {
                alert(result.error);
            } else {
                // Display captions
                captionsDiv.innerHTML = '<ul>' + result.captions.map(caption => `<li>${caption}</li>`).join('') + '</ul>';
                // Display headlines
                headlinesDiv.innerHTML = '<ul>' + result.headlines.map(headline => `<li>${headline}</li>`).join('') + '</ul>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while generating captions.');
        });
    });
});