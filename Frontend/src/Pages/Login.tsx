import { useState } from "react";
import { useAuth } from "../Services/Context/AuthContext";
import { Link, useNavigate } from "react-router-dom";
import { AuthShell } from "../Components/AuthShell";

export const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Email ou mot de passe incorrect");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title="Connexion">
      {error && <p className="text-danger text-sm mb-4 text-center bg-danger/10 border border-danger/25 rounded-xl p-3">{error}</p>}
      <form onSubmit={handleSubmit} className="space-y-4">
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
        <div>
          <label className="text-xs text-gray-400 block mb-1.5">Mot de passe</label>
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input pr-12"
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-cyan-400 transition-colors"
            >
              {showPassword ? (
                <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              )}
            </button>
          </div>
        </div>
        <button type="submit" disabled={loading} className="btn-primary w-full">
          {loading ? "Connexion..." : "Se connecter"}
        </button>
      </form>
      <p className="text-gray-400 text-sm mt-5 text-center">
        <Link to="/forgot-password" className="text-cyan-400 hover:text-cyan-300 hover:underline transition-colors">
          Mot de passe oublié ?
        </Link>
      </p>
      <p className="text-gray-500 text-sm mt-4 text-center border-t border-white/5 pt-4">
        Pas encore de compte ?{" "}
        <Link to="/register" className="text-cyan-400 hover:text-cyan-300 hover:underline transition-colors">
          S'inscrire
        </Link>
      </p>
    </AuthShell>
  );
};
