import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import "@/App.css";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  BrowserRouter,
  Link,
  Navigate,
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
} from "react-router-dom";
import {
  AlertTriangle,
  CalendarRange,
  CheckCircle2,
  CreditCard,
  Dog,
  FileText,
  Home,
  Languages,
  LayoutDashboard,
  Lock,
  LogOut,
  Mail,
  MapPinned,
  PawPrint,
  Phone,
  Search,
  Settings,
  ShieldCheck,
  UploadCloud,
  X,
  ZoomIn,
  ZoomOut,
  Maximize,
  ExternalLink,
  Download,
  Users,
  Trash2,
  Plus,
  KeyRound,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Toaster } from "@/components/ui/sonner";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { adminApi, openProtectedDocument, publicApi } from "@/lib/api";
import { translations } from "@/lib/translations";

const HERO_IMAGE = "https://res.cloudinary.com/dyuksod2i/image/upload/f_auto,q_auto:good,w_1400,c_limit/pawstraining/defaults/hero-default";
const CONTENT_IMAGE = "https://res.cloudinary.com/dyuksod2i/image/upload/f_auto,q_auto:good,w_800,c_limit/pawstraining/defaults/program-default";
const CHART_COLORS = ["#dc2626", "#d4d4d8", "#22c55e", "#3b82f6", "#facc15", "#8b5cf6"];
const STATUS_OPTIONS = ["Pending Review", "Approved", "Rejected", "Scheduled", "In Training", "Delivered", "Cancelled", "Expired"];
const DOC_STATUS_OPTIONS = ["Pending Review", "Verified", "Invalid"];
const ELIGIBILITY_OPTIONS = ["Pending Review", "Eligible", "Ineligible"];
const CURRENCY_OPTIONS = [
  { value: "USD", label: "$ USD" },
  { value: "EUR", label: "€ EUR" },
  { value: "GBP", label: "£ GBP" },
];
const LANDING_FEATURE_CARD_TEMPLATE = [
  { id: "base-capacity", title_es: "", title_en: "", description_es: "", description_en: "" },
  { id: "review-scope", title_es: "", title_en: "", description_es: "", description_en: "" },
  { id: "email-mode", title_es: "", title_en: "", description_es: "", description_en: "" },
];

const formatCurrency = (value, _language, currencyCode = "USD") => {
  const symbols = {
    USD: "$",
    EUR: "€",
    GBP: "£",
  };
  const amount = Number(value || 0);
  const amountText = Number.isInteger(amount) ? `${amount}` : amount.toFixed(2).replace(/\.00$/, "").replace(/(\.[1-9])0$/, "$1");
  return `${symbols[currencyCode] || "$"}${amountText}`;
};

const isValidEmailAddress = (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || "").trim());

const normalizeLandingContent = (landingContent = {}) => ({
  hero_description_es: landingContent?.hero_description_es || "",
  hero_description_en: landingContent?.hero_description_en || "",
  reserve_button_label_es: landingContent?.reserve_button_label_es || "",
  reserve_button_label_en: landingContent?.reserve_button_label_en || "",
  admin_button_label_es: landingContent?.admin_button_label_es || "",
  admin_button_label_en: landingContent?.admin_button_label_en || "",
  feature_cards: LANDING_FEATURE_CARD_TEMPLATE.map((card, index) => ({
    ...card,
    ...(Array.isArray(landingContent?.feature_cards) ? landingContent.feature_cards[index] || {} : {}),
  })),
});

const normalizeSettingsState = (settings = {}) => ({
  ...settings,
  currency: settings?.currency || "USD",
  landing_content: normalizeLandingContent(settings?.landing_content),
  smtp_host: settings?.smtp_host || "smtp.gmail.com",
  smtp_port: settings?.smtp_port || 587,
  smtp_tls: typeof settings?.smtp_tls === "boolean" ? settings.smtp_tls : true,
  smtp_username: settings?.smtp_username || "Pawstraningpr@gmail.com",
  smtp_password: "",
  smtp_password_masked: settings?.smtp_password_masked || "",
  smtp_password_configured: Boolean(settings?.smtp_password_configured),
});

const getLocalizedLandingText = (content, baseKey, language, fallback = "") =>
  content?.[`${baseKey}_${language}`] || fallback;

const calculateDogAge = (dateOfBirth, language) => {
  if (!dateOfBirth) return "";

  const birthDate = new Date(`${dateOfBirth}T00:00:00`);
  if (Number.isNaN(birthDate.getTime())) return "";

  const today = new Date();
  let years = today.getFullYear() - birthDate.getFullYear();
  let months = today.getMonth() - birthDate.getMonth();
  const days = today.getDate() - birthDate.getDate();

  if (days < 0) {
    months -= 1;
  }
  if (months < 0) {
    years -= 1;
    months += 12;
  }

  if (years < 0) return "";

  if (language === "es") {
    if (years > 0 && months > 0) return `${years} ${years === 1 ? "año" : "años"} y ${months} ${months === 1 ? "mes" : "meses"}`;
    if (years > 0) return `${years} ${years === 1 ? "año" : "años"}`;
    return `${months} ${months === 1 ? "mes" : "meses"}`;
  }

  if (years > 0 && months > 0) return `${years} ${years === 1 ? "year" : "years"} and ${months} ${months === 1 ? "month" : "months"}`;
  if (years > 0) return `${years} ${years === 1 ? "year" : "years"}`;
  return `${months} ${months === 1 ? "month" : "months"}`;
};

const formatDisplayDate = (isoDate, language) => {
  if (!isoDate) return "";
  const dateValue = new Date(`${isoDate}T00:00:00`);
  if (Number.isNaN(dateValue.getTime())) return isoDate;
  return new Intl.DateTimeFormat(language === "es" ? "es-ES" : "en-US", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(dateValue);
};

const getProgramDurationDays = (durationValue, durationUnit) => {
  const normalizedValue = Number(durationValue || 0);
  if (!normalizedValue) return 0;
  return durationUnit === "weeks" ? normalizedValue * 7 : normalizedValue;
};

const getProgramSpanWeeks = (program) => {
  if (!program) return 0;
  if (program.duration_unit === "weeks") return Math.max(Number(program.duration_value || 0), 1);
  return Math.max(Math.ceil(Number(program.duration_value || 0) / 7), 1);
};

const shiftIsoDateByWeeks = (isoDate, weekOffset) => {
  const baseDate = new Date(`${isoDate}T00:00:00`);
  if (Number.isNaN(baseDate.getTime())) return "";
  baseDate.setDate(baseDate.getDate() + weekOffset * 7);
  return baseDate.toISOString().split("T")[0];
};

const getScheduleDatesFromProgram = (startDateValue, durationValue, durationUnit) => {
  if (!startDateValue) {
    return { intake_date: "", delivery_date: "" };
  }

  const intakeDate = startDateValue;
  const startDate = new Date(`${intakeDate}T00:00:00`);
  if (Number.isNaN(startDate.getTime())) {
    return { intake_date: intakeDate, delivery_date: "" };
  }

  const totalDays = getProgramDurationDays(durationValue, durationUnit);
  if (!totalDays) {
    return { intake_date: intakeDate, delivery_date: "" };
  }

  const deliveryDate = new Date(startDate);
  deliveryDate.setDate(deliveryDate.getDate() + Math.max(totalDays - 1, 0));
  return {
    intake_date: intakeDate,
    delivery_date: deliveryDate.toISOString().split("T")[0],
  };
};

const formatMonthLabel = (dateValue, language) =>
  new Intl.DateTimeFormat(language === "es" ? "es-ES" : "en-US", {
    month: "long",
    year: "numeric",
  }).format(dateValue);

const buildReservationCalendarMonths = (weeks) => {
  const orderedWeeks = [...weeks].sort((left, right) => left.week_start.localeCompare(right.week_start));
  const monthMap = new Map();

  orderedWeeks.forEach((week) => {
    const dateValue = new Date(`${week.week_start}T00:00:00`);
    const monthKey = `${dateValue.getFullYear()}-${String(dateValue.getMonth() + 1).padStart(2, "0")}`;
    if (!monthMap.has(monthKey)) {
      monthMap.set(monthKey, { monthDate: new Date(dateValue.getFullYear(), dateValue.getMonth(), 1), weeks: [] });
    }
    monthMap.get(monthKey).weeks.push(week);
  });

  return Array.from(monthMap.values()).map(({ monthDate, weeks: monthWeeks }) => {
    const weekLookup = new Map(monthWeeks.map((week) => [week.week_start, week]));
    const firstDayIndex = (monthDate.getDay() + 6) % 7;
    const daysInMonth = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0).getDate();
    const totalCells = Math.ceil((firstDayIndex + daysInMonth) / 7) * 7;
    const cells = Array.from({ length: totalCells }, (_, index) => {
      const dayNumber = index - firstDayIndex + 1;
      if (dayNumber < 1 || dayNumber > daysInMonth) {
        return { id: `empty-${monthDate.toISOString()}-${index}`, isCurrentMonth: false, iso: null, week: null, dayNumber: null };
      }

      const cellDate = new Date(monthDate.getFullYear(), monthDate.getMonth(), dayNumber);
      const iso = `${cellDate.getFullYear()}-${String(cellDate.getMonth() + 1).padStart(2, "0")}-${String(cellDate.getDate()).padStart(2, "0")}`;
      return {
        id: iso,
        isCurrentMonth: true,
        iso,
        week: weekLookup.get(iso) || null,
        dayNumber,
      };
    });

    return { monthDate, cells };
  });
};

const getBookingScheduleDates = (booking) => {
  if (!booking?.start_week) {
    return { intake_date: "", delivery_date: "" };
  }
  return getScheduleDatesFromProgram(booking.start_week, booking.duration_value, booking.duration_unit);
};

