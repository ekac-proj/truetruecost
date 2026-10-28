// TrueTrueCost live calculator — same model as the tables (see how-it-works.html).
// Month 1 at the promo discount, full rate until the increase month, then rate x (1 + increase),
// plus a one-time admin fee and a monthly protection plan. Updates on every keystroke.
(function(){
  var f=document.getElementById('calc'); if(!f) return;
  var out=document.getElementById('calc-out');
  var incFrom=parseInt(f.getAttribute('data-increase-from'),10)||5;
  function v(id,d){var el=document.getElementById(id); if(!el) return d; var x=parseFloat(el.value); return isNaN(x)?d:x;}
  function usd(x){return '$'+Math.round(x).toLocaleString('en-US');}
  function run(e){
    if(e&&e.type==='submit') e.preventDefault();
    var rate=Math.max(0,v('c-rate',0)),
        months=Math.max(1,Math.min(36,Math.round(v('c-months',6)))),
        fee=Math.max(0,v('c-fee',0)),
        prot=Math.max(0,v('c-prot',0)),
        inc=Math.max(0,v('c-inc',0))/100,
        promo=Math.max(0,Math.min(100,v('c-promo',0)))/100;
    var after=rate*(1+inc), rent=rate*(1-promo);
    for(var m=2;m<=months;m++){ rent += (m>=incFrom)?after:rate; }
    var extras=fee+prot*months, total=rent+extras, avg=total/months;
    var gap=rate>0?Math.round((avg/rate-1)*100):0;
    var gapTxt=rate>0?(gap>=0?gap+'% above':Math.abs(gap)+'% below')+' the advertised '+usd(rate)+'/mo':'';
    var incTxt=months>=incFrom?'rate from month '+incFrom+': '+usd(after)+'/mo':'no increase within '+months+' month'+(months>1?'s':'');
    out.innerHTML=
      '<div class="calc-figs">'+
        '<div><span class="k">'+months+'-month true average</span><span class="v">'+usd(avg)+'<small>/mo</small></span></div>'+
        '<div><span class="k">'+months+'-month total</span><span class="v">'+usd(total)+'</span></div>'+
      '</div>'+
      '<p class="small calc-detail">'+(gapTxt?gapTxt+' &middot; ':'')+'rent '+usd(rent)+' &middot; fees + protection '+usd(extras)+' &middot; '+incTxt+'</p>';
  }
  f.addEventListener('submit',run); f.addEventListener('input',run);
  var reset=document.getElementById('calc-reset');
  if(reset) reset.addEventListener('click',function(){ f.reset(); run(); });
  run();
})();
