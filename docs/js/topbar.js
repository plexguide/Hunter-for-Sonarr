// Top bar functionality for documentation pages
document.addEventListener('DOMContentLoaded', function() {
    // Update page title in top bar
    function updatePageTitle() {
        const pageTitle = document.querySelector('.page-title');
        if (pageTitle) {
            // Get the current page title from the document title
            const docTitle = document.title;
            let displayTitle = "Huntarr Documentation";
            
            // Extract the specific page name if possible
            if (docTitle.includes(' - ')) {
                const titleParts = docTitle.split(' - ');
                displayTitle = titleParts[0];
            } else if (docTitle.includes('Applications')) {
                displayTitle = "Applications";
            }
            
            pageTitle.textContent = displayTitle;
        }
    }
    
    // Function to fetch the latest version from GitHub with retries
    async function fetchGitHubInfo(retryCount = 0) {
        try {
            // Fetch GitHub repository information
            const repoResponse = await fetch('https://api.github.com/repos/plexguide/Huntarr.io');
            const repoData = await repoResponse.json();
            
            // Get star count
            if (repoData.stargazers_count) {
                const starsElement = document.getElementById('github-stars-value');
                if (starsElement) {
                    starsElement.textContent = repoData.stargazers_count;
                }
            }
            
            // Fetch releases information
            const releasesResponse = await fetch('https://api.github.com/repos/plexguide/Huntarr.io/releases');
            const releasesData = await releasesResponse.json();
            
            if (releasesData && releasesData.length > 0) {
                // Get the latest version
                const latestVersion = releasesData[0].tag_name;
                const latestElement = document.getElementById('latest-version-value');
                if (latestElement) {
                    latestElement.textContent = latestVersion;
                }
            }
        } catch (error) {
            console.error('Error fetching GitHub data:', error);
            // Retry up to 3 times with exponential backoff
            if (retryCount < 3) {
                setTimeout(() => {
                    fetchGitHubInfo(retryCount + 1);
                }, 1000 * Math.pow(2, retryCount)); // 1s, 2s, 4s backoff
            }
        }
    }
    
    // Function to get version from version.txt file
    async function fetchCurrentVersion() {
        try {
            // We need to use an absolute path from the current page
            const basePath = window.location.pathname.includes('/docs/') ? 
                            window.location.pathname.substring(0, window.location.pathname.lastIndexOf('/docs/') + 6) : 
                            '/docs/';
            
            const response = await fetch(`${basePath}version.txt`);
            if (response.ok) {
                const version = await response.text();
                const versionElement = document.getElementById('version-value');
                if (versionElement) {
                    versionElement.textContent = version.trim();
                }
            } else {
                // Fallback if version.txt is not accessible
                const versionElement = document.getElementById('version-value');
                if (versionElement) {
                    // Use hardcoded version as fallback
                    versionElement.textContent = '6.5.15';
                }
            }
        } catch (error) {
            console.error('Error fetching version:', error);
            // Set fallback version
            const versionElement = document.getElementById('version-value');
            if (versionElement) {
                versionElement.textContent = '6.5.15';
            }
        }
    }
    
    // Initial data fetch
    updatePageTitle();
    fetchCurrentVersion();
    fetchGitHubInfo();
});
