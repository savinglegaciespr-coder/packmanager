import logging
import math
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from starlette.middleware.cors import CORSMiddleware


ROOT_DIR = Path(__file__).parent
UPLOAD_DIR = ROOT_DIR / "storage"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

JWT_SECRET = os.environ["JWT_SECRET"]
DEMO_ADMIN_EMAIL = os.environ["DEMO_ADMIN_EMAIL"]
DEMO_ADMIN_PASSWORD = os.environ["DEMO_ADMIN_PASSWORD"]
DEMO_ADMIN_NAME = os.environ["DEMO_ADMIN_NAME"]

DEFAULT_WEEKLY_CAPACITY = 8
OPERATIONAL_START = date(2026, 3, 30)
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12
ALGORITHM = "HS256"
VALID_BOOKING_STATUSES = {
    "Pending Review",
    "Approved",
    "Rejected",
    "Scheduled",
    "In Training",
    "Delivered",
    "Cancelled",
    "Expired",
}
ACTIVE_CAPACITY_STATUSES = {"Pending Review", "Approved", "Scheduled", "In Training", "Delivered"}
CONFIRMED_CAPACITY_STATUSES = {"Approved", "Scheduled", "In Training", "Delivered"}
DOC_STATUS_VALUES = {"Pending Review", "Verified", "Invalid"}
ELIGIBILITY_VALUES = {"Pending Review", "Eligible", "Ineligible"}
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
CURRENCY_OPTIONS = {
    "USD": {"symbol": "$", "label": "$ USD"},
    "EUR": {"symbol": "€", "label": "€ EUR"},
    "GBP": {"symbol": "£", "label": "£ GBP"},
}
bearer_scheme = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


app = FastAPI(title="PAWS TRAINING API")
api_router = APIRouter(prefix="/api")


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProgramPayload(BaseModel):
    name_es: str
    name_en: str
    description_es: str
    description_en: str
    duration_value: int = Field(ge=1)
    duration_unit: Literal["days", "weeks"]
    price: float = Field(ge=0)
    active: bool = True


class CapacityUpdate(BaseModel):
    capacity: int = Field(ge=1, le=100)


class SettingsUpdate(BaseModel):
    business_name: Optional[str] = None
    slogan: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_address: Optional[str] = None
    admin_notification_email: Optional[str] = None
    logo_url: Optional[str] = None
    service_label_es: Optional[str] = None
    service_label_en: Optional[str] = None
    booking_term_es: Optional[str] = None
    booking_term_en: Optional[str] = None
    primary_color: Optional[str] = None
    accent_color: Optional[str] = None
    surface_color: Optional[str] = None
    currency: Optional[Literal["USD", "EUR", "GBP"]] = None
    landing_content: Optional[Dict[str, Any]] = None


class BookingUpdateRequest(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    vaccination_certificate_status: Optional[str] = None
    eligibility_status: Optional[str] = None
    intake_date: Optional[str] = None
    delivery_date: Optional[str] = None
    internal_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class ManualBookingCreate(BaseModel):
    program_id: str
    start_week: str
    locale: str = "es"
    owner_full_name: str
    owner_email: EmailStr
    owner_phone: str
    owner_address: str
    dog_name: str
    breed: str
    age: Optional[str] = None
    sex: str
    weight: str
    date_of_birth: str
    vaccination_status: str
    allergies: Optional[str] = None
    behavior_goals: str
    current_medication: Optional[str] = None
    additional_notes: Optional[str] = None
    status: str = "Scheduled"
    intake_date: Optional[str] = None
    delivery_date: Optional[str] = None
    internal_notes: Optional[str] = None
    payment_status: str = "Verified"
    vaccination_certificate_status: str = "Verified"
    eligibility_status: str = "Eligible"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)


def parse_week_start(week_value: str) -> date:
    selected = date.fromisoformat(week_value[:10])
    normalized = selected - timedelta(days=selected.weekday())
    if normalized < OPERATIONAL_START:
        raise HTTPException(status_code=400, detail="Selected week is before the operational start date.")
    return normalized


def build_week_starts(start_week: str, span_weeks: int) -> List[str]:
    start_date = parse_week_start(start_week)
    return [(start_date + timedelta(weeks=index)).isoformat() for index in range(span_weeks)]


def get_program_span_weeks(program_doc: Dict[str, Any]) -> int:
    duration_value = int(program_doc["duration_value"])
    if program_doc["duration_unit"] == "weeks":
        return max(1, duration_value)
    return max(1, math.ceil(duration_value / 7))


def create_access_token(admin: Dict[str, Any]) -> str:
    expire = utc_now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": admin["id"], "email": admin["email"], "name": admin["name"], "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[ALGORITHM])
        admin_id = payload.get("sub")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.") from exc

    if not admin_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    admin = await db.admins.find_one({"id": admin_id}, {"_id": 0, "password_hash": 0})
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found.")
    return admin


def sanitize_program(program_doc: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in program_doc.items() if key != "_id"}


def build_medical_flags(booking: Dict[str, Any]) -> List[Dict[str, str]]:
    flags: List[Dict[str, str]] = []
    if booking.get("vaccination_certificate_status") == "Verified":
        flags.append({"icon": "shield-check", "label": "Vaccines Verified", "color": "green"})
    elif booking.get("vaccination_certificate_status") == "Pending Review":
        flags.append({"icon": "shield-alert", "label": "Certificate Pending Review", "color": "yellow"})

    allergies = (booking.get("dog", {}) or {}).get("allergies")
    if allergies:
        flags.append({"icon": "triangle-alert", "label": "Important Allergy", "color": "red"})

    medication = (booking.get("dog", {}) or {}).get("current_medication")
    if medication:
        flags.append({"icon": "pill", "label": "Medication Noted", "color": "blue"})

    if not flags:
        flags.append({"icon": "badge-check", "label": "No Major Medical Concerns", "color": "zinc"})
    return flags


def sanitize_booking(booking_doc: Dict[str, Any]) -> Dict[str, Any]:
    booking = {key: value for key, value in booking_doc.items() if key != "_id"}
    booking["medical_flags"] = build_medical_flags(booking)
    return booking


