async function refreshDomains() {
  if (!selectedUserId) return;
  const domains = await API.json(`/users/${selectedUserId}/domains`);
  const container = document.getElementById("domain-list");
  container.innerHTML = "";
  domains.forEach((domain) => {
    const item = document.createElement("div");
    item.className = "list-item";
    item.innerHTML = `<span>${domain.domain}</span>`;
    const button = document.createElement("button");
    button.className = "danger";
    button.textContent = "Remove";
    button.addEventListener("click", async () => {
      await API.request(`/users/${selectedUserId}/domains/${domain.id}`, { method: "DELETE" });
      await refreshDomains();
    });
    item.appendChild(button);
    container.appendChild(item);
  });
}

document.getElementById("add-domain-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!selectedUserId) return;
  const input = document.getElementById("new-domain");
  await API.json(`/users/${selectedUserId}/domains`, {
    method: "POST",
    body: JSON.stringify({ domain: input.value.trim() }),
  });
  input.value = "";
  await refreshDomains();
});

