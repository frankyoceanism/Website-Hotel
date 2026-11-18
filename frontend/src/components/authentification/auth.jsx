import { useEffect, useState } from "react";
import { api } from "../../api.js";
import "./auth.css";

// Teks sisi kiri tampilan Sign Up
const PANEL_TITLE = "Judul di sini";

const BENEFITS = [
  {
    id: "b1",
    icon: "user",
    title: "Judul keuntungan 1",
    text: "Deskripsi singkat keuntungan 1 ditulis di sini.",
  },
  {
    id: "b2",
    icon: "coin",
    title: "Judul keuntungan 2",
    text: "Deskripsi singkat keuntungan 2 ditulis di sini.",
  },
  {
    id: "b3",
    icon: "crown",
    title: "Judul keuntungan 3",
    text: "Deskripsi singkat keuntungan 3 ditulis di sini.",
  },
];

// Foto latar Sign Up
const PANEL_IMAGE = "/images/auth-bg.jpg";

/* ---------- Ikon ---------- */

function BenefitIcon({ name }) {
  return (
    <svg viewBox="0 0 48 48" width="40" height="40" aria-hidden="true">
      {name === "user" && (
        <>
          <circle cx="24" cy="15" r="7" />
          <path d="M10 40c0-8 6-13 14-13s14 5 14 13" />
        </>
      )}

      {name === "coin" && (
        <>
          <circle cx="24" cy="24" r="16" />
          <circle cx="24" cy="24" r="10" />
        </>
      )}

      {name === "crown" && (
        <path d="M8 36L6 16l11 9 7-13 7 13 11-9-2 20z" />
      )}
    </svg>
  );
}

function EyeIcon({ hidden }) {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
      <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" />
      <circle cx="12" cy="12" r="3" />
      {hidden && <path d="M3 3l18 18" />}
    </svg>
  );
}

/* ---------- Field ---------- */

function Field({
  label,
  name,
  type = "text",
  value,
  onChange,
  placeholder,
  autoComplete,
}) {
  return (
    <div className="auth__field">
      <label className="auth__label" htmlFor={`auth-${name}`}>
        {label}
      </label>

      <input
        id={`auth-${name}`}
        className="auth__input"
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        autoComplete={autoComplete}
        required
      />
    </div>
  );
}

/* ---------- Password Field ---------- */

function PasswordField({ name, value, onChange, autoComplete }) {
  const [show, setShow] = useState(false);

  return (
    <div className="auth__field">
      <label className="auth__label" htmlFor={`auth-${name}`}>
        Password
      </label>

      <div className="auth__password">
        <input
          id={`auth-${name}`}
          className="auth__input"
          name={name}
          type={show ? "text" : "password"}
          value={value}
          onChange={onChange}
          placeholder="********"
          autoComplete={autoComplete}
          required
        />

        <button
          type="button"
          className="auth__eye"
          onClick={() => setShow((s) => !s)}
          aria-label={show ? "Sembunyikan password" : "Tampilkan password"}
        >
          <EyeIcon hidden={!show} />
        </button>
      </div>
    </div>
  );
}

/* ---------- Dialog ---------- */