def default_landing_content() -> Dict[str, Any]:
    return {
        "hero_description_es": "PAWS TRAINING combina una experiencia de reserva clara para clientes con un panel administrativo robusto para validar documentos, pagos y ocupación por semana.",
        "hero_description_en": "PAWS TRAINING combines a clear client booking experience with a robust admin workspace for document validation, payments, and weekly occupancy control.",
        "reserve_button_label_es": "Reservar espacio",
        "reserve_button_label_en": "Book a spot",
        "admin_button_label_es": "Acceso administrativo",
        "admin_button_label_en": "Admin login",
        "feature_cards": [
            {
                "id": "base-capacity",
                "title_es": "Capacidad semanal",
                "title_en": "Weekly capacity",
                "description_es": "8 plazas base por semana con ajustes manuales por parte del administrador.",
                "description_en": "8 base spots per week with manual admin overrides whenever needed.",
            },
            {
                "id": "review-scope",
                "title_es": "Revisión documental",
                "title_en": "Document review",
                "description_es": "Validación de comprobante de pago, vacunas y elegibilidad antes de aprobar.",
                "description_en": "Payment proof, vaccination certificate, and eligibility are validated before approval.",
            },
            {
                "id": "email-mode",
                "title_es": "Notificaciones por email",
                "title_en": "Email notifications",
                "description_es": "Correos de reserva, aprobación y rechazo registrados internamente para control operativo.",
                "description_en": "Booking, approval, and rejection emails are logged internally for operational control.",
            },
        ],
    }


def format_money(amount: float, currency_code: str) -> str:
    currency = CURRENCY_OPTIONS.get(currency_code, CURRENCY_OPTIONS["USD"])
    amount_value = float(amount or 0)
    amount_text = f"{amount_value:.0f}" if amount_value.is_integer() else f"{amount_value:.2f}".rstrip("0").rstrip(".")
    return f"{currency['symbol']}{amount_text}"


async def get_business_settings() -> Dict[str, Any]:
    settings_doc = await db.settings.find_one({"id": "business-config"}, {"_id": 0})
    if not settings_doc:
        raise HTTPException(status_code=500, detail="Business settings are unavailable.")
    return settings_doc


def default_settings() -> Dict[str, Any]:
    return {
        "id": "business-config",
        "business_name": "PAWS TRAINING",
        "slogan": "BY PET LOVERS SITTING",
        "contact_email": "hola@pawstraining.com",
        "contact_phone": "+34 600 123 456",
        "contact_address": "Madrid, España",
        "admin_notification_email": "admin@pawstraining.com",
        "logo_url": "",
        "logo_asset": None,
        "service_label_es": "Programas de entrenamiento",
        "service_label_en": "Training programs",
        "booking_term_es": "Reserva",
        "booking_term_en": "Booking",
        "primary_color": "#dc2626",
        "accent_color": "#d4d4d8",
        "surface_color": "#18181b",
        "currency": "USD",
        "landing_content": default_landing_content(),
        "email_mode": "internal_log",
        "updated_at": iso_now(),
    }


def default_programs() -> List[Dict[str, Any]]:
    now = iso_now()
    return [
        {
            "id": "basic-6-day",
            "name_es": "Programa básico de 6 días",
            "name_en": "Basic 6-day program",
            "description_es": "Trabajo intensivo de obediencia, estructura y manejo diario en una sola semana.",
            "description_en": "Intensive obedience, structure, and daily handling work completed within one week.",
            "duration_value": 6,
            "duration_unit": "days",
            "price": 420.0,
            "active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "multi-week",
            "name_es": "Programa multi-semana",
            "name_en": "Multi-week program",
            "description_es": "Plan configurable para transformación conductual y obediencia prolongada.",
            "description_en": "Configurable plan for longer behavior transformation and obedience work.",
            "duration_value": 3,
            "duration_unit": "weeks",
            "price": 1200.0,
            "active": True,
            "created_at": now,
            "updated_at": now,
        },
    ]


def build_seed_booking(
    *,
    booking_id: str,
    program: Dict[str, Any],
    start_week: str,
    owner_name: str,
    owner_email: str,
    dog_name: str,
    breed: str,
    status_value: str,
    payment_status: str,
    vaccination_status_doc: str,
    eligibility_status: str,
    source: str,
    created_at: str,
    locale: str,
    intake_date: Optional[str] = None,
    delivery_date: Optional[str] = None,
    internal_notes: str = "",
    allergies: str = "",
    behavior_goals: str = "Socialización y obediencia.",
) -> Dict[str, Any]:
    span_weeks = get_program_span_weeks(program)
    week_starts = build_week_starts(start_week, span_weeks)
    reservation_expires_at = None
    if status_value == "Pending Review":
        reservation_expires_at = (parse_iso(created_at) + timedelta(hours=24)).isoformat()

    return {
        "id": booking_id,
        "source": source,
        "locale": locale,
        "program_id": program["id"],
        "program_snapshot": sanitize_program(program),
        "program_name_es": program["name_es"],
        "program_name_en": program["name_en"],
        "program_price": program["price"],
        "duration_value": program["duration_value"],
        "duration_unit": program["duration_unit"],
        "span_weeks": span_weeks,
        "start_week": start_week,
        "week_starts": week_starts,
        "status": status_value,
        "owner": {
            "full_name": owner_name,
            "email": owner_email,
            "phone": "+34 600 000 000",
            "address": "Madrid, España",
        },
        "dog": {
            "name": dog_name,
            "breed": breed,
            "age": "3 años",
            "sex": "Male",
            "weight": "18 kg",
            "date_of_birth": "2023-02-01",
            "vaccination_status": "Up to date",
            "allergies": allergies,
            "behavior_goals": behavior_goals,
            "current_medication": "",
            "additional_notes": "Caso de demostración MVP.",
        },
        "payment_proof": None,
        "vaccination_certificate": None,
        "payment_status": payment_status,
        "vaccination_certificate_status": vaccination_status_doc,
        "eligibility_status": eligibility_status,
        "rejection_reason": "",
        "internal_notes": internal_notes,
        "intake_date": intake_date,
        "delivery_date": delivery_date,
        "reservation_expires_at": reservation_expires_at,
        "created_at": created_at,
        "updated_at": created_at,
        "approved_at": created_at if status_value in {"Approved", "Scheduled", "In Training", "Delivered"} else None,
    }


async def ensure_demo_admin() -> None:
    existing = await db.admins.find_one({"email": DEMO_ADMIN_EMAIL}, {"_id": 0})
    if existing:
        return
    admin_doc = {
        "id": str(uuid.uuid4()),
        "name": DEMO_ADMIN_NAME,
        "email": DEMO_ADMIN_EMAIL,
        "password_hash": pwd_context.hash(DEMO_ADMIN_PASSWORD),
        "created_at": iso_now(),
    }
    await db.admins.insert_one(admin_doc.copy())


