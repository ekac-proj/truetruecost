// Homepage US map. Published states come from the city groups --rebuild writes
// (section.state-block[data-state]). Nothing is fetched; file:// works.
(function(){
  var svg=document.getElementById("us-map");
  var status=document.getElementById("map-status");
  if(!svg) return;
  var blocks={};
  Array.prototype.forEach.call(document.querySelectorAll(".state-block[data-state]"), function(b){
    blocks[b.getAttribute("data-state")]=b;
  });
  var active=null;
  var reduce=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function summary(block){
    var name=block.querySelector(".state-name");
    var cities=Array.prototype.map.call(block.querySelectorAll(".tile .name"), function(n){return n.textContent;});
    var label=name?name.textContent:block.getAttribute("data-state");
    var n=cities.length;
    return label+" · "+n+" "+(n===1?"city":"cities")+": "+cities.join(", ");
  }
  function setStatus(text){ if(status) status.textContent=text; }
  function shapeFor(code){ return svg.querySelector('[data-state="'+code+'"]'); }

  function clear(dropHash){
    if(active){
      active.classList.remove("is-active");
      var prev=shapeFor(active.getAttribute("data-state"));
      if(prev){ prev.classList.remove("is-active"); prev.setAttribute("aria-pressed","false"); }
    }
    active=null;
    setStatus("Select a state to jump to its cities.");
    if(dropHash&&history.replaceState) history.replaceState(null,"",location.href.split("#")[0]);
  }

  function select(code, scroll, dropIfSame){
    var block=blocks[code];
    if(!block){
      var empty=shapeFor(code);
      var title=empty&&empty.querySelector("title");
      setStatus((title?title.textContent:code)+" · no published cities yet.");
      return;
    }
    if(dropIfSame&&active===block){ clear(true); return; }
    if(active&&active!==block){
      active.classList.remove("is-active");
      var prev=shapeFor(active.getAttribute("data-state"));
      if(prev){ prev.classList.remove("is-active"); prev.setAttribute("aria-pressed","false"); }
    }
    block.classList.add("is-active");
    var shape=shapeFor(code);
    if(shape){ shape.classList.add("is-active"); shape.setAttribute("aria-pressed","true"); }
    active=block;
    setStatus(summary(block));
    if(history.replaceState) history.replaceState(null,"","#"+block.id);
    if(scroll) block.scrollIntoView({behavior:reduce?"auto":"smooth", block:"start"});
  }

  Array.prototype.forEach.call(svg.querySelectorAll("[data-state]"), function(shape){
    var code=shape.getAttribute("data-state");
    if(!blocks[code]) return;
    shape.setAttribute("role","button");
    shape.setAttribute("tabindex","0");
    shape.setAttribute("aria-pressed","false");
    shape.setAttribute("aria-label", summary(blocks[code])+". Jump to cities.");
    shape.addEventListener("click", function(){ select(code, true, true); });
    shape.addEventListener("keydown", function(e){
      if(e.key==="Enter"||e.key===" "){ e.preventDefault(); select(code, true, true); }
    });
    shape.addEventListener("mouseenter", function(){ if(active!==blocks[code]) setStatus(summary(blocks[code])); });
    shape.addEventListener("focus", function(){ setStatus(summary(blocks[code])); });
  });
  svg.addEventListener("mouseleave", function(){
    setStatus(active?summary(active):"Select a state to jump to its cities.");
  });

  var hash=(location.hash||"").match(/^#state-([a-z]{2})$/);
  if(hash&&blocks[hash[1].toUpperCase()]) select(hash[1].toUpperCase(), false, false);
})();
