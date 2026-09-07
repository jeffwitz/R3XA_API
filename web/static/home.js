const profileCardsEl = document.getElementById("profile-cards");
const t = (key, fallback) => window.R3XAI18N?.t(key, fallback) || fallback;

const renderProfileCards = (catalog) => {
  if (!profileCardsEl) return;
  profileCardsEl.innerHTML = "";
  Object.entries(catalog.profiles || {}).forEach(([profileId, profile]) => {
    const card = document.createElement("a");
    card.className = "profile-card";
    card.href = profileId === "generic"
      ? "/edit?profile=generic&new=1"
      : `/edit?profile=${encodeURIComponent(profileId)}&prefill=1`;
    const title = document.createElement("strong");
    title.textContent = t(`profile.${profileId}.title`, profile.title || profileId);
    const description = document.createElement("span");
    description.textContent = t(`profile.${profileId}.description`, profile.description || "");
    const action = document.createElement("small");
    action.textContent = profileId === "generic"
      ? t("home.open_generic", "Open schema-driven editor")
      : t("home.open_guided", "Open guided workflow");
    card.append(title, description, action);
    profileCardsEl.appendChild(card);
  });
};

const loadHome = async () => {
  try {
    const response = await fetch("/api/ui");
    if (!response.ok) throw new Error("Unable to load profiles");
    const catalog = await response.json();
    window.R3XAI18N?.installCatalog(catalog);
    window.r3xaUiCatalog = catalog;
    renderProfileCards(catalog);
  } catch (error) {
    if (profileCardsEl) profileCardsEl.textContent = t("home.profiles_unavailable", `Profiles are unavailable: ${error.message}`);
  }
};

document.addEventListener("r3xa-language-changed", () => {
  if (window.r3xaUiCatalog) renderProfileCards(window.r3xaUiCatalog);
});

loadHome();