async def ensure_seed_data() -> None:
    defaults = default_settings()
    current_settings = await db.settings.find_one({"id": "business-config"}, {"_id": 0})
    if not current_settings:
        await db.settings.insert_one(defaults.copy())
    else:
        updates: Dict[str, Any] = {}
        if str(current_settings.get("admin_notification_email", "")).endswith(".local"):
            updates["admin_notification_email"] = defaults["admin_notification_email"]
        if current_settings.get("currency") not in CURRENCY_OPTIONS:
            updates["currency"] = defaults["currency"]

        landing_content = current_settings.get("landing_content")
        if not isinstance(landing_content, dict):
            updates["landing_content"] = defaults["landing_content"]
        else:
            merged_landing = {**defaults["landing_content"], **landing_content}
            existing_cards = landing_content.get("feature_cards") if isinstance(landing_content.get("feature_cards"), list) else []
            merged_cards: List[Dict[str, Any]] = []
            for index, default_card in enumerate(defaults["landing_content"]["feature_cards"]):
                current_card = existing_cards[index] if index < len(existing_cards) and isinstance(existing_cards[index], dict) else {}
                merged_cards.append({**default_card, **current_card})
            merged_landing["feature_cards"] = merged_cards
            if merged_landing != landing_content:
                updates["landing_content"] = merged_landing

        if updates:
            updates["updated_at"] = iso_now()
            await db.settings.update_one({"id": "business-config"}, {"$set": updates})

    for program in default_programs():
        existing = await db.programs.find_one({"id": program["id"]}, {"_id": 0})
        if not existing:
            await db.programs.insert_one(program.copy())

    if not await db.week_capacities.find_one({"week_start": "2026-04-06"}, {"_id": 0}):
        await db.week_capacities.insert_one({"id": str(uuid.uuid4()), "week_start": "2026-04-06", "capacity": 5, "updated_at": iso_now()})

    await ensure_demo_admin()

    booking_count = await db.bookings.count_documents({})
    if not booking_count:
        programs = {program["id"]: program for program in await db.programs.find({}, {"_id": 0}).to_list(50)}
        seed_bookings = [
        build_seed_booking(
            booking_id="seed-1",
            program=programs["basic-6-day"],
            start_week="2026-03-30",
            owner_name="Lucía Ortega",
            owner_email="lucia@example.com",
            dog_name="Rocco",
            breed="Border Collie",
            status_value="Approved",
            payment_status="Verified",
            vaccination_status_doc="Verified",
            eligibility_status="Eligible",
            source="public",
            created_at="2026-03-20T10:00:00+00:00",
            locale="es",
            intake_date="2026-03-30",
            internal_notes="Cliente aprobado para la semana de apertura.",
        ),
        build_seed_booking(
            booking_id="seed-2",
            program=programs["basic-6-day"],
            start_week="2026-03-30",
            owner_name="Diego Martín",
            owner_email="diego@example.com",
            dog_name="Nina",
            breed="Labrador",
            status_value="Pending Review",
            payment_status="Pending Review",
            vaccination_status_doc="Pending Review",
            eligibility_status="Pending Review",
            source="public",
            created_at=(utc_now() - timedelta(hours=3)).isoformat(),
            locale="es",
            internal_notes="Pendiente de validación documental.",
            allergies="Sensibilidad digestiva.",
        ),
        build_seed_booking(
            booking_id="seed-3",
            program=programs["basic-6-day"],
            start_week="2026-03-30",
            owner_name="Emma Brooks",
            owner_email="emma@example.com",
            dog_name="Maple",
            breed="Golden Retriever",
            status_value="In Training",
            payment_status="Verified",
            vaccination_status_doc="Verified",
            eligibility_status="Eligible",
            source="admin",
            created_at="2026-03-18T10:00:00+00:00",
            locale="en",
            intake_date="2026-03-30",
            internal_notes="Bootcamp active.",
        ),
        build_seed_booking(
            booking_id="seed-4",
            program=programs["basic-6-day"],
            start_week="2026-03-30",
            owner_name="Carlos Vega",
            owner_email="carlos@example.com",
            dog_name="Milo",
            breed="Beagle",
            status_value="Scheduled",
            payment_status="Verified",
            vaccination_status_doc="Verified",
            eligibility_status="Eligible",
            source="admin",
            created_at="2026-03-22T10:00:00+00:00",
            locale="es",
            intake_date="2026-03-31",
            internal_notes="Cliente comprometido antes del lanzamiento.",
        ),
        build_seed_booking(
            booking_id="seed-5",
            program=programs["multi-week"],
            start_week="2026-03-30",
            owner_name="Sofía Cruz",
            owner_email="sofia@example.com",
            dog_name="Thor",
            breed="Pastor Alemán",
            status_value="Scheduled",
            payment_status="Verified",
            vaccination_status_doc="Verified",
            eligibility_status="Eligible",
            source="admin",
            created_at="2026-03-21T10:00:00+00:00",
            locale="es",
            intake_date="2026-03-30",
            internal_notes="Programa multi-semana confirmado.",
        ),
        build_seed_booking(
            booking_id="seed-6",
            program=programs["basic-6-day"],
            start_week="2026-03-30",
            owner_name="Álvaro López",
            owner_email="alvaro@example.com",
            dog_name="Luna",
            breed="Mestizo",
            status_value="Approved",
            payment_status="Verified",
            vaccination_status_doc="Verified",
            eligibility_status="Eligible",
            source="public",
            created_at="2026-03-19T10:00:00+00:00",
            locale="es",
            intake_date="2026-04-01",
        ),
        build_seed_booking(
            booking_id="seed-7",
            program=programs["basic-6-day"],
            start_week="2026-03-30",
            owner_name="Oliver Reed",
            owner_email="oliver@example.com",
            dog_name="Scout",
            breed="Australian Shepherd",
            status_value="Delivered",
            payment_status="Verified",
            vaccination_status_doc="Verified",
            eligibility_status="Eligible",
            source="admin",
            created_at="2026-03-15T10:00:00+00:00",
            locale="en",
            intake_date="2026-03-30",
            delivery_date="2026-04-05",
            internal_notes="Programa completado.",
        ),
        build_seed_booking(
            booking_id="seed-8",
            program=programs["basic-6-day"],
            start_week="2026-04-06",
            owner_name="Patricia Mora",
            owner_email="patricia@example.com",
            dog_name="Kira",
            breed="Husky",
            status_value="Approved",
            payment_status="Verified",
            vaccination_status_doc="Verified",
            eligibility_status="Eligible",
            source="public",
            created_at="2026-03-25T10:00:00+00:00",
            locale="es",
            intake_date="2026-04-06",
            allergies="Alergia cutánea leve.",
        ),
        build_seed_booking(
            booking_id="seed-9",
            program=programs["basic-6-day"],
            start_week="2026-04-06",
            owner_name="Noah Carter",
            owner_email="noah@example.com",
            dog_name="Piper",
            breed="Cockapoo",
            status_value="Pending Review",
            payment_status="Pending Review",
            vaccination_status_doc="Pending Review",
            eligibility_status="Pending Review",
            source="public",
            created_at=(utc_now() - timedelta(hours=5)).isoformat(),
            locale="en",
            internal_notes="Awaiting payment and certificate review.",
        ),
        build_seed_booking(
            booking_id="seed-10",
            program=programs["basic-6-day"],
            start_week="2026-04-06",
            owner_name="Marina Soler",
            owner_email="marina@example.com",
            dog_name="Toby",
            breed="Poodle",
            status_value="Scheduled",
            payment_status="Verified",
            vaccination_status_doc="Verified",
            eligibility_status="Eligible",
            source="admin",
            created_at="2026-03-24T10:00:00+00:00",
            locale="es",
            intake_date="2026-04-06",
        ),
        build_seed_booking(
            booking_id="seed-11",
            program=programs["basic-6-day"],
            start_week="2026-04-06",
            owner_name="Javier Rico",
            owner_email="javier@example.com",
            dog_name="Duna",
            breed="Galgo",
            status_value="Rejected",
            payment_status="Invalid",
            vaccination_status_doc="Invalid",
            eligibility_status="Ineligible",
            source="public",
            created_at="2026-03-26T10:00:00+00:00",
            locale="es",
            internal_notes="Documentación inconsistente.",
        ),
        build_seed_booking(
            booking_id="seed-12",
            program=programs["basic-6-day"],
            start_week="2026-04-06",
            owner_name="Grace Hall",
            owner_email="grace@example.com",
            dog_name="Bandit",
            breed="Cattle Dog",
            status_value="Delivered",
            payment_status="Verified",
            vaccination_status_doc="Verified",
            eligibility_status="Eligible",
            source="admin",
            created_at="2026-03-17T10:00:00+00:00",
            locale="en",
            intake_date="2026-04-06",
            delivery_date="2026-04-12",
            internal_notes="Completed with excellent results.",
        ),
        ]
        await db.bookings.insert_many([booking.copy() for booking in seed_bookings])

    if not await db.email_logs.count_documents({}):
        sample_logs = [
            {
                "id": str(uuid.uuid4()),
                "recipient": "admin@pawstraining.com",
                "subject": "Nueva reserva pendiente — Nina",
                "body": "Nueva reserva enviada por Diego Martín para Nina en la semana 2026-03-30. Estado inicial: Pending Review.",
                "audience": "admin",
                "booking_id": "seed-2",
                "locale": "es",
                "mode": "internal_log",
                "created_at": "2026-03-24T09:15:00+00:00",
            },
            {
                "id": str(uuid.uuid4()),
                "recipient": "lucia@example.com",
                "subject": "PAWS TRAINING — Reserva aprobada",
                "body": "Hola Lucía Ortega, la reserva para Rocco fue aprobada. Semana de ingreso: 2026-03-30.",
                "audience": "client",
                "booking_id": "seed-1",
                "locale": "es",
                "mode": "internal_log",
                "created_at": "2026-03-23T14:30:00+00:00",
            },
            {
                "id": str(uuid.uuid4()),
                "recipient": "patricia@example.com",
                "subject": "PAWS TRAINING — Reserva aprobada",
                "body": "Hola Patricia Mora, la reserva para Kira fue aprobada. Semana de ingreso: 2026-04-06.",
                "audience": "client",
                "booking_id": "seed-8",
                "locale": "es",
                "mode": "internal_log",
                "created_at": "2026-03-25T11:00:00+00:00",
            },
        ]
        await db.email_logs.insert_many([log.copy() for log in sample_logs])


