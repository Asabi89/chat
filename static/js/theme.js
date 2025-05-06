// Check for saved theme preference or use the system preference
if (localStorage.getItem('color-theme') === 'dark' || (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
    document.getElementById('theme-toggle-dark-icon').classList.add('hidden');
    document.getElementById('theme-toggle-light-icon').classList.remove('hidden');
    document.getElementById('theme-toggle-text').textContent = 'Light Mode';
} else {
    document.documentElement.classList.remove('dark');
    document.getElementById('theme-toggle-light-icon').classList.add('hidden');
    document.getElementById('theme-toggle-dark-icon').classList.remove('hidden');
    document.getElementById('theme-toggle-text').textContent = 'Dark Mode';
}

// Add event listener to toggle button
document.getElementById('theme-toggle').addEventListener('click', function() {
    // Toggle dark class on html element
    document.documentElement.classList.toggle('dark');
    
    // Update icons and text
    if (document.documentElement.classList.contains('dark')) {
        document.getElementById('theme-toggle-dark-icon').classList.add('hidden');
        document.getElementById('theme-toggle-light-icon').classList.remove('hidden');
        document.getElementById('theme-toggle-text').textContent = 'Light Mode';
        localStorage.setItem('color-theme', 'dark');
    } else {
        document.getElementById('theme-toggle-light-icon').classList.add('hidden');
        document.getElementById('theme-toggle-dark-icon').classList.remove('hidden');
        document.getElementById('theme-toggle-text').textContent = 'Dark Mode';
        localStorage.setItem('color-theme', 'light');
    }
});
