(() => {
  const storageKey = "r3xaLanguage";
  let messages = {default_language: "en", languages: {en: {}}};
  let language = localStorage.getItem(storageKey) || (navigator.language || "en").slice(0, 2);

  const activeMessages = () => messages.languages?.[language] || messages.languages?.[messages.default_language] || {};

  const translate = (key, fallback, values = {}) => {
    const template = activeMessages()[key] || fallback || key;
    return Object.entries(values).reduce(
      (text, [name, value]) => text.replaceAll(`{${name}}`, String(value)),
      template,
    );
  };

  const apply = (root = document) => {
    root.querySelectorAll("[data-i18n]").forEach((element) => {
      element.textContent = translate(element.dataset.i18n, element.dataset.i18nFallback);
    });
    root.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
      element.placeholder = translate(element.dataset.i18nPlaceholder, element.placeholder);
    });
    root.querySelectorAll("[data-language-select]").forEach((select) => {
      select.value = language;
      select.onchange = () => {
        language = select.value;
        localStorage.setItem(storageKey, language);
        apply();
        document.dispatchEvent(new CustomEvent("r3xa-language-changed"));
      };
    });
    document.documentElement.lang = language;
  };

  const installCatalog = (catalog) => {
    if (catalog?.messages?.languages) messages = catalog.messages;
    if (!messages.languages?.[language]) language = messages.default_language || "en";
    apply();
  };

  window.R3XAI18N = {apply, installCatalog, language: () => language, t: translate};
  window.R3XARuntime.loadUiCatalog()
    .catch(() => null)
    .then((catalog) => installCatalog(catalog))
    .catch(() => apply());
})();
