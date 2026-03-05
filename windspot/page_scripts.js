// Page automation scripts for iKitesurf
// These functions are injected into the page via Playwright's add_init_script()

window.PageScripts = {
    /**
     * Extract tide schedule from the Nearby Tides section
     */
    extractTideData: function() {
        const section = [...document.querySelectorAll('h2')].find(h => h.textContent.includes('Nearby Tides'));
        if (!section) return null;

        // Walk up to find the tides container
        let container = section.parentElement;
        for (let i = 0; i < 8 && container; i++) {
            container = container.parentElement;
        }
        if (!container) container = document.body;

        const allText = container.innerText || '';
        const result = { station: '', date: '', tides: [] };

        // Extract tide entries - flexible regex for various formats
        // Pattern: "Low Tide  3:18 AM PST  3.62 ft" or similar
        const tideRegex = /(Low|High)\s+Tide\s+(\d{1,2}:\d{2}\s+[AP]M)\s+(?:PST|PDT|EST|CST|MST)?\s*([\d.-]+)\s*ft/gi;
        let match;
        while ((match = tideRegex.exec(allText)) !== null) {
            result.tides.push({
                type: match[1],
                time: match[2].trim(),
                height: parseFloat(match[3])
            });
        }

        // Get date
        const dateMatch = allText.match(/Today\s+(\w+\s+\d{1,2},\s+\d{4})/);
        if (dateMatch) result.date = dateMatch[1];

        // Get station name - look for text right after "Nearby Tides" heading
        const stationMatch = allText.match(/Nearby Tides[\s\S]*?\n\s*([A-Za-z][\w\s().'-]+?)\n/);
        if (stationMatch) result.station = stationMatch[1].trim();

        return result;
    },

    /**
     * Click the Sign In / Log In link
     */
    clickSignIn: function() {
        const links = [...document.querySelectorAll('a, button')];
        const signIn = links.find(el => /sign.?in|log.?in/i.test(el.textContent));
        if (signIn) signIn.click();
    },

    /**
     * Check if login form (password field) is still visible
     */
    isLoginFormVisible: function() {
        return !!document.querySelector('input[type="password"]:not([style*="display: none"])');
    },

    /**
     * Check if the page shows an error (401, etc.)
     */
    checkPageError: function() {
        const h2 = document.querySelector('h2');
        if (h2 && h2.textContent.includes('Sorry, there was a problem')) {
            const text = document.body.innerText;
            if (text.includes('401')) return '401';
            return 'error';
        }
        return null;
    },

    /**
     * Scroll through sections to trigger lazy loading
     * @param {string[]} sections - Array of section names to scroll to
     */
    scrollToSections: function(sections) {
        for (const name of sections) {
            const h = [...document.querySelectorAll('h2')].find(h => h.textContent.includes(name));
            if (h) h.scrollIntoView({block: 'start'});
        }
    },

    /**
     * Get spot name from page header
     */
    getSpotName: function() {
        const headers = document.querySelectorAll('h1');
        for (const h of headers) {
            const text = h.textContent.trim();
            if (text && text !== 'Search' && !text.includes('City, Zip')) {
                return text;
            }
        }
        // Fallback: page title
        const title = document.title;
        const m = title.match(/^(.+?)\s*\|/);
        return m ? m[1].trim() : 'Unknown';
    },

    /**
     * Scroll to a section by h2 heading text
     * @param {string} sectionName - Text to match in h2
     */
    scrollToSection: function(sectionName) {
        const h = [...document.querySelectorAll('h2')].find(h => h.textContent.includes(sectionName));
        if (h) h.scrollIntoView({block: 'start'});
    },

    /**
     * Click a forecast model button
     * @param {string} modelName - Model name prefix to match
     * @returns {boolean} - True if button was found and clicked
     */
    clickModel: function(modelName) {
        const ftHeader = [...document.querySelectorAll('h2')].find(h => h.textContent.includes('Forecast Table'));
        if (!ftHeader) return false;
        let container = ftHeader.parentElement;
        for (let i = 0; i < 5; i++) {
            const btns = container.querySelectorAll('button');
            const btn = [...btns].find(b => b.textContent.trim().startsWith(modelName));
            if (btn) { btn.click(); return true; }
            if (container.parentElement) container = container.parentElement;
        }
        return false;
    },

    /**
     * Get the currently active/selected model name
     * @returns {string|null} - Active model name or null
     */
    getActiveModel: function() {
        const ftHeader = [...document.querySelectorAll('h2')].find(h => h.textContent.includes('Forecast Table'));
        if (!ftHeader) return null;
        let container = ftHeader.parentElement;
        for (let i = 0; i < 5; i++) {
            // Active model button usually has a distinct style (filled bg, bold, etc.)
            const btns = container.querySelectorAll('button');
            for (const btn of btns) {
                const style = getComputedStyle(btn);
                const bg = style.backgroundColor;
                // Active buttons typically have a colored background
                if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent' && bg !== 'rgb(255, 255, 255)') {
                    const text = btn.textContent.trim().split('\n')[0].trim();
                    if (text && !text.includes('Daily') && !text.includes('7 Day') && !text.includes('Basic') && !text.includes('Detailed')) {
                        return text;
                    }
                }
            }
            if (container.parentElement) container = container.parentElement;
        }
        // Fallback: check the model description line
        const desc = container ? container.innerText : '';
        const m = desc.match(/(BLEND|Beta-WRF|iK-WRF|iK-TRRM|iK-HRRR|NAM|GFS|ICON|WW3)[^\n]*/);
        return m ? m[1] : null;
    }
};

