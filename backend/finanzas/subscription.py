"""
Subscription and family group management module.

Handles user tiers (free, student, family), family group creation/management,
and permission checks based on subscription level.
"""
import secrets
from datetime import datetime
from app.finanzas.database import get_db
from app.finanzas.timezone import now as mx_now


# ─── Tier Constants ───────────────────────────────────────────────────────────

TIER_FREE = "free"
TIER_STUDENT = "student"
TIER_FAMILY = "family"

VALID_TIERS = [TIER_FREE, TIER_STUDENT, TIER_FAMILY]

# Permissions per tier
TIER_PERMISSIONS = {
    TIER_FREE: {
        "dashboard_basico": True,
        "gastos_ingresos": True,
        "cursos_gratuitos": True,
        "agente_limitado": True,
        "inversiones": False,
        "agente_ilimitado": False,
        "analisis_avanzado": False,
        "proyecciones": False,
        "soporte_prioritario": False,
    },
    TIER_STUDENT: {
        "dashboard_basico": True,
        "gastos_ingresos": True,
        "cursos_gratuitos": True,
        "agente_limitado": True,
        "inversiones": True,
        "agente_ilimitado": True,
        "analisis_avanzado": True,
        "proyecciones": True,
        "soporte_prioritario": True,
    },
    TIER_FAMILY: {
        "dashboard_basico": True,
        "gastos_ingresos": True,
        "cursos_gratuitos": True,
        "agente_limitado": True,
        "inversiones": True,
        "agente_ilimitado": True,
        "analisis_avanzado": True,
        "proyecciones": True,
        "soporte_prioritario": True,
    },
}


# ─── Subscription Functions ───────────────────────────────────────────────────

def get_user_subscription(user_id: str) -> dict:
    """Get the subscription info for a user. Returns defaults if not found."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM subscriptions WHERE user_id = ?", (user_id,)
        ).fetchone()

    if not row:
        return {
            "tier": TIER_FREE,
            "status": "active",
            "familyGroupId": None,
            "startedAt": None,
            "expiresAt": None,
        }

    return {
        "tier": row["tier"],
        "status": row["status"],
        "familyGroupId": row["family_group_id"],
        "startedAt": row["started_at"],
        "expiresAt": row["expires_at"],
    }


def set_user_subscription(user_id: str, tier: str, family_group_id: int | None = None) -> dict:
    """Create or update a user's subscription."""
    if tier not in VALID_TIERS:
        raise ValueError(f"Invalid tier: {tier}")

    now = mx_now().isoformat()

    with get_db() as conn:
        conn.execute(
            """INSERT INTO subscriptions (user_id, tier, status, family_group_id, started_at, updated_at)
               VALUES (?, ?, 'active', ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                 tier = ?, status = 'active', family_group_id = ?, updated_at = ?""",
            (user_id, tier, family_group_id, now, now,
             tier, family_group_id, now)
        )

    return get_user_subscription(user_id)


def get_user_permissions(user_id: str) -> dict:
    """Get the full permission set for a user based on their tier."""
    sub = get_user_subscription(user_id)
    tier = sub["tier"]
    permissions = TIER_PERMISSIONS.get(tier, TIER_PERMISSIONS[TIER_FREE])
    return {
        "tier": tier,
        "permissions": permissions,
    }


def has_permission(user_id: str, permission: str) -> bool:
    """Check if a user has a specific permission."""
    info = get_user_permissions(user_id)
    return info["permissions"].get(permission, False)


# ─── Family Group Functions ───────────────────────────────────────────────────

def _generate_invite_code() -> str:
    """Generate a unique 8-character invite code."""
    return secrets.token_urlsafe(6)[:8].upper()


def create_family_group(owner_id: str, name: str = "Mi familia") -> dict:
    """Create a family group. The owner must have or be upgrading to family tier."""
    now = mx_now().isoformat()
    invite_code = _generate_invite_code()

    with get_db() as conn:
        # Check if owner already has a group
        existing = conn.execute(
            "SELECT id FROM family_groups WHERE owner_id = ?", (owner_id,)
        ).fetchone()

        if existing:
            # Return existing group
            return get_family_group(owner_id)

        cursor = conn.execute(
            """INSERT INTO family_groups (owner_id, name, invite_code, max_members, created_at)
               VALUES (?, ?, ?, 4, ?)""",
            (owner_id, name, invite_code, now)
        )
        group_id = cursor.lastrowid

    # Update owner's subscription to reference the group
    set_user_subscription(owner_id, TIER_FAMILY, family_group_id=group_id)

    return get_family_group(owner_id)


