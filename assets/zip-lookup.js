/* ZIP check for near.html. The crosswalk is fetched once; the ZIP is not posted anywhere else. */
(function () {
  var form = document.getElementById("zip-form");
  var out = document.getElementById("zip-result");
  if (!form || !out) return;

  var SIZES = { "5x5": 1, "5x10": 1, "10x10": 1, "10x15": 1, "10x20": 1 };
  var dataPromise = null;

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  function money(n) {
    return "$" + Number(n).toLocaleString("en-US");
  }

  function load() {
    if (!dataPromise) {
      dataPromise = fetch("data/zip-lookup.json").then(function (res) {
        if (!res.ok) throw new Error("load");
        return res.json();
      });
    }
    return dataPromise;
  }

  function params() {
    return new URLSearchParams(window.location.search);
  }

  function keepHidden() {
    var query = params();
    ["from", "size"].forEach(function (name) {
      var field = form.querySelector('[name="' + name + '"]');
      if (field && query.get(name)) field.value = query.get(name);
    });
    var zip = query.get("zip");
    if (zip && /^\d{5}$/.test(zip)) {
      var input = form.querySelector('[name="zip"]');
      if (input) input.value = zip;
    }
  }

  function parseRow(row) {
    return {
      slug: row[0] || "",
      pct: row[1],
      place: row[2] || "",
      state: row[3] || "",
      near: row[4] || [],
      overlap: row[5] || [],
      others: row[6] || []
    };
  }

  function city(data, slug) {
    return data.cities[slug] || null;
  }

  function validSlug(data, slug) {
    return /^[a-z0-9]+(?:-[a-z0-9]+)+$/.test(slug) && !!data.cities[slug];
  }

  function placeLabel(info, data) {
    if (info.slug) {
      var known = city(data, info.slug);
      if (known && known.short && known.short !== info.place) {
        return info.place + " (our " + known.short + " page)";
      }
      return known ? known.short : info.place;
    }
    return info.place;
  }

  function addLink(parent, href, className, text) {
    var link = el("a", className, text);
    link.href = href;
    parent.appendChild(link);
    return link;
  }

  function limitation(parent) {
    var note = el("p", "note");
    note.appendChild(el("strong", null, "Limitation. "));
    note.appendChild(document.createTextNode(
      "Dollar figures on this result are city averages, or named-area street rates copied from a cited source. Nothing here is a quote for this ZIP."
    ));
    parent.appendChild(note);
  }

  function rateLine(data, slug) {
    var info = city(data, slug);
    if (!info) return "";
    var bits = [];
    if (info.rate != null) bits.push("10x10 advertised " + money(info.rate));
    if (info.true != null) bits.push("six-month true average ~" + money(info.true));
    return bits.join(" · ");
  }

  function pageSet(info) {
    var slugs = [];
    function add(slug) {
      if (slug && slugs.indexOf(slug) === -1) slugs.push(slug);
    }
    add(info.slug);
    info.overlap.forEach(function (item) { add(item[0]); });
    info.near.forEach(function (item) { add(item[0]); });
    return slugs;
  }

  function lowestSlug(data, slugs) {
    var best = "";
    var bestTrue = null;
    slugs.forEach(function (slug) {
      var info = city(data, slug);
      if (!info || info.true == null) return;
      if (bestTrue == null || info.true < bestTrue) {
        best = slug;
        bestTrue = info.true;
      }
    });
    return best;
  }

  function renderBands(parent, data, slug) {
    var band = data.bands && data.bands[slug];
    if (!band) {
      parent.appendChild(el("p", null, "Neighborhood street rates are not on file for this city. The city page is the city average."));
      return;
    }
    var unit = band.unit === "10x10"
      ? "These are 10x10 street rates"
      : band.unit === "standard unit"
        ? "These are street rates for what StorageCafe calls a standard unit"
        : "The sentence we copied does not name the unit size";
    parent.appendChild(el("h3", null, "Area examples StorageCafe published (" + band.asof + ")"));
    parent.appendChild(el("p", null, unit + ", copied from that city statistics page. They show the spread between named areas. Your ZIP is not matched to any of these areas, and these are not the six-month true cost."));
    var grid = el("div", "band-grid");
    [["Lower-priced areas they named", band.lower], ["Higher-priced areas they named", band.higher], ["Also cited", band.also || []]].forEach(function (pair) {
      if (!pair[1] || !pair[1].length) return;
      var col = el("div");
      col.appendChild(el("h4", null, pair[0]));
      var list = el("ul");
      pair[1].forEach(function (item) {
        var li = el("li");
        li.appendChild(el("span", "band-name", item.name));
        li.appendChild(el("span", "band-rate", item.rate));
        list.appendChild(li);
      });
      col.appendChild(list);
      grid.appendChild(col);
    });
    parent.appendChild(grid);
    (band.aside || []).forEach(function (sentence) {
      parent.appendChild(el("p", null, sentence));
    });
    if (band.source_url && /^https:\/\//.test(band.source_url)) {
      var src = el("p", "small");
      src.appendChild(document.createTextNode("Source: "));
      var link = el("a", null, band.source_label || "StorageCafe");
      link.href = band.source_url;
      link.rel = "nofollow noopener";
      link.target = "_blank";
      src.appendChild(link);
      parent.appendChild(src);
    }
  }

  function renderCityList(parent, data, items, lowest, referenceSlug, several) {
    var list = el("ul", "near-cities");
    items.forEach(function (item) {
      var slug = item[0];
      var info = city(data, slug);
      if (!info) return;
      var li = el("li");
      addLink(li, "cities/" + slug + ".html", null, info.name);
      var detail = [];
      if (item.length === 3) detail.push("about " + item[1] + "% of the land, " + item[2] + " straight-line miles");
      else detail.push(item[1] + " straight-line miles");
      var rates = rateLine(data, slug);
      if (rates) detail.push(rates);
      li.appendChild(el("span", null, detail.join(" · ")));
      if (several && slug === lowest && lowest !== referenceSlug) {
        li.appendChild(el("span", "band-note", "Lowest six-month city average among these published pages."));
      }
      list.appendChild(li);
    });
    if (list.childNodes.length) parent.appendChild(list);
  }

  function render(data, zip, query) {
    out.textContent = "";
    var row = data.zips[zip];
    var from = query.get("from") || "";
    var size = query.get("size") || "";
    if (!SIZES[size]) size = "";
    if (!validSlug(data, from)) from = "";

    if (!row) {
      out.appendChild(el("h3", null, zip + " is not in the 2020 crosswalk"));
      limitation(out);
      out.appendChild(el("p", null, "This five-digit code is not in the Census 2020 ZIP Code Tabulation Area file we use. PO Box and unique ZIP codes are often missing, and new codes can lag. We will not guess a city from a nearby number, and we will not guess a price."));
      if (from) {
        var back = el("p");
        back.appendChild(document.createTextNode("You can still read the "));
        addLink(back, "cities/" + from + ".html", null, city(data, from).name + " page");
        back.appendChild(document.createTextNode(", which stays a city average."));
        out.appendChild(back);
      }
      return;
    }

    var info = parseRow(row);
    var matched = info.slug ? city(data, info.slug) : null;
    var where = placeLabel(info, data);
    var stateName = matched ? matched.state_name : (info.state || "");

    out.appendChild(el("h3", null, "ZIP " + zip));
    limitation(out);

    if (matched) {
      var lead = el("p");
      lead.appendChild(document.createTextNode(
        "About " + info.pct + "% of this Census area’s land is in " + where +
        (stateName ? ", " + stateName : "") + ". "
      ));
      lead.appendChild(document.createTextNode("That is enough to open the " + matched.name + " page. The rates there are the city average."));
      out.appendChild(lead);
      if (info.others.length) {
        var also = info.others.map(function (place) {
          return place[0] + " (about " + place[2] + "%)";
        }).join("; ");
        out.appendChild(el("p", null, "Other Census places with a large share of the same area: " + also + ". We do not publish separate pages or prices for those places."));
      }
      var figs = el("div", "keyfigs");
      if (matched.rate != null) {
        var adv = el("div");
        adv.appendChild(el("span", "k", "10x10 city average"));
        adv.appendChild(el("span", "v", money(matched.rate)));
        figs.appendChild(adv);
      }
      if (matched.true != null) {
        var tru = el("div", "primary");
        tru.appendChild(el("span", "k", "6-month true average"));
        tru.appendChild(el("span", "v", "~" + money(matched.true)));
        figs.appendChild(tru);
      }
      out.appendChild(figs);
      var actions = el("div", "quiz-actions");
      var sizeHref = "cities/" + info.slug + ".html" + (size ? "#size-" + size : "#prices");
      addLink(actions, sizeHref, "btn solid", size ? "See the " + size + " row in " + matched.short : "Open the " + matched.short + " city page");
      addLink(actions, "cities/" + info.slug + ".html#compare", "btn", "Find storage in " + matched.short);
      out.appendChild(actions);
      renderBands(out, data, info.slug);
    } else {
      var none = el("p");
      if (info.place) {
        none.appendChild(document.createTextNode(
          "The largest Census place in " + zip + " is " + info.place +
          (info.state ? ", " + info.state : "") + ", about " + info.pct + "% of the land. "
        ));
      }
      none.appendChild(document.createTextNode("No published city contains about half or more of this area, so there is no city average to assign to it."));
      out.appendChild(none);
      if (info.others.length) {
        out.appendChild(el("p", null, "Other Census places in the same area: " + info.others.map(function (place) {
          return place[0] + " (about " + place[2] + "%)";
        }).join("; ") + "."));
      }
    }

    if (from && city(data, from)) {
      var fromCity = city(data, from);
      if (info.slug === from) {
        out.appendChild(el("p", null, "You were already on the " + fromCity.short + " page. Stay there for the city average."));
      } else if (info.slug) {
        out.appendChild(el("p", null, "You came from the " + fromCity.name + " page. This ZIP’s land-area match is " + matched.name + "."));
      } else {
        out.appendChild(el("p", null, "You came from the " + fromCity.name + " page. This ZIP is not a land-area match for that city."));
      }
    }

    var pages = pageSet(info);
    var lowest = lowestSlug(data, pages);
    var several = pages.length > 1;
    if (info.overlap.length) {
      out.appendChild(el("h3", null, "Published cities that cover part of this area"));
      out.appendChild(el("p", null, "Land share is the portion of this Census area inside that city. Miles are straight-line, from Census internal points, not drive time. The city page is still that city’s average."));
      renderCityList(out, data, info.overlap, lowest, info.slug, several);
    }

    if (info.near.length) {
      out.appendChild(el("h3", null, "Other published cities within 60 straight-line miles"));
      out.appendChild(el("p", null, "A lower city average helps only if you can use a facility in that city. It is not a discount at this ZIP."));
      renderCityList(out, data, info.near, lowest, info.slug, several);
      if (several && info.slug && lowest === info.slug) {
        out.appendChild(el("p", "small", matched.short + " has the lowest six-month city average among the published pages within 60 miles."));
      }
    } else if (!info.slug && !info.overlap.length) {
      out.appendChild(el("p", null, "No published city page is within 60 straight-line miles. We will not borrow a rate from farther away."));
    }

    var foot = el("p", "small");
    foot.appendChild(document.createTextNode("Geography: Census Bureau 2020 ZCTA-to-place relationship file and Gazetteer internal points. A ZCTA approximates a USPS ZIP code. "));
    if (size) foot.appendChild(document.createTextNode("The size you picked was " + size + ". "));
    foot.appendChild(document.createTextNode("Find storage on a city page opens Neighbor’s public listings, marked sponsored, with no tracking parameters."));
    out.appendChild(foot);
  }

  function show(message) {
    out.textContent = "";
    out.appendChild(el("p", null, message));
  }

  function run() {
    keepHidden();
    var zip = (params().get("zip") || "").replace(/\D/g, "");
    if (!zip) return;
    if (!/^\d{5}$/.test(zip)) {
      show("Enter a five-digit ZIP code. We will not guess from a partial one.");
      return;
    }
    show("Checking " + zip + " against the Census crosswalk…");
    load().then(function (data) {
      render(data, zip, params());
    }).catch(function () {
      show("The ZIP crosswalk did not load. Refresh the page and try again. We will not guess a city without it.");
    });
  }

  run();
})();
