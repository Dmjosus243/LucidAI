import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Logo } from "../Components/Logo";
import { forgotPassword, resetPassword } from "../Services/api";

export const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
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

  return (
    <div className="min-h-screen bg-dark flex items-center justify-center p-6">
      <div className="glass rounded-2xl p-8 w-full max-w-md">
        <div className="flex items-center gap-2 mb-8 justify-center">
          <Logo size={40} />
        </div>

        {done ? (
          <>
            <h2 className="text-lg text-gray-300 mb-6 text-center">Mot de passe réinitialisé</h2>
            <p className="text-gray-400 text-sm mb-6 text-center">
              Votre mot de passe a bien été modifié. Vous pouvez maintenant vous connecter.
            </p>
            <button
              onClick={() => navigate("/login")}
              className="w-full bg-cyan-500 hover:bg-cyan-600 text-dark font-bold py-3 rounded-xl transition-colors"
            >
              Se connecter
            </button>
          </>
        ) : (
          <>
            <h2 className="text-lg text-gray-300 mb-6 text-center">
              {step === "email" ? "Mot de passe oublié ?" : "Réinitialisation"}
            </h2>
            {error && <p className="text-danger text-sm mb-4 text-center">{error}</p>}
            {info && <p className="text-cyan-400 text-sm mb-4 text-center">{info}</p>}

            {step === "email" ? (
              <form onSubmit={handleSendOtp} className="space-y-4">
                <p className="text-gray-400 text-sm text-center">
                  Entrez votre email. Un code de vérification (OTP) vous sera envoyé, valable 30 minutes.
                </p>
                <input
                  type="email"
                  placeholder="Email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full p-3 rounded-xl bg-dark-card border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                  required
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-cyan-500 hover:bg-cyan-600 disabled:opacity-50 text-dark font-bold py-3 rounded-xl transition-colors"
                >
                  {loading ? "Envoi en cours..." : "Envoyer le code"}
                </button>
              </form>
            ) : (
              <form onSubmit={handleReset} className="space-y-4">
                <input
                  type="text"
                  placeholder="Code à 6 chiffres (OTP)"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  className="w-full p-3 rounded-xl bg-dark-card border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                  maxLength={6}
                  required
                />
                <input
                  type="password"
                  placeholder="Nouveau mot de passe"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full p-3 rounded-xl bg-dark-card border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                  required
                />
                <input
                  type="password"
                  placeholder="Confirmer le mot de passe"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  className="w-full p-3 rounded-xl bg-dark-card border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                  required
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-cyan-500 hover:bg-cyan-600 disabled:opacity-50 text-dark font-bold py-3 rounded-xl transition-colors"
                >
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
            <p className="text-gray-400 text-sm mt-6 text-center">
              Vous vous souvenez de votre mot de passe ?{" "}
              <Link to="/login" className="text-cyan-400 hover:underline">Se connecter</Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
};
