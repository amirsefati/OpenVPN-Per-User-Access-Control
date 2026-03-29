let selectedUserId = null;
let usersCache = [];

async function refreshUsers() {
  usersCache = await API.json("/users");
  const container = document.getElementById("user-list");
  if (!container) return;
  container.innerHTML = "";
  usersCache.forEach((user) => {
    const item = document.createElement("button");
    item.className = "list-item";
    item.innerHTML = `
      <span><span class="status-dot ${user.online ? "online" : ""}"></span>${user.username}</span>
      <span class="muted">${user.vpn_ip}</span>
    `;
    item.addEventListener("click", () => selectUser(user.id));
    container.appendChild(item);
  });
}

async function selectUser(userId) {
  selectedUserId = userId;
  const detail = await API.json(`/users/${userId}`);
  document.getElementById("user-detail").classList.add("hidden");
  document.getElementById("user-actions").classList.remove("hidden");
  document.getElementById("user-meta").innerHTML = `
    <div class="list-item"><strong>${detail.username}</strong><span>${detail.vpn_ip}</span></div>
    <div class="list-item"><span>Last seen</span><span>${detail.last_seen_at || "never"}</span></div>
    <div class="list-item"><span>Total RX/TX</span><span>${detail.bytes_rx_total} / ${detail.bytes_tx_total}</span></div>
  `;
  await refreshDomains();
  await refreshLogs();
}

document.getElementById("create-user-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = document.getElementById("new-username").value.trim();
  if (!username) return;
  await API.json("/users", { method: "POST", body: JSON.stringify({ username }) });
  document.getElementById("new-username").value = "";
  await refreshUsers();
});

document.getElementById("delete-user-btn")?.addEventListener("click", async () => {
  if (!selectedUserId) return;
  await API.request(`/users/${selectedUserId}`, { method: "DELETE" });
  selectedUserId = null;
  document.getElementById("user-actions").classList.add("hidden");
  document.getElementById("user-detail").classList.remove("hidden");
  document.getElementById("user-detail").textContent = "Select a user.";
  await refreshUsers();
});

document.getElementById("download-config-btn")?.addEventListener("click", async () => {
  if (!selectedUserId) return;
  const response = await API.request(`/users/${selectedUserId}/config`);
  const blob = await response.blob();
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `user-${selectedUserId}.ovpn`;
  link.click();
  URL.revokeObjectURL(link.href);
});

window.addEventListener("load", async () => {
  if (window.location.pathname === "/dashboard") {
    await refreshUsers();
  }
});

