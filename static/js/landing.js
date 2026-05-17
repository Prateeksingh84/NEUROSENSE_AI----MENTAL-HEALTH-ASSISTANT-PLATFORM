/* ==========================================================================
   NeuroSense AI — Landing Page
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {

  initNavbarScroll();
  initSmoothReveal();
  initCounters();
  initParallax();
  initHeroTyping();
  initFloatingCards();
  initButtons();

});

/* ==========================================================================
   NAVBAR SCROLL
   ========================================================================== */

function initNavbarScroll(){

  const navbar = document.querySelector(".navbar");

  if(!navbar) return;

  window.addEventListener("scroll", () => {

    if(window.scrollY > 40){

      navbar.style.background =
        "rgba(7,7,15,.92)";

      navbar.style.backdropFilter =
        "blur(20px)";

      navbar.style.borderBottom =
        "1px solid rgba(255,255,255,.08)";

    }else{

      navbar.style.background =
        "rgba(7,7,15,.72)";

      navbar.style.borderBottom =
        "1px solid rgba(255,255,255,.04)";
    }

  });

}

/* ==========================================================================
   REVEAL ANIMATION
   ========================================================================== */

function initSmoothReveal(){

  const revealItems = document.querySelectorAll(
    ".feature-card, .step-card, .hero-card, .cta, .section-title"
  );

  if(!revealItems.length) return;

  const observer = new IntersectionObserver(
    (entries) => {

      entries.forEach((entry) => {

        if(entry.isIntersecting){

          entry.target.style.opacity = "1";

          entry.target.style.transform =
            "translateY(0px)";

        }

      });

    },
    {
      threshold:0.15
    }
  );

  revealItems.forEach((item) => {

    item.style.opacity = "0";

    item.style.transform =
      "translateY(40px)";

    item.style.transition =
      "all .7s ease";

    observer.observe(item);

  });

}

/* ==========================================================================
   COUNTERS
   ========================================================================== */

function initCounters(){

  const counters = document.querySelectorAll(
    "[data-counter]"
  );

  if(!counters.length) return;

  const observer = new IntersectionObserver(
    (entries) => {

      entries.forEach((entry) => {

        if(entry.isIntersecting){

          animateCounter(entry.target);

          observer.unobserve(entry.target);

        }

      });

    },
    {
      threshold:0.6
    }
  );

  counters.forEach((counter) => {

    observer.observe(counter);

  });

}

function animateCounter(el){

  const target = parseInt(
    el.dataset.counter || "0"
  );

  const duration = 1800;

  const start = 0;

  const startTime = performance.now();

  function update(now){

    const elapsed = now - startTime;

    const progress = Math.min(
      elapsed / duration,
      1
    );

    const eased =
      1 - Math.pow(1 - progress, 3);

    const value = Math.floor(
      eased * target
    );

    el.textContent =
      value.toLocaleString();

    if(progress < 1){

      requestAnimationFrame(update);

    }

  }

  requestAnimationFrame(update);

}

/* ==========================================================================
   PARALLAX
   ========================================================================== */

function initParallax(){

  const hero = document.querySelector(".hero");

  if(!hero) return;

  const blobs = document.querySelectorAll(
    ".bg-blur"
  );

  window.addEventListener("mousemove", (e) => {

    const x =
      e.clientX / window.innerWidth;

    const y =
      e.clientY / window.innerHeight;

    blobs.forEach((blob, index) => {

      const speed =
        (index + 1) * 25;

      blob.style.transform =
        `translate(${x * speed}px, ${y * speed}px)`;

    });

  });

}

/* ==========================================================================
   HERO TYPING EFFECT
   ========================================================================== */

function initHeroTyping(){

  const target =
    document.querySelector(
      "[data-typing]"
    );

  if(!target) return;

  const phrases = [
    "AI Mental Health Assistant",
    "Emotion Aware Conversations",
    "Voice & Sign AI Therapy",
    "Wellness Analytics Platform"
  ];

  let phraseIndex = 0;
  let charIndex = 0;
  let deleting = false;

  function type(){

    const current =
      phrases[phraseIndex];

    if(!deleting){

      target.textContent =
        current.substring(0, charIndex + 1);

      charIndex++;

      if(charIndex === current.length){

        deleting = true;

        setTimeout(type, 1800);

        return;
      }

    }else{

      target.textContent =
        current.substring(0, charIndex - 1);

      charIndex--;

      if(charIndex === 0){

        deleting = false;

        phraseIndex =
          (phraseIndex + 1) % phrases.length;
      }

    }

    setTimeout(
      type,
      deleting ? 45 : 90
    );

  }

  type();

}

/* ==========================================================================
   FLOATING CARD EFFECT
   ========================================================================== */

