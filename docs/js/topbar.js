// Top bar functionality for documentation pages
document.addEventListener('DOMContentLoaded', function() {
    // Function to fetch the latest version from GitHub
    async function fetchGitHubInfo() {
        try {
            // Fetch GitHub repository information
            const repoResponse = await fetch('https://api.github.com/repos/plexguide/Huntarr.io');
            const repoData = await repoResponse.json();
            
            // Get star count
            if (repoData.stargazers_count) {
                document.getElementById('github-stars-value').textContent = repoData.stargazers_count;
            }
            
            // Fetch releases information
            const releasesResponse = await fetch('https://api.github.com/repos/plexguide/Huntarr.io/releases');
            const releasesData = await releasesResponse.json();
            
            if (releasesData && releasesData.length > 0) {
                // Get the latest version
                const latestVersion = releasesData[0].tag_name;
                document.getElementById('latest-version-value').textContent = latestVersion;
            }
        } catch (error) {
            console.error('Error fetching GitHub data:', error);
        }
    }
    
    // Function to get version from version.txt file
    async function fetchCurrentVersion() {
        try {
            const response = await fetch('/version.txt');
            if (response.ok) {
                const version = await response.text();
                document.getElementById('version-value').textContent = version.trim();
            } else {
                // Fallback if version.txt is not accessible
                const versionElement = document.getElementById('version-value');
                if (versionElement) {
                    // Use the same version as in the main app or a placeholder
                    versionElement.textContent = '6.5.15';
                }
            }
        } catch (error) {
            console.error('Error fetching version:', error);
        }
    }
    
    // Initial data fetch
    fetchCurrentVersion();
    fetchGitHubInfo();
});
