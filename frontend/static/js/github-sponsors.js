/**
 * GitHub Sponsors Integration
 * Fetches and displays sponsors from GitHub for PlexGuide
 */

const GithubSponsors = {
    // Constants
    sponsorsUsername: 'plexguide',
    sponsorsApiUrl: 'https://api.github.com/sponsors/',
    cacheDuration: 3600000, // 1 hour in milliseconds
    
    // Initialize the sponsors display
    init: function() {
        console.log('Initializing GitHub Sponsors display');
        this.loadSponsors();
        
        // Add event listener for manual refresh
        document.addEventListener('click', function(e) {
            if (e.target.closest('.action-button.refresh-sponsors')) {
                GithubSponsors.loadSponsors(true);
            }
        });
    },
    
    // Load sponsors data
    loadSponsors: function(skipCache = false) {
        // Elements
        const loadingEl = document.getElementById('sponsors-loading');
        const sponsorsListEl = document.getElementById('sponsors-list');
        const errorEl = document.getElementById('sponsors-error');
        
        if (!loadingEl || !sponsorsListEl || !errorEl) {
            console.error('Sponsors DOM elements not found');
            return;
        }
        
        // First check for cached data
        const cachedData = this.getCachedSponsors();
        
        if (!skipCache && cachedData && cachedData.sponsors) {
            console.log('Using cached sponsors data');
            this.displaySponsors(cachedData.sponsors);
            return;
        }
        
        // Show loading state
        loadingEl.style.display = 'block';
        sponsorsListEl.style.display = 'none';
        errorEl.style.display = 'none';
        
        // Since GitHub's API requires authentication for the sponsors endpoint,
        // we'll use a mock implementation for demonstration purposes.
        // In a production environment, this would be replaced with a proper server-side
        // implementation that securely accesses the GitHub API with appropriate tokens.
        this.getMockSponsors()
            .then(sponsors => {
                // Cache the sponsors data
                this.cacheSponsors(sponsors);
                
                // Display the sponsors
                this.displaySponsors(sponsors);
                
                // Hide loading state
                loadingEl.style.display = 'none';
                sponsorsListEl.style.display = 'flex';
            })
            .catch(error => {
                console.error('Error fetching sponsors:', error);
                
                // Show error state
                loadingEl.style.display = 'none';
                errorEl.style.display = 'block';
                errorEl.querySelector('span').textContent = 'Could not load sponsors: ' + error.message;
            });
    },
    
    // Get cached sponsors data
    getCachedSponsors: function() {
        const cachedData = localStorage.getItem('huntarr-github-sponsors');
        
        if (!cachedData) {
            return null;
        }
        
        try {
            const data = JSON.parse(cachedData);
            
            // Check if cache is expired
            if (Date.now() - data.timestamp > this.cacheDuration) {
                console.log('Sponsors cache expired');
                return null;
            }
            
            return data;
        } catch (e) {
            console.error('Error parsing cached sponsors data:', e);
            return null;
        }
    },
    
    // Cache sponsors data
    cacheSponsors: function(sponsors) {
        const data = {
            sponsors: sponsors,
            timestamp: Date.now()
        };
        
        localStorage.setItem('huntarr-github-sponsors', JSON.stringify(data));
        console.log('Cached sponsors data');
    },
    
    // Display sponsors in the UI
    displaySponsors: function(sponsors) {
        const sponsorsListEl = document.getElementById('sponsors-list');
        
        if (!sponsorsListEl) {
            console.error('Sponsors list element not found');
            return;
        }
        
        // Clear existing content
        sponsorsListEl.innerHTML = '';
        
        if (!sponsors || sponsors.length === 0) {
            sponsorsListEl.innerHTML = '<div class="no-sponsors">No sponsors found</div>';
            return;
        }
        
        // Create sponsor elements
        sponsors.forEach(sponsor => {
            const sponsorEl = document.createElement('a');
            sponsorEl.href = sponsor.url;
            sponsorEl.target = '_blank';
            sponsorEl.className = 'sponsor-item';
            sponsorEl.title = `${sponsor.name} - ${sponsor.tier}`;
            
            sponsorEl.innerHTML = `
                <img src="${sponsor.avatarUrl}" alt="${sponsor.name}" class="sponsor-avatar">
                <div class="sponsor-name">${sponsor.name}</div>
                <div class="sponsor-tier">${sponsor.tier}</div>
            `;
            
            sponsorsListEl.appendChild(sponsorEl);
        });
    },
    
    // Mock implementation to get sponsors
    getMockSponsors: function() {
        return new Promise((resolve) => {
            // Simulate API delay
            setTimeout(() => {
                const mockSponsors = [
                    {
                        name: 'JohnDoe',
                        url: 'https://github.com/JohnDoe',
                        avatarUrl: 'https://avatars.githubusercontent.com/u/1234567',
                        tier: 'Gold Sponsor'
                    },
                    {
                        name: 'JaneSmith',
                        url: 'https://github.com/JaneSmith',
                        avatarUrl: 'https://avatars.githubusercontent.com/u/2345678',
                        tier: 'Silver Sponsor'
                    },
                    {
                        name: 'TechCorp',
                        url: 'https://github.com/TechCorp',
                        avatarUrl: 'https://avatars.githubusercontent.com/u/3456789',
                        tier: 'Gold Sponsor'
                    },
                    {
                        name: 'MediaSolutions',
                        url: 'https://github.com/MediaSolutions',
                        avatarUrl: 'https://avatars.githubusercontent.com/u/4567890',
                        tier: 'Bronze Sponsor'
                    },
                    {
                        name: 'DevOpsGuru',
                        url: 'https://github.com/DevOpsGuru',
                        avatarUrl: 'https://avatars.githubusercontent.com/u/5678901',
                        tier: 'Silver Sponsor'
                    },
                    {
                        name: 'CloudExperts',
                        url: 'https://github.com/CloudExperts',
                        avatarUrl: 'https://avatars.githubusercontent.com/u/6789012',
                        tier: 'Bronze Sponsor'
                    }
                ];
                
                resolve(mockSponsors);
            }, 800);
        });
    }
};

// Initialize when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    GithubSponsors.init();
});
