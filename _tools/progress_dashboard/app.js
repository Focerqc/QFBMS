const app = document.getElementById("app");
const stamp = document.getElementById("stamp");
const BOARD = "qfbms32.kicad_pcb";

const STATE_LABEL = {
  copper: "copper",
  named: "named",
  ok: "ok",
  partial: "partial",
  wrong: "wrong",
  missing: "missing",
  empty: "empty",
  nc: "nc",
};

let data = null;
let gapsOnly = false;
let selectedPin = null;

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text != null) node.textContent = text;
  return node;
}

function tag(state) {
  return el("span", "tag " + state, STATE_LABEL[state] || state);
}

function meter(value, label) {
  const box = el("div", "meter");
  box.append(el("b", null, value), el("span", null, label));
  return box;
}

function renderPins(ref) {
  const wrap = el("section");
  wrap.append(el("h2", null, ref));
  const grid = el("div", "pin-grid");
  const detail = el("p", "pin-detail", "Select a pin.");
  for (const pin of data.pins.filter((p) => p.ref === ref)) {
    const cell = el("button", "pin " + pin.state);
    cell.type = "button";
    cell.append(el("span", "n", String(pin.pin)), el("span", "f", pin.func));
    cell.title = pin.net ? pin.net : "no net";
    cell.addEventListener("click", () => {
      selectedPin = ref + ":" + pin.pin;
      document.querySelectorAll(".pin.selected").forEach((n) => n.classList.remove("selected"));
      cell.classList.add("selected");
      const reach = pin.reaches ? " Copper reaches " + pin.reaches + "." : "";
      detail.textContent = "Pin " + pin.pin + " " + pin.func + " · " + (pin.net || "no net") + "." + reach;
    });
    grid.append(cell);
  }
  wrap.append(grid, detail);
  return wrap;
}

function render() {
  app.replaceChildren();
  if (!data) return;
  if (data.error) {
    app.append(el("p", "error", data.error));
    return;
  }
  const s = data.summary;
  app.append(el("p", "verdict", data.verdict));

  const meters = el("div", "meters");
  meters.append(
    meter(s.cell_to_rf + " / 32", "cell taps whose copper reaches R_F"),
    meter(s.rf_to_bq + " / 32", "filter resistors that reach a BQ pad"),
    meter(s.bq_named.U_BQ1 + " and " + s.bq_named.U_BQ2, "pins named on U_BQ1 and U_BQ2, out of 48"),
    meter(String(s.bq_copper.U_BQ1 + s.bq_copper.U_BQ2), "BQ pins, both chips, with copper to another part"),
  );
  app.append(meters);

  const layout = el("div", "layout");

  const left = el("section");
  const bar = el("div", "toolbar");
  const titles = el("div");
  titles.append(el("h2", null, "Harness and the circuit behind it"), el("p", "section-note", "Named means the pad net matches the wiring sheet. Copper means two pads share a connected island."));
  const gaps = el("button", gapsOnly ? "on" : "", gapsOnly ? "Showing gaps" : "Show gaps only");
  gaps.type = "button";
  gaps.addEventListener("click", () => { gapsOnly = !gapsOnly; render(); });
  bar.append(titles, gaps);
  left.append(bar);

  const table = el("table");
  table.append(el("thead"));
  const head = el("tr");
  ["", "Check", "On the board"].forEach((h) => head.append(el("th", null, h)));
  table.append(head);
  const body = el("tbody");
  let lastGroup = "";
  for (const row of data.rows) {
    if (gapsOnly && (row.state === "copper" || row.state === "ok" || row.state === "nc")) continue;
    if (row.group !== lastGroup) {
      lastGroup = row.group;
      const g = el("tr", "group");
      const gd = el("td", null, row.group);
      gd.colSpan = 3;
      g.append(gd);
      body.append(g);
    }
    const tr = el("tr");
    const st = el("td");
    st.append(tag(row.state));
    const item = el("td", "item", row.label);
    const found = el("td", "found", row.found + (row.note ? ". " + row.note : ""));
    tr.append(st, item, found);
    body.append(tr);
  }
  table.append(body);
  left.append(table);

  const right = el("section");
  right.append(el("h2", null, "BQ76952 EVM blocks"), el("p", "section-note", "One block per support circuit on the TI reference, counted on this board."));
  const blocks = el("table");
  const bb = el("tbody");
  for (const block of data.blocks) {
    if (gapsOnly && block.state === "copper") continue;
    const tr = el("tr");
    const st = el("td");
    st.append(tag(block.state));
    tr.append(st, el("td", "item", block.title), el("td", "detail", block.detail));
    bb.append(tr);
  }
  blocks.append(bb);
  right.append(blocks);
  layout.append(left, right);
  app.append(layout);

  const pins = el("div", "pins");
  pins.append(renderPins("U_BQ1"), renderPins("U_BQ2"));
  app.append(pins);

  const blank = el("section", "blank");
  blank.append(el("h2", null, "Placed parts with no nets"), el("p", "section-note", data.blank.length + " footprints. Pads exist. Nothing is assigned."));
  const chips = el("div", "chips");
  const used = new Set();
  for (const part of data.blank) {
    if (used.has(part.ref)) continue;
    const m = part.ref.match(/^(.*?)(\d+)$/);
    let labelRef = part.ref;
    if (m) {
      const same = data.blank.filter((p) => p.value === part.value && new RegExp("^" + m[1] + "\\d+$").test(p.ref));
      const nums = same.map((p) => Number(p.ref.slice(m[1].length))).sort((a, b) => a - b);
      const run = nums.length > 2 && nums.every((n, i) => i === 0 || n === nums[i - 1] + 1);
      same.forEach((p) => used.add(p.ref));
      if (run) labelRef = m[1] + nums[0] + "–" + m[1] + nums[nums.length - 1];
    } else {
      used.add(part.ref);
    }
    const chip = el("span", "chip");
    chip.append(el("b", null, labelRef));
    chip.append(document.createTextNode(" " + part.value));
    chips.append(chip);
  }
  blank.append(chips);
  app.append(blank);

  const counts = el("p", "section-note");
  counts.style.marginTop = "18px";
  counts.textContent = s.tracks + " tracks · " + s.vias + " vias · " + (s.unconnected == null ? "—" : s.unconnected) + " ratsnest lines · " + s.signal_pads_unnetted + " signal pads with no net";
  app.append(counts);
}

async function load() {
  stamp.textContent = "reading board…";
  try {
    const res = await fetch("/api/progress?path=" + encodeURIComponent(BOARD));
    data = await res.json();
    if (data.error) stamp.textContent = "audit failed";
    else stamp.textContent = data.path + " · " + data.mtime;
  } catch (err) {
    data = { error: String(err) };
    stamp.textContent = "audit failed";
  }
  render();
}

document.getElementById("reload").addEventListener("click", load);
load();
