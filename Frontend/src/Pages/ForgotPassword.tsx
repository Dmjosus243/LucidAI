import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthShell } from "../Components/AuthShell";
import { forgotPassword, resetPassword } from "../Services/api";

export const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [step, setStep] = useState<"email" | "reset">("email");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const navigate = useNavigate();

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setInfo("");
    setLoading(true);
    try {
      await forgotPassword(email);
      setInfo(
        "Si un compte existe pour cet email, un code à 6 chiffres vous a été envoyé (valable 30 minutes)."
      );
      setStep("reset");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Une erreur est survenue");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== confirm) {
      setError("Les mots de passe ne correspondent pas");
      return;
    }
    setLoading(true);
    try {
      await resetPassword(email, otp, password);
      setDone(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Une erreur est survenue");
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return (
      <AuthShell title="Mot de passe réinitialisé">
        <div className="text-center space-y-5">
          <div className="w-16 h-16 mx-auto rounded-full bg-success/15 border border-success/30 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-8 h-8 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <p className="text-gray-300 text-sm">
            Votre mot de passe a bien été modifié. Vous pouvez maintenant vous connecter.
          </p>
          <button onClick={() => navigate("/login")} className="btn-primary w-full">
            Se connecter
          </button>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell title={step === "email" ? "Mot de passe oublié" : "Réinitialisation"}>
      {error && <p className="text-danger text-sm mb-4 text-center bg-danger/10 border border-danger/25 rounded-xl p-3">{error}</p>}
      {info && <p className="text-cyan-300 text-sm mb-4 text-center bg-cyan-500/10 border border-cyan-500/25 rounded-xl p-3">{info}</p>}

      {step === "email" ? (
        <form onSubmit={handleSendOtp} className="space-y-4">
          <p className="text-gray-400 text-sm text-center">
            Entrez votre email. Un code de vérification (OTP) vous sera envoyé, valable 30 minutes.
          </p>
          <div>
            <label className="text-xs text-gray-400 block mb-1.5">Email</label>
            <input
              type="email"
              placeholder="vous@exemple.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              required
            />
          </div>
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? "Envoi en cours..." : "Envoyer le code"}
          </button>
        </form>
      ) : (
        <form onSubmit={handleReset} className="space-y-4">
          <div>
            <label className="text-xs text-gray-400 block mb-1.5">Code à 6 chiffres (OTP)</label>
            <input
              type="text"
              placeholder="000000"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
              className="input text-center tracking-[0.5em] font-mono"
              maxLength={6}
              required
            />
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1.5">Nouveau mot de passe</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                placeholder="6 caractères minimum"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input pr-12"
                minLength={6}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label="Afficher le mot de passe"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-cyan-400 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </button>
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1.5">Confirmer le mot de passe</label>
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Retapez le mot de passe"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              className="input"
              minLength={6}
              required
            />
          </div>
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? "Enregistrement..." : "Réinitialiser le mot de passe"}
          </button>
          <button
            type="button"
            onClick={() => setStep("email")}
            className="w-full text-gray-400 hover:text-gray-300 text-sm transition-colors"
          >
            ← Changer d'email
          </button>
        </form>
      )}
      <p className="text-gray-500 text-sm mt-6 text-center border-t border-white/5 pt-4">
        Vous vous souvenez de votre mot de passe ?{" "}
        <Link to="/login" className="text-cyan-400 hover:text-cyan-300 hover:underline transition-colors">
          Se connecter
        </Link>
      </p>
    </AuthShell>
  );
};
