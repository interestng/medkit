gsap.registerPlugin(ScrollTrigger);

document.addEventListener("DOMContentLoaded", () => {
    const canvas = document.getElementById("bg-canvas");
    const ctx = canvas.getContext("2d");

    // ==========================================
    // OPTICAL GAP ALIGNMENT
    // ==========================================
    // The video provided is slightly off-center mathematically.
    // The vertical gap between the 2 doors is exactly 48.5 pixels to the left
    // of the 1788x1156 mathematical center.
    // We calculate the object-fit: cover scale to offset the UI perfectly.
    const uiLayer = document.querySelector(".ui-layer");

    function alignToOpticalGap() {
        const imgW = 1788;
        const imgH = 1156;
        const offsetPx = -48.5; // Gap offset from true center

        // Calculate the object-fit: cover scaling multiplier
        const scaleX = window.innerWidth / imgW;
        const scaleY = window.innerHeight / imgH;
        const scale = Math.max(scaleX, scaleY);

        // Apply the exact offset multiplied by the scale to perfectly snap to the gap!
        const dynamicOffset = offsetPx * scale;
        uiLayer.style.transform = `translateX(${dynamicOffset}px)`;
    }

    // Align on load and window resize
    window.addEventListener("resize", alignToOpticalGap);

    // We will dynamically configure canvas size when the first frame loads
    // to match the exact aspect ratio of the extracted video frames.

    // Image Sequence Configuration
    const frameCount = 121; // Extracted 121 frames via OpenCV
    const currentFrame = index => (
        `assets/frames/${(index + 1).toString().padStart(4, '0')}.jpg`
    );

    const images = [];
    const sequence = {
        frame: 0
    };

    // Preload Images
    for (let i = 0; i < frameCount; i++) {
        const img = new Image();
        img.src = currentFrame(i);
        images.push(img);
    }

    // Render the exact frame requested by GSAP onto the canvas
    function render() {
        if (images[sequence.frame] && images[sequence.frame].complete) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(images[sequence.frame], 0, 0, canvas.width, canvas.height);
        }
    }

    // Initial render of first frame once it loads
    images[0].onload = () => {
        canvas.width = images[0].naturalWidth || 1788;
        canvas.height = images[0].naturalHeight || 1156;
        render();

        // Also refresh ScrollTrigger in case layout calculations were disrupted
        ScrollTrigger.refresh();
        alignToOpticalGap(); // Ensure perfectly aligned!
    };
    alignToOpticalGap(); // Ensure perfectly aligned!

    // ==========================================
    // GSAP ScrollTrigger Timeline
    // ==========================================

    // We calculate "openTime" frame - the moment in the sequence when the kit is fully opened.
    // For this 121 frame sequence, we'll assign the halfway point (~frame 60).
    const openFrame = Math.floor(frameCount * 0.5);

    const tl = gsap.timeline({
        scrollTrigger: {
            trigger: ".scroll-container",
            start: "top top",
            end: "bottom bottom",
            scrub: 0.5, // 0.5s smoothing creates butter-smooth scrubbing even on fast scrolls
            onUpdate: render // Force re-render on every GSAP tick
        }
    });

    // ==========================================
    // PHASE 1 & 2: Scrolling down, kit opens (frames 0 -> ~60)
    // ==========================================

    // Fade out Intro Title as user starts scrolling
    tl.to(".phase1-text", {
        autoAlpha: 0,
        y: -50,
        duration: 0.5
    }, "phase2");

    // Animate the image sequence `frame` property up to the open point
    tl.to(sequence, {
        frame: openFrame,
        snap: "frame", // Ensures we only hit whole integers for array indices
        ease: "none",
        duration: 2
    }, "phase2");

    // ==========================================
    // PHASE 3: Kit is fully open, pause sequence, show UI
    // ==========================================

    // Fade in the Interactive Navigation Grid
    tl.to(".phase3-ui", {
        autoAlpha: 1,
        y: 0,
        startAt: { y: 50 },
        duration: 0.5
    }, "phase3");

    // Dummy timeline padding to keep scroll active while sequence is paused
    tl.to({}, { duration: 1.5 }, "phase3");

    // ==========================================
    // PHASE 4: Scroll past buttons, close kit (frames ~60 -> 120)
    // ==========================================

    // Fade out the documentation grid
    tl.to(".phase3-ui", {
        autoAlpha: 0,
        y: -50,
        duration: 0.5
    }, "phase4");

    // Resume sequence animation to the end
    tl.to(sequence, {
        frame: frameCount - 1,
        snap: "frame",
        ease: "none",
        duration: 2
    }, "phase4");

    // ==========================================
    // PHASE 5: Bottom of page, Final CTA
    // ==========================================

    // Fade in the GitHub Call to Action
    tl.to(".phase5-cta", {
        autoAlpha: 1,
        y: 0,
        startAt: { y: 50 },
        duration: 0.5
    });
});