const parseDogDateInput = (value) => {
  if (!value) return "";
  const parsed = new Date(`${value}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return "";

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  if (parsed > today) return "";

  return value;
};

const getStatusStyles = (status) => {
  if (["Approved", "Verified", "Eligible", "Delivered", "Paid in Full"].includes(status)) {
    return "border-green-500/25 bg-green-500/10 text-green-200";
  }
  if (["Pending Review", "almost_full", "In Training", "Scheduled", "Deposit Pending", "Balance Pending"].includes(status)) {
    return "border-yellow-500/25 bg-yellow-500/10 text-yellow-200";
  }
  if (["Deposit Verified"].includes(status)) {
    return "border-blue-500/25 bg-blue-500/10 text-blue-200";
  }
  if (["Rejected", "Invalid", "Cancelled", "Expired", "Ineligible", "full"].includes(status)) {
    return "border-red-500/25 bg-red-500/10 text-red-200";
  }
  return "border-zinc-700 bg-zinc-800/80 text-zinc-200";
};

const BrandMark = ({ compact = false, config }) => (
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

const AppFooter = ({ config, className = "" }) => (
  <footer className={className} data-testid="app-footer">
    <div className="section-shell pb-8 pt-2">
      <div className="rounded-3xl border border-white/10 bg-white/5 px-6 py-4 text-center text-sm text-zinc-500">
        © {config?.business_name || "PAWS TRAINING"}
      </div>
    </div>
  </footer>
);

const LanguageToggle = ({ language, setLanguage }) => (
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

const MeasuredChart = ({ children, className = "h-[200px] sm:h-[260px] md:h-[320px]" }) => {
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

const PublicHeader = ({ compact = false, config, language, setLanguage, showAdminAccess = false, t }) => (
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

const LandingPage = ({ config, programs, language, setLanguage, showAdminAccess }) => {
  const t = translations[language];
  const landingContent = normalizeLandingContent(config?.landing_content);
  const currencyCode = config?.currency || "USD";
  const heroImageSrc = config?.landing_hero_image_url || HERO_IMAGE;
  return (
    <div className="app-shell" data-testid="landing-page">
      <PublicHeader compact config={config} language={language} setLanguage={setLanguage} showAdminAccess={showAdminAccess} t={t} />
      <main className="section-shell space-y-12 pb-12 pt-12 md:pt-16">
        <section className="hero-section grid lg:grid-cols-[minmax(0,1.05fr)_minmax(360px,0.95fr)] lg:items-center">
          <div className="hero-copy-panel surface-panel reveal-up rounded-[2rem]">
            <Badge className="mb-6 border border-red-500/20 bg-red-500/10 px-4 py-2 text-xs uppercase tracking-[0.25em] text-red-200" data-testid="hero-label">
              {t.heroLabel}
            </Badge>
            <h1 className="hero-title max-w-3xl font-semibold text-white" data-testid="hero-title">
              {config?.business_name || "PAWS TRAINING"}
            </h1>
            <p className="hero-slogan" data-testid="hero-slogan">
              {config?.slogan || "BY PET LOVERS SITTING"}
            </p>
            <p className="hero-description" data-testid="hero-body">
              {getLocalizedLandingText(landingContent, "hero_description", language, t.heroBody)}
            </p>
            <div className="hero-actions">
              <Link data-testid="hero-booking-link" to="/book">
                <Button className="hero-primary-button rounded-full bg-primary text-white hover:bg-red-700">
                  {getLocalizedLandingText(landingContent, "reserve_button_label", language, t.reserveSpot)}
                </Button>
              </Link>
              {showAdminAccess && (
                <Link data-testid="hero-admin-link" to="/admin/login">
                  <Button className="hero-secondary-button rounded-full border border-white/10 bg-transparent text-white hover:bg-white/5" variant="outline">
                    {getLocalizedLandingText(landingContent, "admin_button_label", language, t.adminLogin)}
                  </Button>
                </Link>
              )}
            </div>
            <div className="hero-feature-grid">
              {landingContent.feature_cards.map((item) => (
                <div className="hero-feature-card" data-testid={`hero-stat-${item.id}`} key={item.id}>
                  <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">{language === "es" ? item.title_es : item.title_en}</p>
                  <p className="mt-2 text-sm font-semibold leading-6 text-white">{language === "es" ? item.description_es : item.description_en}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="hero-image-column reveal-up delay-1">
            <div className="hero-frame" data-testid="hero-image-frame">
              <img alt="Premium dog training" className="hero-image" src={heroImageSrc} />
            </div>
          </div>
        </section>

        <section className="grid gap-8 lg:grid-cols-[0.8fr_1.2fr]" id="programs">
          <Card className="surface-panel rounded-[2rem] border-white/10 p-0">
            <CardHeader>
              <CardTitle className="text-3xl text-white" data-testid="programs-title">
                {t.programsTitle}
              </CardTitle>
              <CardDescription className="text-zinc-400">
                {language === "es"
                  ? "Programas editables por el administrador con duración, precio y activación independiente."
                  : "Programs are fully manageable by the administrator with independent duration, pricing, and activation."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="media-frame">
                <img alt="Dog training program" src={CONTENT_IMAGE} />
              </div>
            </CardContent>
          </Card>
          <div className="grid gap-5 md:grid-cols-2">
            {programs.map((program, index) => (
              <Card className="surface-panel reveal-up rounded-[1.75rem] border-white/10" data-testid={`program-card-${program.id}`} key={program.id}>
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <CardTitle className="text-2xl text-white">{language === "es" ? program.name_es : program.name_en}</CardTitle>
                      <CardDescription className="mt-3 text-zinc-400">
                        {language === "es" ? program.description_es : program.description_en}
                      </CardDescription>
                    </div>
                    <Badge className={program.active ? "border-green-500/25 bg-green-500/10 text-green-200" : "border-zinc-700 bg-zinc-800 text-zinc-300"}>
                      {program.active ? t.active : t.inactive}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="flex items-center justify-between gap-4">
                  <div data-testid={`program-duration-${program.id}`}>
                    <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">{t.durationValue}</p>
                    <p className="mt-2 text-lg font-semibold text-white">
                      {program.duration_value} {program.duration_unit === "weeks" ? t.weeks : t.days}
                    </p>
                  </div>
                  <div className="text-right" data-testid={`program-price-${program.id}`}>
                    <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">{t.price}</p>
                    <p className="mt-2 text-lg font-semibold text-white">{formatCurrency(program.price, language, currencyCode)}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1fr_0.9fr]" id="process">
          <Card className="surface-panel rounded-[2rem] border-white/10">
            <CardHeader>
              <CardTitle className="text-3xl text-white" data-testid="process-title">
                {t.processTitle}
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4">
              {t.steps.map((step, index) => (
                <div className="rounded-2xl border border-white/10 bg-black/20 p-5" data-testid={`process-step-${index + 1}`} key={step}>
                  <p className="text-xs uppercase tracking-[0.25em] text-red-200">0{index + 1}</p>
                  <p className="mt-3 text-base text-zinc-200">{step}</p>
                </div>
              ))}
            </CardContent>
          </Card>
          <Card className="surface-panel rounded-[2rem] border-white/10">
            <CardHeader>
              <CardTitle className="text-3xl text-white" data-testid="contact-title">
                {t.contactTitle}
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 text-zinc-300">
              <div className="flex items-center gap-3" data-testid="contact-email-display">
                <Mail className="h-4 w-4 text-red-400" /> {config?.contact_email}
              </div>
              <div className="flex items-center gap-3" data-testid="contact-phone-display">
                <Phone className="h-4 w-4 text-red-400" /> {config?.contact_phone}
              </div>
              <div className="flex items-center gap-3" data-testid="contact-address-display">
                <MapPinned className="h-4 w-4 text-red-400" /> {config?.contact_address}
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-5 text-sm leading-7 text-zinc-400" data-testid="contact-note">
                {language === "es"
                  ? "La reserva pública y el panel privado viven en el mismo sistema, pero los documentos subidos permanecen protegidos y visibles solo para administradores."
                  : "The public booking flow and private admin dashboard live in one system, while uploaded documents remain protected and admin-only."}
              </div>
            </CardContent>
          </Card>
        </section>
      </main>
      <AppFooter config={config} />
    </div>
  );
};

const BookingPage = ({ config, programs, language, setLanguage, showAdminAccess }) => {
  const t = translations[language];
  const currencyCode = config?.currency || "USD";
  const [selectedProgramId, setSelectedProgramId] = useState(programs[0]?.id || "");
  const [weeks, setWeeks] = useState([]);
  const [loadingWeeks, setLoadingWeeks] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [bookingResult, setBookingResult] = useState(null);
  const [formState, setFormState] = useState({
    locale: language,
    owner_full_name: "",
    owner_email: "",
    confirm_email: "",
    owner_phone: "",
    owner_address: "",
    dog_name: "",
    breed: "",
    sex: "Male",
    weight: "",
    date_of_birth_input: "",
    vaccination_status: language === "es" ? translations.es.yes : translations.en.yes,
    allergies: "",
    behavior_goals: "",
    current_medication: "",
    additional_notes: "",
    start_week: "",
    payment_proof: null,
    vaccination_certificate: null,
    accept_deposit_policy: false,
  });

  const maxDogBirthDate = useMemo(() => new Date().toISOString().split("T")[0], []);
  const normalizedDogBirthDate = useMemo(() => parseDogDateInput(formState.date_of_birth_input), [formState.date_of_birth_input]);
  const computedDogAge = useMemo(() => calculateDogAge(normalizedDogBirthDate, language), [normalizedDogBirthDate, language]);
  const emailValidationMessage = useMemo(() => {
    if (!formState.owner_email) return "";
    if (!isValidEmailAddress(formState.owner_email)) return t.invalidEmailAddress;
    if (formState.confirm_email && formState.owner_email.trim().toLowerCase() !== formState.confirm_email.trim().toLowerCase()) {
      return t.emailMismatch;
    }
    return "";
  }, [formState.confirm_email, formState.owner_email, t.emailMismatch, t.invalidEmailAddress]);

  const selectedProgram = useMemo(() => programs.find((program) => program.id === selectedProgramId), [programs, selectedProgramId]);
  const calendarMonths = useMemo(() => buildReservationCalendarMonths(weeks), [weeks]);

  const loadWeeks = useCallback(async () => {
    if (!selectedProgramId) return;
    setLoadingWeeks(true);
    try {
      const response = await publicApi.getWeeks(selectedProgramId);
      setWeeks(response.weeks || []);
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoadingWeeks(false);
    }
  }, [selectedProgramId]);

  useEffect(() => {
    if (programs.length && !selectedProgramId) {
      setSelectedProgramId(programs[0].id);
    }
  }, [programs, selectedProgramId]);

  useEffect(() => {
    setFormState((current) => ({
      ...current,
      locale: language,
      vaccination_status: [translations.es.vaccinationUpToDate, translations.en.vaccinationUpToDate, translations.es.yes, translations.en.yes, "Up to date"].includes(current.vaccination_status)
        ? translations[language].yes
        : [translations.es.no, translations.en.no, "No"].includes(current.vaccination_status)
          ? translations[language].no
          : current.vaccination_status,
    }));
  }, [language]);

  useEffect(() => {
    loadWeeks();
  }, [loadWeeks]);

  const updateField = (name, value) => setFormState((current) => ({ ...current, [name]: value }));

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!formState.start_week) {
      toast.error(language === "es" ? "Selecciona una semana." : "Please select a week.");
      return;
    }
    if (!formState.confirm_email || emailValidationMessage) {
      toast.error(emailValidationMessage || t.emailMismatch);
      return;
    }
    if (!normalizedDogBirthDate) {
      toast.error(t.invalidDogBirthDate);
      return;
    }
    if (!formState.payment_proof || !formState.vaccination_certificate) {
      toast.error(language === "es" ? "Debes cargar ambos documentos." : "Both files are required.");
      return;
    }
    if (!formState.accept_deposit_policy) {
      toast.error(language === "es" ? "Debes aceptar la política de depósito." : "You must accept the deposit policy.");
      return;
    }
    setSubmitting(true);
    try {
      const payload = new FormData();
      payload.append("program_id", selectedProgramId);
      Object.entries(formState).forEach(([key, value]) => {
        if (key !== "confirm_email" && value !== null && value !== undefined) {
          payload.append(key, value);
        }
      });
      payload.delete("date_of_birth_input");
      payload.append("date_of_birth", normalizedDogBirthDate);
      payload.append("age", computedDogAge);
      const response = await publicApi.submitBooking(payload);
      setBookingResult(response);
      toast.success(t.bookingSubmitted);
      setFormState((current) => ({
        ...current,
        owner_full_name: "",
        owner_email: "",
        confirm_email: "",
        owner_phone: "",
        owner_address: "",
        dog_name: "",
        breed: "",
        weight: "",
        date_of_birth_input: "",
        vaccination_status: t.yes,
        allergies: "",
        behavior_goals: "",
        current_medication: "",
        additional_notes: "",
        payment_proof: null,
        vaccination_certificate: null,
      }));
      await loadWeeks();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="app-shell" data-testid="booking-page">
      <PublicHeader config={config} language={language} setLanguage={setLanguage} showAdminAccess={showAdminAccess} t={t} />
      <main className="section-shell grid gap-8 pb-12 pt-6 md:pt-10 lg:grid-cols-[0.9fr_1.1fr]">
        <Card className="surface-panel h-fit rounded-[2rem] border-white/10">
          <CardHeader>
            <CardTitle className="text-3xl text-white" data-testid="booking-title">
              {t.bookingFlowTitle}
            </CardTitle>
            <CardDescription className="text-zinc-400">
              {language === "es"
                ? "Selecciona programa, revisa semanas disponibles y sube tus documentos en una sola solicitud."
                : "Choose a program, review live weekly availability, and upload both documents in one request."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <label className="mb-2 block text-sm text-zinc-300">{t.selectProgram}</label>
              <select
                className="h-11 w-full rounded-xl border border-white/10 bg-zinc-950 px-3 text-white"
                data-testid="booking-program-select"
                onChange={(event) => {
                  setSelectedProgramId(event.target.value);
                  updateField("start_week", "");
                }}
                value={selectedProgramId}
              >
                {programs.map((program) => (
                  <option key={program.id} value={program.id}>
                    {language === "es" ? program.name_es : program.name_en}
                  </option>
                ))}
              </select>
            </div>
            {selectedProgram && (
              <div className="rounded-2xl border border-white/10 bg-black/20 p-5" data-testid="selected-program-summary">
                <p className="text-lg font-semibold text-white">{language === "es" ? selectedProgram.name_es : selectedProgram.name_en}</p>
                <p className="mt-2 text-sm text-zinc-400">{language === "es" ? selectedProgram.description_es : selectedProgram.description_en}</p>
                <div className="mt-4 flex flex-wrap gap-4 text-sm text-zinc-300">
                  <span>{selectedProgram.duration_value} {selectedProgram.duration_unit === "weeks" ? t.weeks : t.days}</span>
                  <span>{formatCurrency(selectedProgram.price, language, currencyCode)}</span>
                </div>
              </div>
            )}
            <div>
              <div className="mb-3 flex items-center justify-between gap-4">
                <label className="text-sm text-zinc-300">{t.selectWeek}</label>
                {loadingWeeks && <span className="text-xs text-zinc-500">{t.loadingWeeks}</span>}
              </div>
              <div className="rounded-[1.75rem] border border-white/10 bg-black/20 p-2 sm:p-4 md:p-5" data-testid="reservation-calendar-panel">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-white">{t.reservationCalendar}</p>
                    <p className="mt-1 text-xs text-zinc-500">{t.selectWeek}</p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-300" data-testid="reservation-calendar-legend">
                    <span className="rounded-full border border-green-500/25 bg-green-500/10 px-3 py-1 text-green-200">{t.status.available}</span>
                    <span className="rounded-full border border-yellow-500/25 bg-yellow-500/10 px-3 py-1 text-yellow-200">{t.status.almost_full}</span>
                    <span className="rounded-full border border-red-500/25 bg-red-500/10 px-3 py-1 text-red-200">{t.status.full}</span>
                  </div>
                </div>
                <div className="grid gap-4 xl:grid-cols-2">
                  {calendarMonths.map((month) => (
                    <div className="rounded-2xl border border-white/10 bg-zinc-950/70 p-2 sm:p-3" data-testid={`calendar-month-${month.monthDate.toISOString().slice(0, 7)}`} key={month.monthDate.toISOString()}>
                      <p className="mb-3 text-sm font-semibold capitalize text-white">{formatMonthLabel(month.monthDate, language)}</p>
                      <div className="mb-2 grid grid-cols-7 gap-0.5 sm:gap-1 text-center text-[11px] uppercase tracking-[0.16em] text-zinc-500">
                        {t.weekdaysShort.map((day) => (
                          <span key={`${month.monthDate.toISOString()}-${day}`}>{day}</span>
                        ))}
                      </div>
                      <div className="grid grid-cols-7 gap-0.5 sm:gap-1.5">
                        {month.cells.map((cell) => {
                          if (!cell.isCurrentMonth) {
                            return <div className="min-h-[44px] rounded-xl bg-transparent" key={cell.id} />;
                          }

                          if (!cell.week) {
                            return (
                              <div className="flex min-h-[44px] items-start justify-end rounded-xl border border-white/5 bg-white/[0.02] p-1.5 sm:p-2 text-xs text-zinc-600" key={cell.id}>
                                {cell.dayNumber}
                              </div>
                            );
                          }

                          const availabilityClasses =
                            cell.week.availability_label === "full"
                              ? "border-red-500/30 bg-red-500/12 text-red-100"
                              : cell.week.availability_label === "almost_full"
                                ? "border-yellow-500/30 bg-yellow-500/12 text-yellow-100"
                                : "border-green-500/30 bg-green-500/12 text-green-100";

                          return (
                            <button
                              className={`flex min-h-[44px] flex-col items-start justify-between rounded-xl border p-1.5 sm:p-2 text-left transition-transform duration-200 hover:-translate-y-[1px] disabled:cursor-not-allowed disabled:opacity-80 ${availabilityClasses} ${formState.start_week === cell.week.week_start ? "ring-2 ring-white/80" : ""}`}
                              data-testid={`week-card-${cell.week.week_start}`}
                              disabled={cell.week.remaining === 0}
                              key={cell.id}
                              onClick={() => updateField("start_week", cell.week.week_start)}
                              type="button"
                            >
                              <span className="text-sm font-semibold">{cell.dayNumber}</span>
                              <span className="text-[10px] leading-4">
                                {cell.week.remaining} {t.spacesLeft}
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
                {formState.start_week && (() => {
                  const selectedWeek = weeks.find((week) => week.week_start === formState.start_week);
                  if (!selectedWeek) return null;
                  return (
                    <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4" data-testid="selected-week-summary">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-white">{formatDisplayDate(selectedWeek.week_start, language)}</p>
                          <p className="mt-1 text-xs text-zinc-500">{selectedWeek.week_start}</p>
                        </div>
                        <Badge className={getStatusStyles(selectedWeek.availability_label)} data-testid={`week-status-${selectedWeek.week_start}`}>
                          {t.status[selectedWeek.availability_label]}
                        </Badge>
                      </div>
                      <p className="mt-3 text-sm text-zinc-300" data-testid={`week-capacity-${selectedWeek.week_start}`}>
                        {selectedWeek.remaining} / {selectedWeek.capacity} {t.spotsAvailable}
                      </p>
                    </div>
                  );
                })()}
              </div>
            </div>
            {bookingResult && (
              <div className="rounded-2xl border border-green-500/20 bg-green-500/10 p-4 text-sm text-green-100" data-testid="booking-success-panel">
                <p className="font-semibold">{t.bookingSubmitted}</p>
                <p className="mt-2">ID: {bookingResult.booking_id}</p>
                <p className="mt-1">{t.reservationSummaryPrice}: {formatCurrency(selectedProgram?.price, language, currencyCode)}</p>
                {selectedProgram && (() => {
                  const depType = selectedProgram.deposit_type || "percentage";
                  const depVal = selectedProgram.deposit_value ?? 100;
                  const dep = depType === "fixed" ? Math.min(depVal, selectedProgram.price) : Math.round(selectedProgram.price * depVal / 100 * 100) / 100;
                  const bal = Math.round((selectedProgram.price - dep) * 100) / 100;
                  return <p className="mt-1">{t.depositLabel}: {formatCurrency(dep, language, currencyCode)} · {t.balanceLabel}: {formatCurrency(bal, language, currencyCode)}</p>;
                })()}
                <p className="mt-1">
                  {t.reservationHeldUntil}: {bookingResult.reservation_expires_at}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="surface-panel rounded-[2rem] border-white/10">
          <CardHeader>
            <CardTitle className="text-3xl text-white">{t.bookingFlowTitle}</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="grid gap-6" onSubmit={handleSubmit}>
              <section className="grid gap-4 md:grid-cols-2">
                <div className="md:col-span-2">
                  <p className="mb-2 text-sm uppercase tracking-[0.2em] text-zinc-500">{t.ownerInformation}</p>
                </div>
                <Input data-testid="owner-full-name-input" onChange={(event) => updateField("owner_full_name", event.target.value)} placeholder={t.fullName} required value={formState.owner_full_name} />
                <Input data-testid="owner-email-input" onChange={(event) => updateField("owner_email", event.target.value)} placeholder={t.email} required type="email" value={formState.owner_email} />
                <Input data-testid="owner-confirm-email-input" onChange={(event) => updateField("confirm_email", event.target.value)} placeholder={t.confirmEmail} required type="email" value={formState.confirm_email} />
                <Input data-testid="owner-phone-input" onChange={(event) => updateField("owner_phone", event.target.value)} placeholder={t.phone} required type="tel" value={formState.owner_phone} />
                <Input data-testid="owner-address-input" onChange={(event) => updateField("owner_address", event.target.value)} placeholder={t.address} required value={formState.owner_address} />
                {emailValidationMessage && (
                  <p className="md:col-span-2 text-sm text-red-300" data-testid="owner-email-validation-message">
                    {emailValidationMessage}
                  </p>
                )}
              </section>
              <section className="grid gap-4 md:grid-cols-2">
                <div className="md:col-span-2">
                  <p className="mb-2 text-sm uppercase tracking-[0.2em] text-zinc-500">{t.dogInformation}</p>
                </div>
                <Input data-testid="dog-name-input" onChange={(event) => updateField("dog_name", event.target.value)} placeholder={t.dogName} required value={formState.dog_name} />
                <Input data-testid="dog-breed-input" onChange={(event) => updateField("breed", event.target.value)} placeholder={t.breed} required value={formState.breed} />
                <select className="h-11 rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="dog-sex-select" onChange={(event) => updateField("sex", event.target.value)} value={formState.sex}>
                  <option value="Male">{t.male}</option>
                  <option value="Female">{t.female}</option>
                </select>
                <Input data-testid="dog-weight-input" min="0" onChange={(event) => updateField("weight", event.target.value)} placeholder={t.weight} required step="0.1" type="number" value={formState.weight} />
                <div>
                  <label className="mb-2 block text-sm text-zinc-300" data-testid="dog-dob-label">{t.dob}</label>
                  <Input data-testid="dog-dob-input" max={maxDogBirthDate} onChange={(event) => updateField("date_of_birth_input", event.target.value)} required type="date" value={formState.date_of_birth_input} />
                  <p className="mt-2 text-sm text-zinc-400" data-testid="dog-age-display">
                    {t.automaticAge}: <span className="text-zinc-200">{computedDogAge || t.agePending}</span>
                  </p>
                </div>
                <div>
                  <label className="mb-2 block text-sm text-zinc-300" data-testid="dog-vaccination-status-label">{t.vaccinationStatus}</label>
                  <select className="h-11 w-full rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="dog-vaccination-status-input" onChange={(event) => updateField("vaccination_status", event.target.value)} value={formState.vaccination_status}>
                    <option value={t.yes}>{t.yes}</option>
                    <option value={t.no}>{t.no}</option>
                  </select>
                </div>
                <Input data-testid="dog-allergies-input" onChange={(event) => updateField("allergies", event.target.value)} placeholder={t.allergies} value={formState.allergies} />
                <div className="md:col-span-2">
                  <Textarea data-testid="dog-goals-textarea" onChange={(event) => updateField("behavior_goals", event.target.value)} placeholder={t.goals} required value={formState.behavior_goals} />
                </div>
                <Input data-testid="dog-medication-input" onChange={(event) => updateField("current_medication", event.target.value)} placeholder={t.medication} value={formState.current_medication} />
                <Input data-testid="dog-notes-input" onChange={(event) => updateField("additional_notes", event.target.value)} placeholder={t.notes} value={formState.additional_notes} />
              </section>
              <section className="grid gap-4 md:grid-cols-2">
                <div className="md:col-span-2">
                  <p className="mb-2 text-sm uppercase tracking-[0.2em] text-zinc-500">{t.documents}</p>
                </div>
                <div className="rounded-2xl border border-dashed border-white/10 bg-black/20 p-4">
                  <p className="mb-3 text-sm text-zinc-300">{t.paymentProof}</p>
                  <input accept=".pdf,image/*" data-testid="payment-proof-input" onChange={(event) => updateField("payment_proof", event.target.files?.[0] || null)} required type="file" />
                </div>
                <div className="rounded-2xl border border-dashed border-white/10 bg-black/20 p-4">
                  <p className="mb-3 text-sm text-zinc-300">{t.vaccinationCertificate}</p>
                  <input accept=".pdf,image/*" data-testid="vaccination-certificate-input" onChange={(event) => updateField("vaccination_certificate", event.target.files?.[0] || null)} required type="file" />
                </div>
              </section>
              <div className="rounded-2xl border border-yellow-500/20 bg-yellow-500/5 p-5" data-testid="deposit-policy-notice">
                <p className="text-sm font-semibold text-yellow-200">{t.depositPolicyTitle}</p>
                <p className="mt-2 text-sm text-yellow-200/80">{t.depositPolicyText}</p>
                <label className="mt-4 flex cursor-pointer items-start gap-3" data-testid="deposit-policy-checkbox-label">
                  <input checked={formState.accept_deposit_policy} className="mt-0.5 h-5 w-5 accent-red-500" data-testid="deposit-policy-checkbox" onChange={(event) => updateField("accept_deposit_policy", event.target.checked)} type="checkbox" />
                  <span className="text-sm text-zinc-200">{t.depositPolicyAccept}</span>
                </label>
              </div>
              <Button className="rounded-full bg-primary text-white hover:bg-red-700" data-testid="submit-booking-button" disabled={submitting || !formState.accept_deposit_policy} type="submit">
                {submitting ? "..." : t.submitBooking}
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
      <AppFooter config={config} />
    </div>
  );
};

const FinalPaymentPage = ({ language, setLanguage }) => {
  const { token } = useParams();
  const t = translations[language];
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [file, setFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const data = await publicApi.getBookingByPaymentToken(token);
        setBooking(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [token]);

  const lang = booking?.locale || language;
  const tt = translations[lang] || t;
  const fmt = (amount) => formatCurrency(amount, lang, booking?.currency || "USD");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    setSubmitting(true);
    try {
      await publicApi.uploadFinalPaymentByToken(token, file);
      setSubmitted(true);
      toast.success(tt.finalPaymentSuccess);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="flex min-h-screen items-center justify-center bg-black text-white">...</div>;

  if (error || !booking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-black p-4 text-center text-white" data-testid="payment-link-error">
        <div className="space-y-4">
          <AlertTriangle className="mx-auto h-12 w-12 text-red-500" />
          <p className="text-lg">{tt.finalPaymentLinkInvalid}</p>
        </div>
      </div>
    );
  }

  const depositNotReady = booking.payment_status !== "Verified";
  const alreadyUploaded = booking.final_payment_proof_uploaded;

  return (
    <div className="flex min-h-screen items-center justify-center bg-black p-4" data-testid="final-payment-page">
      <Card className="w-full max-w-lg rounded-[2rem] border-white/10 bg-zinc-950 text-white">
        <CardHeader className="text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-red-500">{booking.business_name}</p>
          <CardTitle className="mt-2 text-2xl">{tt.finalPaymentPageTitle}</CardTitle>
          <CardDescription className="text-zinc-400">{tt.finalPaymentPageSubtitle}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-5 space-y-3" data-testid="payment-booking-summary">
            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">{tt.bookingSummary}</p>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <p className="text-zinc-400">{tt.ownerLabel}</p>
              <p className="text-zinc-200">{booking.owner_name}</p>
              <p className="text-zinc-400">{tt.dogLabel}</p>
              <p className="text-zinc-200">{booking.dog_name}</p>
              <p className="text-zinc-400">{tt.programName}</p>
              <p className="text-zinc-200">{lang === "es" ? booking.program_name_es : booking.program_name_en}</p>
              <p className="text-zinc-400">{tt.reservationSummaryPrice}</p>
              <p className="text-zinc-200">{fmt(booking.program_price)}</p>
              <p className="text-zinc-400">{tt.depositLabel}</p>
              <p className="text-green-400">{fmt(booking.deposit_amount)} <CheckCircle2 className="ml-1 inline h-4 w-4" /></p>
              <p className="text-zinc-400 font-semibold">{tt.remainingBalance}</p>
              <p className="text-white font-semibold text-lg">{fmt(booking.balance_amount)}</p>
            </div>
          </div>

          {depositNotReady ? (
            <div className="rounded-2xl border border-yellow-500/20 bg-yellow-500/5 p-5 text-center text-yellow-200" data-testid="deposit-not-ready-message">
              <AlertTriangle className="mx-auto mb-2 h-8 w-8" />
              <p>{tt.finalPaymentNotReady}</p>
            </div>
          ) : alreadyUploaded && !submitted ? (
            <div className="rounded-2xl border border-blue-500/20 bg-blue-500/5 p-5 text-center text-blue-200" data-testid="already-uploaded-message">
              <CheckCircle2 className="mx-auto mb-2 h-8 w-8" />
              <p>{tt.finalPaymentAlreadyUploaded}</p>
            </div>
          ) : submitted ? (
            <div className="rounded-2xl border border-green-500/20 bg-green-500/5 p-5 text-center text-green-200" data-testid="upload-success-message">
              <CheckCircle2 className="mx-auto mb-2 h-8 w-8" />
              <p>{tt.finalPaymentSuccess}</p>
            </div>
          ) : (
            <form className="space-y-4" data-testid="final-payment-form" onSubmit={handleSubmit}>
              <div className="rounded-2xl border border-dashed border-white/10 bg-black/20 p-4">
                <p className="mb-3 text-sm text-zinc-300">{tt.finalPaymentUploadLabel}</p>
                <input accept=".pdf,image/*" data-testid="final-payment-file-input" onChange={(e) => setFile(e.target.files?.[0] || null)} required type="file" />
              </div>
              <Button className="w-full rounded-full bg-primary text-white hover:bg-red-700" data-testid="final-payment-submit-button" disabled={submitting || !file} type="submit">
                {submitting ? "..." : tt.finalPaymentSubmitButton}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

const AdminLoginPage = ({ config, language, setLanguage, onLogin, showAdminAccess }) => {
  const t = translations[language];
  const navigate = useNavigate();
  const [formState, setFormState] = useState({
    email: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      const response = await onLogin(formState);
      const userRole = response.admin?.role || "operator";
      navigate(userRole === "operator" ? "/admin/bookings" : "/admin/dashboard");
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell" data-testid="admin-login-page">
      <PublicHeader config={config} language={language} setLanguage={setLanguage} showAdminAccess={showAdminAccess} t={t} />
      <main className="section-shell grid gap-8 pt-14 lg:grid-cols-[0.8fr_1fr]">
        <Card className="surface-panel rounded-[2rem] border-white/10">
          <CardHeader>
            <CardTitle className="text-3xl text-white">{t.adminLogin}</CardTitle>
            <CardDescription className="text-zinc-400">
              {language === "es"
                ? "Panel privado para validar documentos, aprobar reservas y ajustar capacidad semanal."
                : "Private workspace to validate documents, approve bookings, and adjust weekly capacity."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-zinc-300">
            <div className="rounded-2xl border border-white/10 bg-black/20 p-5 text-sm leading-7 text-zinc-400">
              {language === "es"
                ? "El acceso administrativo permanece protegido y las notificaciones por correo se gestionan desde la configuración del sistema."
                : "Administrative access stays protected, and email notifications are managed from system settings."}
            </div>
          </CardContent>
        </Card>
        <Card className="surface-panel rounded-[2rem] border-white/10">
          <CardHeader>
            <CardTitle className="text-3xl text-white">{t.login}</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4" onSubmit={handleSubmit}>
              <Input data-testid="admin-email-input" onChange={(event) => setFormState((current) => ({ ...current, email: event.target.value }))} placeholder={t.email} required type="email" value={formState.email} />
              <Input data-testid="admin-password-input" onChange={(event) => setFormState((current) => ({ ...current, password: event.target.value }))} placeholder={t.password} required type="password" value={formState.password} />
              <Button className="rounded-full bg-primary text-white hover:bg-red-700" data-testid="admin-login-submit-button" disabled={loading} type="submit">
                <Lock className="mr-2 h-4 w-4" /> {loading ? "..." : t.login}
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
      <AppFooter config={config} />
    </div>
  );
};

const MetricCard = ({ title, value, subtitle, testId }) => (
  <Card className="surface-panel metric-card rounded-[1.75rem] border-white/10" data-testid={testId}>
    <CardHeader>
      <CardDescription className="text-xs uppercase tracking-[0.2em] text-zinc-500">{title}</CardDescription>
    </CardHeader>
    <CardContent>
      <p className="metric-value text-white">{value}</p>
      <p className="mt-3 text-sm text-zinc-400">{subtitle}</p>
    </CardContent>
  </Card>
);

const DocumentPreviewModal = ({ doc, onClose, language }) => {
  const t = translations[language];
  const [zoom, setZoom] = useState(1);
  if (!doc) return null;
  const openNewTab = () => window.open(doc.url, "_blank", "noopener,noreferrer");
  const downloadFile = () => { const a = document.createElement("a"); a.href = doc.url; a.download = doc.filename; a.click(); };
  return (
    <div className="fixed inset-0 z-[200] flex flex-col bg-black/90" data-testid="doc-preview-overlay" onClick={onClose}>
      <div className="flex items-center justify-between border-b border-white/10 bg-zinc-950 px-4 py-3" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-3">
          <p className="text-sm font-medium text-white truncate max-w-[200px] sm:max-w-none">{doc.filename}</p>
          <span className="rounded-full bg-white/10 px-2 py-0.5 text-xs text-zinc-400">{doc.contentType}</span>
        </div>
        <div className="flex items-center gap-2">
          {doc.type === "image" && (
            <>
              <button className="rounded-lg p-2 text-zinc-400 hover:bg-white/10 hover:text-white" data-testid="zoom-out-btn" onClick={() => setZoom((z) => Math.max(0.25, z - 0.25))} title="Zoom out"><ZoomOut className="h-4 w-4" /></button>
              <span className="w-12 text-center text-xs text-zinc-400">{Math.round(zoom * 100)}%</span>
              <button className="rounded-lg p-2 text-zinc-400 hover:bg-white/10 hover:text-white" data-testid="zoom-in-btn" onClick={() => setZoom((z) => Math.min(5, z + 0.25))} title="Zoom in"><ZoomIn className="h-4 w-4" /></button>
              <button className="rounded-lg p-2 text-zinc-400 hover:bg-white/10 hover:text-white" data-testid="fit-screen-btn" onClick={() => setZoom(1)} title="Fit to screen"><Maximize className="h-4 w-4" /></button>
            </>
          )}
          <button className="rounded-lg p-2 text-zinc-400 hover:bg-white/10 hover:text-white" data-testid="open-new-tab-btn" onClick={openNewTab} title={t.openNewTab}><ExternalLink className="h-4 w-4" /></button>
          <button className="rounded-lg p-2 text-zinc-400 hover:bg-white/10 hover:text-white" data-testid="download-doc-btn" onClick={downloadFile} title={t.downloadFile}><Download className="h-4 w-4" /></button>
          <button className="rounded-lg p-2 text-zinc-400 hover:bg-white/10 hover:text-white" data-testid="close-preview-button" onClick={onClose}><X className="h-5 w-5" /></button>
        </div>
      </div>
      <div className="flex flex-1 items-center justify-center overflow-auto p-4" onClick={(e) => e.stopPropagation()}>
        {doc.type === "image" ? (
          <img alt="Document preview" className="rounded-lg object-contain transition-transform duration-200" data-testid="image-preview-img" src={doc.url} style={{ transform: `scale(${zoom})`, maxHeight: "85vh", maxWidth: "95vw" }} />
        ) : doc.type === "pdf" ? (
          <iframe className="h-full w-full max-w-4xl rounded-lg border border-white/10 bg-white" data-testid="pdf-preview-frame" src={doc.url} style={{ minHeight: "75vh" }} title="PDF Preview" />
        ) : (
          <div className="flex flex-col items-center gap-4 rounded-2xl border border-white/10 bg-zinc-950 p-8 text-center" data-testid="unsupported-preview">
            <FileText className="h-16 w-16 text-zinc-500" />
            <p className="text-lg font-medium text-white">{doc.filename}</p>
            <p className="text-sm text-zinc-400">{doc.contentType}</p>
            <div className="flex gap-3">
              <Button data-testid="unsupported-open-btn" onClick={openNewTab} variant="outline"><ExternalLink className="mr-2 h-4 w-4" /> {t.openNewTab}</Button>
              <Button data-testid="unsupported-download-btn" onClick={downloadFile}><Download className="mr-2 h-4 w-4" /> {t.downloadFile}</Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const DocActionButtons = ({ label, icon: Icon, hasFile, onPreview, onOpenTab, onDownload, testIdPrefix }) => (
  <div className="flex items-center gap-1.5">
    <Button className="touch-button flex-1 rounded-full text-xs" data-testid={`${testIdPrefix}-preview-btn`} disabled={!hasFile} onClick={onPreview} size="sm" variant="outline">
      <Icon className="mr-1.5 h-3.5 w-3.5" /> {label}
    </Button>
    <button className="rounded-lg p-1.5 text-zinc-500 hover:bg-white/10 hover:text-white disabled:opacity-30" data-testid={`${testIdPrefix}-newtab-btn`} disabled={!hasFile} onClick={onOpenTab} title="Open in new tab"><ExternalLink className="h-3.5 w-3.5" /></button>
    <button className="rounded-lg p-1.5 text-zinc-500 hover:bg-white/10 hover:text-white disabled:opacity-30" data-testid={`${testIdPrefix}-download-btn`} disabled={!hasFile} onClick={onDownload} title="Download"><Download className="h-3.5 w-3.5" /></button>
  </div>
);

const BookingDetailDialog = ({ booking, language, onClose, onSave, token, currencyCode, onFinalPaymentUpload, adminRole }) => {
  const t = translations[language];
  const [formState, setFormState] = useState(null);
  const [uploadingFinal, setUploadingFinal] = useState(false);
  const [previewDoc, setPreviewDoc] = useState(null);
  const isOp = adminRole === "operator";

  useEffect(() => {
    if (booking) {
      setFormState({
        status: booking.status,
        payment_status: booking.payment_status,
        final_payment_status: booking.final_payment_status || "Pending Review",
        vaccination_certificate_status: booking.vaccination_certificate_status,
        eligibility_status: booking.eligibility_status,
        internal_notes: booking.internal_notes || "",
        rejection_reason: booking.rejection_reason || "",
      });
    }
  }, [booking]);

  if (!booking || !formState) return null;

  const scheduleDates = getBookingScheduleDates(booking);
  const overallPayment = booking.overall_payment_status || "Deposit Pending";

  const saveChanges = async () => {
    // Operators can only update status field
    const payload = isOp
      ? { status: formState.status }
      : {
          ...formState,
          intake_date: scheduleDates.intake_date || null,
          delivery_date: scheduleDates.delivery_date || null,
        };
    await onSave(booking.id, payload);
    onClose();
  };

  const handleFinalPaymentUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploadingFinal(true);
    try {
      await onFinalPaymentUpload(booking.id, file);
      toast.success(language === "es" ? "Comprobante final subido." : "Final payment proof uploaded.");
    } catch (error) {
      toast.error(error.message);
    } finally {
      setUploadingFinal(false);
      event.target.value = "";
    }
  };

  const fetchDoc = async (documentType) => {
    try {
      return await openProtectedDocument(token, booking.id, documentType);
    } catch (err) {
      toast.error(err.message);
      return null;
    }
  };
  const handlePreview = async (docType) => { const d = await fetchDoc(docType); if (d) setPreviewDoc(d); };
  const handleOpenTab = async (docType) => { const d = await fetchDoc(docType); if (d) window.open(d.url, "_blank", "noopener,noreferrer"); };
  const handleDownload = async (docType) => { const d = await fetchDoc(docType); if (d) { const a = document.createElement("a"); a.href = d.url; a.download = d.filename; a.click(); } };
  const closePreview = () => { if (previewDoc) URL.revokeObjectURL(previewDoc.url); setPreviewDoc(null); };

  return (
    <Dialog onOpenChange={(open) => !open && onClose()} open={Boolean(booking)}>
      <DialogContent aria-describedby="booking-detail-description" className="mobile-dialog-content max-w-4xl border-white/10 bg-zinc-950 text-white" data-testid="booking-detail-dialog">
        <DialogHeader>
          <DialogTitle>{booking.dog.name} · {booking.owner.full_name}</DialogTitle>
          <DialogDescription className="text-zinc-400" id="booking-detail-description">{booking.start_week} · {booking.program_name_es} · {booking.owner.email}</DialogDescription>
        </DialogHeader>
        <div className="mobile-dialog-grid grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
          <div className="space-y-4 rounded-2xl border border-white/10 bg-white/5 p-5">
            <div data-testid="booking-owner-summary">
              <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">{t.ownerLabel}</p>
              <p className="mt-2 text-sm text-zinc-200">{booking.owner.full_name}</p>
              <p className="text-sm text-zinc-400">{booking.owner.email}</p>
              <p className="text-sm text-zinc-400">{booking.owner.phone}</p>
            </div>
            <div data-testid="booking-dog-summary">
              <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">{t.dogLabel}</p>
              <p className="mt-2 text-sm text-zinc-200">{booking.dog.name} · {booking.dog.breed}</p>
              <p className="text-sm text-zinc-400">{booking.dog.behavior_goals}</p>
            </div>
            <div data-testid="booking-program-summary">
              <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">{t.programName}</p>
              <p className="mt-2 text-sm text-zinc-200">{language === "es" ? booking.program_name_es : booking.program_name_en}</p>
              {!isOp && (
                <>
                  <p className="text-sm text-zinc-400">{t.reservationSummaryPrice}: {formatCurrency(booking.program_price, language, currencyCode)}</p>
                  <p className="text-sm text-zinc-400">{t.depositLabel}: {formatCurrency(booking.deposit_amount, language, currencyCode)} · {t.balanceLabel}: {formatCurrency(booking.balance_amount, language, currencyCode)}</p>
                </>
              )}
            </div>
            {!isOp && (
              <div data-testid="booking-overall-payment">
                <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">{t.overallPaymentLabel}</p>
                <Badge className={`mt-2 ${getStatusStyles(overallPayment)}`} data-testid="overall-payment-badge">{t.status[overallPayment] || overallPayment}</Badge>
              </div>
            )}
            {isOp && (
              <div data-testid="booking-payment-status-simple">
                <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">{t.depositProofField}</p>
                <p className="mt-1 text-sm text-zinc-200">{booking.payment_status === "Paid" || booking.payment_status === "Verified" ? (language === "es" ? "Pagado" : "Paid") : (language === "es" ? "Pendiente" : "Pending")}</p>
                <p className="mt-2 text-xs uppercase tracking-[0.2em] text-zinc-500">{t.finalPaymentStatusField}</p>
                <p className="mt-1 text-sm text-zinc-200">{booking.final_payment_status === "Paid" || booking.final_payment_status === "Verified" ? (language === "es" ? "Pagado" : "Paid") : (language === "es" ? "Pendiente" : "Pending")}</p>
              </div>
            )}
            <div className="flex flex-wrap gap-2" data-testid="medical-flags-panel">
              {booking.medical_flags.map((flag) => (
                <span className="status-chip bg-black/20 text-zinc-200" key={flag.label}>{flag.label}</span>
              ))}
            </div>
            <div className="space-y-3">
              <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">{t.documents}</p>
              <DocActionButtons hasFile={!!booking.payment_proof} icon={FileText} label={t.depositProofField} onDownload={() => handleDownload("payment_proof")} onOpenTab={() => handleOpenTab("payment_proof")} onPreview={() => handlePreview("payment_proof")} testIdPrefix="deposit-proof" />
              <DocActionButtons hasFile={!!booking.vaccination_certificate} icon={ShieldCheck} label={t.vaccinationCertificate} onDownload={() => handleDownload("vaccination_certificate")} onOpenTab={() => handleOpenTab("vaccination_certificate")} onPreview={() => handlePreview("vaccination_certificate")} testIdPrefix="vaccine-cert" />
              {!isOp && (booking.final_payment_proof ? (
                <DocActionButtons hasFile icon={CreditCard} label={t.finalPaymentProofField} onDownload={() => handleDownload("final_payment_proof")} onOpenTab={() => handleOpenTab("final_payment_proof")} onPreview={() => handlePreview("final_payment_proof")} testIdPrefix="final-payment" />
              ) : (
                <label className="touch-button inline-flex w-full cursor-pointer items-center justify-center rounded-full border border-dashed border-white/20 px-4 py-2.5 text-sm text-zinc-400 transition-colors hover:border-white/40 hover:text-white" data-testid="upload-final-payment-button">
                  <UploadCloud className="mr-2 h-4 w-4" /> {uploadingFinal ? "..." : t.uploadFinalPaymentProof}
                  <input accept=".pdf,image/*" className="hidden" disabled={uploadingFinal} onChange={handleFinalPaymentUpload} type="file" />
                </label>
              ))}
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm text-zinc-300" data-testid="booking-status-label">{t.bookingStatusField}</label>
              <select className="h-11 w-full rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="booking-status-select" onChange={(event) => setFormState((current) => ({ ...current, status: event.target.value }))} value={formState.status}>
                {STATUS_OPTIONS.map((option) => <option key={option} value={option}>{t.status[option] || option}</option>)}
              </select>
            </div>
            {!isOp && (
              <>
                <div>
                  <label className="mb-2 block text-sm text-zinc-300" data-testid="payment-status-label">{t.depositProofField}</label>
                  <select className="h-11 w-full rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="payment-status-select" onChange={(event) => setFormState((current) => ({ ...current, payment_status: event.target.value }))} value={formState.payment_status}>
                    {DOC_STATUS_OPTIONS.map((option) => <option key={option} value={option}>{t.status[option] || option}</option>)}
                  </select>
                </div>
                <div>
                  <label className="mb-2 block text-sm text-zinc-300" data-testid="final-payment-status-label">{t.finalPaymentStatusField}</label>
                  <select className="h-11 w-full rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="final-payment-status-select" onChange={(event) => setFormState((current) => ({ ...current, final_payment_status: event.target.value }))} value={formState.final_payment_status}>
                    {DOC_STATUS_OPTIONS.map((option) => <option key={option} value={option}>{t.status[option] || option}</option>)}
                  </select>
                </div>
                <div>
                  <label className="mb-2 block text-sm text-zinc-300" data-testid="certificate-status-label">{t.vaccinationCertificateField}</label>
                  <select className="h-11 w-full rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="certificate-status-select" onChange={(event) => setFormState((current) => ({ ...current, vaccination_certificate_status: event.target.value }))} value={formState.vaccination_certificate_status}>
                    {DOC_STATUS_OPTIONS.map((option) => <option key={option} value={option}>{t.status[option] || option}</option>)}
                  </select>
                </div>
                <div>
                  <label className="mb-2 block text-sm text-zinc-300" data-testid="eligibility-status-label">{t.dogEligibilityField}</label>
                  <select className="h-11 w-full rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="eligibility-status-select" onChange={(event) => setFormState((current) => ({ ...current, eligibility_status: event.target.value }))} value={formState.eligibility_status}>
                    {ELIGIBILITY_OPTIONS.map((option) => <option key={option} value={option}>{t.status[option] || option}</option>)}
                  </select>
                </div>
                <div>
                  <label className="mb-2 block text-sm text-zinc-300" data-testid="intake-date-label">{t.intakeDateField}</label>
                  <Input data-testid="intake-date-input" readOnly type="text" value={scheduleDates.intake_date} />
                </div>
                <div>
                  <label className="mb-2 block text-sm text-zinc-300" data-testid="delivery-date-label">{t.deliveryDateField}</label>
                  <Input data-testid="delivery-date-input" readOnly type="text" value={scheduleDates.delivery_date} />
                </div>
                <div className="md:col-span-2">
                  <label className="mb-2 block text-sm text-zinc-300" data-testid="rejection-reason-label">{t.rejectionReasonField}</label>
                  <Input data-testid="rejection-reason-input" onChange={(event) => setFormState((current) => ({ ...current, rejection_reason: event.target.value }))} placeholder={t.rejectionReasonField} value={formState.rejection_reason} />
                </div>
                <div className="md:col-span-2">
                  <label className="mb-2 block text-sm text-zinc-300" data-testid="internal-notes-label">{t.internalNotesField}</label>
                  <Textarea data-testid="internal-notes-textarea" onChange={(event) => setFormState((current) => ({ ...current, internal_notes: event.target.value }))} placeholder={t.internalNotesField} value={formState.internal_notes} />
                </div>
              </>
            )}
            <div className="dialog-actions-row md:col-span-2">
              <Button className="touch-button" data-testid="close-booking-dialog-button" onClick={onClose} type="button" variant="outline">{t.close}</Button>
              <Button className="touch-button bg-primary text-white hover:bg-red-700" data-testid="save-booking-dialog-button" onClick={saveChanges} type="button">
                {t.saveChanges}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
      <DocumentPreviewModal doc={previewDoc} language={language} onClose={closePreview} />
    </Dialog>
  );
};

const ManualBookingDialog = ({ open, onClose, programs, onCreate, language, capacityWeeks }) => {
  const t = translations[language];
  const [formState, setFormState] = useState({
    program_id: programs[0]?.id || "",
    start_week: "2026-03-30",
    locale: language,
    owner_full_name: "",
    owner_email: "",
    owner_phone: "",
    owner_address: "",
    dog_name: "",
    breed: "",
    sex: "Male",
    weight: "",
    date_of_birth: "",
    vaccination_status: language === "es" ? t.yes : translations.en.yes,
    allergies: "",
    behavior_goals: "",
    current_medication: "",
    additional_notes: "",
    status: "Scheduled",
    internal_notes: "",
    payment_status: "Verified",
    final_payment_status: "Pending Review",
    vaccination_certificate_status: "Verified",
    eligibility_status: "Eligible",
  });
  const selectedProgram = useMemo(() => programs.find((program) => program.id === formState.program_id), [formState.program_id, programs]);
  const selectedProgramSpanWeeks = useMemo(() => getProgramSpanWeeks(selectedProgram), [selectedProgram]);
  const manualDogAge = useMemo(() => calculateDogAge(formState.date_of_birth, language), [formState.date_of_birth, language]);
  const manualScheduleDates = useMemo(
    () => getScheduleDatesFromProgram(formState.start_week, selectedProgram?.duration_value, selectedProgram?.duration_unit),
    [formState.start_week, selectedProgram],
  );
  const maxDogBirthDate = useMemo(() => new Date().toISOString().split("T")[0], []);
  const capacityWeekLookup = useMemo(() => new Map(capacityWeeks.map((week) => [week.week_start, week])), [capacityWeeks]);
  const weekOptions = useMemo(
    () =>
      capacityWeeks.map((week) => {
        const blockedBySpan = Array.from({ length: selectedProgramSpanWeeks }, (_, index) => shiftIsoDateByWeeks(week.week_start, index)).some(
          (candidateWeek) => {
            const candidateData = capacityWeekLookup.get(candidateWeek);
            return !candidateData || candidateData.remaining <= 0;
          },
        );

        return {
          ...week,
          isBlockedStart: blockedBySpan,
          displayStatus: blockedBySpan ? "full" : week.availability_label,
        };
      }),
    [capacityWeekLookup, capacityWeeks, selectedProgramSpanWeeks],
  );
  const selectedWeekOption = useMemo(() => weekOptions.find((week) => week.week_start === formState.start_week), [formState.start_week, weekOptions]);

  useEffect(() => {
    if (programs.length && !formState.program_id) {
      setFormState((current) => ({ ...current, program_id: programs[0].id }));
    }
  }, [formState.program_id, programs]);

  useEffect(() => {
    if (selectedWeekOption?.isBlockedStart) {
      setFormState((current) => ({ ...current, start_week: "" }));
    }
  }, [selectedWeekOption]);

  const update = (key, value) => setFormState((current) => ({ ...current, [key]: value }));

  const handleCreate = async () => {
    if (!formState.start_week || selectedWeekOption?.isBlockedStart) {
      toast.error(t.weekFullWarning);
      return;
    }
    await onCreate({
      ...formState,
      age: manualDogAge,
      intake_date: manualScheduleDates.intake_date || null,
      delivery_date: manualScheduleDates.delivery_date || null,
    });
    onClose();
  };

  return (
    <Dialog onOpenChange={(visible) => !visible && onClose()} open={open}>
      <DialogContent aria-describedby="manual-booking-description" className="mobile-dialog-content max-w-3xl border-white/10 bg-zinc-950 text-white" data-testid="manual-booking-dialog">
        <DialogHeader>
          <DialogTitle>{t.manualBooking}</DialogTitle>
          <DialogDescription className="text-zinc-400" id="manual-booking-description">
            {language === "es"
              ? "Registra compromisos existentes para reflejar ocupación real sin pasar por el formulario público."
              : "Create already-committed client bookings so occupancy reflects real operating conditions."}
          </DialogDescription>
        </DialogHeader>
        <div className="mobile-dialog-grid grid gap-4 md:grid-cols-2">
          <div>
            <label className="mb-2 block text-sm text-zinc-300" data-testid="manual-program-label">{t.programName}</label>
            <select className="h-11 w-full rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="manual-program-select" onChange={(event) => update("program_id", event.target.value)} value={formState.program_id}>
              {programs.map((program) => <option key={program.id} value={program.id}>{language === "es" ? program.name_es : program.name_en}</option>)}
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="mb-2 block text-sm text-zinc-300" data-testid="manual-start-week-label">{t.selectWeek}</label>
            <div className="grid max-h-56 gap-2 overflow-y-auto rounded-2xl border border-white/10 bg-black/20 p-3 sm:grid-cols-2" data-testid="manual-week-selector">
              {weekOptions.map((week) => {
                const weekClasses =
                  week.displayStatus === "full"
                    ? "border-red-500/30 bg-red-500/12 text-red-100"
                    : week.displayStatus === "almost_full"
                      ? "border-yellow-500/30 bg-yellow-500/12 text-yellow-100"
                      : "border-green-500/30 bg-green-500/12 text-green-100";

                return (
                  <button
                    className={`rounded-2xl border p-3 text-left transition-transform duration-200 hover:-translate-y-[1px] disabled:cursor-not-allowed disabled:opacity-80 ${weekClasses} ${formState.start_week === week.week_start ? "ring-2 ring-white/80" : ""}`}
                    data-testid={`manual-week-card-${week.week_start}`}
                    disabled={week.isBlockedStart}
                    key={week.week_start}
                    onClick={() => update("start_week", week.week_start)}
                    type="button"
                  >
                    <p className="text-sm font-semibold">{formatDisplayDate(week.week_start, language)}</p>
                    <p className="mt-2 text-xs">{week.remaining} {t.spacesLeft}</p>
                    <p className="mt-2 text-xs font-semibold uppercase tracking-[0.18em]">{t.status[week.displayStatus]}</p>
                  </button>
                );
              })}
            </div>
            {selectedWeekOption?.isBlockedStart && (
              <p className="mt-2 text-sm text-red-300" data-testid="manual-week-full-warning">{t.weekFullWarning}</p>
            )}
          </div>
          <Input data-testid="manual-owner-name-input" onChange={(event) => update("owner_full_name", event.target.value)} placeholder={t.fullName} value={formState.owner_full_name} />
          <Input data-testid="manual-owner-email-input" onChange={(event) => update("owner_email", event.target.value)} placeholder={t.email} type="email" value={formState.owner_email} />
          <Input data-testid="manual-owner-phone-input" onChange={(event) => update("owner_phone", event.target.value)} placeholder={t.phone} value={formState.owner_phone} />
          <Input data-testid="manual-owner-address-input" onChange={(event) => update("owner_address", event.target.value)} placeholder={t.address} value={formState.owner_address} />
          <Input data-testid="manual-dog-name-input" onChange={(event) => update("dog_name", event.target.value)} placeholder={t.dogName} value={formState.dog_name} />
          <Input data-testid="manual-dog-breed-input" onChange={(event) => update("breed", event.target.value)} placeholder={t.breed} value={formState.breed} />
          <Input data-testid="manual-dog-weight-input" onChange={(event) => update("weight", event.target.value)} placeholder={t.weight} value={formState.weight} />
          <div>
            <label className="mb-2 block text-sm text-zinc-300" data-testid="manual-dob-label">{t.dob}</label>
            <Input data-testid="manual-dob-input" max={maxDogBirthDate} onChange={(event) => update("date_of_birth", event.target.value)} type="date" value={formState.date_of_birth} />
          </div>
          <div>
            <label className="mb-2 block text-sm text-zinc-300" data-testid="manual-dog-age-label">{t.automaticAge}</label>
            <Input data-testid="manual-dog-age-input" readOnly type="text" value={manualDogAge || t.agePending} />
          </div>
          <div>
            <label className="mb-2 block text-sm text-zinc-300" data-testid="manual-vaccination-status-label">{t.vaccinationStatus}</label>
            <select className="h-11 w-full rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="manual-vaccination-status-input" onChange={(event) => update("vaccination_status", event.target.value)} value={formState.vaccination_status}>
              <option value={t.yes}>{t.yes}</option>
              <option value={t.no}>{t.no}</option>
            </select>
          </div>
          <div>
            <label className="mb-2 block text-sm text-zinc-300" data-testid="manual-booking-status-label">{t.bookingStatusField}</label>
            <select className="h-11 w-full rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="manual-booking-status-select" onChange={(event) => update("status", event.target.value)} value={formState.status}>
              {STATUS_OPTIONS.map((option) => <option key={option} value={option}>{t.status[option] || option}</option>)}
            </select>
          </div>
          <div>
            <label className="mb-2 block text-sm text-zinc-300" data-testid="manual-intake-date-label">{t.intakeDateField}</label>
            <Input data-testid="manual-intake-date-input" readOnly type="text" value={manualScheduleDates.intake_date || formState.start_week} />
          </div>
          <div>
            <label className="mb-2 block text-sm text-zinc-300" data-testid="manual-delivery-date-label">{t.deliveryDateField}</label>
            <Input data-testid="manual-delivery-date-input" readOnly type="text" value={manualScheduleDates.delivery_date || ""} />
          </div>
          <div className="md:col-span-2">
            <Textarea data-testid="manual-goals-textarea" onChange={(event) => update("behavior_goals", event.target.value)} placeholder={t.goals} value={formState.behavior_goals} />
          </div>
          <div className="dialog-actions-row md:col-span-2">
            <Button className="touch-button" data-testid="manual-booking-close-button" onClick={onClose} type="button" variant="outline">{t.close}</Button>
            <Button className="touch-button bg-primary text-white hover:bg-red-700" data-testid="manual-booking-save-button" onClick={handleCreate} type="button">
              {t.manualBooking}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

const DashboardView = ({ dashboard, language, currencyCode }) => {
  const t = translations[language];
  if (!dashboard) return null;
  const m = dashboard.metrics;
  const balanceOutstanding = m.total_balance_expected - m.total_balance_collected;
  const depositOutstanding = m.total_deposit_expected - m.total_deposit_collected;
  return (
    <div className="grid gap-6" data-testid="admin-dashboard-view">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard subtitle={t.weeklyOccupancy} testId="metric-nearly-full-weeks" title={t.nearlyFullWeeks} value={m.nearly_full_weeks} />
        <MetricCard subtitle={t.weeklyOccupancy} testId="metric-full-weeks" title={t.fullWeeks} value={m.full_weeks} />
        <MetricCard subtitle={t.bookings} testId="metric-dogs-pending-intake" title={t.dogsPendingIntake} value={m.dogs_pending_intake} />
        <MetricCard subtitle={t.bookings} testId="metric-dogs-in-training" title={t.dogsInTraining} value={m.dogs_in_training} />
        <MetricCard subtitle={t.bookings} testId="metric-dogs-delivered" title={t.dogsDelivered} value={m.dogs_delivered} />
        <MetricCard subtitle={t.finance} testId="metric-deposits-pending" title={t.depositsPending} value={m.deposits_pending} />
        <MetricCard subtitle={t.finance} testId="metric-paid-in-full" title={t.paidInFull} value={m.paid_in_full} />
        <MetricCard subtitle={t.finance} testId="metric-confirmed-revenue" title={t.confirmedRevenue} value={formatCurrency(m.confirmed_revenue, language, currencyCode)} />
      </div>

      <Card className="surface-panel rounded-[1.75rem] border-white/10" data-testid="financial-summary-card">
        <CardHeader>
          <CardTitle className="text-white">{t.financialSummary}</CardTitle>
          <CardDescription className="text-zinc-400">{t.financialSummaryDesc}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="rounded-2xl border border-green-500/20 bg-green-500/5 p-4" data-testid="fin-deposit-collected">
              <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">{t.depositCollected}</p>
              <p className="mt-2 text-2xl font-bold text-green-400">{formatCurrency(m.total_deposit_collected, language, currencyCode)}</p>
            </div>
            <div className="rounded-2xl border border-blue-500/20 bg-blue-500/5 p-4" data-testid="fin-final-collected">
              <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">{t.finalPaymentsCollected}</p>
              <p className="mt-2 text-2xl font-bold text-blue-400">{formatCurrency(m.total_balance_collected, language, currencyCode)}</p>
            </div>
            <div className="rounded-2xl border border-yellow-500/20 bg-yellow-500/5 p-4" data-testid="fin-balance-outstanding">
              <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">{t.balancePendingMetric}</p>
              <p className="mt-2 text-2xl font-bold text-yellow-400">{formatCurrency(balanceOutstanding + depositOutstanding, language, currencyCode)}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4" data-testid="fin-total-revenue">
              <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">{t.totalRevenueCollected}</p>
              <p className="mt-2 text-2xl font-bold text-white">{formatCurrency(m.total_revenue_collected, language, currencyCode)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2 xl:grid-cols-3">
        {[{ key: "capacity_breakdown", title: t.capacityBreakdown }, { key: "dog_status_breakdown", title: t.dogStatusBreakdown }].map((chart, chartIndex) => (
          <Card className="surface-panel rounded-[1.75rem] border-white/10" data-testid={`pie-chart-${chart.key}`} key={chart.key}>
            <CardHeader>
              <CardTitle className="text-white">{chart.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <MeasuredChart>
                {({ width, height }) => (
                <PieChart height={height} width={width}>
                  <Pie data={dashboard.charts[chart.key]} dataKey="value" nameKey="name" outerRadius={100}>
                    {dashboard.charts[chart.key].map((entry, index) => (
                      <Cell fill={CHART_COLORS[(chartIndex + index) % CHART_COLORS.length]} key={entry.name} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
                )}
              </MeasuredChart>
            </CardContent>
          </Card>
        ))}
        <Card className="surface-panel rounded-[1.75rem] border-white/10" data-testid="bar-chart-revenue">
          <CardHeader>
            <CardTitle className="text-white">{t.paymentBreakdownChart}</CardTitle>
          </CardHeader>
          <CardContent>
            <MeasuredChart>
              {({ width, height }) => (
              <BarChart data={dashboard.charts.payment_breakdown} height={height} width={width}>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" />
                <XAxis dataKey="month" stroke="#a1a1aa" />
                <YAxis stroke="#a1a1aa" tickFormatter={(value) => formatCurrency(value, language, currencyCode)} />
                <Tooltip formatter={(value) => formatCurrency(value, language, currencyCode)} />
                <Legend />
                <Bar dataKey="deposits" fill="#22c55e" name={t.depositsChartLabel} radius={[8, 8, 0, 0]} />
                <Bar dataKey="final_payments" fill="#3b82f6" name={t.finalPaymentsChartLabel} radius={[8, 8, 0, 0]} />
                <Bar dataKey="outstanding" fill="#eab308" name={t.outstandingChartLabel} radius={[8, 8, 0, 0]} />
              </BarChart>
              )}
            </MeasuredChart>
          </CardContent>
        </Card>
      </div>
      <div className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
        <Card className="surface-panel rounded-[1.75rem] border-white/10">
          <CardHeader>
            <CardTitle className="text-white">{t.weeklyOccupancy}</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
            {dashboard.weekly_occupancy.map((week) => (
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-black/20 p-4" data-testid={`dashboard-week-${week.week_start}`} key={week.week_start}>
                <div>
                  <p className="font-semibold text-white">{week.label}</p>
                  <p className="text-sm text-zinc-500">{week.week_start}</p>
                </div>
                <div className="text-right">
                  <Badge className={getStatusStyles(week.availability_label)}>{t.status[week.availability_label]}</Badge>
                  <p className="mt-2 text-sm text-zinc-300">
                    {t.confirmedLabel}: {week.confirmed} · {t.pendingLabel}: {week.reserved} · {t.availableLabel}: {week.remaining}
                  </p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card className="surface-panel rounded-[1.75rem] border-white/10">
          <CardHeader>
            <CardTitle className="text-white">{t.recentEmails}</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
            {dashboard.recent_email_logs.map((email) => (
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4" data-testid={`email-log-${email.id}`} key={email.id}>
                <p className="text-sm font-semibold text-white">{email.subject}</p>
                <p className="mt-1 text-xs text-zinc-500">{email.recipient}</p>
                <p className="mt-3 line-clamp-2 text-sm text-zinc-400">{email.body}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

const BookingsView = ({ bookings, bookingsMeta = { total: 0, total_pages: 1, page: 1 }, programs, token, language, onUpdateBooking, onFinalPaymentUpload, onManualCreate, onPageChange, currencyCode, capacityWeeks, adminRole }) => {
  const t = translations[language];
  const isOp = adminRole === "operator";
  const [filters, setFilters] = useState({ status: "all", programId: "all", weekStart: "all", search: "" });
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [manualOpen, setManualOpen] = useState(false);

  const weekOptions = useMemo(() => [...new Set(bookings.map((booking) => booking.start_week))], [bookings]);
  const filteredBookings = useMemo(
    () =>
      bookings.filter((booking) => {
        const matchesStatus = filters.status === "all" || booking.status === filters.status;
        const matchesProgram = filters.programId === "all" || booking.program_id === filters.programId;
        const matchesWeek = filters.weekStart === "all" || booking.start_week === filters.weekStart;
        const query = filters.search.toLowerCase();
        const matchesSearch =
          !query ||
          booking.owner.full_name.toLowerCase().includes(query) ||
          booking.dog.name.toLowerCase().includes(query);
        return matchesStatus && matchesProgram && matchesWeek && matchesSearch;
      }),
    [bookings, filters],
  );

  return (
    <div className="grid gap-6" data-testid="admin-bookings-view">
      <Card className="surface-panel rounded-[1.75rem] border-white/10">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <CardTitle className="text-white">{t.bookings}</CardTitle>
              <CardDescription className="text-zinc-400">
                {filteredBookings.length} {language === "es" ? "visibles" : "visible"}
                {bookingsMeta.total > 0 && ` · ${bookingsMeta.total} ${language === "es" ? "total" : "total"}`}
              </CardDescription>
            </div>
            {onManualCreate && (
              <Button className="touch-button rounded-full bg-primary text-white hover:bg-red-700" data-testid="open-manual-booking-button" onClick={() => setManualOpen(true)} type="button">
                {t.manualBooking}
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-zinc-500" />
              <Input className="pl-9" data-testid="booking-search-input" onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))} placeholder={t.searchPlaceholder} value={filters.search} />
            </div>
            <select className="h-11 w-full rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="booking-filter-status" onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))} value={filters.status}>
              <option value="all">{t.allStatuses}</option>
              {STATUS_OPTIONS.map((status) => <option key={status} value={status}>{t.status[status] || status}</option>)}
            </select>
            <select className="h-11 w-full rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="booking-filter-program" onChange={(event) => setFilters((current) => ({ ...current, programId: event.target.value }))} value={filters.programId}>
              <option value="all">{t.allPrograms}</option>
              {programs.map((program) => <option key={program.id} value={program.id}>{language === "es" ? program.name_es : program.name_en}</option>)}
            </select>
            <select className="h-11 w-full rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="booking-filter-week" onChange={(event) => setFilters((current) => ({ ...current, weekStart: event.target.value }))} value={filters.weekStart}>
              <option value="all">{t.allWeeks}</option>
              {weekOptions.map((week) => <option key={week} value={week}>{week}</option>)}
            </select>
          </div>
          <div className="table-shell">
            <table className="w-full border-separate border-spacing-y-3">
              <thead>
                <tr className="text-left text-xs uppercase tracking-[0.2em] text-zinc-500">
                  <th className="px-4">Client</th>
                  <th className="px-4">Dog</th>
                  <th className="px-4">Program</th>
                  <th className="px-4">Week</th>
                  <th className="px-4">Status</th>
                  {!isOp && <th className="px-4">{t.overallPaymentLabel}</th>}
                </tr>
              </thead>
              <tbody>
                {filteredBookings.map((booking) => (
                  <tr className="cursor-pointer rounded-2xl border border-white/10 bg-white/5 transition-colors hover:bg-white/10" data-testid={`booking-row-${booking.id}`} key={booking.id} onClick={() => setSelectedBooking(booking)}>
                    <td className="rounded-l-2xl px-4 py-4 text-sm text-white">{booking.owner.full_name}</td>
                    <td className="px-4 py-4 text-sm text-zinc-300">{booking.dog.name}</td>
                    <td className="px-4 py-4 text-sm text-zinc-300">{language === "es" ? booking.program_name_es : booking.program_name_en}</td>
                    <td className="px-4 py-4 text-sm text-zinc-300">{booking.start_week}</td>
                    <td className="px-4 py-4">
                      <Badge className={getStatusStyles(booking.status)}>{t.status[booking.status] || booking.status}</Badge>
                    </td>
                    {!isOp && (
                      <td className="rounded-r-2xl px-4 py-4 text-sm text-zinc-300">
                        <Badge className={getStatusStyles(booking.overall_payment_status)}>{t.status[booking.overall_payment_status] || booking.overall_payment_status}</Badge>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {bookingsMeta.total_pages > 1 && (
            <div className="flex items-center justify-between border-t border-white/10 pt-4">
              <span className="text-sm text-zinc-400">
                {language === "es"
                  ? `${bookingsMeta.total} reservas · página ${bookingsMeta.page} de ${bookingsMeta.total_pages}`
                  : `${bookingsMeta.total} bookings · page ${bookingsMeta.page} of ${bookingsMeta.total_pages}`}
              </span>
              <div className="flex gap-2">
                <Button
                  className="rounded-full border border-white/10 bg-white/5 text-white hover:bg-white/10"
                  disabled={bookingsMeta.page <= 1}
                  onClick={() => onPageChange(bookingsMeta.page - 1)}
                  size="sm"
                  type="button"
                  variant="outline"
                >
                  {language === "es" ? "Anterior" : "Previous"}
                </Button>
                <Button
                  className="rounded-full border border-white/10 bg-white/5 text-white hover:bg-white/10"
                  disabled={bookingsMeta.page >= bookingsMeta.total_pages}
                  onClick={() => onPageChange(bookingsMeta.page + 1)}
                  size="sm"
                  type="button"
                  variant="outline"
                >
                  {language === "es" ? "Siguiente" : "Next"}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      <BookingDetailDialog adminRole={adminRole} booking={selectedBooking} currencyCode={currencyCode} language={language} onClose={() => setSelectedBooking(null)} onFinalPaymentUpload={onFinalPaymentUpload} onSave={onUpdateBooking} token={token} />
      <ManualBookingDialog capacityWeeks={capacityWeeks} language={language} onClose={() => setManualOpen(false)} onCreate={onManualCreate} open={manualOpen} programs={programs} />
    </div>
  );
};

const ProgramsView = ({ programs, language, onSaveProgram, currencyCode }) => {
  const t = translations[language];
  const [editingProgram, setEditingProgram] = useState(null);
  const [formState, setFormState] = useState({
    name_es: "",
    name_en: "",
    description_es: "",
    description_en: "",
    duration_value: 1,
    duration_unit: "days",
    price: 0,
    deposit_type: "percentage",
    deposit_value: 50,
    active: true,
  });

  useEffect(() => {
    if (editingProgram) {
      setFormState({
        ...editingProgram,
        deposit_type: editingProgram.deposit_type || "percentage",
        deposit_value: editingProgram.deposit_value ?? 50,
      });
    } else {
      setFormState({
        name_es: "",
        name_en: "",
        description_es: "",
        description_en: "",
        duration_value: 1,
        duration_unit: "days",
        price: 0,
        deposit_type: "percentage",
        deposit_value: 50,
        active: true,
      });
    }
  }, [editingProgram]);

  const update = (key, value) => setFormState((current) => ({ ...current, [key]: value }));

  return (
    <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]" data-testid="admin-programs-view">
      <div className="grid gap-4">
        {programs.map((program) => (
          <Card className="surface-panel rounded-[1.75rem] border-white/10" data-testid={`admin-program-card-${program.id}`} key={program.id}>
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <CardTitle className="text-white">{program.name_es}</CardTitle>
                  <CardDescription className="text-zinc-400">{program.name_en}</CardDescription>
                </div>
                <Button className="touch-button" data-testid={`edit-program-button-${program.id}`} onClick={() => setEditingProgram(program)} type="button" variant="outline">{t.edit}</Button>
              </div>
            </CardHeader>
            <CardContent className="text-sm text-zinc-300">
              <p>{program.description_es}</p>
              <p className="mt-3 text-zinc-500">{program.duration_value} {program.duration_unit === "weeks" ? t.weeks : t.days} · {formatCurrency(program.price, language, currencyCode)}</p>
              <p className="mt-1 text-zinc-500">
                {t.depositLabel}: {program.deposit_type === "fixed" ? formatCurrency(program.deposit_value || 0, language, currencyCode) : `${program.deposit_value || 50}%`}
                {" · "}
                {(() => {
                  const dep = program.deposit_type === "fixed"
                    ? Math.min(program.deposit_value || 0, program.price)
                    : Math.round(program.price * (program.deposit_value || 50) / 100 * 100) / 100;
                  return `${formatCurrency(dep, language, currencyCode)} + ${formatCurrency(program.price - dep, language, currencyCode)}`;
                })()}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
      <Card className="surface-panel rounded-[1.75rem] border-white/10">
        <CardHeader>
          <CardTitle className="text-white">{editingProgram ? `${t.edit} program` : t.saveProgram}</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <Input data-testid="program-name-es-input" onChange={(event) => update("name_es", event.target.value)} placeholder={t.nameSpanish} value={formState.name_es} />
          <Input data-testid="program-name-en-input" onChange={(event) => update("name_en", event.target.value)} placeholder={t.nameEnglish} value={formState.name_en} />
          <Textarea className="md:col-span-2" data-testid="program-description-es-input" onChange={(event) => update("description_es", event.target.value)} placeholder={t.descriptionSpanish} value={formState.description_es} />
          <Textarea className="md:col-span-2" data-testid="program-description-en-input" onChange={(event) => update("description_en", event.target.value)} placeholder={t.descriptionEnglish} value={formState.description_en} />
          <Input data-testid="program-duration-value-input" onChange={(event) => update("duration_value", Number(event.target.value))} placeholder={t.durationValue} type="number" value={formState.duration_value} />
          <select className="h-11 rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="program-duration-unit-select" onChange={(event) => update("duration_unit", event.target.value)} value={formState.duration_unit}>
            <option value="days">{t.days}</option>
            <option value="weeks">{t.weeks}</option>
          </select>
          <Input data-testid="program-price-input" onChange={(event) => update("price", Number(event.target.value))} placeholder={t.price} type="number" value={formState.price} />
          <select className="h-11 rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="program-active-select" onChange={(event) => update("active", event.target.value === "true")} value={String(formState.active)}>
            <option value="true">{t.active}</option>
            <option value="false">{t.inactive}</option>
          </select>
          <select className="h-11 rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="program-deposit-type-select" onChange={(event) => update("deposit_type", event.target.value)} value={formState.deposit_type}>
            <option value="percentage">{t.depositPercentage}</option>
            <option value="fixed">{t.depositFixed}</option>
          </select>
          <Input data-testid="program-deposit-value-input" min="0" onChange={(event) => update("deposit_value", Number(event.target.value))} placeholder={formState.deposit_type === "percentage" ? "%" : t.depositLabel} type="number" value={formState.deposit_value} />
          <div className="md:col-span-2 flex justify-end gap-3">
            {editingProgram && <Button className="touch-button" data-testid="cancel-program-edit-button" onClick={() => setEditingProgram(null)} type="button" variant="outline">{t.close}</Button>}
            <Button className="touch-button bg-primary text-white hover:bg-red-700" data-testid="save-program-button" onClick={() => onSaveProgram(editingProgram?.id, formState).then(() => setEditingProgram(null))} type="button">
              {t.saveProgram}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const CapacityView = ({ capacityWeeks, language, onSaveCapacity }) => {
  const t = translations[language];
  const [drafts, setDrafts] = useState({});

  return (
    <Card className="surface-panel rounded-[1.75rem] border-white/10" data-testid="admin-capacity-view">
      <CardHeader>
        <CardTitle className="text-white">{t.weeklyCapacityControl}</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4">
        {capacityWeeks.map((week) => (
          <div className="grid gap-3 rounded-2xl border border-white/10 bg-white/5 p-4 md:grid-cols-[1fr_100px_150px] md:items-center" data-testid={`capacity-row-${week.week_start}`} key={week.week_start}>
            <div>
              <p className="font-semibold text-white">{week.label}</p>
              <p className="text-sm text-zinc-500">{t.confirmedLabel}: {week.confirmed} · {t.pendingLabel}: {week.reserved} · {t.availableLabel}: {week.remaining}</p>
            </div>
            <Input data-testid={`capacity-input-${week.week_start}`} onChange={(event) => setDrafts((current) => ({ ...current, [week.week_start]: event.target.value }))} type="number" value={drafts[week.week_start] ?? week.capacity} />
            <Button className="touch-button rounded-full bg-primary text-white hover:bg-red-700" data-testid={`capacity-save-${week.week_start}`} onClick={() => onSaveCapacity(week.week_start, Number(drafts[week.week_start] ?? week.capacity))} type="button">
              {t.saveWeek}
            </Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

const WeeklyOperationsView = ({ bookings, capacityWeeks, language, adminRole }) => {
  const t = translations[language];
  const isOp = adminRole === "operator";
  const operationalStatuses = ["Pending Review", "Approved", "Scheduled", "In Training", "Delivered"];
  const weeksWithDogs = useMemo(
    () =>
      capacityWeeks.map((week) => ({
        ...week,
        dogs: bookings
          .filter((booking) => operationalStatuses.includes(booking.status) && booking.week_starts?.includes(week.week_start))
          .sort((left, right) => left.dog.name.localeCompare(right.dog.name)),
      })),
    [bookings, capacityWeeks],
  );

  return (
    <Card className="surface-panel rounded-[1.75rem] border-white/10" data-testid="admin-weekly-operations-view">
      <CardHeader>
        <CardTitle className="text-white">{t.weeklyOperationalView}</CardTitle>
        <CardDescription className="text-zinc-400">{t.dogsAssignedThisWeek}</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4">
        {weeksWithDogs.map((week) => (
          <div className="rounded-2xl border border-white/10 bg-black/20 p-4" data-testid={`operations-week-${week.week_start}`} key={week.week_start}>
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-semibold text-white">{formatDisplayDate(week.week_start, language)}</p>
                <p className="text-sm text-zinc-500">{week.week_start}</p>
                <p className="mt-2 text-sm text-zinc-400">{t.confirmedLabel}: {week.confirmed} · {t.pendingLabel}: {week.reserved} · {t.availableLabel}: {week.remaining}</p>
              </div>
              <Badge className={getStatusStyles(week.availability_label)}>{week.dogs.length} {language === "es" ? "perros" : "dogs"}</Badge>
            </div>
            {week.dogs.length ? (
              <div className="grid gap-3">
                {week.dogs.map((booking) => (
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4" data-testid={`operations-dog-${week.week_start}-${booking.id}`} key={`${week.week_start}-${booking.id}`}>
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="font-semibold text-white">{booking.dog.name}</p>
                        <p className="text-sm text-zinc-400">{t.clientName}: {booking.owner.full_name}</p>
                        <p className="text-sm text-zinc-500">{t.programName}: {language === "es" ? booking.program_name_es : booking.program_name_en}</p>
                      </div>
                      <div className="flex flex-wrap gap-2 text-xs">
                        <Badge className={getStatusStyles(booking.status)}>{t.bookingStatusLabel}: {t.status[booking.status] || booking.status}</Badge>
                        {!isOp && <Badge className={getStatusStyles(booking.overall_payment_status)}>{t.overallPaymentLabel}: {t.status[booking.overall_payment_status] || booking.overall_payment_status}</Badge>}
                        <Badge className={getStatusStyles(booking.vaccination_certificate_status)}>{t.vaccinationValidationLabel}: {t.status[booking.vaccination_certificate_status] || booking.vaccination_certificate_status}</Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-zinc-500" data-testid={`operations-empty-${week.week_start}`}>{t.noDogsAssigned}</p>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

const OperationsSummaryCard = ({ title, value, icon: Icon, accentClass, testId }) => (
  <Card className="surface-panel rounded-[2rem] border-white/10 p-0" data-testid={testId}>
    <CardContent className="flex min-h-[200px] flex-col justify-between p-8">
      <div className={`flex h-14 w-14 items-center justify-center rounded-2xl ${accentClass}`}>
        <Icon className="h-7 w-7 text-white" />
      </div>
      <div>
        <p className="text-sm uppercase tracking-[0.2em] text-zinc-500">{title}</p>
        <p className="mt-4 text-5xl font-semibold text-white xl:text-6xl">{value}</p>
      </div>
    </CardContent>
  </Card>
);

const OperationsScreenView = ({ bookings, capacityWeeks, dashboard, language, lastUpdated }) => {
  const t = translations[language];
  const operationalStatuses = ["Pending Review", "Approved", "Scheduled", "In Training", "Delivered"];

  const weeksWithAssignments = useMemo(
    () =>
      capacityWeeks
        .map((week) => ({
          ...week,
          dogs: bookings
            .filter((booking) => operationalStatuses.includes(booking.status) && booking.week_starts?.includes(week.week_start))
            .sort((left, right) => left.dog.name.localeCompare(right.dog.name)),
        }))
        .filter((week) => week.dogs.length > 0),
    [bookings, capacityWeeks],
  );

  const summaryCards = [
    { key: "pending-intake", title: t.dogsPendingIntake, value: dashboard?.metrics?.dogs_pending_intake ?? 0, icon: CalendarRange, accentClass: "bg-yellow-500/30" },
    { key: "in-training", title: t.dogsInTraining, value: dashboard?.metrics?.dogs_in_training ?? 0, icon: Dog, accentClass: "bg-blue-500/30" },
    { key: "delivered", title: t.dogsDelivered, value: dashboard?.metrics?.dogs_delivered ?? 0, icon: CheckCircle2, accentClass: "bg-green-500/30" },
    { key: "almost-full", title: t.nearlyFullWeeks, value: dashboard?.metrics?.nearly_full_weeks ?? 0, icon: AlertTriangle, accentClass: "bg-orange-500/30" },
    { key: "full-weeks", title: t.fullWeeks, value: dashboard?.metrics?.full_weeks ?? 0, icon: PawPrint, accentClass: "bg-red-500/30" },
  ];

  return (
    <div className="grid gap-6" data-testid="admin-operations-screen-view">
      <Card className="surface-panel rounded-[2rem] border-white/10">
        <CardContent className="flex flex-wrap items-center justify-between gap-4 p-8">
          <div>
            <p className="text-xs uppercase tracking-[0.25em] text-zinc-500">PAWS TRAINING</p>
            <h2 className="mt-3 text-4xl font-semibold text-white xl:text-5xl" data-testid="operations-screen-title">{t.operationsScreenTitle}</h2>
            <p className="mt-3 max-w-3xl text-lg text-zinc-400">{t.operationsScreenSubtitle}</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-black/20 px-5 py-4 text-right" data-testid="operations-screen-refresh-status">
            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">{t.autoRefresh30Seconds}</p>
            <p className="mt-2 text-sm text-zinc-300">{t.lastUpdated}: {lastUpdated}</p>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-5 md:grid-cols-2">
        {summaryCards.map((card) => (
          <OperationsSummaryCard
            accentClass={card.accentClass}
            icon={card.icon}
            key={card.key}
            testId={`operations-summary-${card.key}`}
            title={card.title}
            value={card.value}
          />
        ))}
      </div>

      <Card className="surface-panel rounded-[2rem] border-white/10">
        <CardHeader>
          <CardTitle className="text-3xl text-white">{t.weeklyOperationalView}</CardTitle>
          <CardDescription className="text-zinc-400">{t.dogsAssignedThisWeek}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-5">
          {weeksWithAssignments.length ? (
            weeksWithAssignments.map((week) => (
              <div className="rounded-[1.75rem] border border-white/10 bg-black/20 p-6" data-testid={`operations-screen-week-${week.week_start}`} key={week.week_start}>
                <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <p className="text-2xl font-semibold text-white">{formatDisplayDate(week.week_start, language)}</p>
                    <p className="mt-1 text-sm text-zinc-500">{week.week_start}</p>
                    <p className="mt-3 text-sm text-zinc-300">{t.confirmedLabel}: {week.confirmed} · {t.pendingLabel}: {week.reserved} · {t.availableLabel}: {week.remaining}</p>
                  </div>
                  <div className="flex flex-wrap gap-3 text-sm">
                    <Badge className="border-white/10 bg-white/5 px-4 py-2 text-zinc-200">{t.availableLabel}: {week.remaining}</Badge>
                    <Badge className={`${getStatusStyles(week.availability_label)} px-4 py-2`}>{t.status[week.availability_label]}</Badge>
                  </div>
                </div>

                <div className="grid gap-4">
                  {week.dogs.map((booking) => (
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-5" data-testid={`operations-screen-dog-${week.week_start}-${booking.id}`} key={`${week.week_start}-${booking.id}`}>
                      <div className="flex flex-wrap items-center justify-between gap-4">
                        <div>
                          <p className="text-2xl font-semibold text-white">{booking.dog.name}</p>
                          <p className="mt-1 text-base text-zinc-300">{t.clientName}: {booking.owner.full_name}</p>
                          <p className="mt-1 text-base text-zinc-500">{t.programName}: {language === "es" ? booking.program_name_es : booking.program_name_en}</p>
                        </div>
                        <div className="flex flex-wrap gap-2 text-sm">
                          <Badge className={`${getStatusStyles(booking.status)} px-4 py-2`}>{t.bookingStatusLabel}: {t.status[booking.status] || booking.status}</Badge>
                          <Badge className={`${getStatusStyles(booking.overall_payment_status)} px-4 py-2`}>{t.overallPaymentLabel}: {t.status[booking.overall_payment_status] || booking.overall_payment_status}</Badge>
                          <Badge className={`${getStatusStyles(booking.vaccination_certificate_status)} px-4 py-2`}>{t.vaccinationValidationLabel}: {t.status[booking.vaccination_certificate_status] || booking.vaccination_certificate_status}</Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <p className="rounded-2xl border border-white/10 bg-white/5 p-8 text-lg text-zinc-400" data-testid="operations-screen-empty-state">{t.noAssignedDogsScreen}</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

const SettingsView = ({ settings, emailLogs, onSaveSettings, onUploadLogo, onUploadLandingHeroImage, language }) => {
  const t = translations[language];
  const [formState, setFormState] = useState(normalizeSettingsState(settings));

  useEffect(() => {
    setFormState(normalizeSettingsState(settings));
  }, [settings]);

  if (!formState) return null;

  const update = (key, value) => setFormState((current) => ({ ...current, [key]: value }));
  const updateLandingField = (key, value) => setFormState((current) => ({
    ...current,
    landing_content: {
      ...current.landing_content,
      [key]: value,
    },
  }));
  const updateFeatureCard = (index, key, value) => setFormState((current) => ({
    ...current,
    landing_content: {
      ...current.landing_content,
      feature_cards: current.landing_content.feature_cards.map((card, cardIndex) => (
        cardIndex === index ? { ...card, [key]: value } : card
      )),
    },
  }));

  return (
    <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]" data-testid="admin-settings-view">
      <Card className="surface-panel rounded-[1.75rem] border-white/10">
        <CardHeader>
          <CardTitle className="text-white">{t.settings}</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <Input data-testid="settings-business-name-input" onChange={(event) => update("business_name", event.target.value)} placeholder={t.businessName} value={formState.business_name || ""} />
          <Input data-testid="settings-slogan-input" onChange={(event) => update("slogan", event.target.value)} placeholder={t.slogan} value={formState.slogan || ""} />
          <Input data-testid="settings-contact-email-input" onChange={(event) => update("contact_email", event.target.value)} placeholder={t.contactEmail} value={formState.contact_email || ""} />
          <Input data-testid="settings-contact-phone-input" onChange={(event) => update("contact_phone", event.target.value)} placeholder={t.contactPhone} value={formState.contact_phone || ""} />
          <Input className="md:col-span-2" data-testid="settings-contact-address-input" onChange={(event) => update("contact_address", event.target.value)} placeholder={t.contactAddress} value={formState.contact_address || ""} />
          <Input data-testid="settings-admin-email-input" onChange={(event) => update("admin_notification_email", event.target.value)} placeholder={t.adminNotificationEmail} value={formState.admin_notification_email || ""} />
          <Input data-testid="settings-logo-url-input" onChange={(event) => update("logo_url", event.target.value)} placeholder={t.logoUrl} value={formState.logo_url || ""} />
          <Input data-testid="settings-landing-hero-image-url-input" onChange={(event) => update("landing_hero_image_url", event.target.value)} placeholder={t.landingHeroImageUrl} value={formState.landing_hero_image_url || ""} />
          <div className="md:col-span-2 rounded-2xl border border-white/10 bg-black/20 p-4">
            <label className="mb-2 block text-sm text-zinc-300" data-testid="settings-currency-label">{t.currency}</label>
            <select className="h-11 w-full rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="settings-currency-select" onChange={(event) => update("currency", event.target.value)} value={formState.currency || "USD"}>
              {CURRENCY_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
            <p className="mt-2 text-sm text-zinc-500">{t.currencyHelp}</p>
          </div>
          <div className="md:col-span-2 rounded-2xl border border-white/10 bg-black/20 p-5" data-testid="smtp-settings-section">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm font-semibold text-white">{t.smtpSettings}</p>
              <Badge className={formState.smtp_password_configured ? "border-green-500/25 bg-green-500/10 text-green-200" : "border-yellow-500/25 bg-yellow-500/10 text-yellow-200"} data-testid="smtp-config-status-badge">
                {formState.smtp_password_configured ? t.smtpConfigured : t.smtpNotConfigured}
              </Badge>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <Input data-testid="settings-smtp-host-input" onChange={(event) => update("smtp_host", event.target.value)} placeholder={t.smtpHost} value={formState.smtp_host || ""} />
              <Input data-testid="settings-smtp-port-input" onChange={(event) => update("smtp_port", Number(event.target.value))} placeholder={t.smtpPort} type="number" value={formState.smtp_port || 587} />
              <Input data-testid="settings-smtp-username-input" onChange={(event) => update("smtp_username", event.target.value)} placeholder={t.smtpUsername} value={formState.smtp_username || ""} />
              <select className="h-11 w-full rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="settings-smtp-tls-select" onChange={(event) => update("smtp_tls", event.target.value === "true")} value={String(formState.smtp_tls)}>
                <option value="true">{t.yes}</option>
                <option value="false">{t.no}</option>
              </select>
              <div className="md:col-span-2">
                <Input data-testid="settings-smtp-password-input" onChange={(event) => update("smtp_password", event.target.value)} placeholder={formState.smtp_password_masked || "••••••••"} type="password" value={formState.smtp_password} />
                <p className="mt-2 text-sm text-zinc-500">{t.smtpPasswordHelp}</p>
              </div>
            </div>
          </div>
          <div className="md:col-span-2 grid gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-4">
              <label className="mb-3 block text-sm text-zinc-300">{t.uploadLogo}</label>
              <input data-testid="settings-logo-file-input" onChange={(event) => event.target.files?.[0] && onUploadLogo(event.target.files[0])} type="file" />
            </div>
            <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-4">
              <label className="mb-3 block text-sm text-zinc-300">{t.uploadLandingHeroImage}</label>
              <input data-testid="settings-landing-hero-image-file-input" onChange={(event) => event.target.files?.[0] && onUploadLandingHeroImage(event.target.files[0])} type="file" />
              <p className="mt-3 text-sm text-zinc-500">{t.landingHeroImageHelp}</p>
            </div>
          </div>
          <div className="md:col-span-2 rounded-2xl border border-white/10 bg-black/20 p-5">
            <div className="mb-4">
              <p className="text-sm font-semibold text-white">{t.landingContent}</p>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <Textarea data-testid="landing-description-es-input" onChange={(event) => updateLandingField("hero_description_es", event.target.value)} placeholder={t.landingDescriptionSpanish} value={formState.landing_content.hero_description_es} />
              <Textarea data-testid="landing-description-en-input" onChange={(event) => updateLandingField("hero_description_en", event.target.value)} placeholder={t.landingDescriptionEnglish} value={formState.landing_content.hero_description_en} />
              <Input data-testid="landing-book-cta-es-input" onChange={(event) => updateLandingField("reserve_button_label_es", event.target.value)} placeholder={t.reserveButtonSpanish} value={formState.landing_content.reserve_button_label_es} />
              <Input data-testid="landing-book-cta-en-input" onChange={(event) => updateLandingField("reserve_button_label_en", event.target.value)} placeholder={t.reserveButtonEnglish} value={formState.landing_content.reserve_button_label_en} />
              <Input data-testid="landing-admin-cta-es-input" onChange={(event) => updateLandingField("admin_button_label_es", event.target.value)} placeholder={t.adminButtonSpanish} value={formState.landing_content.admin_button_label_es} />
              <Input data-testid="landing-admin-cta-en-input" onChange={(event) => updateLandingField("admin_button_label_en", event.target.value)} placeholder={t.adminButtonEnglish} value={formState.landing_content.admin_button_label_en} />
            </div>
            <div className="mt-5 grid gap-4">
              {formState.landing_content.feature_cards.map((card, index) => (
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4" data-testid={`landing-feature-card-editor-${card.id}`} key={card.id}>
                  <p className="mb-4 text-sm font-semibold text-white">{t.featureCardTitle} {index + 1}</p>
                  <div className="grid gap-4 md:grid-cols-2">
                    <Input data-testid={`landing-feature-title-es-${card.id}`} onChange={(event) => updateFeatureCard(index, "title_es", event.target.value)} placeholder={t.featureTitleSpanish} value={card.title_es} />
                    <Input data-testid={`landing-feature-title-en-${card.id}`} onChange={(event) => updateFeatureCard(index, "title_en", event.target.value)} placeholder={t.featureTitleEnglish} value={card.title_en} />
                    <Textarea data-testid={`landing-feature-description-es-${card.id}`} onChange={(event) => updateFeatureCard(index, "description_es", event.target.value)} placeholder={t.featureDescriptionSpanish} value={card.description_es} />
                    <Textarea data-testid={`landing-feature-description-en-${card.id}`} onChange={(event) => updateFeatureCard(index, "description_en", event.target.value)} placeholder={t.featureDescriptionEnglish} value={card.description_en} />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="md:col-span-2 flex justify-end">
            <Button className="touch-button bg-primary text-white hover:bg-red-700" data-testid="settings-save-button" onClick={() => onSaveSettings(formState)} type="button">
              {t.saveSettings}
            </Button>
          </div>
        </CardContent>
      </Card>
      <Card className="surface-panel rounded-[1.75rem] border-white/10">
        <CardHeader>
          <CardTitle className="text-white">{t.recentEmails}</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3">
          {emailLogs.map((email) => (
            <div className="rounded-2xl border border-white/10 bg-black/20 p-4" data-testid={`settings-email-log-${email.id}`} key={email.id}>
              <p className="text-sm font-semibold text-white">{email.subject}</p>
              <p className="mt-1 text-xs text-zinc-500">{email.recipient}</p>
              <p className="mt-2 text-sm text-zinc-400">{email.body}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
};

const RequireAdmin = ({ session, children }) => {
  if (!session?.token) {
    return <Navigate replace to="/admin/login" />;
  }
  return children;
};

const UserManagementView = ({ token, language, currentRole, currentUserId }) => {
  const t = translations[language];
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "operator" });

  const loadUsers = useCallback(async () => {
    try {
      const data = await adminApi.getUsers(token);
      setUsers(data);
    } catch (e) {
      toast.error(e.message);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { loadUsers(); }, [loadUsers]);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await adminApi.createUser(token, form);
      toast.success(t.userCreated);
      setForm({ name: "", email: "", password: "", role: "operator" });
      setShowForm(false);
      loadUsers();
    } catch (err) {
      toast.error(err.message);
    }
  };

  const handleDelete = async (userId) => {
    if (!window.confirm(t.confirmDeleteUser)) return;
    try {
      await adminApi.deleteUser(token, userId);
      toast.success(t.userDeleted);
      loadUsers();
    } catch (err) {
      toast.error(err.message);
    }
  };

  const roleLabel = (r) => r === "superadmin" ? t.roleSuperadmin : r === "admin" ? t.roleAdmin : t.roleOperator;
  const roleBadgeClass = (r) => r === "superadmin" ? "bg-red-600/20 text-red-400 border-red-600/30" : r === "admin" ? "bg-amber-600/20 text-amber-400 border-amber-600/30" : "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";

  if (loading) return <Card className="surface-panel rounded-[2rem] border-white/10 p-10 text-center text-zinc-400">{t.loadingAdmin}</Card>;

  return (
    <div className="grid gap-6" data-testid="user-management-view">
      <Card className="surface-panel rounded-[2rem] border-white/10">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-lg text-white">{t.userManagement}</CardTitle>
          <Button className="rounded-full" data-testid="create-user-btn" onClick={() => setShowForm(!showForm)} size="sm">
            <Plus className="mr-1 h-4 w-4" /> {t.createUser}
          </Button>
        </CardHeader>
        <CardContent>
          {showForm && (
            <form className="mb-6 grid gap-3 rounded-2xl border border-white/10 bg-black/20 p-4 sm:grid-cols-2 lg:grid-cols-5" data-testid="create-user-form" onSubmit={handleCreate}>
              <Input className="rounded-xl" data-testid="user-name-input" onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder={t.userName} required value={form.name} />
              <Input className="rounded-xl" data-testid="user-email-input" onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder={t.userEmail} required type="email" value={form.email} />
              <Input className="rounded-xl" data-testid="user-password-input" minLength={6} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder={t.userPassword} required type="password" value={form.password} />
              <select className="rounded-xl border border-white/10 bg-zinc-900 px-3 py-2 text-sm text-white" data-testid="user-role-select" onChange={(e) => setForm({ ...form, role: e.target.value })} value={form.role}>
                {currentRole === "superadmin" && <option value="admin">{t.roleAdmin}</option>}
                <option value="operator">{t.roleOperator}</option>
              </select>
              <Button className="rounded-xl" data-testid="submit-create-user-btn" type="submit">{t.createUser}</Button>
            </form>
          )}
          {users.length === 0 ? (
            <p className="text-center text-sm text-zinc-500">{t.noUsers}</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-left text-xs uppercase tracking-wider text-zinc-500">
                    <th className="px-4 py-3">{t.userName}</th>
                    <th className="px-4 py-3">{t.userEmail}</th>
                    <th className="px-4 py-3">{t.userRole}</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr className="border-b border-white/5 hover:bg-white/5" data-testid={`user-row-${u.id}`} key={u.id}>
                      <td className="px-4 py-3 text-white">{u.name}</td>
                      <td className="px-4 py-3 text-zinc-400">{u.email}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-block rounded-full border px-2 py-0.5 text-xs ${roleBadgeClass(u.role)}`}>{roleLabel(u.role)}</span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        {u.id !== currentUserId && (
                          <Button className="h-8 rounded-full text-xs" data-testid={`delete-user-${u.id}`} onClick={() => handleDelete(u.id)} size="sm" variant="ghost">
                            <Trash2 className="mr-1 h-3 w-3 text-red-500" /> {t.deleteUser}
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

const AdminShell = ({ language, setLanguage, session, setSession, onLogout, refreshPublicData, config }) => {
  const t = translations[language];
  const location = useLocation();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [bookings, setBookings] = useState([]);
  const [bookingsPage, setBookingsPage] = useState(1);
  const bookingsPageRef = useRef(1);
  const [bookingsMeta, setBookingsMeta] = useState({ total: 0, total_pages: 1, page: 1 });
  const [programs, setPrograms] = useState([]);
  const [capacityWeeks, setCapacityWeeks] = useState([]);
  const [settings, setSettings] = useState(null);
  const [emailLogs, setEmailLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(() => new Date().toLocaleTimeString(language === "es" ? "es-ES" : "en-US"));
  const [pwOpen, setPwOpen] = useState(false);
  const [pwForm, setPwForm] = useState({ current: "", next: "", confirm: "", email: "" });
  const [pwSaving, setPwSaving] = useState(false);
  const currentSection = location.pathname.split("/")[2] || "dashboard";
  const adminRole = session.admin?.role || "operator";

  const isOperator = adminRole === "operator";

  useEffect(() => {
    bookingsPageRef.current = bookingsPage;
  }, [bookingsPage]);

  const refreshAll = useCallback(async (showLoader = true) => {
    if (showLoader) {
      setLoading(true);
    }
    try {
      const bookingsResponse = await adminApi.getBookings(session.token, { page: bookingsPageRef.current, limit: 20 });
      setBookings(bookingsResponse.bookings || []);
      setBookingsMeta({ total: bookingsResponse.total || 0, total_pages: bookingsResponse.total_pages || 1, page: bookingsResponse.page || 1 });

      if (!isOperator) {
        const [dashboardResponse, programsResponse, capacityResponse] = await Promise.all([
          adminApi.getDashboard(session.token),
          adminApi.getPrograms(session.token),
          adminApi.getCapacity(session.token),
        ]);
        setDashboard(dashboardResponse);
        setPrograms(programsResponse);
        setCapacityWeeks(capacityResponse);
      }

      if (adminRole === "superadmin") {
        const [settingsResponse, emailLogsResponse] = await Promise.all([
          adminApi.getSettings(session.token),
          adminApi.getEmailLogs(session.token),
        ]);
        setSettings(settingsResponse);
        setEmailLogs(emailLogsResponse);
      }

      setLastUpdated(new Date().toLocaleTimeString(language === "es" ? "es-ES" : "en-US"));
    } catch (error) {
      toast.error(error.message);
      onLogout();
      navigate("/admin/login");
    } finally {
      if (showLoader) {
        setLoading(false);
      }
    }
  }, [adminRole, isOperator, language, navigate, onLogout, session.token]);

  useEffect(() => {
    if (location.pathname === "/admin") {
      navigate(isOperator ? "/admin/bookings" : "/admin/dashboard", { replace: true });
    }
  }, [isOperator, location.pathname, navigate]);

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  const fetchBookingsPage = useCallback((page) => {
    adminApi.getBookings(session.token, { page, limit: 20 }).then((res) => {
      setBookings(res.bookings || []);
      setBookingsMeta({ total: res.total || 0, total_pages: res.total_pages || 1, page: res.page || 1 });
    }).catch(() => {});
  }, [session.token]);

  const handlePageChange = useCallback((newPage) => {
    setBookingsPage(newPage);
    fetchBookingsPage(newPage);
  }, [fetchBookingsPage]);

  useEffect(() => {
    if (currentSection !== "operations-screen") {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      refreshAll(false);
    }, 30000);

    return () => window.clearInterval(intervalId);
  }, [currentSection, refreshAll]);

  const saveBooking = async (bookingId, payload) => {
    try {
      await adminApi.updateBooking(session.token, bookingId, payload);
      toast.success(t.bookingSaved);
      await refreshAll();
    } catch (error) {
      toast.error(error.message);
      throw error;
    }
  };

  const uploadFinalPaymentProof = async (bookingId, file) => {
    await adminApi.uploadFinalPaymentProof(session.token, bookingId, file);
    await refreshAll();
  };

  const saveProgram = async (programId, payload) => {
    try {
      if (programId) {
        await adminApi.updateProgram(session.token, programId, payload);
      } else {
        await adminApi.createProgram(session.token, payload);
      }
      toast.success(t.programSaved);
      await refreshAll();
      await refreshPublicData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const saveCapacity = async (weekStart, capacity) => {
    try {
      await adminApi.updateCapacity(session.token, weekStart, capacity);
      toast.success(t.capacitySaved);
      await refreshAll();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const saveSettings = async (payload) => {
    try {
      const sanitizedPayload = { ...payload };
      if (!sanitizedPayload.smtp_password) {
        delete sanitizedPayload.smtp_password;
      }
      await adminApi.updateSettings(session.token, sanitizedPayload);
      toast.success(t.settingsSaved);
      await refreshAll();
      await refreshPublicData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const uploadLogo = async (file) => {
    try {
      await adminApi.uploadLogo(session.token, file);
      toast.success(t.logoUploaded);
      await refreshAll();
      await refreshPublicData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const uploadLandingHeroImage = async (file) => {
    try {
      await adminApi.uploadLandingHeroImage(session.token, file);
      toast.success(t.settingsSaved);
      await refreshAll();
      await refreshPublicData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const createManualBooking = async (payload) => {
    try {
      await adminApi.createManualBooking(session.token, payload);
      toast.success(t.bookingSaved);
      await refreshAll();
    } catch (error) {
      toast.error(error.message);
      throw error;
    }
  };

  const isSuperadminOrAdmin = adminRole === "superadmin" || adminRole === "admin";

  const navigationItems = [
    ...(isSuperadminOrAdmin ? [{ key: "dashboard", label: t.dashboard, icon: LayoutDashboard }] : []),
    ...(isSuperadminOrAdmin ? [{ key: "operations-screen", label: t.operationsScreenNav, icon: Home }] : []),
    { key: "bookings", label: t.bookings, icon: FileText },
    ...(isSuperadminOrAdmin ? [{ key: "weekly-operations", label: t.weeklyOperationsNav, icon: CalendarRange }] : []),
    ...(adminRole === "superadmin" ? [{ key: "programs", label: t.programs, icon: Dog }] : []),
    ...(adminRole === "superadmin" ? [{ key: "capacity", label: t.capacity, icon: CalendarRange }] : []),
    ...(isSuperadminOrAdmin ? [{ key: "users", label: t.userManagement, icon: Users }] : []),
    ...(adminRole === "superadmin" ? [{ key: "settings", label: t.settings, icon: Settings }] : []),
  ];

  return (
    <div className="app-shell section-shell pb-12 pt-10" data-testid="admin-shell">
      <div className="dashboard-layout">
        <aside className="admin-sidebar surface-panel h-fit rounded-[2rem] p-5">
          <div className="flex items-center justify-between gap-3">
            <BrandMark config={config} />
          </div>
          <div className="mt-6">
            <LanguageToggle language={language} setLanguage={setLanguage} />
          </div>
          <nav className="admin-nav-grid mt-6">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink className={({ isActive }) => `sidebar-link ${isActive ? "active" : ""}`} data-testid={`admin-nav-${item.key}`} key={item.key} to={`/admin/${item.key}`}>
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
          <div className="soft-divider mt-6 pt-6">
            <div className="rounded-2xl border border-white/10 bg-black/20 p-4" data-testid="admin-user-card">
              <p className="text-sm font-semibold text-white">{session.admin?.name}</p>
              <p className="text-xs text-zinc-500">{session.admin?.email}</p>
              <span className="mt-1 inline-block rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-xs capitalize text-zinc-400" data-testid="admin-role-badge">{adminRole}</span>
            </div>
            <Button className="touch-button mt-3 w-full rounded-full" data-testid="change-password-btn" onClick={() => { setPwOpen(true); setPwForm({ current: "", next: "", confirm: "", email: "" }); }} size="sm" variant="ghost">
              <KeyRound className="mr-2 h-4 w-4" /> {t.changePassword}
            </Button>
            <Button className="touch-button mt-2 w-full rounded-full" data-testid="admin-logout-button" onClick={onLogout} type="button" variant="outline">
              <LogOut className="mr-2 h-4 w-4" /> {t.logout}
            </Button>
          </div>
          {pwOpen && (
            <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 p-4" data-testid="change-password-overlay" onClick={(e) => { if (e.target === e.currentTarget) setPwOpen(false); }}>
              <div className="w-full max-w-sm rounded-2xl border border-white/10 bg-zinc-900 p-6">
                <h3 className="mb-4 text-lg font-semibold text-white">{t.changePassword}</h3>
                <form className="grid gap-3" data-testid="change-password-form" onSubmit={async (e) => {
                  e.preventDefault();
                  const hasNewPw = pwForm.next.length > 0;
                  const hasNewEmail = pwForm.email.length > 0;
                  if (!hasNewPw && !hasNewEmail) { toast.error(language === "es" ? "Nada que actualizar." : "Nothing to update."); return; }
                  if (hasNewPw && pwForm.next.length < 8) { toast.error(t.passwordTooShort); return; }
                  if (hasNewPw && pwForm.next !== pwForm.confirm) { toast.error(t.passwordMismatch); return; }
                  setPwSaving(true);
                  try {
                    const body = { current_password: pwForm.current };
                    if (hasNewPw) body.new_password = pwForm.next;
                    if (hasNewEmail) body.new_email = pwForm.email;
                    await adminApi.changePassword(session.token, body);
                    toast.success(t.passwordChanged);
                    if (hasNewEmail) {
                      const updated = { ...session, admin: { ...session.admin, email: pwForm.email } };
                      setSession(updated);
                      localStorage.setItem("paws-admin-session", JSON.stringify(updated));
                    }
                    setPwOpen(false);
                  } catch (err) { toast.error(err.message); } finally { setPwSaving(false); }
                }}>
                  <Input className="rounded-xl" data-testid="new-email-input" placeholder={t.newEmail || (language === "es" ? "Nuevo correo (opcional)" : "New email (optional)")} type="email" value={pwForm.email} onChange={(e) => setPwForm({ ...pwForm, email: e.target.value })} />
                  <Input className="rounded-xl" data-testid="current-password-input" placeholder={t.currentPassword} required type="password" value={pwForm.current} onChange={(e) => setPwForm({ ...pwForm, current: e.target.value })} />
                  <Input className="rounded-xl" data-testid="new-password-input" placeholder={language === "es" ? "Nueva contraseña (opcional)" : "New password (optional)"} type="password" value={pwForm.next} onChange={(e) => setPwForm({ ...pwForm, next: e.target.value })} />
                  {pwForm.next && <Input className="rounded-xl" data-testid="confirm-password-input" minLength={8} placeholder={t.confirmPassword} required type="password" value={pwForm.confirm} onChange={(e) => setPwForm({ ...pwForm, confirm: e.target.value })} />}
                  <div className="flex gap-2 pt-2">
                    <Button className="flex-1 rounded-full" data-testid="cancel-password-btn" onClick={() => setPwOpen(false)} type="button" variant="outline">{language === "es" ? "Cancelar" : "Cancel"}</Button>
                    <Button className="flex-1 rounded-full" data-testid="submit-password-btn" disabled={pwSaving} type="submit">{pwSaving ? "..." : (language === "es" ? "Guardar" : "Save")}</Button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </aside>
        <div className="admin-main-column grid gap-6">
          <header className="admin-topbar surface-panel flex flex-wrap items-center justify-between gap-4 rounded-[2rem] p-6">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">PAWS TRAINING</p>
              <h1 className="text-3xl text-white" data-testid="admin-page-title">{navigationItems.find((item) => item.key === currentSection)?.label}</h1>
            </div>
            <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-zinc-300" data-testid="admin-email-mode-pill">
              {settings?.email_mode === "smtp" ? t.emailModeSmtp : t.emailModeInternal}
            </div>
          </header>
          {loading ? (
            <Card className="surface-panel rounded-[2rem] border-white/10 p-10 text-center text-zinc-400">{t.loadingAdmin}</Card>
          ) : (
            <>
              {currentSection === "dashboard" && isSuperadminOrAdmin && <DashboardView currencyCode={config?.currency || "USD"} dashboard={dashboard} language={language} />}
              {currentSection === "operations-screen" && isSuperadminOrAdmin && (
                <OperationsScreenView
                  bookings={bookings}
                  capacityWeeks={capacityWeeks}
                  dashboard={dashboard}
                  language={language}
                  lastUpdated={lastUpdated}
                />
              )}
              {currentSection === "bookings" && (
                <BookingsView
                  adminRole={adminRole}
                  bookings={bookings}
                  bookingsMeta={bookingsMeta}
                  capacityWeeks={capacityWeeks}
                  currencyCode={config?.currency || "USD"}
                  language={language}
                  onManualCreate={isSuperadminOrAdmin ? createManualBooking : null}
                  onPageChange={handlePageChange}
                  onUpdateBooking={saveBooking}
                  onFinalPaymentUpload={isSuperadminOrAdmin ? uploadFinalPaymentProof : null}
                  programs={programs}
                  token={session.token}
                />
              )}
              {currentSection === "weekly-operations" && isSuperadminOrAdmin && <WeeklyOperationsView adminRole={adminRole} bookings={bookings} capacityWeeks={capacityWeeks} language={language} />}
              {currentSection === "programs" && adminRole === "superadmin" && <ProgramsView currencyCode={config?.currency || "USD"} language={language} onSaveProgram={saveProgram} programs={programs} />}
              {currentSection === "capacity" && adminRole === "superadmin" && <CapacityView capacityWeeks={capacityWeeks} language={language} onSaveCapacity={saveCapacity} />}
              {currentSection === "settings" && adminRole === "superadmin" && (
                <SettingsView
                  emailLogs={emailLogs}
                  language={language}
                  onSaveSettings={saveSettings}
                  onUploadLandingHeroImage={uploadLandingHeroImage}
                  onUploadLogo={uploadLogo}
                  settings={settings}
                />
              )}
              {currentSection === "users" && (adminRole === "superadmin" || adminRole === "admin") && (
                <UserManagementView
                  currentRole={adminRole}
                  currentUserId={session.admin?.id}
                  language={language}
                  token={session.token}
                />
              )}
            </>
          )}
        </div>
      </div>
      <AppFooter className="mt-6" config={config} />
    </div>
  );
};

const AppRoutes = ({ publicState, session, setSession, language, setLanguage, refreshPublicData }) => {
  const showAdminAccess = Boolean(session?.token);
  const handleLogin = async (credentials) => {
    const response = await adminApi.login(credentials);
    const nextSession = { token: response.token, admin: response.admin };
    setSession(nextSession);
    localStorage.setItem("paws-admin-session", JSON.stringify(nextSession));
    return response;
  };

  const handleLogout = () => {
    setSession(null);
    localStorage.removeItem("paws-admin-session");
  };

  return (
    <Routes>
      <Route path="/" element={<LandingPage config={publicState.config} language={language} programs={publicState.programs} setLanguage={setLanguage} />} />
      <Route path="/book" element={<BookingPage config={publicState.config} language={language} programs={publicState.programs} setLanguage={setLanguage} showAdminAccess={showAdminAccess} />} />
      <Route path="/payment/:token" element={<FinalPaymentPage language={language} setLanguage={setLanguage} />} />
      <Route path="/admin/login" element={<AdminLoginPage config={publicState.config} language={language} onLogin={handleLogin} setLanguage={setLanguage} showAdminAccess={showAdminAccess} />} />
      <Route
        path="/admin/*"
        element={
          <RequireAdmin session={session}>
            <AdminShell
              config={publicState.config}
              language={language}
              onLogout={handleLogout}
              refreshPublicData={refreshPublicData}
              session={session}
              setSession={setSession}
              setLanguage={setLanguage}
            />
          </RequireAdmin>
        }
      />
      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  );
};

function App() {
  const [language, setLanguage] = useState(() => localStorage.getItem("paws-language") || "es");
  const [session, setSession] = useState(() => {
    const stored = localStorage.getItem("paws-admin-session");
    return stored ? JSON.parse(stored) : null;
  });
  const [publicState, setPublicState] = useState({ config: null, programs: [] });
  const [initError, setInitError] = useState(false);
  const retryCountRef = useRef(0);
  const configLoadedRef = useRef(false);

  const refreshPublicData = useCallback(async () => {
    try {
      const [config, programs] = await Promise.all([publicApi.getConfig(), publicApi.getPrograms()]);
      setPublicState({ config, programs });
      setInitError(false);
      retryCountRef.current = 0;
      configLoadedRef.current = true;
    } catch (error) {
      toast.error(error.message);
      if (!configLoadedRef.current) {
        if (retryCountRef.current < 3) {
          retryCountRef.current += 1;
          setTimeout(() => refreshPublicData(), 2000 * retryCountRef.current);
        } else {
          setInitError(true);
        }
      }
    }
  }, []);

  useEffect(() => {
    document.documentElement.classList.add("dark");
    refreshPublicData();
  }, [refreshPublicData]);

  useEffect(() => {
    localStorage.setItem("paws-language", language);
  }, [language]);

  useEffect(() => {
    const validateSession = async () => {
      if (!session?.token) return;
      try {
        const freshAdmin = await adminApi.me(session.token);
        if (freshAdmin.role && freshAdmin.role !== session.admin?.role) {
          const updated = { ...session, admin: { ...session.admin, role: freshAdmin.role } };
          setSession(updated);
          localStorage.setItem("paws-admin-session", JSON.stringify(updated));
        }
      } catch {
        localStorage.removeItem("paws-admin-session");
        setSession(null);
      }
    };
    validateSession();
  }, [session]);

  if (!publicState.config) {
    return (
      <div className="app-shell flex min-h-screen flex-col items-center justify-center gap-4 text-zinc-400" data-testid="app-loading-screen">
        {initError ? (
          <>
            <AlertTriangle className="h-10 w-10 text-red-500" />
            <p className="text-lg">{language === "es" ? "No se pudo conectar con el servidor." : "Could not connect to the server."}</p>
            <Button className="mt-2 rounded-full bg-primary text-white hover:bg-red-700" data-testid="retry-loading-button" onClick={() => { setInitError(false); retryCountRef.current = 0; refreshPublicData(); }}>
              {language === "es" ? "Reintentar" : "Retry"}
            </Button>
          </>
        ) : (
          <p>Loading PAWS TRAINING...</p>
        )}
        <Toaster richColors theme="dark" />
      </div>
    );
  }

  return (
    <div className="app-shell bg-background text-foreground">
      <BrowserRouter>
        <AppRoutes
          language={language}
          publicState={publicState}
          refreshPublicData={refreshPublicData}
          session={session}
          setLanguage={setLanguage}
          setSession={setSession}
        />
      </BrowserRouter>
      <Toaster richColors theme="dark" />
    </div>
  );
}

export default App;
