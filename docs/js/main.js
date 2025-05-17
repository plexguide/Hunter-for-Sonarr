// Huntarr.io Documentation JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Add copy functionality to code blocks
    const codeBlocks = document.querySelectorAll('pre code');
    if (codeBlocks.length > 0) {
        codeBlocks.forEach(function(codeBlock) {
            const copyButton = document.createElement('button');
            copyButton.className = 'copy-button';
            copyButton.textContent = 'Copy';
            copyButton.addEventListener('click', function() {
                const code = codeBlock.textContent;
                navigator.clipboard.writeText(code).then(function() {
                    copyButton.textContent = 'Copied!';
                    setTimeout(function() {
                        copyButton.textContent = 'Copy';
                    }, 2000);
                }).catch(function(err) {
                    console.error('Could not copy text: ', err);
                });
            });
            
            const pre = codeBlock.parentNode;
            pre.style.position = 'relative';
            copyButton.style.position = 'absolute';
            copyButton.style.right = '10px';
            copyButton.style.top = '10px';
            copyButton.style.padding = '5px 10px';
            copyButton.style.background = '#f1f1f1';
            copyButton.style.border = '1px solid #ccc';
            copyButton.style.borderRadius = '3px';
            copyButton.style.cursor = 'pointer';
            pre.appendChild(copyButton);
        });
    }
    
    // Check for info icon links
    const infoLinks = document.querySelectorAll('.info-link');
    if (infoLinks.length > 0) {
        infoLinks.forEach(function(link) {
            link.setAttribute('title', 'Click for documentation');
        });
    }
    
    // Add active class to current page in navigation
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-menu li a');
    if (navLinks.length > 0) {
        navLinks.forEach(function(link) {
            const linkPath = link.getAttribute('href');
            // Check if the current path contains the link path (for sub-pages)
            if (currentPath.includes(linkPath) && linkPath !== '../index.html') {
                link.parentNode.classList.add('active');
            }
        });
    }
    
    // Add smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    if (anchorLinks.length > 0) {
        anchorLinks.forEach(function(link) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('href');
                if (targetId === '#') return;
                
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    window.scrollTo({
                        top: targetElement.offsetTop - 20,
                        behavior: 'smooth'
                    });
                }
            });
        });
    }
    
    // Add version check notification
    const footer = document.querySelector('footer');
    if (footer) {
        const versionText = footer.textContent;
        const versionMatch = versionText.match(/v(\d+\.\d+\.\d+)/);
        if (versionMatch) {
            const currentVersion = versionMatch[1];
            // This would typically check against an API endpoint for the latest version
            // This is just a placeholder for demonstration
            console.log(`Current documentation version: ${currentVersion}`);
        }
    }
}); 