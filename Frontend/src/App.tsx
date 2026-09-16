import { useState, useEffect, useCallback } from "react";
import { api } from "./api";
import type { Job, UserPreferences } from "./types";
import { COUNTRIES } from "./countries";

// ── Icons ────────────────────────────────────────────────────────────────
function IconBriefcase({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="7" width="20" height="14" rx="2" />
      <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
      <path d="M2 12h20" />
    </svg>
  );
}

function IconClock({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}

function IconGraduationCap({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
      <path d="M6 12v5c3 3 9 3 12 0v-5" />
    </svg>
  );
}

function IconTool({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
    </svg>
  );
}

function IconMapPin({ size = 14, className = "" }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
      <circle cx="12" cy="10" r="3" />
    </svg>
  );
}

function IconBookmark({ size = 16, filled = false }: { size?: number; filled?: boolean }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function IconArrowLeft({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="19" y1="12" x2="5" y2="12" />
      <polyline points="12 19 5 12 12 5" />
    </svg>
  );
}

function IconSearch({ size = 15 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}

function IconUser({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

function IconRefresh({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 4 23 10 17 10" />
      <polyline points="1 20 1 14 7 14" />
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
    </svg>
  );
}

function IconExternalLink({ size = 13 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
      <polyline points="15 3 21 3 21 9" />
      <line x1="10" y1="14" x2="21" y2="3" />
    </svg>
  );
}

function IconCheck({ size = 14 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function IconGlobe({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  );
}

function IconHotel({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  );
}

function IconMonitor({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="3" width="20" height="14" rx="2" />
      <line x1="8" y1="21" x2="16" y2="21" />
      <line x1="12" y1="17" x2="12" y2="21" />
    </svg>
  );
}

function IconBarChart({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="20" x2="12" y2="10" />
      <line x1="18" y1="20" x2="18" y2="4" />
      <line x1="6" y1="20" x2="6" y2="16" />
    </svg>
  );
}

function IconHeart({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
    </svg>
  );
}

function IconDollarSign({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="1" x2="12" y2="23" />
      <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
    </svg>
  );
}

function IconBook({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    </svg>
  );
}

function IconHardHat({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 18a1 1 0 0 0 1 1h18a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1v2z" />
      <path d="M10 10V5a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v5" />
      <path d="M4 15v-3a8 8 0 0 1 16 0v3" />
    </svg>
  );
}

function IconTruck({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <rect x="1" y="3" width="15" height="13" />
      <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
      <circle cx="5.5" cy="18.5" r="2.5" />
      <circle cx="18.5" cy="18.5" r="2.5" />
    </svg>
  );
}

function IconGrid({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" />
      <rect x="14" y="3" width="7" height="7" />
      <rect x="14" y="14" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" />
    </svg>
  );
}

// ── Shared UI ─────────────────────────────────────────────────────────────

function Skeleton({ h = 16, w = "100%", rounded = 6 }: { h?: number; w?: string | number; rounded?: number }) {
  return (
    <div
      className="skeleton"
      style={{ height: h, width: w, borderRadius: rounded }}
    />
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "48px 24px", textAlign: "center", gap: 16 }}>
      <div style={{ width: 48, height: 48, borderRadius: 12, background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", display: "flex", alignItems: "center", justifyContent: "center", color: "#f87171" }}>
        <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      <div>
        <p style={{ fontSize: 14, fontWeight: 600, color: "var(--foreground)", marginBottom: 4 }}>Unable to load</p>
        <p style={{ fontSize: 13, color: "var(--muted-foreground)", lineHeight: 1.5 }}>{message}</p>
      </div>
      <button className="btn-outline" style={{ width: "auto", padding: "10px 24px", display: "flex", alignItems: "center", gap: 8 }} onClick={onRetry}>
        <IconRefresh size={14} />
        Try again
      </button>
    </div>
  );
}

function JobCardSkeleton() {
  return (
    <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: 20 }}>
      <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
        <Skeleton h={42} w={42} rounded={21} />
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 8 }}>
          <Skeleton h={14} w="80%" />
          <Skeleton h={12} w="50%" />
        </div>
      </div>
      <Skeleton h={10} w="40%" rounded={4} />
    </div>
  );
}

// ── Logo ──────────────────────────────────────────────────────────────────
function Logo() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <div style={{ width: 32, height: 32, background: "var(--primary)", borderRadius: 9, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <IconBriefcase size={16} />
      </div>
      <span style={{ fontFamily: "'DM Serif Display', Georgia, serif", fontSize: 18, color: "var(--foreground)", letterSpacing: "-0.01em" }}>
        CareerMatch
      </span>
    </div>
  );
}

// ── Onboarding ────────────────────────────────────────────────────────────
const JOB_TYPE_OPTIONS = [
  { value: "full_time", label: "Full-time job", icon: <IconBriefcase size={22} /> },
  { value: "part_time", label: "Part-time / Flexible", icon: <IconClock size={22} /> },
  { value: "internship", label: "Internship", icon: <IconGraduationCap size={22} /> },
  { value: "freelance", label: "Freelance / Gig", icon: <IconTool size={22} /> },
];

const FIELD_OPTIONS = [
  { value: "hotel_tourism", label: "Hotel & Tourism", icon: <IconHotel size={20} /> },
  { value: "tech_it", label: "Tech & IT", icon: <IconMonitor size={20} /> },
  { value: "marketing_sales", label: "Marketing & Sales", icon: <IconBarChart size={20} /> },
  { value: "health_ngo", label: "Health & NGO", icon: <IconHeart size={20} /> },
  { value: "finance_banking", label: "Finance & Banking", icon: <IconDollarSign size={20} /> },
  { value: "education_teaching", label: "Education & Teaching", icon: <IconBook size={20} /> },
  { value: "construction_engineering", label: "Construction & Engineering", icon: <IconHardHat size={20} /> },
  { value: "logistics_supply_chain", label: "Logistics & Supply Chain", icon: <IconTruck size={20} /> },
  { value: "any", label: "Any / Show me everything", icon: <IconGrid size={20} /> },
];

// Human-readable labels for job.field values returned by the backend, so
// job cards show "Tech & IT" rather than the raw "tech_it" code.
const FIELD_LABELS: Record<string, string> = Object.fromEntries(
  FIELD_OPTIONS.map((o) => [o.value, o.label])
);

type OnboardingState = {
  job_types: string[];
  fields: string[];
  location_type: "cambodia" | "abroad" | null;
  country: string;
};

type Tab = "feed" | "saved" | "profile";

function SelectCard({
  icon,
  label,
  selected,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 14,
        width: "100%",
        padding: "16px 18px",
        background: selected ? "rgba(79,127,255,0.1)" : "var(--card)",
        border: `1.5px solid ${selected ? "var(--primary)" : "var(--border)"}`,
        borderRadius: "var(--radius)",
        color: selected ? "var(--foreground)" : "var(--secondary-foreground)",
        cursor: "pointer",
        textAlign: "left",
        transition: "border-color 0.15s, background 0.15s, color 0.15s",
      }}
    >
      <span style={{ color: selected ? "var(--primary)" : "var(--muted-foreground)", flexShrink: 0 }}>
        {icon}
      </span>
      <span style={{ fontSize: 14, fontWeight: selected ? 600 : 400, flex: 1 }}>{label}</span>
      {selected && (
        <span style={{ color: "var(--primary)", flexShrink: 0 }}>
          <IconCheck size={14} />
        </span>
      )}
    </button>
  );
}

