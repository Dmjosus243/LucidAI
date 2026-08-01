import logo from "../assets/IMG/LucidAILOGO.png";

interface LogoProps {
  size?: number;
  withText?: boolean;
}

export const Logo = ({ size = 32, withText = true }: LogoProps) => {
  return (
    <div className="flex items-center gap-2">
      <img
        src={logo}
        alt="LucidAI"
        width={size}
        height={size}
        className="rounded-lg"
        style={{ width: size, height: size, objectFit: "cover" }}
      />
      {withText && <h1 className="text-2xl font-bold text-white">LucidAI</h1>}
    </div>
  );
};
