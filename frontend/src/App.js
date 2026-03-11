import { useCallback, useEffect, useMemo, useState } from "react";
import "@/App.css";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
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
  ShieldAlert,
  ShieldCheck,
  UploadCloud,
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

const HERO_IMAGE =
  "https://images.unsplash.com/photo-1758125981639-c0925cd2da5f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzB8MHwxfHNlYXJjaHw0fHxkb2clMjB0cmFpbmluZyUyMHByb2Zlc3Npb25hbCUyMHN0dWRpbyUyMGRhcmslMjBiYWNrZ3JvdW5kfGVufDB8fHx8MTc3MzE5Mzk2M3ww&ixlib=rb-4.1.0&q=85";
const CONTENT_IMAGE =
  "https://images.unsplash.com/photo-1536164261511-3a17e671d380?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NTZ8MHwxfHNlYXJjaHwyfHxoYXBweSUyMGRvZyUyMHBvcnRyYWl0JTIwcGxheWZ1bCUyMHNpbHZlciUyMHJlZCUyMGFlc3RoZXRpY3xlbnwwfHx8fDE3NzMxOTM5NjR8MA&ixlib=rb-4.1.0&q=85";
const CHART_COLORS = ["#dc2626", "#d4d4d8", "#22c55e", "#3b82f6", "#facc15", "#8b5cf6"];
const STATUS_OPTIONS = ["Pending Review", "Approved", "Rejected", "Scheduled", "In Training", "Delivered", "Cancelled", "Expired"];
const DOC_STATUS_OPTIONS = ["Pending Review", "Verified", "Invalid"];
const ELIGIBILITY_OPTIONS = ["Pending Review", "Eligible", "Ineligible"];

const formatCurrency = (value, language) =>
  new Intl.NumberFormat(language === "es" ? "es-ES" : "en-US", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));

const getStatusStyles = (status) => {
  if (["Approved", "Verified", "Eligible", "Delivered"].includes(status)) {
    return "border-green-500/25 bg-green-500/10 text-green-200";
  }
  if (["Pending Review", "almost_full", "In Training", "Scheduled"].includes(status)) {
    return "border-yellow-500/25 bg-yellow-500/10 text-yellow-200";
  }
  if (["Rejected", "Invalid", "Cancelled", "Expired", "Ineligible", "full"].includes(status)) {
    return "border-red-500/25 bg-red-500/10 text-red-200";
  }
  return "border-zinc-700 bg-zinc-800/80 text-zinc-200";
};

