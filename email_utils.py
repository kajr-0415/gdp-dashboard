"""
PAN-MED — Email Delivery
=========================
Sends the diagnostic report as a real email (not a mailto: link) with the
generated PDF attached and a branded HTML body.

CONFIGURATION
-------------
Set these via Streamlit secrets (.streamlit/secrets.toml) OR environment
variables — secrets.toml takes priority when running on Streamlit Cloud.

    [smtp]
    host = "smtp.gmail.com"
    port = 587
    username = "your-address@gmail.com"
    password = "your-16-char-app-password"   # NOT your normal password
    sender_name = "PAN-MED"

Environment variable fallback:
    SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_SENDER_NAME

Gmail note: you must create an "App Password" (Google Account → Security →
2-Step Verification → App Passwords) — a normal Gmail password will be
rejected by smtplib. Any standard SMTP provider works the same way
(SendGrid, Mailgun, Outlook, your institution's mail server, etc).
"""

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


class EmailConfigError(Exception):
    pass


def _get_smtp_config():
    """Reads SMTP config from Streamlit secrets first, then env vars."""
    cfg = {}
    try:
        import streamlit as st
        if "smtp" in st.secrets:
            cfg = dict(st.secrets["smtp"])
    except Exception:
        pass

    cfg.setdefault("host", os.environ.get("SMTP_HOST"))
    cfg.setdefault("port", os.environ.get("SMTP_PORT", 587))
    cfg.setdefault("username", os.environ.get("SMTP_USERNAME"))
    cfg.setdefault("password", os.environ.get("SMTP_PASSWORD"))
    cfg.setdefault("sender_name", os.environ.get("SMTP_SENDER_NAME", "PAN-MED"))

    if not cfg.get("host") or not cfg.get("username") or not cfg.get("password"):
        raise EmailConfigError(
            "SMTP is not configured yet. Add [smtp] credentials to "
            ".streamlit/secrets.toml (or SMTP_HOST / SMTP_USERNAME / "
            "SMTP_PASSWORD environment variables) to enable sending real "
            "emails. See the docstring in email_utils.py for the exact format."
        )
    cfg["port"] = int(cfg["port"])
    return cfg


def build_html_email(diagnosis_name, diagnosis_code, confidence, risk_label,
                      risk_tier, category, description, actions):
    """Branded HTML email body matching the site's dark-purple identity."""
    tier_colors = {
        "red":    "#ff4d4d",
        "orange": "#ffb347",
        "yellow": "#ffd166",
        "green":  "#06d6a0",
    }
    accent = tier_colors.get(risk_tier, "#ffd166")
    actions_html = "".join(
        f'<li style="margin-bottom:6px;color:#e6d9ff;font-size:13px;">{a}</li>'
        for a in actions
    )
    return f"""
    <div style="background:#0f0028;padding:32px 16px;font-family:Arial,Helvetica,sans-serif;">
      <div style="max-width:560px;margin:0 auto;background:#150a35;border:1px solid #3d1f7a;border-radius:16px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#4400bb,#9900ff);padding:22px 28px;">
          <div style="color:#fff;font-size:18px;font-weight:800;">✕ PAN<span style="color:#e9c8ff;">MED</span></div>
          <div style="color:rgba(255,255,255,0.85);font-size:12px;margin-top:4px;">AI-Assisted Dermatological Screening Report</div>
        </div>
        <div style="padding:26px 28px;">
          <div style="color:#c77dff;font-size:11px;font-weight:700;letter-spacing:1px;margin-bottom:6px;">PRIMARY FINDING</div>
          <div style="color:#fff;font-size:22px;font-weight:800;margin-bottom:4px;">{diagnosis_name}</div>
          <div style="color:#8a6bb0;font-size:11px;font-family:monospace;margin-bottom:14px;">Code: {diagnosis_code.upper()}</div>
          <span style="display:inline-block;background:{accent}22;color:{accent};border:1px solid {accent}66;border-radius:20px;padding:5px 14px;font-size:11px;font-weight:700;letter-spacing:.5px;">{risk_label}</span>
          <div style="margin:18px 0 6px;color:#d7bfff;font-size:12px;">Confidence Score</div>
          <div style="background:#2a1660;border-radius:8px;height:10px;overflow:hidden;">
            <div style="background:linear-gradient(90deg,#4400bb,#cc00ff);height:100%;width:{confidence:.1f}%;"></div>
          </div>
          <div style="text-align:right;color:#fff;font-size:12px;margin-top:4px;font-weight:700;">{confidence:.1f}%</div>

          <div style="margin-top:24px;padding:16px;background:#1c0f42;border-left:3px solid {accent};border-radius:10px;">
            <div style="color:{accent};font-size:12px;font-weight:700;margin-bottom:8px;">{category}</div>
            <div style="color:#d7bfff;font-size:12.5px;line-height:1.6;margin-bottom:12px;">{description}</div>
            <div style="color:#c77dff;font-size:10.5px;font-weight:700;letter-spacing:.5px;margin-bottom:6px;">RECOMMENDED ACTIONS</div>
            <ul style="margin:0;padding-left:18px;">{actions_html}</ul>
          </div>

          <div style="margin-top:20px;padding:12px 14px;background:#2b1a06;border:1px solid #8a5a1a;border-radius:10px;color:#ffcf8f;font-size:10.5px;line-height:1.6;">
            <strong>Medical Disclaimer:</strong> PAN-MED is an AI-assisted screening tool and does not replace professional medical diagnosis. Always consult a licensed dermatologist for accurate evaluation and treatment.
          </div>

          <div style="margin-top:20px;color:#8a6bb0;font-size:11px;">The full report is attached as a PDF.</div>
        </div>
      </div>
    </div>
    """


def send_report_email(to_email, diagnosis_name, diagnosis_code, confidence,
                       risk_label, risk_tier, category, description, actions,
                       pdf_bytes, pdf_filename="PANMED_report.pdf"):
    """
    Sends the diagnostic report to `to_email` via SMTP with the PDF attached.
    Raises EmailConfigError if SMTP credentials aren't set up yet, or
    smtplib exceptions on send failure — callers should catch and display
    both cases to the user.
    """
    cfg = _get_smtp_config()

    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"PAN-MED Result: {diagnosis_name}"
    msg["From"] = f'{cfg["sender_name"]} <{cfg["username"]}>'
    msg["To"] = to_email

    alt = MIMEMultipart("alternative")
    plain = (
        f"Diagnosis: {diagnosis_name} ({diagnosis_code.upper()})\n"
        f"Confidence: {confidence:.1f}%\n"
        f"Risk: {risk_label}\n\n"
        f"{description}\n\n"
        "Full report attached as PDF. Generated by PAN-MED AI."
    )
    alt.attach(MIMEText(plain, "plain"))
    alt.attach(MIMEText(
        build_html_email(diagnosis_name, diagnosis_code, confidence, risk_label,
                          risk_tier, category, description, actions),
        "html"))
    msg.attach(alt)

    part = MIMEApplication(pdf_bytes, Name=pdf_filename)
    part["Content-Disposition"] = f'attachment; filename="{pdf_filename}"'
    msg.attach(part)

    context = ssl.create_default_context()
    with smtplib.SMTP(cfg["host"], cfg["port"]) as server:
        server.starttls(context=context)
        server.login(cfg["username"], cfg["password"])
        server.sendmail(cfg["username"], [to_email], msg.as_string())