async def expire_stale_bookings() -> int:
    now = iso_now()
    result = await db.bookings.update_many(
        {
            "status": "Pending Review",
            "reservation_expires_at": {"$lt": now},
        },
        {
            "$set": {
                "status": "Expired",
                "updated_at": now,
                "internal_notes": "Reservation automatically expired after 24 hours.",
            }
        },
    )
    return result.modified_count


async def get_active_program(program_id: str) -> Dict[str, Any]:
    program = await db.programs.find_one({"id": program_id, "active": True}, {"_id": 0})
    if not program:
        raise HTTPException(status_code=404, detail="Program not found.")
    return program


async def get_capacity_map() -> Dict[str, int]:
    entries = await db.week_capacities.find({}, {"_id": 0}).to_list(500)
    return {entry["week_start"]: int(entry["capacity"]) for entry in entries}


def classify_week(remaining: int, capacity: int) -> str:
    if remaining <= 0:
        return "full"
    if remaining <= max(2, math.ceil(capacity * 0.25)):
        return "almost_full"
    return "available"


def capacity_counts_for_week(bookings: List[Dict[str, Any]], week_start: str) -> Dict[str, int]:
    reserved = 0
    confirmed = 0
    for booking in bookings:
        if week_start not in booking.get("week_starts", []):
            continue
        if booking["status"] == "Pending Review":
            reserved += 1
        elif booking["status"] in CONFIRMED_CAPACITY_STATUSES:
            confirmed += 1
    occupied = reserved + confirmed
    return {"reserved": reserved, "confirmed": confirmed, "occupied": occupied}


def get_calendar_base_week() -> date:
    today = utc_now().date()
    if today <= OPERATIONAL_START:
        return OPERATIONAL_START
    aligned = today - timedelta(days=today.weekday())
    return aligned if aligned >= OPERATIONAL_START else OPERATIONAL_START


