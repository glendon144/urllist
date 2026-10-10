/* On-screen text size controls. Slider release saves the size and reloads. */
(function () {
  var KEY = "urlListTextSize";
  var MIN = 12;
  var MAX = 28;
  var DEFAULT = 16;

  function clamp(n) {
    return Math.min(MAX, Math.max(MIN, n));
  }

  function apply(px) {
    document.body.style.fontSize = px + "px";
    var slider = document.getElementById("text-size-slider");
    if (slider) {
      slider.value = px;
    }
  }

  function load() {
    var saved = parseInt(localStorage.getItem(KEY), 10);
    return isNaN(saved) ? DEFAULT : clamp(saved);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var slider = document.getElementById("text-size-slider");
    var smaller = document.getElementById("text-smaller");
    var larger = document.getElementById("text-larger");
    var size = load();
    apply(size);

    function setSize(px, reload) {
      size = clamp(px);
      apply(size);
      try {
        localStorage.setItem(KEY, String(size));
      } catch (e) {
        /* storage unavailable; size still applies until reload */
      }
      if (reload) {
        window.location.reload();
      }
    }

    if (slider) {
      slider.addEventListener("input", function () {
        setSize(parseInt(slider.value, 10), false);
      });
      slider.addEventListener("change", function () {
        setSize(parseInt(slider.value, 10), true);
      });
    }
    if (smaller) {
      smaller.addEventListener("click", function () {
        setSize(size - 1, false);
      });
    }
    if (larger) {
      larger.addEventListener("click", function () {
        setSize(size + 1, false);
      });
    }
  });
})();
