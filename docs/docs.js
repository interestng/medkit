document.addEventListener('DOMContentLoaded', () => {
    // Select all syntax highlighted code blocks
    const codeBlocks = document.querySelectorAll('pre');

    codeBlocks.forEach(block => {
        // Ensure the pre block is relatively positioned to anchor the absolute child button
        if (window.getComputedStyle(block).position === 'static') {
            block.style.position = 'relative';
        }

        // Create the copy button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.innerText = 'Copy';
        copyBtn.setAttribute('aria-label', 'Copy code to clipboard');

        // Append to the pre block
        block.appendChild(copyBtn);

        // Add the click listener
        copyBtn.addEventListener('click', async () => {
            // Find the <code> element inside this <pre>
            const codeEl = block.querySelector('code');
            if (!codeEl) return;

            // Extract the raw text without HTML tags
            const textToCopy = codeEl.innerText;

            try {
                // Use the modern clipboard API
                await navigator.clipboard.writeText(textToCopy);

                // Visual feedback
                copyBtn.innerText = 'Copied!';
                copyBtn.classList.add('copied');

                // Reset after 2 seconds
                setTimeout(() => {
                    copyBtn.innerText = 'Copy';
                    copyBtn.classList.remove('copied');
                }, 2000);
            } catch (err) {
                console.error('Failed to copy to clipboard', err);
                copyBtn.innerText = 'Failed';
            }
        });
    });
});