async def generate_weeks(count: int = 16) -> List[Dict[str, Any]]:
    await expire_stale_bookings()
    bookings = await db.bookings.find({"status": {"$in": list(ACTIVE_CAPACITY_STATUSES)}}, {"_id": 0}).to_list(1000)
    capacity_map = await get_capacity_map()
    base_week = get_calendar_base_week()
    weeks: List[Dict[str, Any]] = []
    for offset in range(count):
        week_date = base_week + timedelta(weeks=offset)
        week_start = week_date.isoformat()
        counts = capacity_counts_for_week(bookings, week_start)
        capacity = capacity_map.get(week_start, DEFAULT_WEEKLY_CAPACITY)
        remaining = max(capacity - counts["occupied"], 0)
        weeks.append(
            {
                "week_start": week_start,
                "label": f"{week_date.strftime('%d %b %Y')}",
                "capacity": capacity,
                "remaining": remaining,
                "reserved": counts["reserved"],
                "confirmed": counts["confirmed"],
                "occupied": counts["occupied"],
                "availability_label": classify_week(remaining, capacity),
            }
        )
    return weeks


async def validate_capacity_for_program(start_week: str, span_weeks: int, ignore_booking_id: Optional[str] = None) -> None:
    await expire_stale_bookings()
    affected_weeks = build_week_starts(start_week, span_weeks)
    query: Dict[str, Any] = {"status": {"$in": list(ACTIVE_CAPACITY_STATUSES)}}
    bookings = await db.bookings.find(query, {"_id": 0}).to_list(1000)
    if ignore_booking_id:
        bookings = [booking for booking in bookings if booking["id"] != ignore_booking_id]
    capacity_map = await get_capacity_map()
    for week_start in affected_weeks:
        counts = capacity_counts_for_week(bookings, week_start)
        capacity = capacity_map.get(week_start, DEFAULT_WEEKLY_CAPACITY)
        if counts["occupied"] + 1 > capacity:
            raise HTTPException(status_code=400, detail=f"Week {week_start} is full for the selected program.")


async def save_upload(upload: UploadFile, directory: Path, prefix: str) -> Dict[str, Any]:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and image files are allowed.")
    content = await upload.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    stored_name = f"{prefix}-{uuid.uuid4().hex}{suffix}"
    path = directory / stored_name
    path.write_bytes(content)
    return {
        "original_name": upload.filename,
        "stored_name": stored_name,
        "path": str(path),
        "content_type": upload.content_type,
        "size": len(content),
    }


async def queue_email(recipient: str, subject: str, body: str, *, audience: str, booking_id: str, locale: str) -> None:
    email_log = {
        "id": str(uuid.uuid4()),
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "audience": audience,
        "booking_id": booking_id,
        "locale": locale,
        "mode": "internal_log",
        "created_at": iso_now(),
    }
    await db.email_logs.insert_one(email_log.copy())


async def send_submission_emails(booking: Dict[str, Any], settings_doc: Dict[str, Any]) -> None:
    locale = booking.get("locale", "es")
    price_label = format_money(float(booking.get("program_price", 0)), settings_doc.get("currency", "USD"))
    program_name = booking["program_name_en"] if locale == "en" else booking["program_name_es"]
    if locale == "en":
        client_subject = "PAWS TRAINING — Booking received"
        client_body = (
            f"Hi {booking['owner']['full_name']},\n\n"
            f"We received your booking request for {booking['dog']['name']} in the {program_name}. "
            f"Program total: {price_label}. Your selected start week is {booking['start_week']} and the reservation is held while our team reviews your documents."
        )
    else:
        client_subject = "PAWS TRAINING — Reserva recibida"
        client_body = (
            f"Hola {booking['owner']['full_name']},\n\n"
            f"Hemos recibido tu solicitud para {booking['dog']['name']} en el programa {program_name}. "
            f"Importe del programa: {price_label}. La semana elegida es {booking['start_week']} y la plaza queda reservada mientras revisamos tus documentos."
        )

    admin_subject = f"Nueva reserva pendiente — {booking['dog']['name']}"
    admin_body = (
        f"Nueva reserva enviada por {booking['owner']['full_name']} para {booking['dog']['name']} "
        f"en la semana {booking['start_week']}. Programa: {booking['program_name_es']}. Importe: {price_label}. Estado inicial: Pending Review."
    )
    await queue_email(settings_doc["admin_notification_email"], admin_subject, admin_body, audience="admin", booking_id=booking["id"], locale="es")
    await queue_email(booking["owner"]["email"], client_subject, client_body, audience="client", booking_id=booking["id"], locale=locale)


async def send_approval_email(booking: Dict[str, Any]) -> None:
    locale = booking.get("locale", "es")
    intake_week = booking.get("intake_date") or booking["start_week"]
    settings_doc = await get_business_settings()
    price_label = format_money(float(booking.get("program_price", 0)), settings_doc.get("currency", "USD"))
    program_name = booking["program_name_en"] if locale == "en" else booking["program_name_es"]
    if locale == "en":
        subject = "PAWS TRAINING — Booking approved"
        body = f"Hi {booking['owner']['full_name']}, your booking for {booking['dog']['name']} ({program_name}) has been approved. Program total: {price_label}. Intake week: {intake_week}."
    else:
        subject = "PAWS TRAINING — Reserva aprobada"
        body = f"Hola {booking['owner']['full_name']}, la reserva para {booking['dog']['name']} ({program_name}) fue aprobada. Importe del programa: {price_label}. Semana de ingreso: {intake_week}."
    await queue_email(booking["owner"]["email"], subject, body, audience="client", booking_id=booking["id"], locale=locale)


async def send_rejection_email(booking: Dict[str, Any]) -> None:
    locale = booking.get("locale", "es")
    reason = booking.get("rejection_reason") or ""
    settings_doc = await get_business_settings()
    price_label = format_money(float(booking.get("program_price", 0)), settings_doc.get("currency", "USD"))
    program_name = booking["program_name_en"] if locale == "en" else booking["program_name_es"]
    if locale == "en":
        subject = "PAWS TRAINING — Booking update"
        body = f"Hi {booking['owner']['full_name']}, we are sorry, but your booking for {booking['dog']['name']} ({program_name}, {price_label}) could not be approved. {reason}".strip()
    else:
        subject = "PAWS TRAINING — Actualización de reserva"
        body = f"Hola {booking['owner']['full_name']}, lamentablemente no pudimos aprobar la reserva para {booking['dog']['name']} ({program_name}, {price_label}). {reason}".strip()
    await queue_email(booking["owner"]["email"], subject, body, audience="client", booking_id=booking["id"], locale=locale)