function Onboarding({ onComplete }: { onComplete: () => void }) {
  const [step, setStep] = useState(1);
  const [state, setState] = useState<OnboardingState>({
    job_types: [],
    fields: [],
    location_type: null,
    country: "",
  });
  const [countrySearch, setCountrySearch] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  function toggleMulti(key: "job_types" | "fields", value: string) {
    setState((prev) => {
      const arr = prev[key];
      return {
        ...prev,
        [key]: arr.includes(value) ? arr.filter((v) => v !== value) : [...arr, value],
      };
    });
  }

  const filteredCountries = COUNTRIES.filter((c) =>
    c.toLowerCase().includes(countrySearch.toLowerCase())
  );

  const canContinue = (() => {
    if (step === 1) return state.job_types.length > 0;
    if (step === 2) return state.fields.length > 0;
    if (step === 3) {
      if (state.location_type === "cambodia") return true;
      if (state.location_type === "abroad") return state.country !== "";
      return false;
    }
    return false;
  })();

  async function handleFinish() {
    if (!canContinue || submitting) return;
    setSubmitting(true);
    setSubmitError(null);

    const preferences = {
      job_types: state.job_types,
      fields: state.fields === state.fields.filter((f) => f === "any") ? [] : state.fields.filter((f) => f !== "any"),
      location_type: state.location_type as "cambodia" | "abroad",
      country: state.location_type === "abroad" ? state.country : undefined,
    };

    try {
      await api.updatePreferences(preferences);
      onComplete();
    } catch {
      setSubmitError("Could not save your preferences. Please check your connection and try again.");
      setSubmitting(false);
    }
  }

  return (
    <div style={{ minHeight: "100%", display: "flex", flexDirection: "column", padding: "0 24px 32px" }}>
      <div style={{ paddingTop: 48, paddingBottom: 32 }}>
        <Logo />

        {/* Progress */}
        <div style={{ display: "flex", gap: 6, marginTop: 36, marginBottom: 36 }}>
          {[1, 2, 3].map((n) => (
            <div key={n} style={{ flex: 1, height: 3, borderRadius: 2, background: n <= step ? "var(--primary)" : "var(--secondary)", transition: "background 0.3s" }} />
          ))}
        </div>

        <p className="section-label" style={{ marginBottom: 8 }}>{step} of 3</p>
        <h1 className="font-display" style={{ fontSize: 26, fontWeight: 400, lineHeight: 1.2, color: "var(--foreground)", marginBottom: 6 }}>
          {step === 1 && "What are you looking for?"}
          {step === 2 && "What field are you interested in?"}
          {step === 3 && "Where would you like to work?"}
        </h1>
      </div>

      {/* Step 1 — Job type */}
      {step === 1 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10, flex: 1 }}>
          {JOB_TYPE_OPTIONS.map((opt) => (
            <SelectCard
              key={opt.value}
              icon={opt.icon}
              label={opt.label}
              selected={state.job_types.includes(opt.value)}
              onClick={() => toggleMulti("job_types", opt.value)}
            />
          ))}
        </div>
      )}

      {/* Step 2 — Field */}
      {step === 2 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8, flex: 1, overflowY: "auto" }} className="scrollbar-hide">
          {FIELD_OPTIONS.map((opt) => (
            <SelectCard
              key={opt.value}
              icon={opt.icon}
              label={opt.label}
              selected={state.fields.includes(opt.value)}
              onClick={() => toggleMulti("fields", opt.value)}
            />
          ))}
        </div>
      )}

      {/* Step 3 — Location */}
      {step === 3 && (
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 10 }}>
          <SelectCard
            icon={<IconMapPin size={20} />}
            label="Cambodia"
            selected={state.location_type === "cambodia"}
            onClick={() => setState((s) => ({ ...s, location_type: "cambodia", country: "" }))}
          />
          <SelectCard
            icon={<IconGlobe size={20} />}
            label="Abroad"
            selected={state.location_type === "abroad"}
            onClick={() => setState((s) => ({ ...s, location_type: "abroad" }))}
          />

          {/* Country sub-step */}
          {state.location_type === "abroad" && (
            <div style={{ marginTop: 8, background: "var(--secondary)", borderRadius: "var(--radius)", border: "1px solid var(--border)", overflow: "hidden" }}>
              <p style={{ fontSize: 12, fontWeight: 600, color: "var(--muted-foreground)", padding: "12px 16px 8px", letterSpacing: "0.06em", textTransform: "uppercase" }}>
                Which country?
              </p>
              <div style={{ position: "relative", padding: "0 12px 8px" }}>
                <span style={{ position: "absolute", left: 24, top: "50%", transform: "translateY(-50%)", color: "var(--muted-foreground)", pointerEvents: "none" }}>
                  <IconSearch size={14} />
                </span>
                <input
                  type="text"
                  placeholder="Search countries…"
                  value={countrySearch}
                  onChange={(e) => setCountrySearch(e.target.value)}
                  style={{
                    width: "100%",
                    background: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    color: "var(--foreground)",
                    padding: "10px 14px 10px 34px",
                    fontSize: 13,
                    outline: "none",
                  }}
                  autoFocus
                />
              </div>
              <div style={{ maxHeight: 200, overflowY: "auto" }} className="scrollbar-hide">
                {filteredCountries.slice(0, 60).map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setState((s) => ({ ...s, country: c }))}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      width: "100%",
                      padding: "11px 16px",
                      background: state.country === c ? "rgba(79,127,255,0.1)" : "none",
                      border: "none",
                      color: state.country === c ? "var(--primary)" : "var(--foreground)",
                      fontSize: 13,
                      fontWeight: state.country === c ? 600 : 400,
                      cursor: "pointer",
                      textAlign: "left",
                      borderTop: "1px solid var(--border)",
                      transition: "background 0.1s",
                    }}
                  >
                    {c}
                    {state.country === c && <IconCheck size={13} />}
                  </button>
                ))}
                {filteredCountries.length === 0 && (
                  <p style={{ padding: "16px", fontSize: 13, color: "var(--muted-foreground)", textAlign: "center" }}>No countries found</p>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {submitError && (
        <p style={{ fontSize: 13, color: "#f87171", marginTop: 12, lineHeight: 1.5 }}>{submitError}</p>
      )}

      {/* Navigation */}
      <div style={{ marginTop: 28, display: "flex", flexDirection: "column", gap: 10 }}>
        <button
          className="btn-primary"
          disabled={!canContinue || submitting}
          style={{ opacity: canContinue && !submitting ? 1 : 0.4 }}
          onClick={() => {
            if (step < 3) setStep((s) => s + 1);
            else handleFinish();
          }}
        >
          {step === 3 ? (submitting ? "Saving…" : "Get my recommendations") : "Continue"}
        </button>
        {step > 1 && (
          <button className="btn-outline" onClick={() => setStep((s) => s - 1)} disabled={submitting}>
            Back
          </button>
        )}
      </div>
    </div>
  );
}