const BrandMark = ({ config }) => (
  <div className="flex items-center gap-3" data-testid="brand-mark">
    <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/5">
      {config?.logo_url ? (
        <img alt={config.business_name} className="h-8 w-8 object-contain" src={config.logo_url} />
      ) : (
        <PawPrint className="h-5 w-5 text-red-500" />
      )}
    </div>
    <div>
      <p className="font-heading text-sm font-semibold tracking-[0.25em] text-zinc-300" data-testid="brand-name">
        {config?.business_name || "PAWS TRAINING"}
      </p>
      <p className="text-xs text-zinc-500" data-testid="brand-slogan">
        {config?.slogan || "BY PET LOVERS SITTING"}
      </p>
    </div>
  </div>
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

const PublicHeader = ({ config, language, setLanguage, t }) => (
  <header className="section-shell sticky top-0 z-40 pt-6">
    <div className="surface-panel flex flex-wrap items-center justify-between gap-4 rounded-3xl px-5 py-4 backdrop-blur">
      <BrandMark config={config} />
      <div className="flex flex-wrap items-center gap-3">
        <nav className="flex items-center gap-2 text-sm text-zinc-300">
          <Link className="rounded-full px-4 py-2 transition-colors hover:bg-white/5" data-testid="nav-home-link" to="/">
            {t.home}
          </Link>
          <Link className="rounded-full px-4 py-2 transition-colors hover:bg-white/5" data-testid="nav-book-link" to="/book">
            {t.booking}
          </Link>
          <Link className="rounded-full px-4 py-2 transition-colors hover:bg-white/5" data-testid="nav-admin-link" to="/admin/login">
            {t.admin}
          </Link>
        </nav>
        <LanguageToggle language={language} setLanguage={setLanguage} />
      </div>
    </div>
  </header>
);

const LandingPage = ({ config, programs, language, setLanguage }) => {
  const t = translations[language];
  return (
    <div className="app-shell pb-16" data-testid="landing-page">
      <PublicHeader config={config} language={language} setLanguage={setLanguage} t={t} />
      <main className="section-shell space-y-12 pb-12 pt-10">
        <section className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-stretch">
          <div className="surface-panel reveal-up rounded-[2rem] p-8 md:p-12">
            <Badge className="mb-6 border border-red-500/20 bg-red-500/10 px-4 py-2 text-xs uppercase tracking-[0.25em] text-red-200" data-testid="hero-label">
              {t.heroLabel}
            </Badge>
            <h1 className="max-w-3xl text-4xl font-semibold leading-tight text-white sm:text-5xl lg:text-6xl" data-testid="hero-title">
              {config?.business_name || "PAWS TRAINING"}
            </h1>
            <p className="mt-4 max-w-2xl text-base text-zinc-300 md:text-lg" data-testid="hero-slogan">
              {config?.slogan || "BY PET LOVERS SITTING"}
            </p>
            <p className="mt-6 max-w-2xl text-sm leading-7 text-zinc-400 sm:text-base" data-testid="hero-body">
              {t.heroBody}
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Link data-testid="hero-booking-link" to="/book">
                <Button className="rounded-full bg-primary px-6 text-white hover:bg-red-700">{t.reserveSpot}</Button>
              </Link>
              <Link data-testid="hero-admin-link" to="/admin/login">
                <Button className="rounded-full border border-white/10 bg-transparent px-6 text-white hover:bg-white/5" variant="outline">
                  {t.adminLogin}
                </Button>
              </Link>
            </div>
            <div className="mt-10 grid gap-4 md:grid-cols-3">
              {[
                { label: language === "es" ? "Capacidad base" : "Base capacity", value: "8 / semana" },
                { label: language === "es" ? "Revisión" : "Review", value: language === "es" ? "Pago + vacunas" : "Payment + vaccines" },
                { label: language === "es" ? "Modo email" : "Email mode", value: language === "es" ? "Registro interno" : "Internal log" },
              ].map((item) => (
                <div className="rounded-2xl border border-white/10 bg-black/20 p-4" data-testid={`hero-stat-${item.label}`} key={item.label}>
                  <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">{item.label}</p>
                  <p className="mt-2 text-lg font-semibold text-white">{item.value}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="hero-frame reveal-up delay-1 min-h-[520px] p-6">
            <img alt="Premium dog training" className="absolute inset-0 h-full w-full object-cover object-center opacity-80" src={HERO_IMAGE} />
            <div className="flex h-full flex-col justify-end rounded-[1.5rem] border border-white/10 bg-black/30 p-8">
              <p className="text-xs uppercase tracking-[0.25em] text-zinc-300">{t.brandTagline}</p>
              <p className="mt-4 max-w-md text-2xl font-semibold text-white md:text-3xl" data-testid="hero-side-copy">
                {t.heroTitle}
              </p>
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
                    <p className="mt-2 text-lg font-semibold text-white">{formatCurrency(program.price, language)}</p>
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
    </div>
  );
};

const BookingPage = ({ config, programs, language, setLanguage }) => {
  const t = translations[language];
  const [selectedProgramId, setSelectedProgramId] = useState(programs[0]?.id || "");
  const [weeks, setWeeks] = useState([]);
  const [loadingWeeks, setLoadingWeeks] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [bookingResult, setBookingResult] = useState(null);
  const [formState, setFormState] = useState({
    locale: language,
    owner_full_name: "",
    owner_email: "",
    owner_phone: "",
    owner_address: "",
    dog_name: "",
    breed: "",
    age: "",
    sex: "Male",
    weight: "",
    date_of_birth: "",
    vaccination_status: "Up to date",
    allergies: "",
    behavior_goals: "",
    current_medication: "",
    additional_notes: "",
    start_week: "",
    payment_proof: null,
    vaccination_certificate: null,
  });

  const selectedProgram = useMemo(() => programs.find((program) => program.id === selectedProgramId), [programs, selectedProgramId]);

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
    setFormState((current) => ({ ...current, locale: language }));
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
    if (!formState.payment_proof || !formState.vaccination_certificate) {
      toast.error(language === "es" ? "Debes cargar ambos documentos." : "Both files are required.");
      return;
    }
    setSubmitting(true);
    try {
      const payload = new FormData();
      payload.append("program_id", selectedProgramId);
      Object.entries(formState).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          payload.append(key, value);
        }
      });
      const response = await publicApi.submitBooking(payload);
      setBookingResult(response);
      toast.success(t.bookingSubmitted);
      setFormState((current) => ({
        ...current,
        owner_full_name: "",
        owner_email: "",
        owner_phone: "",
        owner_address: "",
        dog_name: "",
        breed: "",
        age: "",
        weight: "",
        date_of_birth: "",
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
    <div className="app-shell pb-16" data-testid="booking-page">
      <PublicHeader config={config} language={language} setLanguage={setLanguage} t={t} />
      <main className="section-shell grid gap-8 pb-12 pt-10 lg:grid-cols-[0.9fr_1.1fr]">
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
                  <span>{formatCurrency(selectedProgram.price, language)}</span>
                </div>
              </div>
            )}
            <div>
              <div className="mb-3 flex items-center justify-between gap-4">
                <label className="text-sm text-zinc-300">{t.selectWeek}</label>
                {loadingWeeks && <span className="text-xs text-zinc-500">Loading...</span>}
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {weeks.map((week) => (
                  <button
                    className={`week-card rounded-2xl border p-4 text-left ${formState.start_week === week.week_start ? "border-red-500 bg-red-500/10" : "border-white/10 bg-white/5"}`}
                    data-testid={`week-card-${week.week_start}`}
                    disabled={week.remaining === 0}
                    key={week.week_start}
                    onClick={() => updateField("start_week", week.week_start)}
                    type="button"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{week.label}</p>
                        <p className="mt-1 text-xs text-zinc-500">{week.week_start}</p>
                      </div>
                      <Badge className={getStatusStyles(week.availability_label)} data-testid={`week-status-${week.week_start}`}>
                        {t.status[week.availability_label]}
                      </Badge>
                    </div>
                    <p className="mt-4 text-sm text-zinc-300" data-testid={`week-capacity-${week.week_start}`}>
                      {week.remaining} / {week.capacity} {t.spotsAvailable}
                    </p>
                  </button>
                ))}
              </div>
            </div>
            {bookingResult && (
              <div className="rounded-2xl border border-green-500/20 bg-green-500/10 p-4 text-sm text-green-100" data-testid="booking-success-panel">
                <p className="font-semibold">{t.bookingSubmitted}</p>
                <p className="mt-2">ID: {bookingResult.booking_id}</p>
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
                <Input data-testid="owner-phone-input" onChange={(event) => updateField("owner_phone", event.target.value)} placeholder={t.phone} required value={formState.owner_phone} />
                <Input data-testid="owner-address-input" onChange={(event) => updateField("owner_address", event.target.value)} placeholder={t.address} required value={formState.owner_address} />
              </section>
              <section className="grid gap-4 md:grid-cols-2">
                <div className="md:col-span-2">
                  <p className="mb-2 text-sm uppercase tracking-[0.2em] text-zinc-500">{t.dogInformation}</p>
                </div>
                <Input data-testid="dog-name-input" onChange={(event) => updateField("dog_name", event.target.value)} placeholder={t.dogName} required value={formState.dog_name} />
                <Input data-testid="dog-breed-input" onChange={(event) => updateField("breed", event.target.value)} placeholder={t.breed} required value={formState.breed} />
                <Input data-testid="dog-age-input" onChange={(event) => updateField("age", event.target.value)} placeholder={t.age} value={formState.age} />
                <select className="h-11 rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="dog-sex-select" onChange={(event) => updateField("sex", event.target.value)} value={formState.sex}>
                  <option value="Male">{t.male}</option>
                  <option value="Female">{t.female}</option>
                </select>
                <Input data-testid="dog-weight-input" onChange={(event) => updateField("weight", event.target.value)} placeholder={t.weight} required value={formState.weight} />
                <Input data-testid="dog-dob-input" onChange={(event) => updateField("date_of_birth", event.target.value)} required type="date" value={formState.date_of_birth} />
                <Input data-testid="dog-vaccination-status-input" onChange={(event) => updateField("vaccination_status", event.target.value)} placeholder={t.vaccinationStatus} required value={formState.vaccination_status} />
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
              <Button className="rounded-full bg-primary text-white hover:bg-red-700" data-testid="submit-booking-button" disabled={submitting} type="submit">
                {submitting ? "..." : t.submitBooking}
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

const AdminLoginPage = ({ config, language, setLanguage, onLogin }) => {
  const t = translations[language];
  const navigate = useNavigate();
  const [formState, setFormState] = useState({
    email: config?.demo_admin?.email || "",
    password: config?.demo_admin?.password || "",
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setFormState({ email: config?.demo_admin?.email || "", password: config?.demo_admin?.password || "" });
  }, [config]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      await onLogin(formState);
      navigate("/admin/dashboard");
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell pb-16" data-testid="admin-login-page">
      <PublicHeader config={config} language={language} setLanguage={setLanguage} t={t} />
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
            <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-5" data-testid="demo-credentials-panel">
              <p className="text-xs uppercase tracking-[0.2em] text-red-100">{t.demoCredentials}</p>
              <p className="mt-3 text-sm">{config?.demo_admin?.email}</p>
              <p className="text-sm">{config?.demo_admin?.password}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/20 p-5 text-sm leading-7 text-zinc-400">
              {language === "es"
                ? "Los correos del MVP quedan registrados internamente hasta que añadas credenciales SMTP reales en una siguiente fase."
                : "For this MVP, outgoing emails are stored internally until real SMTP credentials are added later."}
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

const BookingDetailDialog = ({ booking, language, onClose, onSave, token }) => {
  const t = translations[language];
  const [formState, setFormState] = useState(null);

  useEffect(() => {
    if (booking) {
      setFormState({
        status: booking.status,
        payment_status: booking.payment_status,
        vaccination_certificate_status: booking.vaccination_certificate_status,
        eligibility_status: booking.eligibility_status,
        intake_date: booking.intake_date || "",
        delivery_date: booking.delivery_date || "",
        internal_notes: booking.internal_notes || "",
        rejection_reason: booking.rejection_reason || "",
      });
    }
  }, [booking]);

  if (!booking || !formState) return null;

  const saveChanges = async () => {
    await onSave(booking.id, {
      ...formState,
      intake_date: formState.intake_date || null,
      delivery_date: formState.delivery_date || null,
    });
    onClose();
  };

  return (
    <Dialog onOpenChange={(open) => !open && onClose()} open={Boolean(booking)}>
      <DialogContent className="max-w-4xl border-white/10 bg-zinc-950 text-white" data-testid="booking-detail-dialog">
        <DialogHeader>
          <DialogTitle>{booking.dog.name} · {booking.owner.full_name}</DialogTitle>
          <DialogDescription className="text-zinc-400">{booking.start_week} · {booking.program_name_es}</DialogDescription>
        </DialogHeader>
        <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
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
            <div className="flex flex-wrap gap-2" data-testid="medical-flags-panel">
              {booking.medical_flags.map((flag) => (
                <span className="status-chip bg-black/20 text-zinc-200" key={flag.label}>{flag.label}</span>
              ))}
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <Button className="rounded-full" data-testid="open-payment-proof-button" onClick={() => openProtectedDocument(token, booking.id, "payment_proof")} type="button" variant="outline">
                <FileText className="mr-2 h-4 w-4" /> {t.paymentProof}
              </Button>
              <Button className="rounded-full" data-testid="open-certificate-button" onClick={() => openProtectedDocument(token, booking.id, "vaccination_certificate")} type="button" variant="outline">
                <ShieldCheck className="mr-2 h-4 w-4" /> {t.vaccinationCertificate}
              </Button>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <select className="h-11 rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="booking-status-select" onChange={(event) => setFormState((current) => ({ ...current, status: event.target.value }))} value={formState.status}>
              {STATUS_OPTIONS.map((option) => <option key={option} value={option}>{t.status[option] || option}</option>)}
            </select>
            <select className="h-11 rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="payment-status-select" onChange={(event) => setFormState((current) => ({ ...current, payment_status: event.target.value }))} value={formState.payment_status}>
              {DOC_STATUS_OPTIONS.map((option) => <option key={option} value={option}>{t.status[option] || option}</option>)}
            </select>
            <select className="h-11 rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="certificate-status-select" onChange={(event) => setFormState((current) => ({ ...current, vaccination_certificate_status: event.target.value }))} value={formState.vaccination_certificate_status}>
              {DOC_STATUS_OPTIONS.map((option) => <option key={option} value={option}>{t.status[option] || option}</option>)}
            </select>
            <select className="h-11 rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="eligibility-status-select" onChange={(event) => setFormState((current) => ({ ...current, eligibility_status: event.target.value }))} value={formState.eligibility_status}>
              {ELIGIBILITY_OPTIONS.map((option) => <option key={option} value={option}>{t.status[option] || option}</option>)}
            </select>
            <Input data-testid="intake-date-input" onChange={(event) => setFormState((current) => ({ ...current, intake_date: event.target.value }))} type="date" value={formState.intake_date} />
            <Input data-testid="delivery-date-input" onChange={(event) => setFormState((current) => ({ ...current, delivery_date: event.target.value }))} type="date" value={formState.delivery_date} />
            <div className="md:col-span-2">
              <Input data-testid="rejection-reason-input" onChange={(event) => setFormState((current) => ({ ...current, rejection_reason: event.target.value }))} placeholder="Rejection reason" value={formState.rejection_reason} />
            </div>
            <div className="md:col-span-2">
              <Textarea data-testid="internal-notes-textarea" onChange={(event) => setFormState((current) => ({ ...current, internal_notes: event.target.value }))} placeholder="Internal notes" value={formState.internal_notes} />
            </div>
            <div className="md:col-span-2 flex justify-end gap-3">
              <Button data-testid="close-booking-dialog-button" onClick={onClose} type="button" variant="outline">{t.close}</Button>
              <Button className="bg-primary text-white hover:bg-red-700" data-testid="save-booking-dialog-button" onClick={saveChanges} type="button">
                {t.saveChanges}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

const ManualBookingDialog = ({ open, onClose, programs, onCreate, language }) => {
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
    age: "",
    sex: "Male",
    weight: "",
    date_of_birth: "",
    vaccination_status: "Up to date",
    allergies: "",
    behavior_goals: "",
    current_medication: "",
    additional_notes: "",
    status: "Scheduled",
    intake_date: "",
    delivery_date: "",
    internal_notes: "",
    payment_status: "Verified",
    vaccination_certificate_status: "Verified",
    eligibility_status: "Eligible",
  });

  useEffect(() => {
    if (programs.length && !formState.program_id) {
      setFormState((current) => ({ ...current, program_id: programs[0].id }));
    }
  }, [formState.program_id, programs]);

  const update = (key, value) => setFormState((current) => ({ ...current, [key]: value }));

  const handleCreate = async () => {
    await onCreate({
      ...formState,
      intake_date: formState.intake_date || null,
      delivery_date: formState.delivery_date || null,
    });
    onClose();
  };

  return (
    <Dialog onOpenChange={(visible) => !visible && onClose()} open={open}>
      <DialogContent className="max-w-3xl border-white/10 bg-zinc-950 text-white" data-testid="manual-booking-dialog">
        <DialogHeader>
          <DialogTitle>{t.manualBooking}</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 md:grid-cols-2">
          <select className="h-11 rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="manual-program-select" onChange={(event) => update("program_id", event.target.value)} value={formState.program_id}>
            {programs.map((program) => <option key={program.id} value={program.id}>{language === "es" ? program.name_es : program.name_en}</option>)}
          </select>
          <Input data-testid="manual-start-week-input" onChange={(event) => update("start_week", event.target.value)} type="date" value={formState.start_week} />
          <Input data-testid="manual-owner-name-input" onChange={(event) => update("owner_full_name", event.target.value)} placeholder={t.fullName} value={formState.owner_full_name} />
          <Input data-testid="manual-owner-email-input" onChange={(event) => update("owner_email", event.target.value)} placeholder={t.email} type="email" value={formState.owner_email} />
          <Input data-testid="manual-owner-phone-input" onChange={(event) => update("owner_phone", event.target.value)} placeholder={t.phone} value={formState.owner_phone} />
          <Input data-testid="manual-owner-address-input" onChange={(event) => update("owner_address", event.target.value)} placeholder={t.address} value={formState.owner_address} />
          <Input data-testid="manual-dog-name-input" onChange={(event) => update("dog_name", event.target.value)} placeholder={t.dogName} value={formState.dog_name} />
          <Input data-testid="manual-dog-breed-input" onChange={(event) => update("breed", event.target.value)} placeholder={t.breed} value={formState.breed} />
          <Input data-testid="manual-dog-age-input" onChange={(event) => update("age", event.target.value)} placeholder={t.age} value={formState.age} />
          <Input data-testid="manual-dog-weight-input" onChange={(event) => update("weight", event.target.value)} placeholder={t.weight} value={formState.weight} />
          <Input data-testid="manual-dob-input" onChange={(event) => update("date_of_birth", event.target.value)} type="date" value={formState.date_of_birth} />
          <Input data-testid="manual-vaccination-status-input" onChange={(event) => update("vaccination_status", event.target.value)} placeholder={t.vaccinationStatus} value={formState.vaccination_status} />
          <select className="h-11 rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="manual-booking-status-select" onChange={(event) => update("status", event.target.value)} value={formState.status}>
            {STATUS_OPTIONS.map((option) => <option key={option} value={option}>{t.status[option] || option}</option>)}
          </select>
          <Input data-testid="manual-intake-date-input" onChange={(event) => update("intake_date", event.target.value)} type="date" value={formState.intake_date} />
          <div className="md:col-span-2">
            <Textarea data-testid="manual-goals-textarea" onChange={(event) => update("behavior_goals", event.target.value)} placeholder={t.goals} value={formState.behavior_goals} />
          </div>
          <div className="md:col-span-2 flex justify-end gap-3">
            <Button data-testid="manual-booking-close-button" onClick={onClose} type="button" variant="outline">{t.close}</Button>
            <Button className="bg-primary text-white hover:bg-red-700" data-testid="manual-booking-save-button" onClick={handleCreate} type="button">
              {t.manualBooking}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

const DashboardView = ({ dashboard, language }) => {
  const t = translations[language];
  if (!dashboard) return null;
  return (
    <div className="grid gap-6" data-testid="admin-dashboard-view">
      <div className="grid gap-4 xl:grid-cols-4 md:grid-cols-2">
        <MetricCard subtitle={t.weeklyOccupancy} testId="metric-nearly-full-weeks" title={t.nearlyFullWeeks} value={dashboard.metrics.nearly_full_weeks} />
        <MetricCard subtitle={t.weeklyOccupancy} testId="metric-full-weeks" title={t.fullWeeks} value={dashboard.metrics.full_weeks} />
        <MetricCard subtitle={t.bookings} testId="metric-dogs-pending-intake" title={t.dogsPendingIntake} value={dashboard.metrics.dogs_pending_intake} />
        <MetricCard subtitle={t.bookings} testId="metric-dogs-in-training" title={t.dogsInTraining} value={dashboard.metrics.dogs_in_training} />
        <MetricCard subtitle={t.bookings} testId="metric-dogs-delivered" title={t.dogsDelivered} value={dashboard.metrics.dogs_delivered} />
        <MetricCard subtitle={t.finance} testId="metric-pending-payments" title={t.pendingPayments} value={dashboard.metrics.pending_payments} />
        <MetricCard subtitle={t.finance} testId="metric-confirmed-payments" title={t.confirmedPayments} value={dashboard.metrics.confirmed_payments} />
      </div>
      <div className="grid gap-6 xl:grid-cols-3">
        {[{ key: "capacity_breakdown", title: t.capacityBreakdown }, { key: "dog_status_breakdown", title: t.dogStatusBreakdown }].map((chart, chartIndex) => (
          <Card className="surface-panel rounded-[1.75rem] border-white/10" data-testid={`pie-chart-${chart.key}`} key={chart.key}>
            <CardHeader>
              <CardTitle className="text-white">{chart.title}</CardTitle>
            </CardHeader>
            <CardContent className="h-[320px]">
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={dashboard.charts[chart.key]} dataKey="value" nameKey="name" outerRadius={100}>
                    {dashboard.charts[chart.key].map((entry, index) => (
                      <Cell fill={CHART_COLORS[(chartIndex + index) % CHART_COLORS.length]} key={entry.name} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        ))}
        <Card className="surface-panel rounded-[1.75rem] border-white/10" data-testid="bar-chart-revenue">
          <CardHeader>
            <CardTitle className="text-white">{t.revenueByMonth}</CardTitle>
          </CardHeader>
          <CardContent className="h-[320px]">
            <ResponsiveContainer>
              <BarChart data={dashboard.charts.revenue}>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" />
                <XAxis dataKey="month" stroke="#a1a1aa" />
                <YAxis stroke="#a1a1aa" />
                <Tooltip />
                <Legend />
                <Bar dataKey="confirmed" fill="#22c55e" radius={[8, 8, 0, 0]} />
                <Bar dataKey="pending" fill="#dc2626" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
      <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
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
                    {week.occupied}/{week.capacity} {t.occupiedLabel} · {week.remaining} {t.remainingLabel}
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

const BookingsView = ({ bookings, programs, token, language, onUpdateBooking, onManualCreate }) => {
  const t = translations[language];
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
              <CardDescription className="text-zinc-400">{filteredBookings.length} {language === "es" ? "reservas visibles" : "visible bookings"}</CardDescription>
            </div>
            <Button className="rounded-full bg-primary text-white hover:bg-red-700" data-testid="open-manual-booking-button" onClick={() => setManualOpen(true)} type="button">
              {t.manualBooking}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-3 xl:grid-cols-4 md:grid-cols-2">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-zinc-500" />
              <Input className="pl-9" data-testid="booking-search-input" onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))} placeholder={t.searchPlaceholder} value={filters.search} />
            </div>
            <select className="h-11 rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="booking-filter-status" onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))} value={filters.status}>
              <option value="all">{t.allStatuses}</option>
              {STATUS_OPTIONS.map((status) => <option key={status} value={status}>{t.status[status] || status}</option>)}
            </select>
            <select className="h-11 rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="booking-filter-program" onChange={(event) => setFilters((current) => ({ ...current, programId: event.target.value }))} value={filters.programId}>
              <option value="all">{t.allPrograms}</option>
              {programs.map((program) => <option key={program.id} value={program.id}>{language === "es" ? program.name_es : program.name_en}</option>)}
            </select>
            <select className="h-11 rounded-xl border border-white/10 bg-zinc-950 px-3 text-white" data-testid="booking-filter-week" onChange={(event) => setFilters((current) => ({ ...current, weekStart: event.target.value }))} value={filters.weekStart}>
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
                  <th className="px-4">Docs</th>
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
                    <td className="rounded-r-2xl px-4 py-4 text-sm text-zinc-300">
                      {t.status[booking.payment_status] || booking.payment_status} / {t.status[booking.vaccination_certificate_status] || booking.vaccination_certificate_status}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
      <BookingDetailDialog booking={selectedBooking} language={language} onClose={() => setSelectedBooking(null)} onSave={onUpdateBooking} token={token} />
      <ManualBookingDialog language={language} onClose={() => setManualOpen(false)} onCreate={onManualCreate} open={manualOpen} programs={programs} />
    </div>
  );
};

const ProgramsView = ({ programs, language, onSaveProgram }) => {
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
    active: true,
  });

  useEffect(() => {
    if (editingProgram) {
      setFormState(editingProgram);
    } else {
      setFormState({
        name_es: "",
        name_en: "",
        description_es: "",
        description_en: "",
        duration_value: 1,
        duration_unit: "days",
        price: 0,
        active: true,
      });
    }
  }, [editingProgram]);

  const update = (key, value) => setFormState((current) => ({ ...current, [key]: value }));

  return (
    <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]" data-testid="admin-programs-view">
      <div className="grid gap-4">
        {programs.map((program) => (
          <Card className="surface-panel rounded-[1.75rem] border-white/10" data-testid={`admin-program-card-${program.id}`} key={program.id}>
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <CardTitle className="text-white">{program.name_es}</CardTitle>
                  <CardDescription className="text-zinc-400">{program.name_en}</CardDescription>
                </div>
                <Button data-testid={`edit-program-button-${program.id}`} onClick={() => setEditingProgram(program)} type="button" variant="outline">{t.edit}</Button>
              </div>
            </CardHeader>
            <CardContent className="text-sm text-zinc-300">
              <p>{program.description_es}</p>
              <p className="mt-3 text-zinc-500">{program.duration_value} {program.duration_unit === "weeks" ? t.weeks : t.days} · {formatCurrency(program.price, language)}</p>
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
          <div className="md:col-span-2 flex justify-end gap-3">
            {editingProgram && <Button data-testid="cancel-program-edit-button" onClick={() => setEditingProgram(null)} type="button" variant="outline">{t.close}</Button>}
            <Button className="bg-primary text-white hover:bg-red-700" data-testid="save-program-button" onClick={() => onSaveProgram(editingProgram?.id, formState).then(() => setEditingProgram(null))} type="button">
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
              <p className="text-sm text-zinc-500">{week.occupied} {t.occupiedLabel} · {week.remaining} {t.remainingLabel}</p>
            </div>
            <Input data-testid={`capacity-input-${week.week_start}`} onChange={(event) => setDrafts((current) => ({ ...current, [week.week_start]: event.target.value }))} type="number" value={drafts[week.week_start] ?? week.capacity} />
            <Button className="rounded-full bg-primary text-white hover:bg-red-700" data-testid={`capacity-save-${week.week_start}`} onClick={() => onSaveCapacity(week.week_start, Number(drafts[week.week_start] ?? week.capacity))} type="button">
              {t.saveWeek}
            </Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

const SettingsView = ({ settings, emailLogs, onSaveSettings, onUploadLogo, language }) => {
  const t = translations[language];
  const [formState, setFormState] = useState(settings);

  useEffect(() => {
    setFormState(settings);
  }, [settings]);

  if (!formState) return null;

  const update = (key, value) => setFormState((current) => ({ ...current, [key]: value }));

  return (
    <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]" data-testid="admin-settings-view">
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
          <div className="md:col-span-2 rounded-2xl border border-dashed border-white/10 bg-white/5 p-4">
            <label className="mb-3 block text-sm text-zinc-300">{t.uploadLogo}</label>
            <input data-testid="settings-logo-file-input" onChange={(event) => event.target.files?.[0] && onUploadLogo(event.target.files[0])} type="file" />
          </div>
          <div className="md:col-span-2 flex justify-end">
            <Button className="bg-primary text-white hover:bg-red-700" data-testid="settings-save-button" onClick={() => onSaveSettings(formState)} type="button">
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

const AdminShell = ({ language, setLanguage, session, onLogout, refreshPublicData, config }) => {
  const t = translations[language];
  const location = useLocation();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [bookings, setBookings] = useState([]);
  const [programs, setPrograms] = useState([]);
  const [capacityWeeks, setCapacityWeeks] = useState([]);
  const [settings, setSettings] = useState(null);
  const [emailLogs, setEmailLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const refreshAll = useCallback(async () => {
    setLoading(true);
    try {
      const [dashboardResponse, bookingsResponse, programsResponse, capacityResponse, settingsResponse, emailLogsResponse] = await Promise.all([
        adminApi.getDashboard(session.token),
        adminApi.getBookings(session.token),
        adminApi.getPrograms(session.token),
        adminApi.getCapacity(session.token),
        adminApi.getSettings(session.token),
        adminApi.getEmailLogs(session.token),
      ]);
      setDashboard(dashboardResponse);
      setBookings(bookingsResponse);
      setPrograms(programsResponse);
      setCapacityWeeks(capacityResponse);
      setSettings(settingsResponse);
      setEmailLogs(emailLogsResponse);
    } catch (error) {
      toast.error(error.message);
      onLogout();
      navigate("/admin/login");
    } finally {
      setLoading(false);
    }
  }, [navigate, onLogout, session.token]);

  useEffect(() => {
    if (location.pathname === "/admin") {
      navigate("/admin/dashboard", { replace: true });
    }
  }, [location.pathname, navigate]);

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  const currentSection = location.pathname.split("/")[2] || "dashboard";

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
      await adminApi.updateSettings(session.token, payload);
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

  const navigationItems = [
    { key: "dashboard", label: t.dashboard, icon: LayoutDashboard },
    { key: "bookings", label: t.bookings, icon: FileText },
    { key: "programs", label: t.programs, icon: Dog },
    { key: "capacity", label: t.capacity, icon: CalendarRange },
    { key: "settings", label: t.settings, icon: Settings },
  ];

  return (
    <div className="app-shell section-shell pb-12 pt-10" data-testid="admin-shell">
      <div className="dashboard-layout">
        <aside className="surface-panel h-fit rounded-[2rem] p-5">
          <div className="flex items-center justify-between gap-3">
            <BrandMark config={config} />
          </div>
          <div className="mt-6">
            <LanguageToggle language={language} setLanguage={setLanguage} />
          </div>
          <nav className="mt-6 grid gap-2">
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
            </div>
            <Button className="mt-4 w-full rounded-full" data-testid="admin-logout-button" onClick={onLogout} type="button" variant="outline">
              <LogOut className="mr-2 h-4 w-4" /> {t.logout}
            </Button>
          </div>
        </aside>
        <div className="grid gap-6">
          <header className="surface-panel flex flex-wrap items-center justify-between gap-4 rounded-[2rem] p-6">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">PAWS TRAINING</p>
              <h1 className="text-3xl text-white" data-testid="admin-page-title">{navigationItems.find((item) => item.key === currentSection)?.label}</h1>
            </div>
            <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-zinc-300" data-testid="admin-email-mode-pill">
              {t.emailModeLabel}
            </div>
          </header>
          {loading ? (
            <Card className="surface-panel rounded-[2rem] border-white/10 p-10 text-center text-zinc-400">{t.loadingAdmin}</Card>
          ) : (
            <>
              {currentSection === "dashboard" && <DashboardView dashboard={dashboard} language={language} />}
              {currentSection === "bookings" && (
                <BookingsView
                  bookings={bookings}
                  language={language}
                  onManualCreate={createManualBooking}
                  onUpdateBooking={saveBooking}
                  programs={programs}
                  token={session.token}
                />
              )}
              {currentSection === "programs" && <ProgramsView language={language} onSaveProgram={saveProgram} programs={programs} />}
              {currentSection === "capacity" && <CapacityView capacityWeeks={capacityWeeks} language={language} onSaveCapacity={saveCapacity} />}
              {currentSection === "settings" && (
                <SettingsView
                  emailLogs={emailLogs}
                  language={language}
                  onSaveSettings={saveSettings}
                  onUploadLogo={uploadLogo}
                  settings={settings}
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const AppRoutes = ({ publicState, session, setSession, language, setLanguage, refreshPublicData }) => {
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
      <Route path="/book" element={<BookingPage config={publicState.config} language={language} programs={publicState.programs} setLanguage={setLanguage} />} />
      <Route path="/admin/login" element={<AdminLoginPage config={publicState.config} language={language} onLogin={handleLogin} setLanguage={setLanguage} />} />
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

  const refreshPublicData = useCallback(async () => {
    try {
      const [config, programs] = await Promise.all([publicApi.getConfig(), publicApi.getPrograms()]);
      setPublicState({ config, programs });
    } catch (error) {
      toast.error(error.message);
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
        await adminApi.me(session.token);
      } catch {
        localStorage.removeItem("paws-admin-session");
        setSession(null);
      }
    };
    validateSession();
  }, [session]);

  if (!publicState.config) {
    return <div className="app-shell flex min-h-screen items-center justify-center text-zinc-400">Loading PAWS TRAINING...</div>;
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
