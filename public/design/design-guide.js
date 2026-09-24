/* Agnes Studio Visual Spec · interactions */
(function () {
  const toast = document.getElementById("toast");
  let toastTimer = null;

  function showToast(msg) {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 1600);
  }

  async function copyText(text) {
    try {
      if (navigator.clipboard && window.isSecureContext !== false) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.left = "-9999px";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        ta.remove();
      }
      showToast("已复制 " + text);
    } catch (e) {
      showToast("复制失败，请手动选择");
    }
  }

  document.querySelectorAll("[data-copy]").forEach((el) => {
    el.addEventListener("click", () => copyText(el.getAttribute("data-copy") || ""));
  });

  function bindZoneToggle(toggleId, frameIds) {
    const toggle = document.getElementById(toggleId);
    if (!toggle) return;
    const apply = () => {
      frameIds.forEach((id) => {
        const frame = document.getElementById(id);
        if (!frame) return;
        frame.classList.toggle("zones-off", !toggle.checked);
      });
    };
    toggle.addEventListener("change", apply);
    apply();
  }

  bindZoneToggle("toggleWxZones", ["frameWxMain", "frameWxSq"]);
  bindZoneToggle("toggleXhsZones", ["frameXhsMain", "frameXhsSq"]);

  const navToggle = document.getElementById("navToggle");
  const nav = document.querySelector(".nav");
  if (navToggle && nav) {
    navToggle.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    nav.querySelectorAll("a").forEach((a) => {
      a.addEventListener("click", () => {
        nav.classList.remove("open");
        navToggle.setAttribute("aria-expanded", "false");
      });
    });
  }
})();
