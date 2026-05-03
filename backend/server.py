import asyncio
import json
import logging
import math
import os
import secrets
import smtplib
import uuid
import base64
import hashlib
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status, Query
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from starlette.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import cloudinary
import cloudinary.uploader
import httpx
import stripe

from utils.notifications import send_telegram_message
from utils.telegram_bot import handle_update as handle_telegram_update, register_webhook as register_telegram_webhook


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"],
)

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
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif"}
CURRENCY_OPTIONS = {
    "USD": {"symbol": "$", "label": "$ USD"},
    "EUR": {"symbol": "€", "label": "€ EUR"},
    "GBP": {"symbol": "£", "label": "£ GBP"},
}
bearer_scheme = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="PAWS TRAINING API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import re
    msg = str(exc)[:200]
    msg = re.sub(r'(?i)(token|password|MONGO_URL)[=:\s]*[^\s\'"]+', r'\1=***', msg)
    await send_telegram_message(f"❌ Error: {msg}")
    raise exc


@app.post("/telegram/webhook/{token}")
async def telegram_webhook(token: str, request: Request):
    if token != os.environ.get("TELEGRAM_BOT_TOKEN", ""):
        return {"ok": False}
    await handle_telegram_update(await request.json())
    return {"ok": True}


api_router = APIRouter(prefix="/api")


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


VALID_ROLES = {"superadmin", "admin", "operator"}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    role: Literal["admin", "operator"]


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: Optional[str] = Field(default=None, min_length=8)
    new_email: Optional[EmailStr] = None


class ProgramPayload(BaseModel):
    name_es: str
    name_en: str
    description_es: str
    description_en: str
    duration_value: int = Field(ge=1)
    duration_unit: Literal["days", "weeks"]
    price: float = Field(ge=0)
    deposit_type: Literal["percentage", "fixed"] = "percentage"
    deposit_value: float = Field(ge=0, default=50.0)
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
    landing_hero_image_url: Optional[str] = None
    service_label_es: Optional[str] = None
    service_label_en: Optional[str] = None
    booking_term_es: Optional[str] = None
    booking_term_en: Optional[str] = None
    primary_color: Optional[str] = None
    accent_color: Optional[str] = None
    surface_color: Optional[str] = None
    currency: Optional[Literal["USD", "EUR", "GBP"]] = None
    landing_content: Optional[Dict[str, Any]] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_tls: Optional[bool] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    stripe_enabled: Optional[bool] = None


class BookingUpdateRequest(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    final_payment_status: Optional[str] = None
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
    final_payment_status: str = "Pending Review"
    vaccination_certificate_status: str = "Verified"
    eligibility_status: str = "Eligible"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def get_fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(JWT_SECRET.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    return get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str) -> str:
    try:
        return get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise HTTPException(status_code=500, detail="Stored SMTP password could not be decrypted.") from exc


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


def compute_deposit_amounts(program_price: float, deposit_type: str, deposit_value: float) -> Dict[str, float]:
    if deposit_type == "fixed":
        deposit = min(deposit_value, program_price)
    else:
        deposit = round(program_price * min(deposit_value, 100.0) / 100.0, 2)
    return {"deposit_amount": round(deposit, 2), "balance_amount": round(program_price - deposit, 2)}


def compute_overall_payment_status(booking_doc: Dict[str, Any]) -> str:
    deposit = booking_doc.get("payment_status", "Pending Review")
    final = booking_doc.get("final_payment_status", "Pending Review")
    if deposit != "Verified":
        return "Deposit Pending"
    if final == "Verified":
        return "Paid in Full"
    if booking_doc.get("final_payment_proof"):
        return "Balance Pending"
    return "Deposit Verified"


def sanitize_booking(booking_doc: Dict[str, Any]) -> Dict[str, Any]:
    booking = {key: value for key, value in booking_doc.items() if key != "_id"}
    booking["medical_flags"] = build_medical_flags(booking)
    booking.setdefault("final_payment_proof", None)
    booking.setdefault("final_payment_status", "Pending Review")
    booking["overall_payment_status"] = compute_overall_payment_status(booking)
    snapshot = booking.get("program_snapshot") or {}
    price = float(booking.get("program_price", 0))
    dep_type = snapshot.get("deposit_type", "percentage")
    dep_val = snapshot.get("deposit_value", 100.0)
    amounts = compute_deposit_amounts(price, dep_type, dep_val)
    booking["deposit_amount"] = amounts["deposit_amount"]
    booking["balance_amount"] = amounts["balance_amount"]
    return booking


OPERATOR_FINANCIAL_FIELDS = {
    "program_price", "deposit_amount", "balance_amount",
    "overall_payment_status", "program_snapshot",
}

OPERATOR_ALLOWED_UPDATE_FIELDS = {"status"}


def sanitize_booking_for_operator(booking: Dict[str, Any]) -> Dict[str, Any]:
    result = {k: v for k, v in booking.items() if k not in OPERATOR_FINANCIAL_FIELDS}
    if "payment_status" in result:
        result["payment_status"] = "Paid" if result["payment_status"] == "Verified" else "Pending"
    if "final_payment_status" in result:
        result["final_payment_status"] = "Paid" if result["final_payment_status"] == "Verified" else "Pending"
    return result


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
                "title_es": "Notificaciones automáticas",
                "title_en": "Email notifications",
                "description_es": "Correos reales por Gmail SMTP para reservas nuevas, aprobaciones y rechazos.",
                "description_en": "Real Gmail SMTP delivery for new bookings, approvals, and rejections.",
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
        "admin_notification_email": DEMO_ADMIN_EMAIL,
        "logo_url": "",
        "logo_asset": None,
        "landing_hero_image_url": "",
        "landing_hero_image_asset": None,
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
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_tls": True,
        "smtp_username": "Pawstraningpr@gmail.com",
        "smtp_password_encrypted": None,
        "stripe_account_id": "",
        "stripe_onboarding_complete": False,
        "updated_at": iso_now(),
    }


def sanitize_settings(settings_doc: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = {key: value for key, value in settings_doc.items() if key not in {"_id", "smtp_password_encrypted"}}
    sanitized["smtp_password"] = ""
    sanitized["smtp_password_configured"] = bool(settings_doc.get("smtp_password_encrypted"))
    sanitized["smtp_password_masked"] = "••••••••" if settings_doc.get("smtp_password_encrypted") else ""
    return sanitized


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
            "deposit_type": "percentage",
            "deposit_value": 50.0,
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
            "deposit_type": "percentage",
            "deposit_value": 50.0,
            "active": True,
            "created_at": now,
            "updated_at": now,
        },
    ]




