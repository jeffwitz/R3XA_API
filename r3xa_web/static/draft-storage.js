(() => {
  const databaseName = "r3xa-webui";
  const storeName = "drafts";
  const documentKey = "current";
  const localKey = "r3xaDraft";
  const legacyKey = "r3xaDraftLast";
  const localLimit = 1_000_000;
  let databasePromise = null;
  let pendingText = null;
  let activeSave = null;

  const openDatabase = () => {
    if (!databasePromise) {
      databasePromise = new Promise((resolve, reject) => {
        if (!window.indexedDB) {
          reject(new Error("IndexedDB is unavailable in this browser."));
          return;
        }
        const request = indexedDB.open(databaseName, 1);
        request.onupgradeneeded = () => {
          request.result.createObjectStore(storeName);
        };
        request.onsuccess = () => {
          request.result.onversionchange = () => {
            request.result.close();
            databasePromise = null;
          };
          resolve(request.result);
        };
        request.onerror = () => reject(request.error);
      }).catch((error) => {
        databasePromise = null;
        throw error;
      });
    }
    return databasePromise;
  };

  const readIndexedDraft = async () => {
    const database = await openDatabase();
    return new Promise((resolve, reject) => {
      const transaction = database.transaction(storeName, "readonly");
      const request = transaction.objectStore(storeName).get(documentKey);
      request.onsuccess = () => resolve(typeof request.result === "string" ? request.result : null);
      request.onerror = () => reject(request.error);
      transaction.onabort = () => reject(transaction.error);
    });
  };

  const changeIndexedDraft = async (text) => {
    const database = await openDatabase();
    return new Promise((resolve, reject) => {
      const transaction = database.transaction(storeName, "readwrite");
      const store = transaction.objectStore(storeName);
      if (text === null) store.delete(documentKey);
      else store.put(text, documentKey);
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
      transaction.onabort = () => reject(transaction.error);
    });
  };

  const persist = async (text) => {
    localStorage.removeItem(legacyKey);
    if (text.length <= localLimit) {
      try {
        localStorage.setItem(localKey, text);
        try {
          await changeIndexedDraft(null);
        } catch {
          return;
        }
        return;
      } catch (error) {
        if (error?.name !== "QuotaExceededError") throw error;
      }
    }
    await changeIndexedDraft(text);
    localStorage.removeItem(localKey);
  };

  const drain = async () => {
    while (pendingText !== null) {
      const text = pendingText;
      pendingText = null;
      await persist(text);
    }
  };

  const save = (text) => {
    pendingText = String(text);
    if (!activeSave) {
      activeSave = Promise.resolve().then(drain).finally(() => {
        activeSave = null;
        if (pendingText !== null) save(pendingText).catch(() => {});
      });
    }
    return activeSave;
  };

  const flush = async () => {
    while (activeSave) await activeSave;
  };

  const load = async () => {
    await flush();
    const local = localStorage.getItem(localKey);
    if (local !== null) return local;
    try {
      const indexed = await readIndexedDraft();
      if (indexed !== null) return indexed;
    } catch {
      return localStorage.getItem(legacyKey);
    }
    return localStorage.getItem(legacyKey);
  };

  window.R3XADraftStorage = {load, save, flush};
})();
