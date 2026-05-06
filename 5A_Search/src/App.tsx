import { useState, useEffect, useCallback } from "react";
import SearchHome from "./components/SearchHome";
import ResultsPage from "./components/ResultsPage";
import { sanitizeQuery, secureConsole, getShellCommandCount, incrementShellCommandCount, checkSecurityHeaders } from "./utils/security";

type Page = "home" | "results";

export default function App() {
  const [page, setPage] = useState<Page>("home");
  const [query, setQuery] = useState("");
  const [activeTab, setActiveTab] = useState("all");
  const [isDark, setIsDark] = useState(false);
  const [shellCount, setShellCount] = useState(0);

  // Load preferences
  useEffect(() => {
    try {
      const savedDark = localStorage.getItem("5*A-dark-mode");
      if (savedDark === "true") setIsDark(true);
    } catch {}

    // Initialize security
    secureConsole();

    // Load shell command counter
    const count = getShellCommandCount();
    setShellCount(count);
    incrementShellCommandCount();
    console.log(`[5*A] Shell session #${count + 1} | Security initialized`);

    // Check security headers in development
    if (import.meta.env.DEV) {
      const score = checkSecurityHeaders();
      console.log(`[5*A] Security Score: ${score.score}/${score.maxScore}`);
    }
  }, []);

  // Handle URL params for bookmarkability
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const q = params.get("q");
    if (q) {
      setQuery(q);
      setPage("results");
    }
  }, []);

  // Save dark mode preference
  useEffect(() => {
    try {
      localStorage.setItem("5*A-dark-mode", String(isDark));
    } catch {}
  }, [isDark]);

  const handleSearch = useCallback((searchQuery: string) => {
    // Sanitize query before processing
    const sanitized = sanitizeQuery(searchQuery);
    if (!sanitized) return;

    setQuery(sanitized);
    setPage("results");
    setActiveTab("all");
    window.history.pushState({}, "", `?q=${encodeURIComponent(sanitized)}`);
    document.title = `${sanitized} — 5*A Search`;
  }, []);

  const handleGoHome = useCallback(() => {
    setPage("home");
    setQuery("");
    setActiveTab("all");
    window.history.pushState({}, "", "/");
    document.title = "5*A — Search Engine";
  }, []);

  const handleTabChange = useCallback((tab: string) => {
    setActiveTab(tab);
  }, []);

  const handleToggleDark = useCallback((dark: boolean) => {
    setIsDark(dark);
  }, []);

  return (
    <div
      className={`min-h-screen transition-colors duration-500 ${
        isDark ? "bg-[#0a0a0a] text-white" : "bg-white text-[#111]"
      }`}
    >
      {page === "home" ? (
        <SearchHome
          onSearch={handleSearch}
          isDark={isDark}
          onToggleDark={handleToggleDark}
          shellCount={shellCount}
        />
      ) : (
        <ResultsPage
          query={query}
          activeTab={activeTab}
          onTabChange={handleTabChange}
          onSearch={handleSearch}
          onGoHome={handleGoHome}
          isDark={isDark}
          onToggleDark={handleToggleDark}
        />
      )}
    </div>
  );
}