async def ensure_demo_admin() -> None:
    existing = await db.admins.find_one({"email": DEMO_ADMIN_EMAIL}, {"_id": 0})
    if existing:
        await db.admins.update_one(
            {"email": DEMO_ADMIN_EMAIL}, 
            {"$set": {"name": DEMO_ADMIN_NAME, "role": "superadmin"}}
        )
        return
    target = {
        "name": DEMO_ADMIN_NAME,
        "email": DEMO_ADMIN_EMAIL,
        "password_hash": pwd_context.hash(DEMO_ADMIN_PASSWORD),
        "role": "superadmin",
    }
    admin_doc = {
        "id": str(uuid.uuid4()),
        **target,
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
        if "landing_hero_image_url" not in current_settings:
            updates["landing_hero_image_url"] = defaults["landing_hero_image_url"]
        if "landing_hero_image_asset" not in current_settings:
            updates["landing_hero_image_asset"] = defaults["landing_hero_image_asset"]
        if not current_settings.get("smtp_host"):
            updates["smtp_host"] = defaults["smtp_host"]
        if not current_settings.get("smtp_port"):
            updates["smtp_port"] = defaults["smtp_port"]
        if "smtp_tls" not in current_settings:
            updates["smtp_tls"] = defaults["smtp_tls"]
        if not current_settings.get("smtp_username"):
            updates["smtp_username"] = defaults["smtp_username"]
        if "smtp_password_encrypted" not in current_settings:
            updates["smtp_password_encrypted"] = defaults["smtp_password_encrypted"]
        if "stripe_account_id" not in current_settings:
            updates["stripe_account_id"] = defaults["stripe_account_id"]
        if "stripe_onboarding_complete" not in current_settings:
            updates["stripe_onboarding_complete"] = defaults["stripe_onboarding_complete"]

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

    # Backfill delivery_status for old logs that lack it
    await db.email_logs.update_many(
        {"delivery_status": {"$exists": False}},
        {"$set": {"delivery_status": "logged", "delivery_error": ""}},
    )
    await db.email_logs.update_many(
        {"delivery_status": None},
        {"$set": {"delivery_status": "logged", "delivery_error": ""}},
    )

    # Backfill two-stage payment fields for bookings that lack them
    await db.bookings.update_many(
        {"final_payment_status": {"$exists": False}},
        {"$set": {"final_payment_proof": None, "final_payment_status": "Pending Review"}},
    )

    # Backfill deposit config for programs that lack it
    await db.programs.update_many(
        {"deposit_type": {"$exists": False}},
        {"$set": {"deposit_type": "percentage", "deposit_value": 50.0}},
    )

    # Backfill final_payment_token for bookings that lack it
    bookings_without_token = await db.bookings.find(
        {"final_payment_token": {"$exists": False}}, {"_id": 0, "id": 1}
    ).to_list(5000)
    for b in bookings_without_token:
        await db.bookings.update_one(
            {"id": b["id"]},
            {"$set": {"final_payment_token": secrets.token_urlsafe(32)}},
        )


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


async def save_upload(upload: UploadFile, folder: str, prefix: str) -> Dict[str, Any]:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and image files are allowed.")
    content = await upload.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")

    content_type = upload.content_type or "application/octet-stream"

    # Convert HEIC/HEIF to JPEG for browser compatibility
    if suffix in {".heic", ".heif"}:
        try:
            from io import BytesIO
            from PIL import Image
            import pillow_heif
            pillow_heif.register_heif_opener()
            img = Image.open(BytesIO(content))
            buf = BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality=90)
            content = buf.getvalue()
            suffix = ".jpg"
            content_type = "image/jpeg"
            logger.info("Converted HEIC/HEIF to JPEG for %s", upload.filename)
        except Exception:
            logger.exception("HEIC conversion failed for %s, storing original", upload.filename)

    stored_name = f"{prefix}-{uuid.uuid4().hex}"
    result = await asyncio.to_thread(
        cloudinary.uploader.upload,
        content,
        folder=f"pawstraining/{folder}",
        public_id=stored_name,
        resource_type="auto",
        use_filename=False,
        unique_filename=False,
    )
    return {
        "original_name": upload.filename,
        "stored_name": stored_name,
        "cloudinary_url": result["secure_url"],
        "content_type": content_type,
        "size": len(content),
    }


def _smtp_send(smtp_host: str, smtp_port: int, smtp_tls: bool, smtp_username: str, smtp_password: str, recipient: str, subject: str, body: str) -> None:
    """Blocking SMTP send – runs inside a thread via asyncio.to_thread."""
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp_username
    message["To"] = recipient
    message.set_content(body)

    logger.info("SMTP INIT host=%s port=%d tls=%s username=%s to=%s", smtp_host, smtp_port, smtp_tls, smtp_username, recipient)
    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            logger.info("SMTP CONNECTED host=%s port=%d", smtp_host, smtp_port)
            if smtp_tls:
                server.starttls()
                logger.info("SMTP STARTTLS OK")
            server.login(smtp_username, smtp_password)
            logger.info("SMTP AUTH OK username=%s", smtp_username)
            server.send_message(message)
            logger.info("SMTP SEND SUCCESS to=%s subject='%s'", recipient, subject)
    except smtplib.SMTPAuthenticationError as exc:
        logger.error("SMTP ERROR: authentication failed for %s — %s", smtp_username, exc)
        raise
    except smtplib.SMTPConnectError as exc:
        logger.error("SMTP ERROR: could not connect to %s:%d — %s", smtp_host, smtp_port, exc)
        raise
    except smtplib.SMTPException as exc:
        logger.error("SMTP ERROR: %s — %s", type(exc).__name__, exc)
        raise
    except OSError as exc:
        logger.error("SMTP ERROR: network/OS error — %s", exc)
        raise


async def send_email_via_smtp(settings_doc: Dict[str, Any], recipient: str, subject: str, body: str) -> None:
    env_password = os.environ.get("SMTP_PASSWORD")
    smtp_password_encrypted = settings_doc.get("smtp_password_encrypted")
    if env_password:
        password = env_password
    elif smtp_password_encrypted:
        password = decrypt_secret(smtp_password_encrypted)
    else:
        raise RuntimeError("SMTP password is not configured.")

    host = os.environ.get("SMTP_HOST") or settings_doc.get("smtp_host", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT") or settings_doc.get("smtp_port", 587))
    env_tls = os.environ.get("SMTP_TLS")
    tls = (env_tls.lower() not in ("false", "0", "no")) if env_tls else settings_doc.get("smtp_tls", True)
    username = os.environ.get("SMTP_USERNAME") or settings_doc.get("smtp_username", "")
    if not username:
        raise RuntimeError("SMTP username is not configured.")

    logger.info("SMTP send → to=%s subject='%s' host=%s port=%d", recipient, subject, host, port)
    await asyncio.to_thread(_smtp_send, host, port, tls, username, password, recipient, subject, body)
    logger.info("SMTP send OK → to=%s", recipient)


async def send_email_via_resend(recipient: str, subject: str, body: str) -> None:
    api_key = os.environ["RESEND_API_KEY"]
    logger.info("Resend send → to=%s subject='%s'", recipient, subject)
    async with httpx.AsyncClient(timeout=30) as http:
        response = await http.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "from": "PAWS TRAINING <onboarding@resend.dev>",
                "to": [recipient],
                "subject": subject,
                "text": body,
            },
        )
    if response.status_code not in (200, 201):
        logger.error("Resend error: status=%d body=%s", response.status_code, response.text)
        raise RuntimeError(f"Resend API error {response.status_code}: {response.text}")
    logger.info("Resend send OK → to=%s id=%s", recipient, response.json().get("id", ""))


