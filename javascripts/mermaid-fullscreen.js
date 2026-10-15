(() => {
  const SELECTOR = ".mermaid-fullscreen";

  function fullscreenElement() {
    return document.fullscreenElement || document.webkitFullscreenElement || null;
  }

  function requestFullscreen(element) {
    if (element.requestFullscreen) {
      return element.requestFullscreen();
    }
    if (element.webkitRequestFullscreen) {
      element.webkitRequestFullscreen();
    }
    return undefined;
  }

  function exitFullscreen() {
    if (document.exitFullscreen) {
      return document.exitFullscreen();
    }
    if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    }
    return undefined;
  }

  function updateButtons() {
    const active = fullscreenElement();
    document.querySelectorAll(`${SELECTOR} .mermaid-fullscreen__button`).forEach((button) => {
      const wrapper = button.closest(SELECTOR);
      const isActive = wrapper === active;
      button.textContent = isActive ? "Exit fullscreen" : "Fullscreen";
      button.setAttribute("aria-label", isActive ? "Exit diagram fullscreen" : "Open diagram fullscreen");
      button.setAttribute("aria-pressed", String(isActive));
    });
  }

  function initializeFullscreenDiagrams() {
    document.querySelectorAll(SELECTOR).forEach((wrapper) => {
      if (wrapper.dataset.fullscreenReady === "true") return;

      const button = document.createElement("button");
      button.type = "button";
      button.className = "mermaid-fullscreen__button";
      button.textContent = "Fullscreen";
      button.setAttribute("aria-label", "Open diagram fullscreen");
      button.setAttribute("aria-pressed", "false");

      button.addEventListener("click", async () => {
        try {
          if (fullscreenElement() === wrapper) {
            await exitFullscreen();
          } else {
            await requestFullscreen(wrapper);
          }
        } catch (error) {
          console.warn("Unable to toggle Mermaid fullscreen mode.", error);
        }
      });

      wrapper.appendChild(button);
      wrapper.dataset.fullscreenReady = "true";
    });

    updateButtons();
  }

  if (!window.__kgfeMermaidFullscreenListener) {
    document.addEventListener("fullscreenchange", updateButtons);
    document.addEventListener("webkitfullscreenchange", updateButtons);
    window.__kgfeMermaidFullscreenListener = true;
  }

  if (typeof document$ !== "undefined") {
    document$.subscribe(initializeFullscreenDiagrams);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeFullscreenDiagrams);
  } else {
    initializeFullscreenDiagrams();
  }
})();
