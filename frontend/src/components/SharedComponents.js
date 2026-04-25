import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Languages, PawPrint } from "lucide-react";
import { Button } from "@/components/ui/button";
import { translations } from "@/lib/translations";

export const BrandMark = ({ compact = false, config }) => (
  <div className="flex items-center gap-3" data-testid="brand-mark">
    <div className={`flex items-center justify-center rounded-2xl border border-white/10 bg-white/5 ${compact ? "h-9 w-9 md:h-11 md:w-11" : "h-11 w-11"}`}>
      {config?.logo_url ? (
        <img alt={config.business_name} className={`${compact ? "h-6 w-6 md:h-8 md:w-8" : "h-8 w-8"} object-contain`} src={config.logo_url} />
      ) : (
        <PawPrint className={`${compact ? "h-4 w-4 md:h-5 md:w-5" : "h-5 w-5"} text-red-500`} />
      )}
    </div>
    <div>
      <p className={`font-heading font-semibold tracking-[0.25em] text-zinc-300 ${compact ? "text-xs md:text-sm" : "text-sm"}`} data-testid="brand-name">
        {config?.business_name || "PAWS TRAINING"}
      </p>
      <p className={`${compact ? "hidden text-[11px] md:block" : "text-xs"} text-zinc-500`} data-testid="brand-slogan">
        {config?.slogan || "BY PET LOVERS SITTING"}
      </p>
    </div>
  </div>
);

export const AppFooter = ({ config, className = "" }) => (
  <footer className={className} data-testid="app-footer">
    <div className="section-shell pb-8 pt-2">
      <div className="rounded-3xl border border-white/10 bg-white/5 px-6 py-4 text-center text-sm text-zinc-500">
        © {config?.business_name || "PAWS TRAINING"}
      </div>
    </div>
  </footer>
);

export const LanguageToggle = ({ language, setLanguage }) => (
  <div className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 p-1" data-testid="language-toggle">
    <Button
      className={language === "es" ? "bg-primary text-white hover:bg-red-700" : "bg-transparent text-zinc-300 hover:bg-white/5"}
      data-testid="language-es-button"
      onClick={() => setLanguage("es")}
      size="sm"
      type="button"
      variant="ghost"
    >
      <Languages className="mr-1 h-4 w-4" /> ES
    </Button>
    <Button
      className={language === "en" ? "bg-primary text-white hover:bg-red-700" : "bg-transparent text-zinc-300 hover:bg-white/5"}
      data-testid="language-en-button"
      onClick={() => setLanguage("en")}
      size="sm"
      type="button"
      variant="ghost"
    >
      EN
    </Button>
  </div>
);

export const PublicHeader = ({ compact = false, config, language, setLanguage, showAdminAccess = false, t }) => (
  <header className={`section-shell sticky top-0 z-40 ${compact ? "pt-2 md:pt-6" : "pt-6"}`}>
    <div className={`surface-panel flex flex-wrap items-center justify-between rounded-3xl backdrop-blur ${compact ? "gap-2 px-3 py-2 md:gap-3 md:px-5 md:py-4" : "gap-4 px-5 py-4"}`}>
      <BrandMark compact={compact} config={config} />
      <div className={`flex items-center gap-2 ${compact ? "w-full justify-between md:w-auto md:flex-wrap md:justify-normal md:gap-3" : "flex-wrap gap-3"}`}>
        <nav className={`flex items-center text-zinc-300 ${compact ? "gap-1 text-xs md:gap-2 md:text-sm" : "gap-2 text-sm"}`}>
          <Link className={`rounded-full transition-colors hover:bg-white/5 ${compact ? "px-2.5 py-1.5 md:px-4 md:py-2" : "px-4 py-2"}`} data-testid="nav-home-link" to="/">
            {t.home}
          </Link>
          <Link className={`rounded-full transition-colors hover:bg-white/5 ${compact ? "px-2.5 py-1.5 md:px-4 md:py-2" : "px-4 py-2"}`} data-testid="nav-book-link" to="/book">
            {t.booking}
          </Link>
          {showAdminAccess && (
            <Link className={`rounded-full transition-colors hover:bg-white/5 ${compact ? "px-2.5 py-1.5 md:px-4 md:py-2" : "px-4 py-2"}`} data-testid="nav-admin-link" to="/admin/login">
              {t.admin}
            </Link>
          )}
        </nav>
        <LanguageToggle language={language} setLanguage={setLanguage} />
      </div>
    </div>
  </header>
);

export const MeasuredChart = ({ children, className = "h-[200px] sm:h-[260px] md:h-[320px]" }) => {
  const containerRef = useRef(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return undefined;
    const updateSize = () => {
      const rect = element.getBoundingClientRect();
      setSize({ width: Math.floor(rect.width), height: Math.floor(rect.height) });
    };
    updateSize();
    const observer = new ResizeObserver(updateSize);
    observer.observe(element);
    window.requestAnimationFrame(updateSize);
    return () => observer.disconnect();
  }, []);

  return (
    <div className={`${className} min-w-0 w-full`} ref={containerRef}>
      {size.width > 0 && size.height > 0 ? children(size) : <div className="h-full w-full rounded-2xl bg-white/5" />}
    </div>
  );
};

export const useTranslation = (language) => translations[language];
