// example-service frontend — deliberately minimal.
// Gọi API cùng origin khi đã triển khai; khi chạy local, trỏ về cổng 8000.
const API_BASE =
  window.location.port === "3000" ? "http://localhost:8000" : "";

async function refresh() {
  const list = document.getElementById("item-list");
  list.innerHTML = "";
  try {
    const res = await fetch(`${API_BASE}/api/items`);
    const data = await res.json();
    for (const item of data.items) {
      const li = document.createElement("li");
      li.textContent = `#${item.id} — ${item.name} (${item.status})`;
      list.appendChild(li);
    }
  } catch (e) {
    const li = document.createElement("li");
    li.textContent = `Không gọi được API: ${e.message}`;
    list.appendChild(li);
  }
}

document.getElementById("refresh").addEventListener("click", refresh);

document
  .getElementById("item-form")
  .addEventListener("submit", async (event) => {
    event.preventDefault();
    const result = document.getElementById("form-result");
    const payload = { name: document.getElementById("name").value };
    try {
      const res = await fetch(`${API_BASE}/api/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      result.textContent = res.ok
        ? `Đã tạo item #${data.id}.`
        : `Lỗi ${res.status}: ${data.detail || "unknown"}`;
      if (res.ok) await refresh();
    } catch (e) {
      result.textContent = `Không gọi được API: ${e.message}`;
    }
  });

refresh();
