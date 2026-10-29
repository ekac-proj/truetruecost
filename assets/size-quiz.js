/* Size quiz for size-guide.html. Runs entirely in the browser; nothing is sent. */
(function (factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (typeof document !== "undefined") mount(api);
})(function () {
  var ORDER = ["5x5", "5x10", "10x10", "10x15", "10x20"];
  var BASE = { boxes: 0, studio: 1, br1: 2, br2: 3, br3: 4 };

  var FIT = {
    "5x5": {
      sq: "25 sq ft",
      like: "a large walk-in closet",
      fits: "Boxes, suitcases, a small dresser, seasonal decor. You reach in from the door."
    },
    "5x10": {
      sq: "50 sq ft",
      like: "a walk-in closet",
      fits: "A mattress and box spring on end, a dresser, a bike, and boxes — or a motorcycle and gear."
    },
    "10x10": {
      sq: "100 sq ft",
      like: "a small bedroom",
      fits: "Furniture from a one-bedroom: bed, dresser, sofa, a broken-down table, and boxes."
    },
    "10x15": {
      sq: "150 sq ft",
      like: "a large bedroom",
      fits: "A two-bedroom apartment: two beds, a living room, a dining set, and boxes."
    },
    "10x20": {
      sq: "200 sq ft",
      like: "a one-car garage",
      fits: "A three-bedroom's furniture, or a car. A sedan uses the length."
    }
  };

  var WHY = {
    "boxes|light": "A few boxes and small items fit a 5x5. Treat it like a closet: you unload from the doorway.",
    "boxes|typical": "A closet's worth of boxes, bags, and one small piece of furniture is a 5x5. If a mattress is coming too, use a 5x10.",
    "boxes|packed": "A dresser, a bike, or more than a closet of boxes is easier to use in a 5x10.",
    "studio|light": "If the bed and sofa stay behind, a studio's leftovers usually fit a 5x5.",
    "studio|typical": "A studio's bed, a few pieces, and boxes are the usual 5x10. You will stack, and you may not have an aisle.",
    "studio|packed": "A furnished studio, or a studio plus room to walk in, is a 10x10 — the same footprint as a small bedroom.",
    "br1|light": "Part of a one-bedroom — boxes and the pieces that are not staying in the apartment — often fits a 5x10.",
    "br1|typical": "A one-bedroom's furniture is the most common 10x10: bed, dresser, sofa, a broken-down table, and boxes.",
    "br1|packed": "A one-bedroom with appliances, a home office, or a second sofa is more comfortable in a 10x15.",
    "br2|light": "If one bedroom's furniture stays in use, the rest of a two-bedroom often fits a 10x10.",
    "br2|typical": "Two bedrooms plus a living room is a 10x15. Stand mattresses on end and break the table down.",
    "br2|packed": "A packed two-bedroom — appliances, extra seating, and boxes with an aisle — is a 10x20.",
    "br3|light": "If you are storing one or two rooms of a three-bedroom, not the whole house, start with a 10x15.",
    "br3|typical": "A three-bedroom household of furniture is a 10x20, about a one-car garage. What stays in the kitchen usually stays there.",
    "br3|packed": "A full three-bedroom with appliances can fill a 10x20 with no aisle. That is the largest size these pages price. A second, smaller unit is often a clearer choice than a size we do not list.",
    "vehicle|light": "A motorcycle, bikes, or a season of patio and holiday gear usually fits a 5x10. A car does not — a car needs a 10x20.",
    "vehicle|typical": "A car needs the length of a 10x20. A modest stack of boxes can share it. A whole apartment on top of the car usually cannot.",
    "vehicle|packed": "A car plus household goods still starts at a 10x20, and it will be tight. Price the 10x20. If the quote is only for the vehicle, a few boxes do not require a second unit."
  };

  var CLIMATE = {
    standard: "Standard (non-climate) matches what you described. City pages price that kind of unit, unless a note on the row says otherwise.",
    climate: "Climate control does not change this footprint. It usually costs more than the non-climate rate on the city page. Wood, electronics, photos, fabric, and instruments are the usual reasons to ask for it. Type the real quote into that city's calculator — a later increase applies to the higher rent, not to the first-month promo.",
    unsure: "If the load includes wood, electronics, photos, fabric, or instruments, ask the facility for a climate-controlled price and compare that quote. Otherwise use the non-climate row. The size stays the same either way."
  };

  var TRUE_COST = "Size changes the true cost in two directions. A larger unit means a higher monthly rent, so the increase a few months later is a larger dollar amount. A smaller unit still picks up the same kind of one-time admin fee and monthly protection plan, which can be a large share of a 5x5. On a city page, read the six-month true average for this size — not the first month on the sign.";

  var WHAT = {
    id: "what",
    prompt: "What are you storing?",
    options: [
      { id: "boxes", label: "Boxes and small items", hint: "Closet overflow, not a room of furniture" },
      { id: "studio", label: "A studio apartment", hint: "Bed, a few pieces, and boxes" },
      { id: "br1", label: "A one-bedroom apartment", hint: "One bedroom plus living-room furniture" },
      { id: "br2", label: "A two-bedroom apartment", hint: "Two bedrooms, a living room, and boxes" },
      { id: "br3", label: "A three-bedroom home", hint: "Most of a household of furniture" },
      { id: "vehicle", label: "A car or seasonal gear", hint: "A vehicle, or patio, holiday, and sports equipment" }
    ]
  };

  var CLIMATE_Q = {
    id: "climate",
    prompt: "Do you need climate control?",
    options: [
      { id: "standard", label: "Standard is fine", hint: "Boxes, metal, plastic, outdoor gear" },
      { id: "climate", label: "Yes — climate control", hint: "Wood, electronics, photos, fabric, instruments, paperwork" },
      { id: "unsure", label: "Not sure", hint: "You can price both once you have a city and a quote" }
    ]
  };

  function howQuestion(what) {
    if (what === "vehicle") {
      return {
        id: "how",
        prompt: "Roughly how much?",
        options: [
          { id: "light", label: "A motorcycle or seasonal gear", hint: "Bikes, a patio set, holiday decor, sports equipment — no car" },
          { id: "typical", label: "A car", hint: "A sedan, plus maybe a few boxes" },
          { id: "packed", label: "A car and household goods", hint: "The vehicle plus furniture, or a lot of boxes" }
        ]
      };
    }
    if (what === "boxes") {
      return {
        id: "how",
        prompt: "Roughly how much?",
        options: [
          { id: "light", label: "A few boxes", hint: "Suitcases, files, seasonal decor" },
          { id: "typical", label: "A closet's worth", hint: "Boxes plus a small dresser, or a bike" },
          { id: "packed", label: "More than a closet", hint: "Several small pieces, still not a whole room" }
        ]
      };
    }
    return {
      id: "how",
      prompt: "Roughly how much of it?",
      options: [
        { id: "light", label: "Only part of it", hint: "The big furniture stays in use; you are storing the rest" },
        { id: "typical", label: "The usual amount", hint: "The furniture and boxes you would expect for that home" },
        { id: "packed", label: "Packed, with room to walk", hint: "Appliances, extra pieces, or you want an aisle" }
      ]
    };
  }

  function recommend(answers) {
    if (!answers || !answers.what || !answers.how) return "";
    if (answers.what === "vehicle") return answers.how === "light" ? "5x10" : "10x20";
    var i = BASE[answers.what];
    if (i == null) return "";
    if (answers.how === "light") i -= 1;
    if (answers.how === "packed") i += 1;
    if (i < 0) i = 0;
    if (i > 4) i = 4;
    return ORDER[i];
  }

  function explain(answers) {
    var size = recommend(answers);
    var fit = FIT[size] || { sq: "", like: "", fits: "" };
    return {
      size: size,
      sq: fit.sq,
      like: fit.like,
      fits: fit.fits,
      why: WHY[answers.what + "|" + answers.how] || "",
      climate: CLIMATE[answers.climate] || CLIMATE.unsure,
      trueCost: TRUE_COST
    };
  }

  function selfCheck() {
    var errors = [];
    var whats = ["boxes", "studio", "br1", "br2", "br3", "vehicle"];
    var hows = ["light", "typical", "packed"];
    var expect = {
      "boxes|light": "5x5", "boxes|typical": "5x5", "boxes|packed": "5x10",
      "studio|light": "5x5", "studio|typical": "5x10", "studio|packed": "10x10",
      "br1|light": "5x10", "br1|typical": "10x10", "br1|packed": "10x15",
      "br2|light": "10x10", "br2|typical": "10x15", "br2|packed": "10x20",
      "br3|light": "10x15", "br3|typical": "10x20", "br3|packed": "10x20",
      "vehicle|light": "5x10", "vehicle|typical": "10x20", "vehicle|packed": "10x20"
    };
    whats.forEach(function (w) {
      hows.forEach(function (h) {
        var key = w + "|" + h;
        var size = recommend({ what: w, how: h, climate: "climate" });
        if (size !== expect[key]) errors.push(key + " -> " + size);
        var info = explain({ what: w, how: h, climate: "standard" });
        if (!info.why || !info.fits || !info.climate) errors.push("copy " + key);
      });
    });
    if (recommend({ what: "nope", how: "light" })) errors.push("unknown what");
    return errors;
  }

  return {
    recommend: recommend,
    explain: explain,
    selfCheck: selfCheck,
    whatQuestion: WHAT,
    climateQuestion: CLIMATE_Q,
    howQuestion: howQuestion
  };
});