async def queue_email(recipient: str, subject: str, body: str, *, audience: str, booking_id: str, locale: str) -> None:
    settings_doc = await get_business_settings()
    if os.environ.get("RESEND_API_KEY"):
        delivery_mode = "resend"
    elif os.environ.get("SMTP_PASSWORD") or os.environ.get("SMTP_USERNAME"):
        delivery_mode = "smtp"
    else:
        delivery_mode = settings_doc.get("email_mode", "internal_log")
    delivery_status = "logged"
    delivery_error = ""

    if delivery_mode == "resend":
        try:
            await send_email_via_resend(recipient, subject, body)
            delivery_status = "sent"
        except Exception as exc:  # noqa: BLE001
            logger.exception("Resend delivery failed for %s: %s", recipient, exc)
            delivery_status = "failed"
            delivery_error = str(exc)
    elif delivery_mode == "smtp":
        try:
            await send_email_via_smtp(settings_doc, recipient, subject, body)
            delivery_status = "sent"
        except Exception as exc:  # noqa: BLE001
            logger.exception("SMTP delivery failed for %s: %s", recipient, exc)
            delivery_status = "failed"
            delivery_error = str(exc)
    else:
        logger.info("Email logged (mode=%s) → to=%s subject='%s'", delivery_mode, recipient, subject)

    email_log = {
        "id": str(uuid.uuid4()),
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "audience": audience,
        "booking_id": booking_id,
        "locale": locale,
        "mode": delivery_mode,
        "delivery_status": delivery_status,
        "delivery_error": delivery_error,
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


async def send_deposit_verified_email(booking: Dict[str, Any]) -> None:
    locale = booking.get("locale", "es")
    settings_doc = await get_business_settings()
    currency = settings_doc.get("currency", "USD")
    price = float(booking.get("program_price", 0))
    snapshot = booking.get("program_snapshot") or {}
    amounts = compute_deposit_amounts(price, snapshot.get("deposit_type", "percentage"), snapshot.get("deposit_value", 100.0))
    balance_label = format_money(amounts["balance_amount"], currency)
    token = booking.get("final_payment_token", "")
    frontend_url = os.environ.get("FRONTEND_URL", "")
    if not frontend_url:
        frontend_url = settings_doc.get("site_url", settings_doc.get("frontend_url", ""))
    payment_link = f"{frontend_url}/payment/{token}" if token else ""
    program_name = booking["program_name_en"] if locale == "en" else booking["program_name_es"]

    deposit_label = format_money(amounts["deposit_amount"], currency)

    if locale == "en":
        subject = "PAWS TRAINING — Deposit verified"
        body = (
            f"Hi {booking['owner']['full_name']},\n\n"
            f"Your deposit of {deposit_label} for {booking['dog']['name']} ({program_name}) has been verified.\n\n"
            f"Remaining balance: {balance_label}.\n\n"
            f"Please upload your final payment proof using this secure link:\n{payment_link}\n\n"
            f"IMPORTANT NOTICE:\n"
            f"The deposit is non-refundable once processed. If the client cancels the reservation "
            f"or requests a date change, a new deposit will be required to secure a new training date.\n\n"
            f"Thank you for choosing PAWS TRAINING."
        )
    else:
        subject = "PAWS TRAINING — Depósito verificado"
        body = (
            f"Hola {booking['owner']['full_name']},\n\n"
            f"Tu depósito de {deposit_label} para {booking['dog']['name']} ({program_name}) ha sido verificado.\n\n"
            f"Saldo pendiente: {balance_label}.\n\n"
            f"Por favor sube tu comprobante de pago final usando este enlace seguro:\n{payment_link}\n\n"
            f"AVISO IMPORTANTE:\n"
            f"El depósito no es reembolsable una vez procesado. Si el cliente cancela la reserva "
            f"o solicita un cambio de fecha, se requerirá un nuevo depósito para asegurar una nueva fecha de entrenamiento.\n\n"
            f"Gracias por confiar en PAWS TRAINING."
        )
    await queue_email(booking["owner"]["email"], subject, body, audience="client", booking_id=booking["id"], locale=locale)


async def send_final_payment_confirmed_emails(booking: Dict[str, Any], settings_doc: Dict[str, Any]) -> None:
    locale = booking.get("locale", "es")
    program_name = booking["program_name_en"] if locale == "en" else booking["program_name_es"]
    price_label = format_money(float(booking.get("program_price", 0)), settings_doc.get("currency", "USD"))
    intake_week = booking.get("intake_date") or booking.get("start_week", "")
    if locale == "en":
        client_subject = "PAWS TRAINING — Payment complete"
        client_body = (
            f"Hi {booking['owner']['full_name']},\n\n"
            f"Your final payment for {booking['dog']['name']} ({program_name}) has been confirmed.\n\n"
            f"Program: {program_name}\n"
            f"Intake week: {intake_week}\n"
            f"Total paid: {price_label}\n\n"
            f"Thank you for choosing PAWS TRAINING."
        )
    else:
        client_subject = "PAWS TRAINING — Pago completo confirmado"
        client_body = (
            f"Hola {booking['owner']['full_name']},\n\n"
            f"Tu pago final para {booking['dog']['name']} ({program_name}) ha sido confirmado.\n\n"
            f"Programa: {program_name}\n"
            f"Semana de ingreso: {intake_week}\n"
            f"Total pagado: {price_label}\n\n"
            f"Gracias por confiar en PAWS TRAINING."
        )
    admin_subject = f"Pago final recibido — {booking['owner']['full_name']}"
    admin_body = (
        f"{booking['owner']['full_name']} ha completado el pago final para {booking['dog']['name']} ({booking['program_name_es']}). "
        f"Semana de ingreso: {intake_week}. Total: {price_label}. Estado: Paid in Full."
    )
    client_email = booking["owner"]["email"]
    admin_email = settings_doc.get("admin_notification_email", "")
    logger.info("FINAL PAYMENT EMAILS QUEUED: booking_id=%s client=%s admin=%s", booking["id"], client_email, admin_email or "(none)")
    await queue_email(client_email, client_subject, client_body, audience="client", booking_id=booking["id"], locale=locale)
    if admin_email:
        await queue_email(admin_email, admin_subject, admin_body, audience="admin", booking_id=booking["id"], locale="es")
    else:
        logger.warning("FINAL PAYMENT EMAIL: no admin_notification_email configured, skipping admin email — booking_id=%s", booking["id"])


# --- Public endpoints: token-based final payment upload ---


@api_router.get("/public/booking-payment/{token}")
async def get_booking_by_payment_token(token: str) -> Dict[str, Any]:
    booking = await db.bookings.find_one({"final_payment_token": token}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found or link expired.")
    settings_doc = await get_business_settings()
    currency = settings_doc.get("currency", "USD")
    price = float(booking.get("program_price", 0))
    snapshot = booking.get("program_snapshot") or {}
    amounts = compute_deposit_amounts(price, snapshot.get("deposit_type", "percentage"), snapshot.get("deposit_value", 100.0))
    return {
        "booking_id": booking["id"],
        "owner_name": booking["owner"]["full_name"],
        "dog_name": booking["dog"]["name"],
        "program_name_es": booking["program_name_es"],
        "program_name_en": booking["program_name_en"],
        "program_price": price,
        "deposit_amount": amounts["deposit_amount"],
        "balance_amount": amounts["balance_amount"],
        "start_week": booking["start_week"],
        "status": booking["status"],
        "payment_status": booking.get("payment_status", "Pending Review"),
        "final_payment_status": booking.get("final_payment_status", "Pending Review"),
        "overall_payment_status": compute_overall_payment_status(booking),
        "final_payment_proof_uploaded": booking.get("final_payment_proof") is not None,
        "locale": booking.get("locale", "es"),
        "currency": currency,
        "business_name": settings_doc.get("business_name", "PAWS TRAINING"),
        "stripe_enabled": bool(settings_doc.get("stripe_onboarding_complete", False)),
    }


@api_router.post("/public/booking-payment/{token}/upload")
async def upload_final_payment_via_token(token: str, file: UploadFile = File(...)) -> Dict[str, Any]:
    booking = await db.bookings.find_one({"final_payment_token": token}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found or link expired.")
    if booking.get("final_payment_proof"):
        raise HTTPException(status_code=400, detail="Final payment proof has already been uploaded.")
    if booking.get("payment_status") != "Verified":
        raise HTTPException(status_code=400, detail="Deposit must be verified before uploading final payment.")
    file_info = await save_upload(file, booking["id"], "final-payment-proof")
    await db.bookings.update_one(
        {"id": booking["id"]},
        {"$set": {"final_payment_proof": file_info, "updated_at": iso_now()}},
    )
    settings_doc = await get_business_settings()
    admin_email = settings_doc.get("admin_notification_email", "")
    if admin_email:
        admin_subject = f"Pago final recibido — {booking['dog']['name']}"
        admin_body = f"{booking['owner']['full_name']} ha subido el comprobante de pago final para {booking['dog']['name']}. Programa: {booking['program_name_es']}. Revisa en el panel de administración."
        await queue_email(admin_email, admin_subject, admin_body, audience="admin", booking_id=booking["id"], locale="es")
    return {"message": "Final payment proof uploaded successfully.", "overall_payment_status": "Balance Pending"}


@api_router.post("/public/booking-payment/{token}/create-stripe-final-session")
async def create_stripe_final_session(token: str) -> Dict[str, Any]:
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe_key:
        raise HTTPException(status_code=503, detail="Stripe not configured.")

    booking = await db.bookings.find_one({"final_payment_token": token}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found or link expired.")
    if booking.get("payment_status") != "Verified":
        raise HTTPException(status_code=400, detail="Deposit must be verified before paying the balance.")
    if booking.get("final_payment_status") == "Verified":
        raise HTTPException(status_code=400, detail="Final payment already completed.")

    stripe.api_key = stripe_key
    existing_session_id = booking.get("stripe_final_session_id")
    if existing_session_id:
        try:
            existing = await asyncio.to_thread(stripe.checkout.Session.retrieve, existing_session_id)
            if existing.status == "open":
                return {"url": existing.url}
        except Exception:
            pass

    settings_doc = await get_business_settings()
    connected_account_id = settings_doc.get("stripe_account_id", "")
    if not connected_account_id:
        raise HTTPException(status_code=503, detail="Stripe Connect account not configured.")

    price = float(booking.get("program_price", 0))
    snapshot = booking.get("program_snapshot") or {}
    amounts = compute_deposit_amounts(price, snapshot.get("deposit_type", "percentage"), snapshot.get("deposit_value", 100.0))
    balance_cents = int(round(amounts["balance_amount"] * 100))
    if balance_cents <= 0:
        raise HTTPException(status_code=400, detail="No balance remaining.")

    currency = settings_doc.get("currency", "USD").lower()
    product_name = booking.get("program_name_es") or booking.get("program_name_en") or "Pago final"
    owner_email = booking.get("owner", {}).get("email") or None
    platform_fee_cents = max(1, int(round(balance_cents * 0.006)))
    booking_id = booking["id"]
    frontend_url = os.environ.get("FRONTEND_URL", "https://frontend-production-d4977.up.railway.app")

    session = await asyncio.to_thread(
        stripe.checkout.Session.create,
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": currency,
                "product_data": {"name": f"{product_name} — Saldo final"},
                "unit_amount": balance_cents,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{frontend_url}/payment/{token}?stripe_paid=true",
        cancel_url=f"{frontend_url}/payment/{token}",
        customer_email=owner_email,
        metadata={"booking_id": booking_id, "payment_type": "final"},
        payment_intent_data={
            "application_fee_amount": platform_fee_cents,
            "transfer_data": {"destination": connected_account_id},
        },
    )

    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"stripe_final_session_id": session.id, "updated_at": iso_now()}}
    )
    return {"url": session.url}


async def build_dashboard_payload() -> Dict[str, Any]:
    await expire_stale_bookings()
    bookings = [sanitize_booking(item) for item in await db.bookings.find({}, {"_id": 0}).to_list(2000)]
    weeks = await generate_weeks(10)

    dog_status_breakdown: Dict[str, int] = {}
    revenue_summary: Dict[str, Dict[str, float]] = {}
    payment_summary: Dict[str, Dict[str, float]] = {}
    pending_payments = 0
    confirmed_payments = 0
    deposits_pending = 0
    deposits_verified = 0
    balance_pending = 0
    paid_in_full = 0
    total_deposit_expected = 0.0
    total_deposit_collected = 0.0
    total_balance_expected = 0.0
    total_balance_collected = 0.0
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
        overall_ps = booking.get("overall_payment_status", "Deposit Pending")
        if overall_ps == "Deposit Pending":
            deposits_pending += 1
        elif overall_ps == "Deposit Verified":
            deposits_verified += 1
        elif overall_ps == "Balance Pending":
            balance_pending += 1
        elif overall_ps == "Paid in Full":
            paid_in_full += 1
        # Deposit/balance financial tracking
        if booking["status"] not in {"Rejected", "Cancelled", "Expired"}:
            snapshot = booking.get("program_snapshot") or {}
            price = float(booking.get("program_price", 0))
            amounts = compute_deposit_amounts(price, snapshot.get("deposit_type", "percentage"), snapshot.get("deposit_value", 100.0))
            total_deposit_expected += amounts["deposit_amount"]
            total_balance_expected += amounts["balance_amount"]
            payment_summary.setdefault(month_key, {"deposits": 0.0, "final_payments": 0.0, "outstanding": 0.0})
            if booking.get("payment_status") == "Verified":
                total_deposit_collected += amounts["deposit_amount"]
                payment_summary[month_key]["deposits"] += amounts["deposit_amount"]
            if booking.get("final_payment_status") == "Verified":
                total_balance_collected += amounts["balance_amount"]
                payment_summary[month_key]["final_payments"] += amounts["balance_amount"]
            outstanding = 0.0
            if booking.get("payment_status") != "Verified":
                outstanding += amounts["deposit_amount"]
            if booking.get("final_payment_status") != "Verified":
                outstanding += amounts["balance_amount"]
            payment_summary[month_key]["outstanding"] += outstanding
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
            "deposits_pending": deposits_pending,
            "deposits_verified": deposits_verified,
            "balance_pending": balance_pending,
            "paid_in_full": paid_in_full,
            "total_deposit_expected": round(total_deposit_expected, 2),
            "total_deposit_collected": round(total_deposit_collected, 2),
            "total_balance_expected": round(total_balance_expected, 2),
            "total_balance_collected": round(total_balance_collected, 2),
            "total_revenue_collected": round(total_deposit_collected + total_balance_collected, 2),
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
            "payment_breakdown": [
                {"month": key, "deposits": round(value["deposits"], 2), "final_payments": round(value["final_payments"], 2), "outstanding": round(value["outstanding"], 2)}
                for key, value in sorted(payment_summary.items())
            ],
        },
        "recent_email_logs": email_logs,
    }