// ── Feed ──────────────────────────────────────────────────────────────────
function ScoreBadge({ score }: { score: number | undefined }) {
  if (score === undefined) return null;
  const cls = score >= 85 ? "score-high" : score >= 70 ? "score-mid" : "";
  return (
    <div className={`score-badge ${cls}`} title={`${score}% match`}>
      {score}
    </div>
  );
}

function JobCard({
  job,
  isSaved,
  onToggleSave,
  onClick,
}: {
  job: Job;
  isSaved: boolean;
  onToggleSave: (e: React.MouseEvent) => void;
  onClick: () => void;
}) {
  return (
    <div className="job-card" onClick={onClick}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
        <ScoreBadge score={job.match_score} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "flex-start" }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, lineHeight: 1.35, color: "var(--foreground)", margin: 0 }}>
              {job.title}
            </h3>
            <button
              style={{ background: "none", border: "none", padding: "2px 0 0 8px", cursor: "pointer", color: isSaved ? "var(--primary)" : "var(--muted-foreground)", flexShrink: 0, transition: "color 0.15s" }}
              onClick={onToggleSave}
              aria-label={isSaved ? "Remove from saved" : "Save job"}
            >
              <IconBookmark size={15} filled={isSaved} />
            </button>
          </div>
          <p style={{ fontSize: 13, color: "var(--primary)", fontWeight: 500, margin: "4px 0 8px" }}>
            {job.organization}
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "5px 12px" }}>
            {job.location ? (
              <span style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12, color: "var(--muted-foreground)" }}>
                <IconMapPin size={12} />{job.location}
              </span>
            ) : (
              <span style={{ fontSize: 12, color: "var(--muted-foreground)" }}>Location not specified</span>
            )}
            {job.closing_date && (
              <span style={{ fontSize: 12, color: "var(--muted-foreground)" }}>
                Closes {job.closing_date}
              </span>
            )}
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 10 }}>
            {job.job_type && <span className="chip">{job.job_type}</span>}
            {job.field && <span className="chip">{FIELD_LABELS[job.field] ?? job.field}</span>}
          </div>
          {job.match_reason && (
            <p style={{ marginTop: 10, fontSize: 12, color: "var(--muted-foreground)", lineHeight: 1.5, paddingTop: 10, borderTop: "1px solid var(--border)" }}>
              {job.match_reason}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function Feed({
  onSelectJob,
}: {
  onSelectJob: (job: Job) => void;
}) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [savedIds, setSavedIds] = useState<Set<string | number>>(new Set());

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getRecommendations();
      setJobs(res.results);
    } catch {
      setError("Could not load recommendations. Check your connection.");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchWithSearch = useCallback(async () => {
    if (!search.trim()) {
      fetchJobs();
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.getJobs({ search: search.trim() });
      setJobs(res.results);
    } catch {
      setError("Search failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [search, fetchJobs]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  useEffect(() => {
    const t = setTimeout(() => {
      if (search.trim()) fetchWithSearch();
      else fetchJobs();
    }, 400);
    return () => clearTimeout(t);
  }, [search, fetchWithSearch, fetchJobs]);

  async function toggleSave(e: React.MouseEvent, job: Job) {
    e.stopPropagation();
    const id = job.id;
    const wasSaved = savedIds.has(id);
    setSavedIds((prev) => {
      const next = new Set(prev);
      wasSaved ? next.delete(id) : next.add(id);
      return next;
    });
    try {
      if (wasSaved) await api.unsaveJob(id);
      else await api.saveJob(id);
    } catch {
      setSavedIds((prev) => {
        const next = new Set(prev);
        wasSaved ? next.add(id) : next.delete(id);
        return next;
      });
    }
  }

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "20px 20px 0" }}>
        <p className="section-label" style={{ marginBottom: 6 }}>Matched for you</p>
        <h2 className="font-display" style={{ fontSize: 22, fontWeight: 400, color: "var(--foreground)", marginBottom: 16 }}>
          Recommendations
        </h2>
        <div style={{ position: "relative", marginBottom: 12 }}>
          <span style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: "var(--muted-foreground)", pointerEvents: "none" }}>
            <IconSearch size={14} />
          </span>
          <input
            type="text"
            placeholder="Search roles, organisations…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: "100%",
              background: "var(--secondary)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              color: "var(--foreground)",
              padding: "10px 14px 10px 34px",
              fontSize: 13,
              outline: "none",
            }}
          />
        </div>
      </div>
      <div className="divider" />
      <div style={{ flex: 1, overflowY: "auto", padding: "12px 20px 80px", display: "flex", flexDirection: "column", gap: 10 }} className="scrollbar-hide">
        {loading && Array.from({ length: 4 }).map((_, i) => <JobCardSkeleton key={i} />)}
        {!loading && error && <ErrorState message={error} onRetry={fetchJobs} />}
        {!loading && !error && jobs.length === 0 && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "48px 0", textAlign: "center", gap: 12 }}>
            <p style={{ fontSize: 15, fontWeight: 500, color: "var(--foreground)" }}>No matching jobs found</p>
            <p style={{ fontSize: 13, color: "var(--muted-foreground)", lineHeight: 1.5 }}>
              Try changing your preferences or broadening your search.
            </p>
          </div>
        )}
        {!loading && !error && jobs.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            isSaved={savedIds.has(job.id) || !!job.is_saved}
            onToggleSave={(e) => toggleSave(e, job)}
            onClick={() => onSelectJob(job)}
          />
        ))}
      </div>
    </div>
  );
}

