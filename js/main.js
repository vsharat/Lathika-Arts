/* Lathika Arts — shared site behavior: theme, nav, galleries, lightbox,
   shop inquiries and contact form. Requires config.js (and works-data.js on
   pages that render works). */
(function () {
  "use strict";

  var CFG = window.SITE_CONFIG || {};

  /* ------------------------------ theme ---------------------------------- */

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    var btn = document.querySelector(".theme-toggle");
    if (btn) {
      btn.textContent = theme === "dark" ? "☀" : "☾";
      btn.setAttribute("aria-label",
        theme === "dark" ? "Switch to light mode" : "Switch to dark mode");
    }
  }

  function initTheme() {
    var saved = null;
    try { saved = localStorage.getItem("la-theme"); } catch (e) {}
    var prefersDark = window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches;
    applyTheme(saved || (prefersDark ? "dark" : "light"));

    var btn = document.querySelector(".theme-toggle");
    if (btn) {
      btn.addEventListener("click", function () {
        var next = document.documentElement.getAttribute("data-theme") === "dark"
          ? "light" : "dark";
        applyTheme(next);
        try { localStorage.setItem("la-theme", next); } catch (e) {}
      });
    }
  }

  /* ------------------------------- nav ------------------------------------ */

  function initNav() {
    var toggle = document.querySelector(".nav-toggle");
    var links = document.querySelector(".nav-links");
    if (toggle && links) {
      toggle.addEventListener("click", function () {
        var open = links.classList.toggle("open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
    }
  }

  /* ----------------------------- lightbox --------------------------------- */

  var lbItems = [];   // array of works currently browsable
  var lbIndex = 0;

  function ensureLightbox() {
    var lb = document.getElementById("lightbox");
    if (lb) return lb;
    lb = document.createElement("div");
    lb.id = "lightbox";
    lb.className = "lightbox";
    lb.setAttribute("role", "dialog");
    lb.setAttribute("aria-modal", "true");
    lb.setAttribute("aria-label", "Artwork viewer");
    lb.innerHTML =
      '<button class="lb-close" aria-label="Close">✕</button>' +
      '<button class="lb-nav lb-prev" aria-label="Previous artwork">←</button>' +
      '<img alt="">' +
      '<div class="lightbox-caption"></div>' +
      '<button class="lb-nav lb-next" aria-label="Next artwork">→</button>';
    document.body.appendChild(lb);

    lb.querySelector(".lb-close").addEventListener("click", closeLightbox);
    lb.querySelector(".lb-prev").addEventListener("click", function () { stepLightbox(-1); });
    lb.querySelector(".lb-next").addEventListener("click", function () { stepLightbox(1); });
    lb.addEventListener("click", function (e) { if (e.target === lb) closeLightbox(); });
    document.addEventListener("keydown", function (e) {
      if (!lb.classList.contains("open")) return;
      if (e.key === "Escape") closeLightbox();
      if (e.key === "ArrowLeft") stepLightbox(-1);
      if (e.key === "ArrowRight") stepLightbox(1);
    });
    return lb;
  }

  function openLightbox(items, index) {
    lbItems = items;
    lbIndex = index;
    var lb = ensureLightbox();
    renderLightbox();
    lb.classList.add("open");
    document.body.style.overflow = "hidden";
  }

  function closeLightbox() {
    var lb = document.getElementById("lightbox");
    if (lb) lb.classList.remove("open");
    document.body.style.overflow = "";
  }

  function stepLightbox(d) {
    lbIndex = (lbIndex + d + lbItems.length) % lbItems.length;
    renderLightbox();
  }

  function renderLightbox() {
    var lb = document.getElementById("lightbox");
    var work = lbItems[lbIndex];
    var img = lb.querySelector("img");
    img.src = work.full;
    img.alt = work.title;
    var cap = lb.querySelector(".lightbox-caption");
    cap.innerHTML = "";
    var label = document.createElement("span");
    var catLabel = window.WORKS_DATA
      ? WORKS_DATA.categories[work.category].label : "";
    label.textContent = work.title + (catLabel ? " — " + catLabel : "");
    cap.appendChild(label);
    if (work.forSale) {
      var btn = document.createElement("button");
      btn.className = "btn btn-primary";
      btn.textContent = "Inquire about this piece";
      btn.addEventListener("click", function () {
        closeLightbox();
        openInquiry(work);
      });
      cap.appendChild(btn);
    }
  }

  /* --------------------------- work rendering ----------------------------- */

  function workTile(work, onOpen) {
    var el = document.createElement("button");
    el.className = "work";
    el.type = "button";
    el.setAttribute("aria-label", "View " + work.title);
    var img = document.createElement("img");
    img.src = work.thumb;
    img.alt = work.title;
    img.loading = "lazy";
    img.width = 640;
    img.height = Math.round(640 * work.h / work.w);
    el.appendChild(img);
    if (work.forSale) {
      var b = document.createElement("span");
      b.className = "badge-sale";
      b.textContent = "Available";
      el.appendChild(b);
    }
    var info = document.createElement("span");
    info.className = "work-info";
    info.textContent = work.title;
    el.appendChild(info);
    el.addEventListener("click", onOpen);
    return el;
  }

  function initPortfolio() {
    var grid = document.getElementById("portfolio-grid");
    if (!grid || !window.WORKS_DATA) return;

    var portfolioCats = Object.keys(WORKS_DATA.categories).filter(function (k) {
      return WORKS_DATA.categories[k].section === "portfolio";
    });
    var works = WORKS_DATA.works.filter(function (w) {
      return portfolioCats.indexOf(w.category) !== -1;
    });
    var current = "all";
    var params = new URLSearchParams(location.search);
    if (portfolioCats.indexOf(params.get("cat")) !== -1) {
      current = params.get("cat");
    }

    var bar = document.getElementById("filter-bar");
    if (bar) {
      var cats = [["all", "All Works"]].concat(
        portfolioCats.map(function (k) {
          return [k, WORKS_DATA.categories[k].label];
        }));
      cats.forEach(function (pair) {
        var btn = document.createElement("button");
        btn.className = "filter-btn" + (pair[0] === current ? " active" : "");
        btn.textContent = pair[1];
        btn.dataset.cat = pair[0];
        btn.addEventListener("click", function () {
          current = pair[0];
          bar.querySelectorAll(".filter-btn").forEach(function (b) {
            b.classList.toggle("active", b.dataset.cat === current);
          });
          var url = new URL(location.href);
          if (current === "all") url.searchParams.delete("cat");
          else url.searchParams.set("cat", current);
          history.replaceState(null, "", url);
          render();
        });
        bar.appendChild(btn);
      });
    }

    function render() {
      grid.innerHTML = "";
      var visible = works.filter(function (w) {
        return current === "all" || w.category === current;
      });
      visible.forEach(function (w, i) {
        grid.appendChild(workTile(w, function () { openLightbox(visible, i); }));
      });
    }
    render();
  }

  function initFeatured() {
    var grid = document.getElementById("featured-grid");
    if (!grid || !window.WORKS_DATA) return;
    var picks = ["dscf1118", "55eebeab-dee9-4865-8cda-817367889662",
                 "dsc00095-small", "ed8ed12e-b08f-400c-87fa-e48b2cf3d47b",
                 "panel1", "mummys-art-work-16",
                 "20190627-042607000-ios", "c943d45c-5183-4595-8364-332214c6273d"];
    var featured = picks.map(function (slug) {
      return WORKS_DATA.works.find(function (w) { return w.slug === slug; });
    }).filter(Boolean);
    featured.forEach(function (w, i) {
      grid.appendChild(workTile(w, function () { openLightbox(featured, i); }));
    });
  }

  /* -------------------------------- shop ---------------------------------- */

  function initShop() {
    var host = document.getElementById("shop-sections");
    if (!host || !window.WORKS_DATA) return;

    var shopCats = Object.keys(WORKS_DATA.categories).filter(function (k) {
      return WORKS_DATA.categories[k].section === "shop";
    });

    var jumps = document.getElementById("shop-jumps");
    if (jumps) {
      shopCats.forEach(function (k) {
        var a = document.createElement("a");
        a.className = "filter-btn";
        a.href = "#" + k;
        a.textContent = WORKS_DATA.categories[k].label;
        jumps.appendChild(a);
      });
    }

    shopCats.forEach(function (k) {
      var cat = WORKS_DATA.categories[k];
      var items = WORKS_DATA.works.filter(function (w) {
        return w.category === k;
      });
      var section = document.createElement("section");
      section.className = "shop-section";
      section.id = k;
      var head = document.createElement("div");
      head.className = "shop-section-head";
      var h2 = document.createElement("h2");
      h2.textContent = cat.label;
      var count = document.createElement("span");
      count.className = "shop-count";
      count.textContent = items.length + " pieces";
      var blurb = document.createElement("p");
      blurb.textContent = cat.blurb;
      head.appendChild(h2);
      head.appendChild(count);
      head.appendChild(blurb);
      section.appendChild(head);
      var grid = document.createElement("div");
      grid.className = "shop-grid";
      renderShopCards(items, grid);
      section.appendChild(grid);
      host.appendChild(section);
    });
  }

  function renderShopCards(items, grid) {
    items.forEach(function (w, i) {
      var card = document.createElement("article");
      card.className = "shop-card";

      var imgBtn = document.createElement("button");
      imgBtn.className = "shop-img";
      imgBtn.type = "button";
      imgBtn.setAttribute("aria-label", "View " + w.title + " larger");
      var img = document.createElement("img");
      img.src = w.thumb;
      img.alt = w.title;
      img.loading = "lazy";
      imgBtn.appendChild(img);
      imgBtn.addEventListener("click", function () { openLightbox(items, i); });
      card.appendChild(imgBtn);

      var body = document.createElement("div");
      body.className = "shop-body";
      var cat = document.createElement("span");
      cat.className = "shop-cat";
      cat.textContent = WORKS_DATA.categories[w.category].label;
      var h = document.createElement("h3");
      h.textContent = w.title;
      var p = document.createElement("p");
      p.textContent = w.description ||
        "A one-of-a-kind hand-sculpted piece. Reach out for details.";
      var btn = document.createElement("button");
      btn.className = "btn btn-primary";
      btn.type = "button";
      btn.textContent = "Inquire";
      btn.addEventListener("click", function () { openInquiry(w); });
      body.appendChild(cat);
      body.appendChild(h);
      body.appendChild(p);
      body.appendChild(btn);
      card.appendChild(body);
      grid.appendChild(card);
    });
  }

  /* --------------------------- inquiry modal ------------------------------ */

  function ensureModal() {
    var m = document.getElementById("inquiry-modal");
    if (m) return m;
    m = document.createElement("div");
    m.id = "inquiry-modal";
    m.className = "modal";
    m.setAttribute("role", "dialog");
    m.setAttribute("aria-modal", "true");
    m.setAttribute("aria-labelledby", "inquiry-title");
    m.innerHTML =
      '<div class="modal-box">' +
      '  <button class="modal-close" aria-label="Close">✕</button>' +
      '  <h3 id="inquiry-title">Inquire</h3>' +
      '  <p class="modal-sub">Interested in this piece? Send a note and ' +
      "Lathika will get back to you about availability, sizing and delivery.</p>" +
      '  <form id="inquiry-form" novalidate>' +
      '    <input type="hidden" name="piece">' +
      '    <div class="form-field"><label for="inq-name">Your name</label>' +
      '      <input id="inq-name" name="name" type="text" required autocomplete="name"></div>' +
      '    <div class="form-field"><label for="inq-email">Your email</label>' +
      '      <input id="inq-email" name="email" type="email" required autocomplete="email"></div>' +
      '    <div class="form-field"><label for="inq-msg">Message</label>' +
      '      <textarea id="inq-msg" name="message" rows="4" required></textarea></div>' +
      '    <input type="text" name="_honey" style="display:none" tabindex="-1" autocomplete="off">' +
      '    <button class="btn btn-primary" type="submit">Send inquiry</button>' +
      '    <p class="form-status" role="status"></p>' +
      "  </form>" +
      "</div>";
    document.body.appendChild(m);
    m.querySelector(".modal-close").addEventListener("click", closeModal);
    m.addEventListener("click", function (e) { if (e.target === m) closeModal(); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && m.classList.contains("open")) closeModal();
    });
    wireForm(m.querySelector("#inquiry-form"), function () {
      var piece = m.querySelector('input[name="piece"]').value;
      return "Inquiry about “" + piece + "” — " + (CFG.siteName || "Lathika Arts");
    });
    return m;
  }

  function openInquiry(work) {
    var m = ensureModal();
    m.querySelector("#inquiry-title").textContent = "Inquire — " + work.title;
    m.querySelector('input[name="piece"]').value = work.title;
    var msg = m.querySelector("#inq-msg");
    if (!msg.value) {
      msg.value = "Hello, I’m interested in “" + work.title +
        "” and would love to know more.";
    } else {
      msg.value = msg.value.replace(/“[^”]*”/,
        "“" + work.title + "”");
    }
    var status = m.querySelector(".form-status");
    status.className = "form-status";
    m.classList.add("open");
    document.body.style.overflow = "hidden";
    m.querySelector("#inq-name").focus();
  }

  function closeModal() {
    var m = document.getElementById("inquiry-modal");
    if (m) m.classList.remove("open");
    document.body.style.overflow = "";
  }

  /* ------------------------- form submission ------------------------------ */

  function wireForm(form, subjectFn) {
    if (!form) return;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var status = form.querySelector(".form-status");
      status.className = "form-status";

      if (!form.checkValidity()) {
        status.textContent = "Please fill in your name, a valid email and a message.";
        status.className = "form-status err";
        return;
      }
      var data = new FormData(form);
      if (data.get("_honey")) return; // spam bot filled the hidden field

      var payload = {
        name: data.get("name"),
        email: data.get("email"),
        message: data.get("message"),
        _subject: subjectFn(),
        _template: "table",
        _captcha: "false",
      };
      if (data.get("piece")) payload.piece = data.get("piece");

      var submitBtn = form.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      status.textContent = "Sending…";
      status.className = "form-status ok";

      fetch("https://formsubmit.co/ajax/" + encodeURIComponent(CFG.inquiryEmail), {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
      })
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.json();
        })
        .then(function () {
          status.textContent =
            "Thank you! Your message is on its way — you’ll hear back soon.";
          status.className = "form-status ok";
          form.reset();
          submitBtn.disabled = false;
        })
        .catch(function () {
          submitBtn.disabled = false;
          status.className = "form-status err";
          status.innerHTML =
            "Sorry, the message couldn’t be sent automatically. " +
            'You can email directly instead: <a href="' + mailtoHref(payload) +
            '">' + CFG.inquiryEmail + "</a>";
        });
    });
  }

  function mailtoHref(payload) {
    var body = payload.message + "\n\n— " + payload.name +
      " (" + payload.email + ")";
    return "mailto:" + CFG.inquiryEmail +
      "?subject=" + encodeURIComponent(payload._subject) +
      "&body=" + encodeURIComponent(body);
  }

  /* ----------------------------- boot ------------------------------------- */

  document.addEventListener("DOMContentLoaded", function () {
    initTheme();
    initNav();
    initPortfolio();
    initFeatured();
    initShop();
    wireForm(document.getElementById("contact-form"), function () {
      return "Message from " + (CFG.siteName || "Lathika Arts") + " contact form";
    });
    var y = document.getElementById("year");
    if (y) y.textContent = new Date().getFullYear();
  });
})();
