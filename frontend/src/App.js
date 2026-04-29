import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import "@/App.css";
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useParams,
  useSearchParams,
} from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  Mail,
  MapPinned,
  Phone,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Toaster } from "@/components/ui/sonner";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { adminApi, clearAdminCache, publicApi } from "@/lib/api";
import { translations } from "@/lib/translations";
import {
  normalizeLandingContent,
  getLocalizedLandingText,
  formatCurrency,
  parseDogDateInput,
  calculateDogAge,
  buildReservationCalendarMonths,
  formatMonthLabel,
  formatDisplayDate,
  getStatusStyles,
  isValidEmailAddress,
} from "@/lib/sharedUtils";
import { AppFooter, PublicHeader } from "@/components/SharedComponents";

const HERO_IMAGE = "https://res.cloudinary.com/dyuksod2i/image/upload/f_auto,q_auto:good,w_1400,c_limit/pawstraining/defaults/hero-default";
const CONTENT_IMAGE = "https://res.cloudinary.com/dyuksod2i/image/upload/f_auto,q_auto:good,w_800,c_limit/pawstraining/defaults/program-default";

const LazyAdminLoginPage = lazy(() => import("./AdminPanel").then((m) => ({ default: m.AdminLoginPage })));
const LazyAdminShell = lazy(() => import("./AdminPanel").then((m) => ({ default: m.AdminShell })));
const LazyRequireAdmin = lazy(() => import("./AdminPanel").then((m) => ({ default: m.RequireAdmin })));

const ADMIN_FALLBACK = <div className="flex min-h-screen items-center justify-center bg-black text-zinc-400">Loading...</div>;

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
            {programs.map((program) => (
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
  const [searchParams] = useSearchParams();
  const [paymentMethod, setPaymentMethod] = useState("manual");
  const [selectedProgramId, setSelectedProgramId] = useState(programs[0]?.id || "");
  const [weeks, setWeeks] = useState([]);
  const [loadingWeeks, setLoadingWeeks] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [bookingResult, setBookingResult] = useState(() =>
    searchParams.get("stripe_success") === "true" && searchParams.get("booking_id")
      ? { booking_id: searchParams.get("booking_id"), reservation_expires_at: null, stripe: true }
      : null
  );
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

  useEffect(() => { loadWeeks(); }, [loadWeeks]);

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
    if ((paymentMethod === "manual" && !formState.payment_proof) || !formState.vaccination_certificate) {
      toast.error(language === "es" ? "Debes cargar todos los documentos requeridos." : "Please upload all required documents.");
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
      payload.append("payment_method", paymentMethod);
      Object.entries(formState).forEach(([key, value]) => {
        if (key !== "confirm_email" && value !== null && value !== undefined) {
          payload.append(key, value);
        }
      });
      payload.delete("date_of_birth_input");
      payload.append("date_of_birth", normalizedDogBirthDate);
      payload.append("age", computedDogAge);
      const response = await publicApi.submitBooking(payload);
      if (paymentMethod === "stripe") {
        const { url } = await publicApi.createStripeSession(response.booking_id);
        window.location.href = url;
        return;
      }
      setBookingResult(response);
      toast.success(t.bookingSubmitted);
      setFormState((current) => ({
        ...current,
        owner_full_name: "", owner_email: "", confirm_email: "", owner_phone: "",
        owner_address: "", dog_name: "", breed: "", weight: "", date_of_birth_input: "",
        vaccination_status: t.yes, allergies: "", behavior_goals: "",
        current_medication: "", additional_notes: "", payment_proof: null, vaccination_certificate: null,
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
                onChange={(event) => { setSelectedProgramId(event.target.value); updateField("start_week", ""); }}
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
                              <span className="text-[10px] leading-4">{cell.week.remaining} {t.spacesLeft}</span>
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
                {bookingResult.stripe ? (
                  <p className="mt-2 font-medium">
                    {language === "es"
                      ? "✅ Pago con tarjeta completado. Recibirás una confirmación por correo."
                      : "✅ Card payment completed. You will receive a confirmation by email."}
                  </p>
                ) : (
                  <>
                    <p className="mt-1">{t.reservationSummaryPrice}: {formatCurrency(selectedProgram?.price, language, currencyCode)}</p>
                    {selectedProgram && (() => {
                      const depType = selectedProgram.deposit_type || "percentage";
                      const depVal = selectedProgram.deposit_value ?? 100;
                      const dep = depType === "fixed" ? Math.min(depVal, selectedProgram.price) : Math.round(selectedProgram.price * depVal / 100 * 100) / 100;
                      const bal = Math.round((selectedProgram.price - dep) * 100) / 100;
                      return <p className="mt-1">{t.depositLabel}: {formatCurrency(dep, language, currencyCode)} · {t.balanceLabel}: {formatCurrency(bal, language, currencyCode)}</p>;
                    })()}
                    <p className="mt-1">{t.reservationHeldUntil}: {bookingResult.reservation_expires_at}</p>
                  </>
                )}
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
                  <p className="md:col-span-2 text-sm text-red-300" data-testid="owner-email-validation-message">{emailValidationMessage}</p>
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
              <div className="space-y-3">
                <p className="text-sm text-zinc-300">Método de pago</p>

                <div className="flex gap-3">
                  <button type="button"
                    onClick={() => setPaymentMethod("manual")}
                    className={paymentMethod === "manual" ? "bg-red-600 text-white px-4 py-2 rounded" : "bg-zinc-800 text-white px-4 py-2 rounded"}>
                    Manual
                  </button>

                  {config?.stripe_enabled && (
                    <button type="button"
                      onClick={() => setPaymentMethod("stripe")}
                      className={paymentMethod === "stripe" ? "bg-red-600 text-white px-4 py-2 rounded" : "bg-zinc-800 text-white px-4 py-2 rounded"}>
                      Tarjeta
                    </button>
                  )}
                </div>
              </div>

              {paymentMethod === "manual" && (
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
              )}

              {paymentMethod === "stripe" && (
                <div className="text-white text-sm">
                  Pago con tarjeta disponible al continuar.
                </div>
              )}
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
    clearAdminCache();
  };

  return (
    <Routes>
      <Route path="/" element={<LandingPage config={publicState.config} language={language} programs={publicState.programs} setLanguage={setLanguage} showAdminAccess={showAdminAccess} />} />
      <Route path="/book" element={<BookingPage config={publicState.config} language={language} programs={publicState.programs} setLanguage={setLanguage} showAdminAccess={showAdminAccess} />} />
      <Route path="/payment/:token" element={<FinalPaymentPage language={language} setLanguage={setLanguage} />} />
      <Route
        path="/admin/login"
        element={
          <Suspense fallback={ADMIN_FALLBACK}>
            <LazyAdminLoginPage config={publicState.config} language={language} onLogin={handleLogin} setLanguage={setLanguage} showAdminAccess={showAdminAccess} />
          </Suspense>
        }
      />
      <Route
        path="/admin/*"
        element={
          <Suspense fallback={ADMIN_FALLBACK}>
            <LazyRequireAdmin session={session}>
              <LazyAdminShell
                config={publicState.config}
                language={language}
                onLogout={handleLogout}
                refreshPublicData={refreshPublicData}
                session={session}
                setSession={setSession}
                setLanguage={setLanguage}
              />
            </LazyRequireAdmin>
          </Suspense>
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