function AuthDialog({ onClose, initialView, onSuccess }) {
  const [view, setView] = useState(initialView);

  const [signIn, setSignIn] = useState({
    username: "",
    password: "",
  });

  const [signUp, setSignUp] = useState({
    username: "",
    email: "",
    password: "",
  });

  const [busy, setBusy] = useState(false);

  const [message, setMessage] = useState({
    type: "",
    text: "",
  });

  // Tutup dengan Esc dan kunci scroll halaman
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
    };

    document.addEventListener("keydown", onKey);

    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [onClose]);

  // Pindah tampilan dan bersihkan pesan lama
  const changeView = (nextView) => {
    setView(nextView);
    setMessage({ type: "", text: "" });
  };

  /* ---------- SIGN IN ---------- */

  const handleSignIn = async (e) => {
    e.preventDefault();

    if (busy) return;

    setBusy(true);
    setMessage({ type: "", text: "" });

    try {
      const result = await api.login({
        username: signIn.username.trim(),
        password: signIn.password,
      });

      if (!result.ok) {
        throw new Error(
          result.error || result.message || "Username atau password salah."
        );
      }

      // Mengirim data user ke Navbar / AuthContext
      onSuccess?.(result.user);

      onClose();
    } catch (error) {
      setMessage({
        type: "error",
        text: error.message || "Unable to connect to server.",
      });
    } finally {
      setBusy(false);
    }
  };

  /* ---------- SIGN UP ---------- */

  const handleSignUp = async (e) => {
    e.preventDefault();

    if (busy) return;

    setBusy(true);
    setMessage({ type: "", text: "" });

    try {
      const result = await api.register({
        username: signUp.username.trim(),
        email: signUp.email.trim(),
        password: signUp.password,
      });

      if (!result.ok) {
        throw new Error(
          result.error || result.message || "Registration failed."
        );
      }

      // Registrasi berhasil, kembali ke Sign In
      setSignIn({
        username: signUp.username.trim(),
        password: "",
      });

      setSignUp({
        username: "",
        email: "",
        password: "",
      });

      setView("signin");

      setMessage({
        type: "success",
        text: result.message || "Account created. Please sign in.",
      });
    } catch (error) {
      setMessage({
        type: "error",
        text: error.message || "Unable to connect to server.",
      });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="auth"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !busy) onClose();
      }}
    >
      <button
        type="button"
        className="auth__close"
        onClick={onClose}
        aria-label="Tutup"
      >
        <svg viewBox="0 0 24 24" width="34" height="34" aria-hidden="true">
          <path d="M3 3l18 18M21 3L3 21" />
        </svg>
      </button>

      <div
        className={`auth__dialog auth__dialog--${view}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-title"
      >
        {view === "signin" ? (
          /* ---------- SIGN IN VIEW ---------- */
          <div className="auth__body">
            <h2
              id="auth-title"
              className="auth__heading auth__heading--center"
            >
              SIGN IN
            </h2>

            {message.text && (
              <p
                className={`auth__message auth__message--${message.type}`}
                role="status"
              >
                {message.text}
              </p>
            )}

            <form onSubmit={handleSignIn} className="auth__form">
              <Field
                label="Username"
                name="signin-username"
                value={signIn.username}
                onChange={(e) =>
                  setSignIn({ ...signIn, username: e.target.value })
                }
                placeholder="username"
                autoComplete="username"
              />

              <PasswordField
                name="signin-password"
                value={signIn.password}
                onChange={(e) =>
                  setSignIn({ ...signIn, password: e.target.value })
                }
                autoComplete="current-password"
              />

              <button
                type="submit"
                className="auth__submit"
                disabled={busy}
              >
                {busy ? "PLEASE WAIT..." : "SIGN IN"}
              </button>
            </form>

            <div className="auth__member">
              <h3 className="auth__subheading">OR BECOME A MEMBER</h3>

              <p className="auth__text">Ubah teks</p>

              <button
                type="button"
                className="auth__outline"
                onClick={() => changeView("signup")}
              >
                SIGN UP
              </button>
            </div>
          </div>
        ) : (
          /* ---------- SIGN UP VIEW ---------- */
          <>
            <aside className="auth__panel">
              <img
                className="auth__panel-img"
                src={PANEL_IMAGE}
                alt=""
              />

              <div className="auth__panel-shade" />

              <div className="auth__panel-content">
                <p className="auth__panel-title">{PANEL_TITLE}</p>

                <ul className="auth__benefits">
                  {BENEFITS.map((b) => (
                    <li className="auth__benefit" key={b.id}>
                      <span className="auth__benefit-icon">
                        <BenefitIcon name={b.icon} />
                      </span>

                      <div>
                        <h3 className="auth__benefit-title">
                          {b.title}
                        </h3>

                        <p className="auth__benefit-text">
                          {b.text}
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </aside>

            <div className="auth__body auth__body--form">
              <h2 id="auth-title" className="auth__heading">
                LET&rsquo;S GET STARTED
              </h2>

              {message.text && (
                <p
                  className={`auth__message auth__message--${message.type}`}
                  role="status"
                >
                  {message.text}
                </p>
              )}

              <form onSubmit={handleSignUp} className="auth__form auth__form--grow">
                <Field
                  label="Username"
                  name="signup-username"
                  value={signUp.username}
                  onChange={(e) =>
                    setSignUp({ ...signUp, username: e.target.value })
                  }
                  placeholder="Create a username"
                  autoComplete="username"
                />

                <Field
                  label="Email"
                  name="signup-email"
                  value={signUp.email}
                  onChange={(e) =>
                    setSignUp({ ...signUp, email: e.target.value })
                  }
                  placeholder="Choose an Email"
                  type="email"
                  autoComplete="email"
                />

                <PasswordField
                  name="signup-password"
                  value={signUp.password}
                  onChange={(e) =>
                    setSignUp({ ...signUp, password: e.target.value })
                  }
                  autoComplete="new-password"
                />

                <button
                  type="submit"
                  className="auth__submit auth__submit--bottom"
                  disabled={busy}
                >
                  {busy ? "PLEASE WAIT..." : "JOIN"}
                </button>

                <p className="auth__switch">
                  Already a member?{" "}

                  <button
                    type="button"
                    className="auth__link"
                    onClick={() => changeView("signin")}
                  >
                    Sign in
                  </button>
                </p>
              </form>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ---------- EXPORT ---------- */

export default function Auth({
  open,
  onClose,
  onSuccess,
  initialView = "signin",
}) {
  if (!open) return null;

  return (
    <AuthDialog
      onClose={onClose}
      onSuccess={onSuccess}
      initialView={initialView}
    />
  );
}
