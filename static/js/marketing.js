(function () {
  const ease = "cubic-bezier(0.4, 0, 0.2, 1)";
  const nav = document.querySelector("[data-mkt-nav]");
  const menu = document.querySelector("[data-mkt-menu]");
  const panel = document.querySelector(".mkt-nav-panel");

  const updateNav = () => {
    if (!nav) return;
    nav.classList.toggle("is-scrolled", window.scrollY > 18);
  };

  updateNav();
  window.addEventListener("scroll", updateNav, { passive: true });

  if (menu && panel) {
    menu.addEventListener("click", () => {
      panel.classList.toggle("is-open");
    });
  }

  const reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.16, rootMargin: "0px 0px -40px 0px" }
    );

    reveals.forEach((item) => observer.observe(item));
  } else {
    reveals.forEach((item) => item.classList.add("is-visible"));
  }

  const tilt = document.querySelector("[data-tilt] .mkt-window");
  if (tilt && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const parent = tilt.closest("[data-tilt]");
    parent.addEventListener("mousemove", (event) => {
      const rect = parent.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width - 0.5;
      const y = (event.clientY - rect.top) / rect.height - 0.5;
      tilt.style.transition = "transform 120ms " + ease;
      tilt.style.transform = `rotateX(${y * -7}deg) rotateY(${x * 9}deg) translateY(-3px)`;
    });

    parent.addEventListener("mouseleave", () => {
      tilt.style.transition = "transform 320ms " + ease;
      tilt.style.transform = "";
    });
  }

  const parallaxItems = document.querySelectorAll("[data-parallax]");
  const updateParallax = () => {
    const y = window.scrollY;
    parallaxItems.forEach((item) => {
      const strength = Number(item.dataset.parallax || 0);
      item.style.transform = `translate3d(0, ${y * strength}px, 0) rotate(${item.classList.contains("mkt-ribbon-b") ? 18 : -16}deg)`;
    });
  };

  updateParallax();
  window.addEventListener("scroll", updateParallax, { passive: true });
})();
