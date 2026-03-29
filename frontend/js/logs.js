let activeLogTab = "dns";

async function refreshLogs() {
  const container = document.getElementById("log-content");
  if (!container) return;
  const suffix = selectedUserId ? `?user_id=${selectedUserId}` : "";
  const path = activeLogTab === "dns" ? `/logs/dns${suffix}` : `/logs/connections${suffix}`;
  const rows = await API.json(path);
  container.innerHTML = "";
  rows.forEach((row) => {
    const item = document.createElement("div");
    item.className = "list-item";
    if (activeLogTab === "dns") {
      item.innerHTML = `<span>${row.domain}</span><span class="muted">${row.resolved_ip || "pending"}</span>`;
    } else {
      item.innerHTML = `<span>${row.real_ip || "unknown"}</span><span class="muted">${row.connected_at}</span>`;
    }
    container.appendChild(item);
  });
}

function setLogTab(tab) {
  activeLogTab = tab;
  document.getElementById("tab-dns").classList.toggle("active", tab === "dns");
  document.getElementById("tab-connections").classList.toggle("active", tab === "connections");
  refreshLogs();
}

document.getElementById("tab-dns")?.addEventListener("click", () => setLogTab("dns"));
document.getElementById("tab-connections")?.addEventListener("click", () => setLogTab("connections"));

window.addEventListener("load", () => {
  if (window.location.pathname === "/dashboard") {
    refreshLogs();
    const token = localStorage.getItem("token");
    if (!token) return;
    const protocol = location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${location.host}/ws/status?token=${encodeURIComponent(token)}`);
    socket.addEventListener("open", () => socket.send("subscribe"));
    socket.addEventListener("message", async () => {
      await refreshUsers();
      if (selectedUserId) {
        await selectUser(selectedUserId);
      }
    });
  }
});

