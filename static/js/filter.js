let activeFilters = [];

function toggleRowDetails(event) {
    const row = event.currentTarget;
    const hiddenContent = row.querySelectorAll('.hidden-content');
    const arrow = row.querySelector('.arrow');
    
    hiddenContent.forEach(content => {
        content.style.display = content.style.display === 'none' || content.style.display === '' ? 'block' : 'none';
    });

    arrow.style.transform = arrow.style.transform === 'rotate(0deg)' ? 'rotate(-90deg)' : 'rotate(0deg)';
}

function toggleFilterPanel() {
    const panel = document.getElementById('filterPanel');
    const container = document.querySelector('.filter-container');

    if (panel.style.display === 'none' || panel.style.display === '') {
        panel.style.display = 'flex';
    } else {
        panel.style.display = 'none';
    }
}


function applyFilter(status) {
    const rows = document.querySelectorAll('.clickable');
    const buttons = document.querySelectorAll('.filter-panel div');

    // Handle the 'Show All' case
    if (status === 'all') {
        activeFilters = [];
        rows.forEach(row => {
            row.style.display = ''; // Show all rows
        });
        buttons.forEach(button => button.classList.remove('active')); // Remove active class from all buttons
        return;
    }
    
    // Toggle the active filter and button state
    if (activeFilters.includes(status)) {
        activeFilters = activeFilters.filter(filter => filter !== status);
        document.querySelector(`.filter-panel div[onclick="applyFilter('${status}')"]`).classList.remove('active');
    } else {
        activeFilters.push(status);
        document.querySelector(`.filter-panel div[onclick="applyFilter('${status}')"]`).classList.add('active');
    }

    // Apply the filter
    rows.forEach(row => {
        const connection = row.querySelector('td:nth-child(2) img').alt.toLowerCase();
        const robotsTxt = row.querySelector('td:nth-child(3) img').alt.toLowerCase();
        const sitemap = row.querySelector('td:nth-child(4) img').alt.toLowerCase();

        const rowStatus = [connection, robotsTxt, sitemap].filter(Boolean);

        // Check if the row has exactly the same statuses as active filters
        const hasExactMatch = activeFilters.length === rowStatus.length && activeFilters.every(filter => rowStatus.includes(filter));

        row.style.display = hasExactMatch ? '' : 'none'; // Show or hide row based on exact match
    });
}
