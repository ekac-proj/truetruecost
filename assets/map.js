/* Homepage state map. Reads the city groups written between CITY_LIST markers. */
(function () {
  var NAMES = {
    AL: "Alabama", AK: "Alaska", AZ: "Arizona", AR: "Arkansas", CA: "California",
    CO: "Colorado", CT: "Connecticut", DE: "Delaware", DC: "District of Columbia",
    FL: "Florida", GA: "Georgia", HI: "Hawaii", ID: "Idaho", IL: "Illinois",
    IN: "Indiana", IA: "Iowa", KS: "Kansas", KY: "Kentucky", LA: "Louisiana",
    ME: "Maine", MD: "Maryland", MA: "Massachusetts", MI: "Michigan", MN: "Minnesota",
    MS: "Mississippi", MO: "Missouri", MT: "Montana", NE: "Nebraska", NV: "Nevada",
    NH: "New Hampshire", NJ: "New Jersey", NM: "New Mexico", NY: "New York",
    NC: "North Carolina", ND: "North Dakota", OH: "Ohio", OK: "Oklahoma", OR: "Oregon",
    PA: "Pennsylvania", RI: "Rhode Island", SC: "South Carolina", SD: "South Dakota",
    TN: "Tennessee", TX: "Texas", UT: "Utah", VT: "Vermont", VA: "Virginia",
    WA: "Washington", WV: "West Virginia", WI: "Wisconsin", WY: "Wyoming"
  };

  var map = document.getElementById("us-map");
  var status = document.getElementById("map-status");
  if (!map || !status) return;

  var groups = Array.prototype.slice.call(document.querySelectorAll(".state-group"));
  var chips = Array.prototype.slice.call(document.querySelectorAll(".state-chips .chip"));
  var shapes = Array.prototype.slice.call(map.querySelectorAll("[data-state]"));
  var byCode = {};
  groups.forEach(function (g) { byCode[g.getAttribute("data-state")] = g; });

  shapes.forEach(function (el) {
    var code = el.getAttribute("data-state");
    var name = NAMES[code] || el.getAttribute("aria-label") || code;
    var group = byCode[code];
    if (group) {
      el.classList.add("has-cities");
      var n = group.querySelectorAll(".tile").length;
      el.setAttribute("aria-label", name + ", " + n + (n === 1 ? " city" : " cities"));
    } else {
      el.setAttribute("aria-label", name + ", no city pages yet");
    }
    el.addEventListener("click", function () { select(code); });
    el.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        select(code);
      }
    });
  });

  chips.forEach(function (btn) {
    btn.addEventListener("click", function () { select(btn.getAttribute("data-state")); });
  });

  var current = "";

  function setStatus(text, empty) {
    status.textContent = text;
    status.classList.toggle("is-empty", !!empty);
  }

  function clearFilter() {
    current = "";
    shapes.forEach(function (s) {
      s.classList.remove("is-active");
      s.setAttribute("aria-pressed", "false");
    });
    chips.forEach(function (c) {
      var on = c.getAttribute("data-state") === "*";
      c.classList.toggle("is-active", on);
      c.setAttribute("aria-pressed", on ? "true" : "false");
    });
    groups.forEach(function (g) { g.hidden = false; });
  }

  function select(code) {
    if (!code || code === "*") {
      clearFilter();
      setStatus("Showing every published city.", false);
      return;
    }
    var group = byCode[code];
    var name = (group && group.getAttribute("data-state-name")) || NAMES[code] || code;
    if (!group) {
      clearFilter();
      setStatus("No city pages for " + name + " yet.", true);
      return;
    }
    if (current === code) {
      clearFilter();
      setStatus("Showing every published city.", false);
      return;
    }
    current = code;
    shapes.forEach(function (s) {
      var on = s.getAttribute("data-state") === code;
      s.classList.toggle("is-active", on);
      s.setAttribute("aria-pressed", on ? "true" : "false");
    });
    chips.forEach(function (c) {
      var on = c.getAttribute("data-state") === code;
      c.classList.toggle("is-active", on);
      c.setAttribute("aria-pressed", on ? "true" : "false");
    });
    groups.forEach(function (g) { g.hidden = g.getAttribute("data-state") !== code; });
    var n = group.querySelectorAll(".tile").length;
    setStatus(name + " — " + n + (n === 1 ? " city page." : " city pages."), false);
    var heading = group.querySelector(".state-heading");
    if (heading) heading.focus({ preventScroll: true });
    group.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  clearFilter();
  setStatus("Showing every published city. Select a state to jump to that group.", false);
})();