async def build_dashboard_payload() -> Dict[str, Any]:
    await expire_stale_bookings()
    bookings = [sanitize_booking(item) for item in await db.bookings.find({}, {"_id": 0}).to_list(2000)]
    weeks = await generate_weeks(10)

    dog_status_breakdown: Dict[str, int] = {}
    revenue_summary: Dict[str, Dict[str, float]] = {}
    pending_payments = 0
    confirmed_payments = 0
    pending_intake = 0
    in_training = 0
    delivered = 0
    confirmed_revenue_total = 0.0
    pending_revenue_total = 0.0

    for booking in bookings:
        dog_status_breakdown[booking["status"]] = dog_status_breakdown.get(booking["status"], 0) + 1
        month_key = booking["start_week"][:7]
        revenue_summary.setdefault(month_key, {"confirmed": 0.0, "pending": 0.0})
        if booking["status"] in {"Approved", "Scheduled", "In Training", "Delivered"}:
            revenue_summary[month_key]["confirmed"] += float(booking["program_price"])
            confirmed_revenue_total += float(booking["program_price"])
        elif booking["status"] == "Pending Review":
            revenue_summary[month_key]["pending"] += float(booking["program_price"])
            pending_revenue_total += float(booking["program_price"])

        if booking["payment_status"] == "Pending Review":
            pending_payments += 1
        if booking["payment_status"] == "Verified":
            confirmed_payments += 1
        if booking["status"] in {"Approved", "Scheduled"}:
            pending_intake += 1
        if booking["status"] == "In Training":
            in_training += 1
        if booking["status"] == "Delivered":
            delivered += 1

    capacity_breakdown = {"confirmed": 0, "reserved": 0, "remaining": 0}
    nearly_full_weeks = 0
    full_weeks = 0
    for week in weeks:
        capacity_breakdown["confirmed"] += week["confirmed"]
        capacity_breakdown["reserved"] += week["reserved"]
        capacity_breakdown["remaining"] += week["remaining"]
        if week["availability_label"] == "almost_full":
            nearly_full_weeks += 1
        if week["availability_label"] == "full":
            full_weeks += 1

    email_logs = await db.email_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(6)
    return {
        "metrics": {
            "nearly_full_weeks": nearly_full_weeks,
            "full_weeks": full_weeks,
            "dogs_pending_intake": pending_intake,
            "dogs_in_training": in_training,
            "dogs_delivered": delivered,
            "pending_payments": pending_payments,
            "confirmed_payments": confirmed_payments,
            "confirmed_revenue": round(confirmed_revenue_total, 2),
            "pending_revenue": round(pending_revenue_total, 2),
        },
        "weekly_occupancy": weeks,
        "charts": {
            "capacity_breakdown": [
                {"name": "Confirmed", "value": capacity_breakdown["confirmed"]},
                {"name": "Reserved", "value": capacity_breakdown["reserved"]},
                {"name": "Remaining", "value": capacity_breakdown["remaining"]},
            ],
            "dog_status_breakdown": [{"name": key, "value": value} for key, value in dog_status_breakdown.items()],
            "revenue": [
                {"month": key, "confirmed": round(value["confirmed"], 2), "pending": round(value["pending"], 2)}
                for key, value in sorted(revenue_summary.items())
            ],
        },
        "recent_email_logs": email_logs,
    }


@app.on_event("startup")
async def startup_event() -> None:
    await ensure_seed_data()
    await expire_stale_bookings()


@app.on_event("shutdown")
async def shutdown_db_client() -> None:
    client.close()


@api_router.get("/")
async def root() -> Dict[str, str]:
    return {"message": "PAWS TRAINING API is running."}


