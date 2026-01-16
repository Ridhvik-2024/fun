const cards = document.querySelectorAll(".card");
const STATUS = ["none", "done", "partial", "skipped"];

function getISTDate() {
  const n = new Date();
  return new Date(n.getTime() + (330 - n.getTimezoneOffset()) * 60000);
}

function dayName(d) {
  return new Date(d).toLocaleDateString("en-IN", { weekday: "long" });
}

const dateInput = document.getElementById("dateInput");
const dayLabel = document.getElementById("dayName");

dateInput.value = getISTDate().toISOString().split("T")[0];
dayLabel.innerText = dayName(dateInput.value);

dateInput.onchange = () => {
  dayLabel.innerText = dayName(dateInput.value);
  load(dateInput.value);
};

function apply(card, s) {
  card.dataset.status = s;
  card.className = "card " + s;
}

function recalc() {
  let c = 0, e = 0;
  cards.forEach(card => {
    const s = card.dataset.status;
    if (s === "skipped") return;
    e++;
    if (s === "done" || s === "partial") c++;
  });
  const p = e ? Math.round((c / e) * 100) : 0;
  document.getElementById("progressText").innerText = p + "%";
  document.getElementById("progress").style.strokeDashoffset = 213 - 213 * p / 100;
}

cards.forEach(card => {
  card.dataset.status = "none";
  card.onclick = () => {
    const s = card.dataset.status;
    const n = STATUS[(STATUS.indexOf(s) + 1) % STATUS.length];
    apply(card, n);
    if (n !== "none") save(card, n);
    recalc();
  };
});

function save(card, status) {
  fetch("/log", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      date: dateInput.value,
      meal_type: card.dataset.meal,
      planned_item: card.dataset.item,
      status,
      discomfort: card.querySelector(".discomfort-select").value,
      notes: card.querySelector(".note-box").value
    })
  });
}

function load(d) {
  fetch("/logs/" + d).then(r => r.json()).then(data => {
    cards.forEach(c => apply(c, "none"));
    data.forEach(x => {
      const c = [...cards].find(y => y.dataset.meal === x.meal_type);
      if (!c) return;
      apply(c, x.status);
      c.querySelector(".note-box").value = x.notes || "";
      c.querySelector(".discomfort-select").value = x.discomfort || "";
      if (x.image) {
        const img = c.querySelector(".meal-image");
        img.src = "/uploads/" + x.image;
        img.hidden = false;
      }
    });
    recalc();
    report(d);
  });
}

function report(d) {
  fetch("/report/day/" + d).then(r => r.json()).then(x => {
    document.getElementById("dailyReport").innerText =
      `Today: ${x.percent}% (${x.completed}/${x.eligible}, skipped ${x.skipped})`;
  });

  fetch("/report/week/" + d).then(r => r.json()).then(w => {
    document.getElementById("weeklyReport").innerHTML =
      w.map(x => `${x.date}: ${x.percent}%`).join("<br>");
  });
}

function toggleNote(h) {
  h.nextElementSibling.classList.toggle("open");
}

function uploadImage(input) {
  const card = input.closest(".card");
  const fd = new FormData();
  fd.append("image", input.files[0]);
  fd.append("date", dateInput.value);
  fd.append("meal_type", card.dataset.meal);

  fetch("/upload", { method: "POST", body: fd })
    .then(r => r.json())
    .then(x => {
      const img = card.querySelector(".meal-image");
      img.src = "/uploads/" + x.filename;
      img.hidden = false;
    });
}

const themeToggle = document.getElementById("themeToggle");
themeToggle.onclick = () => {
  document.body.classList.toggle("light");
  localStorage.setItem("theme",
    document.body.classList.contains("light") ? "light" : "dark");
};

document.body.classList.toggle(
  "light",
  localStorage.getItem("theme") === "light"
);

load(dateInput.value);
