// payments-sample frontend — deliberately minimal.
//
// API base URL: for local development the API runs on :8000 while this page
// is served from a static server on :3000. In the reference deployment both
// sit behind the same ALB origin; set API_BASE to "" in that case.
const API_BASE = "http://localhost:8000";

const listEl = document.getElementById("payment-list");
const resultEl = document.getElementById("form-result");

async function refreshPayments() {
  listEl.innerHTML = "";
  try {
    const res = await fetch(`${API_BASE}/api/payments`);
    const data = await res.json();
    for (const p of data.payments) {
      const li = document.createElement("li");
      li.textContent = `#${p.id} — ${p.amount} ${p.currency} — ${p.status} — ${p.description}`;
      listEl.appendChild(li);
    }
  } catch (err) {
    const li = document.createElement("li");
    li.textContent = `Could not reach the API at ${API_BASE} (${err.message}). Is the backend running?`;
    listEl.appendChild(li);
  }
}

document.getElementById("refresh").addEventListener("click", refreshPayments);

document.getElementById("payment-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    amount: Number(document.getElementById("amount").value),
    currency: document.getElementById("currency").value,
    description: document.getElementById("description").value,
  };
  try {
    const res = await fetch(`${API_BASE}/api/payments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    resultEl.textContent = res.ok
      ? `Recorded payment #${data.id} (${data.status}).`
      : `Rejected: ${data.detail}`;
  } catch (err) {
    resultEl.textContent = `Could not reach the API (${err.message}).`;
  }
  refreshPayments();
});

refreshPayments();