// ── Job Detail ──────────────────────────────────────────────────────────
function JobDetail({ jobId, onBack }: { jobId: string | number; onBack: () => void }) {
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const fetchJob = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getJob(jobId);
      setJob(data);
      setSaved(!!data.is_saved);
    } catch {
      setError("The job could not be loaded. It may no longer be available.");
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => { fetchJob(); }, [fetchJob]);

  async function toggleSave() {
    if (!job) return;
    const was = saved;
    setSaved(!was);
    try {
      if (was) await api.unsaveJob(job.id);
      else await api.saveJob(job.id);
    } catch {
      setSaved(was);
    }
  }

  return (
    <div style={{ height: "100%", overflowY: "auto" }} className="scrollbar-hide">
      <div style={{ position: "sticky", top: 0, background: "var(--background)", borderBottom: "1px solid var(--border)", padding: "12px 20px", display: "flex", alignItems: "center", justifyContent: "space-between", zIndex: 10 }}>
        <button onClick={onBack} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--foreground)", display: "flex", alignItems: "center", gap: 8, fontSize: 14, fontWeight: 500, padding: "4px 0" }}>
          <IconArrowLeft size={18} /> Back
        </button>
        {job && (
          <button style={{ background: "none", border: "none", cursor: "pointer", color: saved ? "var(--primary)" : "var(--muted-foreground)", transition: "color 0.15s" }} onClick={toggleSave}>
            <IconBookmark size={20} filled={saved} />
          </button>
        )}
      </div>

      <div style={{ padding: "24px 20px 48px" }}>
        {loading && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <Skeleton h={24} w="75%" />
            <Skeleton h={16} w="50%" />
            <Skeleton h={12} w="35%" />
            <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 8 }}>
              {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} h={12} />)}
            </div>
          </div>
        )}
        {!loading && error && <ErrorState message={error} onRetry={fetchJob} />}
        {!loading && !error && !job && (
          <div style={{ textAlign: "center", padding: "48px 0" }}>
            <p style={{ fontSize: 15, color: "var(--muted-foreground)" }}>The job is no longer available.</p>
          </div>
        )}
        {!loading && !error && job && (
          <>
            {job.match_score !== undefined && (
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
                <ScoreBadge score={job.match_score} />
                <div>
                  <p className="section-label" style={{ marginBottom: 3 }}>Match score</p>
                  {job.match_reason && <p style={{ fontSize: 13, color: "var(--muted-foreground)" }}>{job.match_reason}</p>}
                </div>
              </div>
            )}
            <div className="divider" style={{ marginBottom: 20 }} />
            <h1 className="font-display" style={{ fontSize: 24, fontWeight: 400, lineHeight: 1.25, marginBottom: 6, color: "var(--foreground)" }}>
              {job.title}
            </h1>
            <p style={{ fontSize: 15, color: "var(--primary)", fontWeight: 600, marginBottom: 16 }}>{job.organization}</p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px 18px", marginBottom: 16 }}>
              {job.location ? (
                <span style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 13, color: "var(--muted-foreground)" }}><IconMapPin size={13} />{job.location}</span>
              ) : (
                <span style={{ fontSize: 13, color: "var(--muted-foreground)" }}>Location not specified</span>
              )}
              {job.job_type && <span style={{ fontSize: 13, color: "var(--muted-foreground)" }}>{job.job_type}</span>}
              {job.field && <span style={{ fontSize: 13, color: "var(--muted-foreground)" }}>{FIELD_LABELS[job.field] ?? job.field}</span>}
              {job.closing_date ? (
                <span style={{ fontSize: 13, color: "var(--muted-foreground)" }}>Closes {job.closing_date}</span>
              ) : (
                <span style={{ fontSize: 13, color: "var(--muted-foreground)" }}>Closing date not provided</span>
              )}
            </div>
            <div className="divider" style={{ marginBottom: 20 }} />
            <p className="section-label" style={{ marginBottom: 10 }}>About the role</p>
            <p style={{ fontSize: 14, lineHeight: 1.75, color: "var(--secondary-foreground)", marginBottom: 24, whiteSpace: "pre-wrap" }}>
              {job.description}
            </p>
            {job.skills.length > 0 && (
              <>
                <p className="section-label" style={{ marginBottom: 10 }}>Skills</p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 24 }}>
                  {job.skills.map((s) => <span key={s} className="chip">{s}</span>)}
                </div>
              </>
            )}
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {job.source_url && (
                <a href={job.source_url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: "none" }}>
                  <button className="btn-primary" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
                    Apply on {job.source || "ReliefWeb"} <IconExternalLink size={13} />
                  </button>
                </a>
              )}
              <button className="btn-outline" onClick={toggleSave}>
                {saved ? "Remove from saved" : "Save for later"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── Saved Jobs ────────────────────────────────────────────────────────────
function SavedJobs({ onSelectJob }: { onSelectJob: (job: Job) => void }) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSaved = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getSavedJobs();
      setJobs(res.results);
    } catch {
      setError("Could not load saved jobs.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchSaved(); }, [fetchSaved]);

  async function unsave(e: React.MouseEvent, job: Job) {
    e.stopPropagation();
    try {
      await api.unsaveJob(job.id);
      setJobs((prev) => prev.filter((j) => j.id !== job.id));
    } catch { /* keep in list if fails */ }
  }

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "20px 20px 16px" }}>
        <p className="section-label" style={{ marginBottom: 6 }}>Your collection</p>
        <h2 className="font-display" style={{ fontSize: 22, fontWeight: 400, color: "var(--foreground)" }}>Saved Jobs</h2>
      </div>
      <div className="divider" />
      <div style={{ flex: 1, overflowY: "auto", padding: "12px 20px 80px", display: "flex", flexDirection: "column", gap: 10 }} className="scrollbar-hide">
        {loading && Array.from({ length: 3 }).map((_, i) => <JobCardSkeleton key={i} />)}
        {!loading && error && <ErrorState message={error} onRetry={fetchSaved} />}
        {!loading && !error && jobs.length === 0 && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", flex: 1, padding: "48px 0", textAlign: "center", gap: 12 }}>
            <div style={{ width: 48, height: 48, borderRadius: 12, background: "var(--secondary)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--muted-foreground)" }}>
              <IconBookmark size={22} />
            </div>
            <p style={{ fontSize: 15, fontWeight: 500, color: "var(--foreground)" }}>No saved jobs yet</p>
            <p style={{ fontSize: 13, color: "var(--muted-foreground)" }}>Tap the bookmark icon on any listing.</p>
          </div>
        )}
        {!loading && !error && jobs.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            isSaved={true}
            onToggleSave={(e) => unsave(e, job)}
            onClick={() => onSelectJob(job)}
          />
        ))}
      </div>
    </div>
  );
}

