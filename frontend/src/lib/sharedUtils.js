export const CHART_COLORS = ["#dc2626", "#d4d4d8", "#22c55e", "#3b82f6", "#facc15", "#8b5cf6"];
export const STATUS_OPTIONS = ["Pending Review", "Approved", "Rejected", "Scheduled", "In Training", "Delivered", "Cancelled", "Expired"];
export const DOC_STATUS_OPTIONS = ["Pending Review", "Verified", "Invalid"];
export const ELIGIBILITY_OPTIONS = ["Pending Review", "Eligible", "Ineligible"];
export const CURRENCY_OPTIONS = [
  { value: "USD", label: "$ USD" },
  { value: "EUR", label: "€ EUR" },
  { value: "GBP", label: "£ GBP" },
];
export const LANDING_FEATURE_CARD_TEMPLATE = [
  { id: "base-capacity", title_es: "", title_en: "", description_es: "", description_en: "" },
  { id: "review-scope", title_es: "", title_en: "", description_es: "", description_en: "" },
  { id: "email-mode", title_es: "", title_en: "", description_es: "", description_en: "" },
];

export const formatCurrency = (value, _language, currencyCode = "USD") => {
  const symbols = { USD: "$", EUR: "€", GBP: "£" };
  const amount = Number(value || 0);
  const amountText = Number.isInteger(amount) ? `${amount}` : amount.toFixed(2).replace(/\.00$/, "").replace(/(\.[1-9])0$/, "$1");
  return `${symbols[currencyCode] || "$"}${amountText}`;
};

export const isValidEmailAddress = (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || "").trim());

export const normalizeLandingContent = (landingContent = {}) => ({
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

export const normalizeSettingsState = (settings = {}) => ({
  ...settings,
  stripe_enabled: Boolean(settings?.stripe_onboarding_complete ?? settings?.stripe_enabled),
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

export const getLocalizedLandingText = (content, baseKey, language, fallback = "") =>
  content?.[`${baseKey}_${language}`] || fallback;

export const calculateDogAge = (dateOfBirth, language) => {
  if (!dateOfBirth) return "";
  const birthDate = new Date(`${dateOfBirth}T00:00:00`);
  if (Number.isNaN(birthDate.getTime())) return "";
  const today = new Date();
  let years = today.getFullYear() - birthDate.getFullYear();
  let months = today.getMonth() - birthDate.getMonth();
  const days = today.getDate() - birthDate.getDate();
  if (days < 0) months -= 1;
  if (months < 0) { years -= 1; months += 12; }
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

export const formatDisplayDate = (isoDate, language) => {
  if (!isoDate) return "";
  const dateValue = new Date(`${isoDate}T00:00:00`);
  if (Number.isNaN(dateValue.getTime())) return isoDate;
  return new Intl.DateTimeFormat(language === "es" ? "es-ES" : "en-US", {
    day: "2-digit", month: "short", year: "numeric",
  }).format(dateValue);
};

export const getProgramDurationDays = (durationValue, durationUnit) => {
  const normalizedValue = Number(durationValue || 0);
  if (!normalizedValue) return 0;
  return durationUnit === "weeks" ? normalizedValue * 7 : normalizedValue;
};

export const getProgramSpanWeeks = (program) => {
  if (!program) return 0;
  if (program.duration_unit === "weeks") return Math.max(Number(program.duration_value || 0), 1);
  return Math.max(Math.ceil(Number(program.duration_value || 0) / 7), 1);
};

export const shiftIsoDateByWeeks = (isoDate, weekOffset) => {
  const baseDate = new Date(`${isoDate}T00:00:00`);
  if (Number.isNaN(baseDate.getTime())) return "";
  baseDate.setDate(baseDate.getDate() + weekOffset * 7);
  return baseDate.toISOString().split("T")[0];
};

export const getScheduleDatesFromProgram = (startDateValue, durationValue, durationUnit) => {
  if (!startDateValue) return { intake_date: "", delivery_date: "" };
  const intakeDate = startDateValue;
  const startDate = new Date(`${intakeDate}T00:00:00`);
  if (Number.isNaN(startDate.getTime())) return { intake_date: intakeDate, delivery_date: "" };
  const totalDays = getProgramDurationDays(durationValue, durationUnit);
  if (!totalDays) return { intake_date: intakeDate, delivery_date: "" };
  const deliveryDate = new Date(startDate);
  deliveryDate.setDate(deliveryDate.getDate() + Math.max(totalDays - 1, 0));
  return { intake_date: intakeDate, delivery_date: deliveryDate.toISOString().split("T")[0] };
};

export const formatMonthLabel = (dateValue, language) =>
  new Intl.DateTimeFormat(language === "es" ? "es-ES" : "en-US", { month: "long", year: "numeric" }).format(dateValue);

export const buildReservationCalendarMonths = (weeks) => {
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
      return { id: iso, isCurrentMonth: true, iso, week: weekLookup.get(iso) || null, dayNumber };
    });
    return { monthDate, cells };
  });
};

export const getBookingScheduleDates = (booking) => {
  if (!booking?.start_week) return { intake_date: "", delivery_date: "" };
  return getScheduleDatesFromProgram(booking.start_week, booking.duration_value, booking.duration_unit);
};

export const parseDogDateInput = (value) => {
  if (!value) return "";
  const parsed = new Date(`${value}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return "";
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  if (parsed > today) return "";
  return value;
};

export const getStatusStyles = (status) => {
  if (["Approved", "Verified", "Eligible", "Delivered", "Paid in Full"].includes(status)) return "border-green-500/25 bg-green-500/10 text-green-200";
  if (["Pending Review", "almost_full", "In Training", "Scheduled", "Deposit Pending", "Balance Pending"].includes(status)) return "border-yellow-500/25 bg-yellow-500/10 text-yellow-200";
  if (["Deposit Verified"].includes(status)) return "border-blue-500/25 bg-blue-500/10 text-blue-200";
  if (["Rejected", "Invalid", "Cancelled", "Expired", "Ineligible", "full"].includes(status)) return "border-red-500/25 bg-red-500/10 text-red-200";
  return "border-zinc-700 bg-zinc-800/80 text-zinc-200";
};
