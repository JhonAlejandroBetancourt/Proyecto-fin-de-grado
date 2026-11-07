(() => {
  const url = document.querySelector(
    'meta[name="supabase-url"]'
  )?.content;
  const anonKey = document.querySelector(
    'meta[name="supabase-anon-key"]'
  )?.content;
  if (!url || !anonKey) return;

  const loginUrl = () => {
    const next = `${location.pathname}${location.search}`;
    return `/login?${new URLSearchParams({ next })}`;
  };

  const showError = (text) => {
    let message = document.getElementById("auth-session-error");
    if (!message) {
      message = document.createElement("p");
      message.id = "auth-session-error";
      message.setAttribute("role", "alert");
      message.style.cssText =
        "position:fixed;z-index:9999;top:12px;left:12px;" +
        "right:12px;padding:14px;border-radius:8px;" +
        "color:#7a1515;background:#fff0f0;text-align:center;";
      (document.body || document.documentElement).appendChild(message);
    }
    message.textContent = text;
  };

  const loadSupabase = () =>
    new Promise((resolve, reject) => {
      if (window.supabase?.createClient) {
        resolve();
        return;
      }
      const script = document.createElement("script");
      script.src =
        "https://cdn.jsdelivr.net/npm/" +
        "@supabase/supabase-js@2.119.0/dist/umd/supabase.js";
      script.integrity =
        "sha256-qGftvPsCk3Cu7HIj3WGAtWC2IfvjvGTGWE+wNp0be84=";
      script.crossOrigin = "anonymous";
      script.onload = resolve;
      script.onerror = () =>
        reject(
          new Error(
            "No se pudo cargar el servicio de autenticación."
          )
        );
      document.head.appendChild(script);
    });

  const start = async () => {
    await loadSupabase();
    const auth = window.supabase.createClient(url, anonKey, {
      auth: {
        flowType: "pkce",
        persistSession: true,
        storage: window.sessionStorage,
        autoRefreshToken: true,
        detectSessionInUrl: false
      }
    });

    const syncCookie = async (session) => {
      const response = await fetch("/auth/session", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          access_token: session.access_token
        })
      });
      if (response.status === 401 || response.status === 403) {
        const logoutResponse = await fetch("/auth/logout", {
          method: "POST",
          credentials: "same-origin"
        });
        if (!logoutResponse.ok) {
          throw new Error("No fue posible cerrar la sesión vencida.");
        }
        location.replace(loginUrl());
        return false;
      }
      if (!response.ok) {
        throw new Error("No fue posible renovar la sesión de Quirón.");
      }
      return true;
    };

    auth.auth.onAuthStateChange((event, session) => {
      if (event === "TOKEN_REFRESHED" && session) {
        setTimeout(() => {
          syncCookie(session).catch((error) =>
            showError(error.message)
          );
        }, 0);
      }
    });

    const status = await fetch("/auth/status", {
      credentials: "same-origin"
    });
    if (status.ok) return;
    if (status.status !== 401) {
      throw new Error("No fue posible verificar la sesión de Quirón.");
    }

    const { data, error } = await auth.auth.getSession();
    if (error) throw error;
    if (!data.session) {
      location.replace(loginUrl());
      return;
    }
    const { data: assurance, error: assuranceError } =
      await auth.auth.mfa.getAuthenticatorAssuranceLevel();
    if (assuranceError) throw assuranceError;
    if (assurance.currentLevel !== "aal2") {
      location.replace(loginUrl());
      return;
    }
    if (await syncCookie(data.session)) location.reload();
  };

  start().catch((error) => {
    showError(
      error.message ||
      "No fue posible verificar la sesión. Recarga la página o inicia sesión de nuevo."
    );
  });
})();