// ── Profile ───────────────────────────────────────────────────────────────
function Profile({ onResetPreferences }: { onResetPreferences: () => void }) {
  const [profile, setProfile] = useState<import("./types").UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);

  const fetchProfile = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getProfile();
      setProfile(data);
    } catch {
      setError("Could not load your profile.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchProfile(); }, [fetchProfile]);

  async function handleUpdatePreferences() {
    if (!profile) return;
    setUpdating(true);
    setUpdateError(null);
    try {
      await api.updatePreferences(profile.preferences);
    } catch {
      setUpdateError("Could not update preferences. Please try again.");
    } finally {
      setUpdating(false);
    }
  }

  return (
    <div style={{ height: "100%", overflowY: "auto" }} className="scrollbar-hide">
      <div style={{ padding: "20px 20px 0" }}>
        <p className="section-label" style={{ marginBottom: 6 }}>Account</p>
        <h2 className="font-display" style={{ fontSize: 22, fontWeight: 400, color: "var(--foreground)", marginBottom: 24 }}>
          My Profile
        </h2>
      </div>

      {loading && (
        <div style={{ padding: "0 20px", display: "flex", flexDirection: "column", gap: 12 }}>
          <Skeleton h={80} rounded={10} />
          <Skeleton h={160} rounded={10} />
        </div>
      )}
      {!loading && error && (
        <div style={{ padding: "0 20px" }}>
          <ErrorState message={error} onRetry={fetchProfile} />
        </div>
      )}
      {!loading && !error && profile && (
        <>
          <div style={{ margin: "0 20px 20px", background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: "20px", display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ width: 48, height: 48, borderRadius: 24, background: "rgba(79,127,255,0.1)", border: "2px solid rgba(79,127,255,0.2)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--primary)" }}>
              <IconUser size={20} />
            </div>
            <div>
              <p style={{ fontSize: 14, fontWeight: 600, color: "var(--foreground)" }}>
                {profile.telegram_id ? `User ${profile.telegram_id}` : "Telegram User"}
              </p>
              <p style={{ fontSize: 12, color: "var(--muted-foreground)" }}>Connected via Telegram</p>
            </div>
          </div>

          <div style={{ margin: "0 20px 16px", background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)", overflow: "hidden" }}>
            <p className="section-label" style={{ padding: "14px 16px 10px" }}>Preferences</p>
            {[
              { label: "Job types", value: profile.preferences.job_types?.join(", ") || "—" },
              { label: "Fields", value: profile.preferences.fields?.join(", ") || "—" },
              { label: "Location", value: profile.preferences.location_type === "abroad" ? `Abroad — ${profile.preferences.country || ""}` : (profile.preferences.location_type === "cambodia" ? "Cambodia" : "—") },
            ].map((row, i) => (
              <div key={i}>
                <div className="divider" />
                <div style={{ padding: "13px 16px", display: "flex", justifyContent: "space-between", gap: 12 }}>
                  <p style={{ fontSize: 12, color: "var(--muted-foreground)", flexShrink: 0 }}>{row.label}</p>
                  <p style={{ fontSize: 13, color: "var(--foreground)", textAlign: "right", lineHeight: 1.4 }}>{row.value}</p>
                </div>
              </div>
            ))}
          </div>

          <div style={{ margin: "0 20px", background: "rgba(79,127,255,0.05)", border: "1px solid rgba(79,127,255,0.12)", borderRadius: "var(--radius)", padding: "14px 16px", marginBottom: 16 }}>
            <p className="section-label" style={{ marginBottom: 5 }}>Data source</p>
            <p style={{ fontSize: 12, color: "var(--muted-foreground)", lineHeight: 1.6 }}>
              Jobs are ingested from <span style={{ color: "var(--primary)" }}>ReliefWeb (reliefweb.int)</span> — a UN OCHA humanitarian job API — and ranked by the CareerMatch recommendation engine.
            </p>
          </div>

          {updateError && (
            <p style={{ fontSize: 13, color: "#f87171", margin: "0 20px 12px", lineHeight: 1.5 }}>{updateError}</p>
          )}

          <div style={{ padding: "0 20px 80px", display: "flex", flexDirection: "column", gap: 10 }}>
            <button className="btn-outline" style={{ width: "100%" }} onClick={handleUpdatePreferences} disabled={updating}>
              {updating ? "Updating…" : "Update Preferences"}
            </button>
            <button className="btn-outline" style={{ width: "100%", color: "var(--muted-foreground)", borderColor: "var(--border)" }} onClick={onResetPreferences}>
              Redo Onboarding
            </button>
          </div>
        </>
      )}
    </div>
  );
}

// ── Bottom Nav ────────────────────────────────────────────────────────────
function BottomNav({ tab, setTab }: { tab: Tab; setTab: (t: Tab) => void }) {
  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "feed", label: "Matches", icon: <IconBriefcase size={18} /> },
    { id: "saved", label: "Saved", icon: <IconBookmark size={18} /> },
    { id: "profile", label: "Profile", icon: <IconUser size={18} /> },
  ];
  return (
    <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, background: "rgba(10,15,30,0.95)", backdropFilter: "blur(12px)", borderTop: "1px solid var(--border)", display: "flex" }}>
      {tabs.map((t) => (
        <button key={t.id} className={`tab-btn ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4, color: tab === t.id ? "var(--foreground)" : "var(--muted-foreground)", transition: "color 0.15s" }}>
            {t.icon}
            <span style={{ fontSize: 10, fontWeight: tab === t.id ? 600 : 400 }}>{t.label}</span>
          </div>
        </button>
      ))}
    </div>
  );
}

// ── App ───────────────────────────────────────────────────────────────────
type AppView = "checking" | "onboarding" | "main";

export default function App() {
  const [view, setView] = useState<AppView>("checking");
  const [tab, setTab] = useState<Tab>("feed");
  const [detailJobId, setDetailJobId] = useState<string | number | null>(null);

  // On startup, ask the backend whether this Telegram user already
  // completed onboarding (preferences persist in Postgres). Only show the
  // onboarding flow once, not on every open — the API is the source of
  // truth, not local state.
  useEffect(() => {
    let cancelled = false;
    api
      .getProfile()
      .then((profile) => {
        if (cancelled) return;
        setView(profile.preferences?.onboarding_completed ? "main" : "onboarding");
      })
      .catch(() => {
        if (cancelled) return;
        // If we can't reach the backend yet, default to onboarding rather
        // than getting stuck on a blank screen; the onboarding form itself
        // will surface a clear connection error if saving also fails.
        setView("onboarding");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (view === "checking") {
    return (
      <div style={{ height: "100%", maxWidth: 480, margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--background)" }}>
        <Logo />
      </div>
    );
  }

  return (
    <div style={{ height: "100%", maxWidth: 480, margin: "0 auto", position: "relative", overflow: "hidden", background: "var(--background)" }}>
      {view === "onboarding" ? (
        <div style={{ height: "100%", overflowY: "auto" }} className="scrollbar-hide">
          <Onboarding onComplete={() => { setView("main"); setTab("feed"); }} />
        </div>
      ) : detailJobId !== null ? (
        <JobDetail jobId={detailJobId} onBack={() => setDetailJobId(null)} />
      ) : (
        <>
          <div style={{ height: "100%", paddingBottom: 60 }}>
            {tab === "feed" && <Feed onSelectJob={(job) => setDetailJobId(job.id)} />}
            {tab === "saved" && <SavedJobs onSelectJob={(job) => setDetailJobId(job.id)} />}
            {tab === "profile" && <Profile onResetPreferences={() => setView("onboarding")} />}
          </div>
          <BottomNav tab={tab} setTab={setTab} />
        </>
      )}
    </div>
  );
}
