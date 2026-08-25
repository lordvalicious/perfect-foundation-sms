import { Languages } from "lucide-react";
import { useLang } from "../i18n";

export default function LanguageToggle() {
  const { lang, setLang } = useLang();

  return (
    <button
      className="theme-toggle"
      style={{ fontWeight: 700, fontSize: 12 }}
      onClick={() => setLang(lang === "en" ? "ur" : "en")}
      title={lang === "en" ? "اردو میں دیکھیں" : "Switch to English"}
    >
      <Languages size={16} />
      {lang === "en" ? "اردو" : "EN"}
    </button>
  );
}