def get_family_group(user_id: str) -> dict | None:
    """Get family group info. Works for both owner and members."""
    with get_db() as conn:
        # Check if user is an owner
        group = conn.execute(
            "SELECT * FROM family_groups WHERE owner_id = ?", (user_id,)
        ).fetchone()

        if not group:
            # Check if user is a member (via subscription)
            sub = conn.execute(
                "SELECT family_group_id FROM subscriptions WHERE user_id = ?", (user_id,)
            ).fetchone()
            if sub and sub["family_group_id"]:
                group = conn.execute(
                    "SELECT * FROM family_groups WHERE id = ?", (sub["family_group_id"],)
                ).fetchone()

        if not group:
            return None

        # Get all members of this group
        members = conn.execute(
            "SELECT user_id, tier FROM subscriptions WHERE family_group_id = ?",
            (group["id"],)
        ).fetchall()

    return {
        "id": group["id"],
        "ownerId": group["owner_id"],
        "name": group["name"],
        "inviteCode": group["invite_code"],
        "maxMembers": group["max_members"],
        "createdAt": group["created_at"],
        "members": [{"userId": m["user_id"], "tier": m["tier"]} for m in members],
        "memberCount": len(members),
        "isOwner": group["owner_id"] == user_id,
    }


def join_family_group(user_id: str, invite_code: str) -> dict:
    """Join a family group using an invite code."""
    with get_db() as conn:
        group = conn.execute(
            "SELECT * FROM family_groups WHERE invite_code = ?", (invite_code,)
        ).fetchone()

    if not group:
        raise ValueError("Código de invitación inválido.")

    # Check capacity
    group_info = get_family_group(group["owner_id"])
    if group_info and group_info["memberCount"] >= group["max_members"]:
        raise ValueError("El grupo familiar ya está lleno (máximo 4 personas).")

    # Check if user is already in this group
    if group_info:
        for member in group_info["members"]:
            if member["userId"] == user_id:
                raise ValueError("Ya eres miembro de este grupo familiar.")

    # Add user to the group
    set_user_subscription(user_id, TIER_FAMILY, family_group_id=group["id"])

    return get_family_group(user_id)


def leave_family_group(user_id: str) -> dict:
    """Remove a member from their family group. Owner cannot leave (must delete)."""
    with get_db() as conn:
        # Check if user is owner
        group = conn.execute(
            "SELECT id FROM family_groups WHERE owner_id = ?", (user_id,)
        ).fetchone()

        if group:
            raise ValueError("El propietario no puede salir del grupo. Debe eliminarlo.")

    # Downgrade to free tier and remove group reference
    set_user_subscription(user_id, TIER_FREE, family_group_id=None)
    return get_user_subscription(user_id)


def remove_family_member(owner_id: str, member_id: str) -> dict:
    """Owner removes a member from the family group."""
    with get_db() as conn:
        group = conn.execute(
            "SELECT id FROM family_groups WHERE owner_id = ?", (owner_id,)
        ).fetchone()

    if not group:
        raise ValueError("No tienes un grupo familiar.")

    if member_id == owner_id:
        raise ValueError("No puedes removerte a ti mismo.")

    # Verify the member is in this group
    sub = get_user_subscription(member_id)
    if sub["familyGroupId"] != group["id"]:
        raise ValueError("Este usuario no es miembro de tu grupo.")

    # Downgrade member to free
    set_user_subscription(member_id, TIER_FREE, family_group_id=None)
    return get_family_group(owner_id)


def delete_family_group(owner_id: str) -> bool:
    """Delete a family group. All members are downgraded to free tier."""
    with get_db() as conn:
        group = conn.execute(
            "SELECT id FROM family_groups WHERE owner_id = ?", (owner_id,)
        ).fetchone()

        if not group:
            raise ValueError("No tienes un grupo familiar.")

        # Downgrade all members
        conn.execute(
            """UPDATE subscriptions SET tier = 'free', family_group_id = NULL, updated_at = ?
               WHERE family_group_id = ?""",
            (mx_now().isoformat(), group["id"])
        )

        # Delete the group
        conn.execute("DELETE FROM family_groups WHERE id = ?", (group["id"],))

    return True