@app.on_event("startup")
async def startup_event() -> None:
    await db.bookings.create_index("id", background=True)
    await db.bookings.create_index("status", background=True)
    await db.bookings.create_index("program_id", background=True)
    await db.bookings.create_index("reservation_expires_at", background=True)
    await db.admins.create_index("email", background=True)
    await db.programs.create_index("id", background=True)
    await ensure_seed_data()
    await expire_stale_bookings()
    await register_telegram_webhook()
    await send_telegram_message("🚀 Backend started successfully")
    await send_telegram_message("✅ Deployment completed")


@app.on_event("shutdown")
async def shutdown_db_client() -> None:
    client.close()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@api_router.get("/")
async def root() -> Dict[str, str]:
    return {"message": "PAWS TRAINING API is running."}


@api_router.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, payload: LoginRequest) -> Dict[str, Any]:
    admin = await db.admins.find_one({"email": payload.email}, {"_id": 0})
    if not admin or not pwd_context.verify(payload.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    token = create_access_token(admin)
    return {"token": token, "admin": {"id": admin["id"], "name": admin["name"], "email": admin["email"], "role": admin.get("role", "operator")}}


@api_router.get("/auth/me")
async def me(admin: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    return admin


@api_router.put("/auth/change-password")
async def change_password(payload: ChangePasswordRequest, admin: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, str]:
    if not payload.new_password and not payload.new_email:
        raise HTTPException(status_code=400, detail="Nothing to update.")
    full = await db.admins.find_one({"id": admin["id"]}, {"_id": 0})
    if not full or not pwd_context.verify(payload.current_password, full["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    updates: Dict[str, Any] = {}
    if payload.new_password:
        updates["password_hash"] = pwd_context.hash(payload.new_password)
    if payload.new_email:
        existing = await db.admins.find_one({"email": payload.new_email, "id": {"$ne": admin["id"]}}, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use.")
        updates["email"] = payload.new_email
    await db.admins.update_one({"id": admin["id"]}, {"$set": updates})
    return {"detail": "Profile updated successfully."}


def require_role(*allowed_roles: str):
    async def _check(admin: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
        if admin.get("role", "operator") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions.")
        return admin
    return _check


@api_router.get("/admin/users")
async def list_users(admin: Dict[str, Any] = Depends(require_role("superadmin", "admin"))) -> List[Dict[str, Any]]:
    role = admin.get("role", "operator")
    if role == "superadmin":
        users = await db.admins.find({}, {"_id": 0, "password_hash": 0}).to_list(500)
    else:
        users = await db.admins.find(
            {"created_by": admin["id"], "role": "operator"},
            {"_id": 0, "password_hash": 0},
        ).to_list(500)
    for u in users:
        u.setdefault("role", "operator")
    return users


@api_router.post("/admin/users")
async def create_user(
    payload: CreateUserRequest,
    admin: Dict[str, Any] = Depends(require_role("superadmin", "admin")),
) -> Dict[str, Any]:
    caller_role = admin.get("role", "operator")

    if caller_role == "admin":
        if payload.role != "operator":
            raise HTTPException(status_code=403, detail="Admins can only create operator accounts.")
        count = await db.admins.count_documents({"created_by": admin["id"], "role": "operator"})
        if count >= 3:
            raise HTTPException(status_code=400, detail="Operator limit reached (max 3).")

    if caller_role == "superadmin" and payload.role not in ("admin", "operator"):
        raise HTTPException(status_code=400, detail="Invalid role.")

    existing = await db.admins.find_one({"email": payload.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    user_doc = {
        "id": str(uuid.uuid4()),
        "name": payload.name,
        "email": payload.email,
        "password_hash": pwd_context.hash(payload.password),
        "role": payload.role,
        "created_by": admin["id"],
        "created_at": iso_now(),
    }
    await db.admins.insert_one(user_doc.copy())
    return {k: v for k, v in user_doc.items() if k not in ("_id", "password_hash")}


@api_router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: Dict[str, Any] = Depends(require_role("superadmin", "admin")),
) -> Dict[str, str]:
    caller_role = admin.get("role", "operator")
    target = await db.admins.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")

    target_role = target.get("role", "operator")

    if caller_role == "admin":
        if target_role != "operator" or target.get("created_by") != admin["id"]:
            raise HTTPException(status_code=403, detail="You can only delete operators you created.")

    if caller_role == "superadmin" and target["id"] == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account.")

    await db.admins.delete_one({"id": user_id})
    return {"detail": "User deleted."}


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
        "landing_hero_image_url": settings_doc.get("landing_hero_image_url") or ("/api/public/assets/landing-hero" if settings_doc.get("landing_hero_image_asset") else ""),
        "operational_start": OPERATIONAL_START.isoformat(),
        "stripe_enabled": bool(settings_doc.get("stripe_onboarding_complete", False)),
    }


@api_router.get("/public/assets/logo")
async def get_logo_asset():
    settings_doc = await get_business_settings()
    logo_asset = settings_doc.get("logo_asset")
    if not logo_asset or not isinstance(logo_asset, str) or not logo_asset.startswith("http"):
        raise HTTPException(status_code=404, detail="Logo not found.")
    return RedirectResponse(url=logo_asset)


@api_router.get("/public/assets/landing-hero")
async def get_landing_hero_asset():
    settings_doc = await get_business_settings()
    hero_asset = settings_doc.get("landing_hero_image_asset")
    if not hero_asset or not isinstance(hero_asset, str) or not hero_asset.startswith("http"):
        raise HTTPException(status_code=404, detail="Landing hero image not found.")
    return RedirectResponse(url=hero_asset)


@api_router.get("/public/programs")
async def get_public_programs() -> List[Dict[str, Any]]:
    programs = await db.programs.find({"active": True}, {"_id": 0}).sort("created_at", 1).to_list(100)
    return [sanitize_program(program) for program in programs]


@api_router.get("/public/weeks")
async def get_public_weeks(program_id: str, count: int = Query(16, ge=1, le=52)) -> Dict[str, Any]:
    program = await get_active_program(program_id)
    weeks = await generate_weeks(count)
    return {"program_id": program_id, "span_weeks": get_program_span_weeks(program), "weeks": weeks}


@api_router.post("/public/bookings")
@limiter.limit("10/minute")
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
    payment_method: str = Form("manual"),
    payment_proof: Optional[UploadFile] = File(None),
    vaccination_certificate: UploadFile = File(...),
) -> Dict[str, Any]:
    if payment_method not in {"manual", "stripe"}:
        raise HTTPException(status_code=400, detail="Invalid payment method.")

    program = await get_active_program(program_id)
    span_weeks = get_program_span_weeks(program)
    normalized_start = parse_week_start(start_week).isoformat()
    await validate_capacity_for_program(normalized_start, span_weeks)

    booking_id = str(uuid.uuid4())
    final_payment_token = secrets.token_urlsafe(32)
    
    if payment_method == "manual":
        if not payment_proof:
            raise HTTPException(status_code=400, detail="Payment proof is required for manual payments.")
        payment_file = await save_upload(payment_proof, booking_id, "payment-proof")
    else:
        payment_file = None
        
    certificate_file = await save_upload(vaccination_certificate, booking_id, "vaccination-certificate")
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
        "payment_method": payment_method,
        "payment_stage": "deposit",
        "stripe_session_id": None,
        "stripe_payment_status": None,
        "payment_proof": payment_file,
        "vaccination_certificate": certificate_file,
        "payment_status": "Pending Review",
        "final_payment_proof": None,
        "final_payment_status": "Pending Review",
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
        "final_payment_token": final_payment_token,
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


@api_router.post("/public/bookings/{booking_id}/create-stripe-session")
async def create_stripe_checkout_session(booking_id: str) -> Dict[str, Any]:
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe_key:
        raise HTTPException(status_code=503, detail="Stripe not configured.")

    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    if booking.get("payment_method") != "stripe":
        raise HTTPException(status_code=400, detail="Booking does not use Stripe.")

    stripe.api_key = stripe_key
    existing_session_id = booking.get("stripe_session_id")
    if existing_session_id:
        try:
            existing = await asyncio.to_thread(stripe.checkout.Session.retrieve, existing_session_id)
            if existing.status == "open":
                return {"url": existing.url}
        except Exception:
            pass

    program_snapshot = booking.get("program_snapshot", {})
    price = float(booking.get("program_price", 0))
    dep_type = program_snapshot.get("deposit_type", "percentage")
    dep_val = float(program_snapshot.get("deposit_value", 100.0))
    amounts = compute_deposit_amounts(price, dep_type, dep_val)
    deposit_cents = int(round(amounts["deposit_amount"] * 100))
    if deposit_cents <= 0:
        raise HTTPException(status_code=400, detail="Invalid deposit amount.")

    settings_doc = await get_business_settings()
    connected_account_id = settings_doc.get("stripe_account_id", "")
    if not connected_account_id:
        raise HTTPException(status_code=503, detail="Stripe Connect account not configured.")

    currency = settings_doc.get("currency", "USD").lower()
    product_name = booking.get("program_name_es") or booking.get("program_name_en") or "Depósito"
    owner_email = booking.get("owner", {}).get("email") or None

    # 0.6% platform fee; connected account receives the remainder automatically
    platform_fee_cents = max(1, int(round(deposit_cents * 0.006)))

    session = await asyncio.to_thread(
        stripe.checkout.Session.create,
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": currency,
                "product_data": {"name": product_name},
                "unit_amount": deposit_cents,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"https://frontend-production-d4977.up.railway.app/book?stripe_success=true&booking_id={booking_id}",
        cancel_url="https://frontend-production-d4977.up.railway.app/book?stripe_cancel=true",
        customer_email=owner_email,
        metadata={"booking_id": booking_id},
        payment_intent_data={
            "application_fee_amount": platform_fee_cents,
            "transfer_data": {"destination": connected_account_id},
        },
    )

    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"stripe_session_id": session.id, "updated_at": iso_now()}}
    )
    return {"url": session.url}


@api_router.get("/admin/dashboard")
async def get_dashboard(_: Dict[str, Any] = Depends(require_role("superadmin", "admin"))) -> Dict[str, Any]:
    return await build_dashboard_payload()


@api_router.get("/admin/bookings")
async def get_admin_bookings(
    status_filter: Optional[str] = None,
    program_id: Optional[str] = None,
    week_start: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = Query(default=20, ge=1, le=100),
    admin: Dict[str, Any] = Depends(get_current_admin),
) -> Dict[str, Any]:
    await expire_stale_bookings()
    
    query: Dict[str, Any] = {}
    if status_filter:
        query["status"] = status_filter
    if program_id:
        query["program_id"] = program_id
    if week_start:
        query["start_week"] = week_start
    if search:
        query["$or"] = [
            {"owner.full_name": {"$regex": search, "$options": "i"}},
            {"dog.name": {"$regex": search, "$options": "i"}}
        ]
        
    total = await db.bookings.count_documents(query)
    
    skip = (page - 1) * limit
    cursor = db.bookings.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    
    raw_bookings = await cursor.to_list(length=limit)
    bookings = [sanitize_booking(b) for b in raw_bookings]
    
    if admin.get("role", "operator") == "operator":
        bookings = [sanitize_booking_for_operator(b) for b in bookings]
        
    return {
        "bookings": bookings,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": math.ceil(total / limit) if limit > 0 else 0
    }


@api_router.get("/admin/bookings/{booking_id}")
async def get_booking_detail(booking_id: str, admin: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    result = sanitize_booking(booking)
    if admin.get("role", "operator") == "operator":
        result = sanitize_booking_for_operator(result)
    return result


@api_router.patch("/admin/bookings/{booking_id}")
async def update_booking(booking_id: str, payload: BookingUpdateRequest, admin: Dict[str, Any] = Depends(get_current_admin)) -> Dict[str, Any]:
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")

    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return sanitize_booking(booking)

    caller_role = admin.get("role", "operator")
    if caller_role == "operator":
        forbidden = set(updates.keys()) - OPERATOR_ALLOWED_UPDATE_FIELDS
        if forbidden:
            raise HTTPException(status_code=403, detail=f"Operators can only update: {', '.join(OPERATOR_ALLOWED_UPDATE_FIELDS)}.")

    if updates.get("status") and updates["status"] not in VALID_BOOKING_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid booking status.")
    if updates.get("payment_status") and updates["payment_status"] not in DOC_STATUS_VALUES:
        raise HTTPException(status_code=400, detail="Invalid payment proof status.")
    if updates.get("final_payment_status") and updates["final_payment_status"] not in DOC_STATUS_VALUES:
        raise HTTPException(status_code=400, detail="Invalid final payment status.")
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

    old_deposit = booking.get("payment_status", "Pending Review")
    new_deposit = updated_booking.get("payment_status", "Pending Review")
    if old_deposit != "Verified" and new_deposit == "Verified":
        await send_deposit_verified_email(updated_booking)

    return sanitize_booking(updated_booking)


@api_router.post("/admin/bookings/manual")
async def create_manual_booking(payload: ManualBookingCreate, _: Dict[str, Any] = Depends(require_role("superadmin", "admin"))) -> Dict[str, Any]:
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
        "final_payment_proof": None,
        "final_payment_status": payload.final_payment_status,
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
        "final_payment_token": secrets.token_urlsafe(32),
    }
    await db.bookings.insert_one(booking_doc.copy())
    return sanitize_booking(booking_doc)


@api_router.get("/admin/programs")
async def get_admin_programs(_: Dict[str, Any] = Depends(get_current_admin)) -> List[Dict[str, Any]]:
    programs = await db.programs.find({}, {"_id": 0}).sort("created_at", 1).to_list(200)
    return [sanitize_program(program) for program in programs]


@api_router.post("/admin/programs")
async def create_program(payload: ProgramPayload, _: Dict[str, Any] = Depends(require_role("superadmin"))) -> Dict[str, Any]:
    now = iso_now()
    program_doc = payload.model_dump()
    program_doc["id"] = f"program-{uuid.uuid4().hex[:8]}"
    program_doc["created_at"] = now
    program_doc["updated_at"] = now
    await db.programs.insert_one(program_doc.copy())
    return sanitize_program(program_doc)


@api_router.put("/admin/programs/{program_id}")
async def update_program(program_id: str, payload: ProgramPayload, _: Dict[str, Any] = Depends(require_role("superadmin"))) -> Dict[str, Any]:
    existing = await db.programs.find_one({"id": program_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Program not found.")
    updates = payload.model_dump()
    updates["updated_at"] = iso_now()
    await db.programs.update_one({"id": program_id}, {"$set": updates})
    updated = await db.programs.find_one({"id": program_id}, {"_id": 0})
    return sanitize_program(updated)


@api_router.get("/admin/capacity")
async def get_capacity(_: Dict[str, Any] = Depends(get_current_admin), count: int = Query(16, ge=1, le=52)) -> List[Dict[str, Any]]:
    return await generate_weeks(count)


@api_router.put("/admin/capacity/{week_start}")
async def update_capacity(week_start: str, payload: CapacityUpdate, _: Dict[str, Any] = Depends(require_role("superadmin"))) -> Dict[str, Any]:
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
async def get_settings(_: Dict[str, Any] = Depends(require_role("superadmin"))) -> Dict[str, Any]:
    settings_doc = await get_business_settings()
    return sanitize_settings(settings_doc)


@api_router.put("/admin/settings")
async def update_settings(payload: SettingsUpdate, _: Dict[str, Any] = Depends(require_role("superadmin"))) -> Dict[str, Any]:
    updates = payload.model_dump(exclude_none=True)
    if "stripe_enabled" in updates:
        updates["stripe_onboarding_complete"] = updates.pop("stripe_enabled")
    smtp_password = updates.pop("smtp_password", None)
    if smtp_password and smtp_password.strip():
        updates["smtp_password_encrypted"] = encrypt_secret(smtp_password.strip())
        updates["email_mode"] = "smtp"
    elif "email_mode" not in updates:
        current_settings = await get_business_settings()
        if current_settings.get("smtp_password_encrypted"):
            updates["email_mode"] = "smtp"

    updates["updated_at"] = iso_now()
    await db.settings.update_one({"id": "business-config"}, {"$set": updates})
    updated = await db.settings.find_one({"id": "business-config"}, {"_id": 0})
    return sanitize_settings(updated)


@api_router.post("/admin/settings/logo")
async def upload_logo(file: UploadFile = File(...), _: Dict[str, Any] = Depends(require_role("superadmin"))) -> Dict[str, str]:
    logo_asset = await save_upload(file, "branding", "brand-logo")
    await db.settings.update_one(
        {"id": "business-config"},
        {"$set": {"logo_asset": logo_asset["cloudinary_url"], "updated_at": iso_now()}},
    )
    return {"logo_url": "/api/public/assets/logo"}


@api_router.post("/admin/settings/landing-hero-image")
async def upload_landing_hero_image(file: UploadFile = File(...), _: Dict[str, Any] = Depends(require_role("superadmin"))) -> Dict[str, str]:
    hero_asset = await save_upload(file, "branding", "landing-hero")
    await db.settings.update_one(
        {"id": "business-config"},
        {"$set": {"landing_hero_image_asset": hero_asset["cloudinary_url"], "updated_at": iso_now()}},
    )
    return {"landing_hero_image_url": "/api/public/assets/landing-hero"}


@api_router.get("/admin/email-logs")
async def get_email_logs(_: Dict[str, Any] = Depends(require_role("superadmin", "admin"))) -> List[Dict[str, Any]]:
    return await db.email_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)


class TestEmailRequest(BaseModel):
    recipient: str


@api_router.post("/admin/settings/test-email")
async def test_email_send(payload: TestEmailRequest, _: Dict[str, Any] = Depends(require_role("superadmin"))) -> Dict[str, Any]:
    settings_doc = await get_business_settings()
    resend_key = os.environ.get("RESEND_API_KEY")
    env_password = os.environ.get("SMTP_PASSWORD")
    smtp_password_encrypted = settings_doc.get("smtp_password_encrypted")
    diag = {
        "resend_configured": bool(resend_key),
        "email_mode_in_db": settings_doc.get("email_mode", "internal_log"),
        "smtp_host": settings_doc.get("smtp_host", "smtp.gmail.com"),
        "smtp_port": settings_doc.get("smtp_port", 587),
        "smtp_tls": settings_doc.get("smtp_tls", True),
        "smtp_username": settings_doc.get("smtp_username", ""),
        "smtp_password_in_db": bool(smtp_password_encrypted),
        "smtp_password_in_env": bool(env_password),
    }
    try:
        if resend_key:
            await send_email_via_resend(
                payload.recipient,
                "PAWS TRAINING — Test / Prueba",
                "This is a test email from PAWS TRAINING. Resend is working.\n\nEste es un email de prueba de PAWS TRAINING. Resend funciona correctamente.",
            )
            diag["delivery_method"] = "resend"
        else:
            await send_email_via_smtp(
                settings_doc,
                payload.recipient,
                "PAWS TRAINING — Test / Prueba",
                "This is a test email from PAWS TRAINING. SMTP is working.\n\nEste es un email de prueba de PAWS TRAINING. El SMTP funciona correctamente.",
            )
            diag["delivery_method"] = "smtp"
        return {"success": True, "diagnostic": diag}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Test email failed → %s", exc)
        return {"success": False, "error": str(exc), "error_type": type(exc).__name__, "diagnostic": diag}


@api_router.get("/admin/documents/{booking_id}/{document_type}")
async def get_document(booking_id: str, document_type: str, _: Dict[str, Any] = Depends(get_current_admin)):
    if document_type not in {"payment_proof", "vaccination_certificate", "final_payment_proof"}:
        raise HTTPException(status_code=400, detail="Invalid document type.")
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    document = booking.get(document_type)
    if not document:
        raise HTTPException(status_code=404, detail="Document not available.")
    cloudinary_url = document.get("cloudinary_url")
    if not cloudinary_url:
        raise HTTPException(status_code=404, detail="Document not available.")
    return RedirectResponse(url=cloudinary_url)


@api_router.get("/test/stripe-connect-link")
async def test_stripe_connect(request: Request):
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173")

    settings_doc = await get_business_settings()
    account_id = settings_doc.get("stripe_account_id")

    if not account_id:
        account = await asyncio.to_thread(stripe.Account.create, type="express")
        account_id = account.id
        await db.settings.update_one(
            {"id": "business-config"},
            {"$set": {"stripe_account_id": account_id}}
        )

    account_link = await asyncio.to_thread(
        stripe.AccountLink.create,
        account=account_id,
        refresh_url=f"{frontend_url}/",
        return_url=f"{frontend_url}/",
        type="account_onboarding"
    )

    return {"url": account_link.url}


@api_router.post("/admin/bookings/{booking_id}/final-payment-proof")
async def upload_final_payment_proof(booking_id: str, file: UploadFile = File(...), _: Dict[str, Any] = Depends(require_role("superadmin", "admin"))) -> Dict[str, Any]:
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    file_info = await save_upload(file, booking_id, "final-payment-proof")
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"final_payment_proof": file_info, "updated_at": iso_now()}},
    )
    updated = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    return sanitize_booking(updated)


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

    if webhook_secret:
        try:
            event = stripe.Webhook.construct_event(payload, sig, webhook_secret)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid webhook signature.")
    else:
        try:
            event = json.loads(payload)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid payload.")

    event_type = event.get("type")
    logger.info("STRIPE WEBHOOK RECEIVED: type=%s", event_type)

    if event_type == "checkout.session.completed":
        session_data = event["data"]["object"]
        metadata = session_data.get("metadata") or {}
        booking_id = metadata.get("booking_id")
        payment_type = metadata.get("payment_type", "deposit")

        logger.info("STRIPE WEBHOOK checkout.session.completed: booking_id=%s payment_type=%s", booking_id, payment_type)

        if booking_id:
            if payment_type == "final":
                logger.info("FINAL PAYMENT WEBHOOK RECEIVED: booking_id=%s", booking_id)
                booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})

                if not booking:
                    logger.error("FINAL PAYMENT WEBHOOK: booking not found — booking_id=%s", booking_id)
                elif booking.get("final_payment_status") == "Verified":
                    logger.info("FINAL PAYMENT WEBHOOK: already verified, skipping (idempotent) — booking_id=%s", booking_id)
                else:
                    logger.info("FINAL PAYMENT BOOKING FOUND: booking_id=%s owner=%s", booking_id, booking.get("owner", {}).get("full_name", "?"))
                    settings_doc = await get_business_settings()
                    await db.bookings.update_one(
                        {"id": booking_id},
                        {"$set": {
                            "final_payment_status": "Verified",
                            "payment_status": "Paid in Full",
                            "stripe_final_payment_status": "paid",
                            "updated_at": iso_now(),
                        }}
                    )
                    updated_booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
                    if not updated_booking:
                        logger.error("FINAL PAYMENT WEBHOOK: booking disappeared after update — booking_id=%s", booking_id)
                    else:
                        try:
                            await send_final_payment_confirmed_emails(updated_booking, settings_doc)
                            logger.info("FINAL PAYMENT EMAILS QUEUED: booking_id=%s", booking_id)
                        except Exception as exc:  # noqa: BLE001
                            logger.exception("FINAL PAYMENT EMAIL ERROR: booking_id=%s error=%s", booking_id, exc)
            else:
                await db.bookings.update_one(
                    {"id": booking_id},
                    {"$set": {
                        "stripe_payment_status": "paid",
                        "payment_status": "Pending Review",
                        "updated_at": iso_now(),
                    }}
                )

    return {"ok": True}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ["CORS_ORIGINS"].split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)