function initFloatingCards(){

  const cards = document.querySelectorAll(
    ".feature-card, .hero-card"
  );

  cards.forEach((card) => {

    card.addEventListener("mousemove", (e) => {

      const rect =
        card.getBoundingClientRect();

      const x =
        e.clientX - rect.left;

      const y =
        e.clientY - rect.top;

      const centerX =
        rect.width / 2;

      const centerY =
        rect.height / 2;

      const rotateX =
        ((y - centerY) / centerY) * -6;

      const rotateY =
        ((x - centerX) / centerX) * 6;

      card.style.transform =
        `
        perspective(1000px)
        rotateX(${rotateX}deg)
        rotateY(${rotateY}deg)
        translateY(-5px)
        `;
    });

    card.addEventListener("mouseleave", () => {

      card.style.transform =
        `
        perspective(1000px)
        rotateX(0deg)
        rotateY(0deg)
        translateY(0px)
        `;

    });

  });

}

/* ==========================================================================
   BUTTON RIPPLE
   ========================================================================== */

function initButtons(){

  const buttons = document.querySelectorAll(
    ".btn-primary, .btn-secondary"
  );

  buttons.forEach((btn) => {

    btn.addEventListener("click", (e) => {

      const ripple =
        document.createElement("span");

      const rect =
        btn.getBoundingClientRect();

      const size =
        Math.max(rect.width, rect.height);

      ripple.style.width =
        ripple.style.height =
        `${size}px`;

      ripple.style.left =
        `${e.clientX - rect.left - size / 2}px`;

      ripple.style.top =
        `${e.clientY - rect.top - size / 2}px`;

      ripple.style.position = "absolute";

      ripple.style.borderRadius = "50%";

      ripple.style.background =
        "rgba(255,255,255,.35)";

      ripple.style.transform =
        "scale(0)";

      ripple.style.animation =
        "ripple .6s linear";

      ripple.style.pointerEvents =
        "none";

      btn.style.position = "relative";

      btn.style.overflow = "hidden";

      btn.appendChild(ripple);

      setTimeout(() => {

        ripple.remove();

      }, 600);

    });

  });

}

/* ==========================================================================
   GLOBAL RIPPLE STYLE
   ========================================================================== */

const style =
document.createElement("style");

style.innerHTML = `
@keyframes ripple{
  to{
    transform:scale(4);
    opacity:0;
  }
}
`;

document.head.appendChild(style);

/* ==========================================================================
   SCROLL TO TOP
   ========================================================================== */

const scrollBtn =
document.createElement("button");

scrollBtn.innerHTML = "↑";

scrollBtn.className =
  "scroll-top-btn";

document.body.appendChild(scrollBtn);

scrollBtn.style.cssText = `
position:fixed;
right:24px;
bottom:24px;
width:52px;
height:52px;
border:none;
border-radius:18px;
background:linear-gradient(135deg,#7c6fff,#9f8dff);
color:#fff;
font-size:1.2rem;
font-weight:800;
cursor:pointer;
opacity:0;
pointer-events:none;
transition:.25s;
z-index:9999;
box-shadow:0 15px 40px rgba(0,0,0,.35);
`;

window.addEventListener("scroll", () => {

  if(window.scrollY > 400){

    scrollBtn.style.opacity = "1";

    scrollBtn.style.pointerEvents =
      "auto";

  }else{

    scrollBtn.style.opacity = "0";

    scrollBtn.style.pointerEvents =
      "none";
  }

});

scrollBtn.addEventListener("click", () => {

  window.scrollTo({
    top:0,
    behavior:"smooth"
  });

});

/* ==========================================================================
   PRELOADER
   ========================================================================== */

window.addEventListener("load", () => {

  const preloader =
    document.querySelector(".preloader");

  if(preloader){

    preloader.style.opacity = "0";

    preloader.style.pointerEvents =
      "none";

    setTimeout(() => {

      preloader.remove();

    }, 500);
  }

});

/* ==========================================================================
   DEMO DASHBOARD ANIMATION
   ========================================================================== */

const bars =
document.querySelectorAll(".bar-fill");

bars.forEach((bar, index) => {

  const width =
    bar.dataset.width || "80";

  bar.style.width = "0%";

  setTimeout(() => {

    bar.style.transition =
      "width 1.2s ease";

    bar.style.width =
      `${width}%`;

  }, 500 + index * 150);

});

/* ==========================================================================
   FEATURE CARD GLOW
   ========================================================================== */

document.querySelectorAll(
  ".feature-card"
).forEach((card) => {

  card.addEventListener(
    "mousemove",
    (e) => {

      const rect =
        card.getBoundingClientRect();

      const x =
        e.clientX - rect.left;

      const y =
        e.clientY - rect.top;

      card.style.background =
        `
        radial-gradient(
          circle at ${x}px ${y}px,
          rgba(124,111,255,.14),
          rgba(20,24,39,.92)
        )
        `;
    }
  );

  card.addEventListener(
    "mouseleave",
    () => {

      card.style.background =
        "rgba(20,24,39,.92)";
    }
  );

});