@api_router.post("/auth/login")
async def login(payload: LoginRequest) -> Dict[str, Any]:
    admin = await db.admins.find_one({"email": payload.email}, {"_id": 0})
    if not admin or not pwd_context.verify(payload.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    token = create_access_token(admin)
    return {"token": token, "admin": {"id": admin["id"], "name": admin["name"], "email": admin["email"]}}


@api_router.get("/auth/me")
async def me(admin: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    return admin


@api_router.get("/public/config")
async def get_public_config() -> Dict[str, Any]:
    settings_doc = await get_business_settings()
    return {
        "business_name": settings_doc["business_name"],
        "slogan": settings_doc["slogan"],
        "contact_email": settings_doc["contact_email"],
        "contact_phone": settings_doc["contact_phone"],
        "contact_address": settings_doc["contact_address"],
        "primary_color": settings_doc["primary_color"],
        "accent_color": settings_doc["accent_color"],
        "surface_color": settings_doc["surface_color"],
        "service_label_es": settings_doc["service_label_es"],
        "service_label_en": settings_doc["service_label_en"],
        "booking_term_es": settings_doc["booking_term_es"],
        "booking_term_en": settings_doc["booking_term_en"],
        "currency": settings_doc.get("currency", "USD"),
        "landing_content": settings_doc.get("landing_content", default_landing_content()),
        "logo_url": settings_doc.get("logo_url") or ("/api/public/assets/logo" if settings_doc.get("logo_asset") else ""),
        "demo_admin": {"email": DEMO_ADMIN_EMAIL, "password": DEMO_ADMIN_PASSWORD},
        "operational_start": OPERATIONAL_START.isoformat(),
    }


@api_router.get("/public/assets/logo")
async def get_logo_asset() -> FileResponse:
    settings_doc = await get_business_settings()
    logo_asset = settings_doc.get("logo_asset")
    if not logo_asset or not Path(logo_asset).exists():
        raise HTTPException(status_code=404, detail="Logo not found.")
    return FileResponse(Path(logo_asset))


@api_router.get("/public/programs")
async def get_public_programs() -> List[Dict[str, Any]]:
    programs = await db.programs.find({"active": True}, {"_id": 0}).sort("created_at", 1).to_list(100)
    return [sanitize_program(program) for program in programs]


@api_router.get("/public/weeks")
async def get_public_weeks(program_id: str, count: int = 16) -> Dict[str, Any]:
    program = await get_active_program(program_id)
    weeks = await generate_weeks(count)
    return {"program_id": program_id, "span_weeks": get_program_span_weeks(program), "weeks": weeks}


@api_router.post("/public/bookings")
async def create_public_booking(
    request: Request,
    program_id: str = Form(...),
    start_week: str = Form(...),
    locale: str = Form("es"),
    owner_full_name: str = Form(...),
    owner_email: str = Form(...),
    owner_phone: str = Form(...),
    owner_address: str = Form(...),
    dog_name: str = Form(...),
    breed: str = Form(...),
    age: str = Form(""),
    sex: str = Form(...),
    weight: str = Form(...),
    date_of_birth: str = Form(...),
    vaccination_status: str = Form(...),
    allergies: str = Form(""),
    behavior_goals: str = Form(...),
    current_medication: str = Form(""),
    additional_notes: str = Form(""),
    payment_proof: UploadFile = File(...),
    vaccination_certificate: UploadFile = File(...),
) -> Dict[str, Any]:
    program = await get_active_program(program_id)
    span_weeks = get_program_span_weeks(program)
    normalized_start = parse_week_start(start_week).isoformat()
    await validate_capacity_for_program(normalized_start, span_weeks)

    booking_id = str(uuid.uuid4())
    booking_dir = UPLOAD_DIR / booking_id
    booking_dir.mkdir(parents=True, exist_ok=True)
    payment_file = await save_upload(payment_proof, booking_dir, "payment-proof")
    certificate_file = await save_upload(vaccination_certificate, booking_dir, "vaccination-certificate")
    now = iso_now()
    booking_doc = {
        "id": booking_id,
        "source": "public",
        "locale": locale,
        "program_id": program["id"],
        "program_snapshot": sanitize_program(program),
        "program_name_es": program["name_es"],
        "program_name_en": program["name_en"],
        "program_price": float(program["price"]),
        "duration_value": int(program["duration_value"]),
        "duration_unit": program["duration_unit"],
        "span_weeks": span_weeks,
        "start_week": normalized_start,
        "week_starts": build_week_starts(normalized_start, span_weeks),
        "status": "Pending Review",
        "owner": {
            "full_name": owner_full_name,
            "email": owner_email,
            "phone": owner_phone,
            "address": owner_address,
        },
        "dog": {
            "name": dog_name,
            "breed": breed,
            "age": age,
            "sex": sex,
            "weight": weight,
            "date_of_birth": date_of_birth,
            "vaccination_status": vaccination_status,
            "allergies": allergies,
            "behavior_goals": behavior_goals,
            "current_medication": current_medication,
            "additional_notes": additional_notes,
        },
        "payment_proof": payment_file,
        "vaccination_certificate": certificate_file,
        "payment_status": "Pending Review",
        "vaccination_certificate_status": "Pending Review",
        "eligibility_status": "Pending Review",
        "rejection_reason": "",
        "internal_notes": "",
        "intake_date": None,
        "delivery_date": None,
        "reservation_expires_at": (utc_now() + timedelta(hours=24)).isoformat(),
        "created_at": now,
        "updated_at": now,
        "approved_at": None,
        "request_source": str(request.client.host) if request.client else "unknown",
    }
    await db.bookings.insert_one(booking_doc.copy())
    settings_doc = await get_business_settings()
    await send_submission_emails(booking_doc, settings_doc)
    return {
        "booking_id": booking_id,
        "status": booking_doc["status"],
        "reservation_expires_at": booking_doc["reservation_expires_at"],
        "message": "Booking request submitted successfully.",
    }


@api_router.get("/admin/dashboard")
async def get_dashboard(_: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    return await build_dashboard_payload()


@api_router.get("/admin/bookings")
async def get_admin_bookings(
    status_filter: Optional[str] = None,
    program_id: Optional[str] = None,
    week_start: Optional[str] = None,
    search: Optional[str] = None,
    _: Dict[str, Any] = Depends(get_current_admin),
) -> List[Dict[str, Any]]:
    await expire_stale_bookings()
    bookings = [sanitize_booking(item) for item in await db.bookings.find({}, {"_id": 0}).sort("created_at", -1).to_list(2000)]
    if status_filter:
        bookings = [booking for booking in bookings if booking["status"] == status_filter]
    if program_id:
        bookings = [booking for booking in bookings if booking["program_id"] == program_id]
    if week_start:
        bookings = [booking for booking in bookings if booking["start_week"] == week_start]
    if search:
        search_value = search.lower()
        bookings = [
            booking
            for booking in bookings
            if search_value in booking["owner"]["full_name"].lower() or search_value in booking["dog"]["name"].lower()
        ]
    return bookings


@api_router.get("/admin/bookings/{booking_id}")
async def get_booking_detail(booking_id: str, _: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    return sanitize_booking(booking)


@api_router.patch("/admin/bookings/{booking_id}")
async def update_booking(booking_id: str, payload: BookingUpdateRequest, _: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")

    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return sanitize_booking(booking)

    if updates.get("status") and updates["status"] not in VALID_BOOKING_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid booking status.")
    if updates.get("payment_status") and updates["payment_status"] not in DOC_STATUS_VALUES:
        raise HTTPException(status_code=400, detail="Invalid payment proof status.")
    if updates.get("vaccination_certificate_status") and updates["vaccination_certificate_status"] not in DOC_STATUS_VALUES:
        raise HTTPException(status_code=400, detail="Invalid vaccination certificate status.")
    if updates.get("eligibility_status") and updates["eligibility_status"] not in ELIGIBILITY_VALUES:
        raise HTTPException(status_code=400, detail="Invalid eligibility status.")

    new_status = updates.get("status", booking["status"])
    payment_status = updates.get("payment_status", booking.get("payment_status"))
    vaccination_status_value = updates.get("vaccination_certificate_status", booking.get("vaccination_certificate_status"))
    eligibility_status = updates.get("eligibility_status", booking.get("eligibility_status"))

    if new_status == "Approved":
        if payment_status != "Verified" or vaccination_status_value != "Verified" or eligibility_status != "Eligible":
            raise HTTPException(status_code=400, detail="Payment, vaccination certificate, and eligibility must all be verified before approval.")
        updates["approved_at"] = booking.get("approved_at") or iso_now()
        updates["reservation_expires_at"] = None

    if new_status in {"Rejected", "Cancelled", "Expired"}:
        updates["reservation_expires_at"] = None

    if new_status == "Delivered" and not updates.get("delivery_date"):
        updates["delivery_date"] = booking.get("delivery_date") or utc_now().date().isoformat()

    updates["updated_at"] = iso_now()
    await db.bookings.update_one({"id": booking_id}, {"$set": updates})
    updated_booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})

    if booking["status"] != updated_booking["status"] and updated_booking["status"] == "Approved":
        await send_approval_email(updated_booking)
    if booking["status"] != updated_booking["status"] and updated_booking["status"] == "Rejected":
        await send_rejection_email(updated_booking)

    return sanitize_booking(updated_booking)


@api_router.post("/admin/bookings/manual")
async def create_manual_booking(payload: ManualBookingCreate, _: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    if payload.status not in VALID_BOOKING_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid manual booking status.")
    if payload.payment_status not in DOC_STATUS_VALUES or payload.vaccination_certificate_status not in DOC_STATUS_VALUES:
        raise HTTPException(status_code=400, detail="Invalid document status for manual booking.")
    if payload.eligibility_status not in ELIGIBILITY_VALUES:
        raise HTTPException(status_code=400, detail="Invalid eligibility status for manual booking.")

    program = await db.programs.find_one({"id": payload.program_id}, {"_id": 0})
    if not program:
        raise HTTPException(status_code=404, detail="Program not found.")
    span_weeks = get_program_span_weeks(program)
    normalized_start = parse_week_start(payload.start_week).isoformat()
    if payload.status in ACTIVE_CAPACITY_STATUSES:
        await validate_capacity_for_program(normalized_start, span_weeks)

    now = iso_now()
    booking_doc = {
        "id": str(uuid.uuid4()),
        "source": "admin",
        "locale": payload.locale,
        "program_id": program["id"],
        "program_snapshot": sanitize_program(program),
        "program_name_es": program["name_es"],
        "program_name_en": program["name_en"],
        "program_price": float(program["price"]),
        "duration_value": int(program["duration_value"]),
        "duration_unit": program["duration_unit"],
        "span_weeks": span_weeks,
        "start_week": normalized_start,
        "week_starts": build_week_starts(normalized_start, span_weeks),
        "status": payload.status,
        "owner": {
            "full_name": payload.owner_full_name,
            "email": str(payload.owner_email),
            "phone": payload.owner_phone,
            "address": payload.owner_address,
        },
        "dog": {
            "name": payload.dog_name,
            "breed": payload.breed,
            "age": payload.age,
            "sex": payload.sex,
            "weight": payload.weight,
            "date_of_birth": payload.date_of_birth,
            "vaccination_status": payload.vaccination_status,
            "allergies": payload.allergies,
            "behavior_goals": payload.behavior_goals,
            "current_medication": payload.current_medication,
            "additional_notes": payload.additional_notes,
        },
        "payment_proof": None,
        "vaccination_certificate": None,
        "payment_status": payload.payment_status,
        "vaccination_certificate_status": payload.vaccination_certificate_status,
        "eligibility_status": payload.eligibility_status,
        "rejection_reason": "",
        "internal_notes": payload.internal_notes or "",
        "intake_date": payload.intake_date,
        "delivery_date": payload.delivery_date,
        "reservation_expires_at": None,
        "created_at": now,
        "updated_at": now,
        "approved_at": now if payload.status in {"Approved", "Scheduled", "In Training", "Delivered"} else None,
    }
    await db.bookings.insert_one(booking_doc.copy())
    return sanitize_booking(booking_doc)


@api_router.get("/admin/programs")
async def get_admin_programs(_: Dict[str, Any] = Depends(get_current_admin)) -> List[Dict[str, Any]]:
    programs = await db.programs.find({}, {"_id": 0}).sort("created_at", 1).to_list(200)
    return [sanitize_program(program) for program in programs]


@api_router.post("/admin/programs")
async def create_program(payload: ProgramPayload, _: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    now = iso_now()
    program_doc = payload.model_dump()
    program_doc["id"] = f"program-{uuid.uuid4().hex[:8]}"
    program_doc["created_at"] = now
    program_doc["updated_at"] = now
    await db.programs.insert_one(program_doc.copy())
    return sanitize_program(program_doc)


@api_router.put("/admin/programs/{program_id}")
async def update_program(program_id: str, payload: ProgramPayload, _: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    existing = await db.programs.find_one({"id": program_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Program not found.")
    updates = payload.model_dump()
    updates["updated_at"] = iso_now()
    await db.programs.update_one({"id": program_id}, {"$set": updates})
    updated = await db.programs.find_one({"id": program_id}, {"_id": 0})
    return sanitize_program(updated)


@api_router.get("/admin/capacity")
async def get_capacity(_: Dict[str, Any] = Depends(get_current_admin), count: int = 16) -> List[Dict[str, Any]]:
    return await generate_weeks(count)


@api_router.put("/admin/capacity/{week_start}")
async def update_capacity(week_start: str, payload: CapacityUpdate, _: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    normalized = parse_week_start(week_start).isoformat()
    existing = await db.week_capacities.find_one({"week_start": normalized}, {"_id": 0})
    if existing:
        await db.week_capacities.update_one({"week_start": normalized}, {"$set": {"capacity": payload.capacity, "updated_at": iso_now()}})
    else:
        await db.week_capacities.insert_one({"id": str(uuid.uuid4()), "week_start": normalized, "capacity": payload.capacity, "updated_at": iso_now()})
    weeks = await generate_weeks(16)
    match = next((week for week in weeks if week["week_start"] == normalized), None)
    return match or {"week_start": normalized, "capacity": payload.capacity}


@api_router.get("/admin/settings")
async def get_settings(_: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    settings_doc = await get_business_settings()
    return {key: value for key, value in settings_doc.items() if key != "_id"}


@api_router.put("/admin/settings")
async def update_settings(payload: SettingsUpdate, _: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    updates = payload.model_dump(exclude_none=True)
    updates["updated_at"] = iso_now()
    await db.settings.update_one({"id": "business-config"}, {"$set": updates})
    updated = await db.settings.find_one({"id": "business-config"}, {"_id": 0})
    return updated


@api_router.post("/admin/settings/logo")
async def upload_logo(file: UploadFile = File(...), _: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, str]:
    branding_dir = UPLOAD_DIR / "branding"
    branding_dir.mkdir(parents=True, exist_ok=True)
    logo_asset = await save_upload(file, branding_dir, "brand-logo")
    await db.settings.update_one(
        {"id": "business-config"},
        {"$set": {"logo_asset": logo_asset["path"], "updated_at": iso_now()}},
    )
    return {"logo_url": "/api/public/assets/logo"}


@api_router.get("/admin/email-logs")
async def get_email_logs(_: Dict[str, Any] = Depends(get_current_admin)) -> List[Dict[str, Any]]:
    return await db.email_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)


@api_router.get("/admin/documents/{booking_id}/{document_type}")
async def get_document(booking_id: str, document_type: str, _: Dict[str, Any] = Depends(get_current_admin)) -> FileResponse:
    if document_type not in {"payment_proof", "vaccination_certificate"}:
        raise HTTPException(status_code=400, detail="Invalid document type.")
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    document = booking.get(document_type)
    if not document or not document.get("path") or not Path(document["path"]).exists():
        raise HTTPException(status_code=404, detail="Document not available.")
    return FileResponse(Path(document["path"]), filename=document.get("original_name"))


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ["CORS_ORIGINS"].split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)