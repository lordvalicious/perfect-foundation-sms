/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useState } from "react";

/* Urdu translations. Keys are the English source strings; anything
   missing falls back to English, so coverage can grow page by page. */

const URDU = {
  // Navigation
  Dashboard: "ڈیش بورڈ",
  "My Profile": "میرا پروفائل",
  "Parent Portal": "پیرنٹل پورٹل",
  Students: "طلبہ",
  Admissions: "داخلیں",
  Teachers: "اساتذہ",
  Staff: "عملہ",
  "Human Resources": "انسانی وسائل",
  Assignments: "سبکہات",
  Attendance: "حاضری",
  Discipline: "نظم و ضبط",
  Homework: "ہوم ورک",
  Finance: "مالیات",
  "Bulk Finance": "بلک مالیات",
  Exams: "امتحانات",
  "Report Cards": "رپورٹ کارڈز",
  Timetable: "ٹائم ٹیبل",
  Campuses: "کیمپس",
  "Campus Dashboard": "کیمپس ڈیش بورڈ",
  Announcements: "اعلانات",
  Messages: "پیغامات",
  SMS: "ایس ایم ایس",
  Templates: "سانچے",
  Library: "لائبریری",
  Transport: "ٹرانسپورٹ",
  Inventory: "انوینٹری",
  Documents: "دستاویزات",
  Payroll: "تنخواہ",
  Reports: "رپورٹس",
  "Report Builder": "رپورٹ بلدر",
  "Data Export": "ڈیٹا ایکسپورٹ",
  "Data Import": "ڈیٹا امپورٹ",
  Events: "تقریبات",
  Settings: "ترتیبات",
  Branding: "برانڈنگ",
  "System Health": "سسٹم ہیلتھ",
  "Audit Logs": "آڈٹ لاگز",

  // Common actions / words
  Save: "محفوظ کریں",
  Submit: "جمع کریں",
  Cancel: "منسوخ",
  Close: "بند کریں",
  Search: "تلاش",
  Download: "ڈاؤن لوڈ",
  Export: "ایکسپورٹ",
  Import: "امپورٹ",
  Approve: "منظور",
  Reject: "مسترد",
  Status: "صورتِ حال",
  Total: "کل",
  Active: "فعال",
  Campus: "کیمپس",
  Class: "جماعت",
  Section: "سیکشن",
  Teacher: "استاد",
  Student: "طالب علم",
  Guardian: "سرپرست",
  Date: "تاریخ",
  Amount: "رقم",
  Grade: "گریڈ",
  Result: "نتیجہ",
  Present: "حاضر",
  Absent: "غیر حاضر",
  Late: "تاخیر",
  Leave: "رخصت",

  // Login
  "Username or Email": "یوزر نیم یا ای میل",
  Password: "پاس ورڈ",
  "Sign In": "سائن ان",
  "Signing in...": "سائن ان ہو رہا ہے...",
  "Authenticator code": "توثیقی کوڈ",

  // Dashboard
  "Dashboard Overview": "ڈیش بورڈ جائزہ",
  "Total Students": "کل طلبہ",
  "Active Students": "فعال طلبہ",
  Teachers2: "اساتذہ",
  Classes: "جماعتیں",
  Sections: "سیکشنز",
  Enrollments: "داخلے",
  "Fee Collection Trend": "فیس وصولی کا رجحان",
  "Enrollment by Campus": "کیمپس کے لحاظ سے داخلے",
  "Attendance Rate by Class": "جماعت کے لحاظ سے حاضری",
};

const DICT = { ur: URDU };
const LANG_KEY = "pf-lang";

const LangContext = createContext({
  lang: "en",
  setLang: () => {},
  t: (key) => key,
});

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    try {
      return localStorage.getItem(LANG_KEY) === "ur" ? "ur" : "en";
    } catch {
      return "en";
    }
  });

  useEffect(() => {
    document.documentElement.setAttribute(
      "dir",
      lang === "ur" ? "rtl" : "ltr"
    );
    document.documentElement.setAttribute("lang", lang);
  }, [lang]);

  const setLang = (next) => {
    setLangState(next);
    try {
      localStorage.setItem(LANG_KEY, next);
    } catch {
      /* storage unavailable — language resets on reload */
    }
  };

  const t = (key) => {
    if (lang !== "ur") return key;
    return DICT.ur[key] || key;
  };

  return (
    <LangContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  return useContext(LangContext);
}