function mount(api) {
  var app = document.getElementById("quiz-app");
  if (!app) return;
  var answers = {};
  var step = 0;

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  function cityContext() {
    var params;
    try { params = new URLSearchParams(window.location.search); }
    catch (e) { return null; }
    var slug = params.get("city") || "";
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)+$/.test(slug)) return null;
    var name = (params.get("name") || "").replace(/\s+/g, " ").trim();
    if (!/^[A-Za-z0-9 .,'-]{2,48}$/.test(name)) name = labelFromSlug(slug);
    if (!name) return null;
    return { slug: slug, name: name };
  }

  function labelFromSlug(slug) {
    var parts = slug.split("-");
    var st = parts[parts.length - 1];
    if (!/^[a-z]{2}$/.test(st) || parts.length < 2) return "";
    var words = parts.slice(0, -1).map(function (word) {
      return word.charAt(0).toUpperCase() + word.slice(1);
    });
    return words.join(" ") + ", " + st.toUpperCase();
  }

  function questionAt(index) {
    if (index === 0) return api.whatQuestion;
    if (index === 1) return api.howQuestion(answers.what);
    return api.climateQuestion;
  }

  function focusHeading() {
    var heading = app.querySelector("h3");
    if (!heading) return;
    heading.tabIndex = -1;
    heading.focus();
  }

  function renderQuestion(moveFocus) {
    var q = questionAt(step);
    app.textContent = "";
    app.appendChild(el("p", "quiz-progress", "Question " + (step + 1) + " of 3"));
    var heading = el("h3", null, q.prompt);
    heading.id = "quiz-q";
    app.appendChild(heading);
    var group = el("div", "quiz-options");
    group.setAttribute("role", "group");
    group.setAttribute("aria-labelledby", "quiz-q");
    q.options.forEach(function (opt) {
      var button = el("button", "quiz-opt");
      button.type = "button";
      button.appendChild(el("strong", null, opt.label));
      button.appendChild(el("span", null, opt.hint));
      button.addEventListener("click", function (event) {
        answers[q.id] = opt.id;
        var byKeyboard = event.detail === 0;
        if (step < 2) {
          step += 1;
          renderQuestion(byKeyboard);
        } else {
          renderResult(byKeyboard);
        }
      });
      group.appendChild(button);
    });
    app.appendChild(group);
    if (step > 0) {
      var nav = el("div", "quiz-nav");
      var back = el("button", "calc-reset", "Back");
      back.type = "button";
      back.addEventListener("click", function (event) {
        step -= 1;
        renderQuestion(event.detail === 0);
      });
      nav.appendChild(back);
      app.appendChild(nav);
    }
    if (moveFocus) focusHeading();
  }

  function renderResult(moveFocus) {
    var info = api.explain(answers);
    var city = cityContext();
    app.textContent = "";
    app.appendChild(el("p", "quiz-progress", "Suggested size"));
    var heading = el("h3", null, "A " + info.size + " is the size to price");
    heading.id = "quiz-q";
    app.appendChild(heading);
    app.appendChild(el("p", "quiz-size", info.size));
    app.appendChild(el("p", null, info.sq + " · about " + info.like + "."));
    app.appendChild(el("p", null, info.why));
    var fits = el("p", null, "");
    fits.appendChild(el("strong", null, "What usually fits. "));
    fits.appendChild(document.createTextNode(info.fits));
    app.appendChild(fits);
    var climate = el("p", null, "");
    climate.appendChild(el("strong", null, "Climate. "));
    climate.appendChild(document.createTextNode(info.climate));
    app.appendChild(climate);
    var panel = el("div", "panel");
    panel.appendChild(el("p", null, info.trueCost));
    app.appendChild(panel);

    var actions = el("div", "quiz-actions");
    if (city) {
      actions.appendChild(el("a", "btn solid", "See " + info.size + " true cost in " + city.name)).href =
        "cities/" + city.slug + ".html#size-" + info.size;
      actions.appendChild(el("a", "btn", "Find storage in " + city.name)).href =
        "cities/" + city.slug + ".html#compare";
    } else {
      actions.appendChild(el("a", "btn solid", "Find storage in your city")).href = "index.html#cities";
    }
    actions.appendChild(el("a", "btn", "Check a ZIP for this size")).href = "near.html?size=" + info.size;
    var sizeField = document.getElementById("zip-size");
    if (sizeField) sizeField.value = info.size;
    var guideLink = el("a", "btn", "What fits in a " + info.size);
    guideLink.href = "#size-" + info.size;
    actions.appendChild(guideLink);
    app.appendChild(actions);

    app.appendChild(el("p", "small", "Find storage on a city page opens Neighbor’s public listings, marked sponsored, with no tracking parameters. We do not earn a commission on those clicks yet. It does not change this suggestion or the estimates."));

    var nav = el("div", "quiz-nav");
    var back = el("button", "calc-reset", "Back");
    back.type = "button";
    back.addEventListener("click", function (event) {
      renderQuestion(event.detail === 0);
    });
    var again = el("button", "calc-reset", "Start over");
    again.type = "button";
    again.addEventListener("click", function (event) {
      answers = {};
      step = 0;
      renderQuestion(event.detail === 0);
    });
    nav.appendChild(back);
    nav.appendChild(again);
    app.appendChild(nav);
    if (moveFocus) focusHeading();
  }

  renderQuestion(false);
}
