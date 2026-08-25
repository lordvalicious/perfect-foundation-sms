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

  // ---------- Students page ----------
  "Home / Students": "ہوم / طلبہ",
  "Manage students enrolled at Perfect Foundation School.":
    "پرفیکٹ فاؤنڈیشن اسکول میں داخل شدہ طلبہ کا انتظام۔",
  "+ Add Student": "+ نیا طالب علم",
  "Search by name, admission number or phone...":
    "نام، داخلہ نمبر یا فون سے تلاش کریں...",
  "Admission No.": "داخلہ نمبر",
  "Admission No": "داخلہ نمبر",
  "Date of Birth": "تاریخِ پیدائش",
  Gender: "جنس",
  Phone: "فون",
  "First name": "پہلا نام",
  "Middle name": "درمیانی نام",
  "Last name": "آخری نام",
  "Home address": "گھر کا پتہ",
  "Full name": "پورا نام",
  "Alternate phone": "متبادل فون",
  Guardian2: "سرپرست",

  // ---------- Attendance page ----------
  "Home / Attendance": "ہوم / حاضری",
  "Mark Attendance": "حاضری لگائیں",
  "Select a class and date to mark attendance":
    "حاضری کے لیے جماعت اور تاریخ منتخب کریں",
  "Mark and view daily attendance records for students.":
    "طلبہ کی روزانہ حاضری درج کریں اور دیکھیں۔",
  "Attendance Records": "حاضری کے ریکارڈز",
  "records found": "ریکارڈز ملے",
  "No attendance records found": "کوئی حاضری ریکارڈ نہیں ملا",
  STUDENT: "طالب علم",
  "ADMISSION NO.": "داخلہ نمبر",
  CAMPUS: "کیمپس",
  CLASS: "جماعت",
  SECTION: "سیکشن",
  DATE: "تاریخ",
  STATUS: "صورتِ حال",

  // ---------- Finance page ----------
  "Track invoices, payments and fee categories.":
    "انوائسز، ادائیگیاں اور فیس کی اقسام کا انتظام۔",
  "Fee Structures": "فیس ڈھانچے",
  "structures configured": "فیس ڈھانچے ترتیب دیے گئے",
  "No fee structures": "کوئی فیس ڈھانچہ نہیں",
  Invoices: "انوائسز",
  "invoices found": "انوائسز ملیں",
  "No invoices found": "کوئی انوائس نہیں ملی",
  Payments: "ادائیگیاں",
  "ACADEMIC YEAR": "تعلیمی سال",
  CATEGORY: "قسم",
  AMOUNT: "رقم",
  "DUE DAY": "آخری تاریخ",
  TOTAL: "کل",
  PAID: "ادا شدہ",
  BALANCE: "بقایا",
  "INVOICE NO.": "انوائس نمبر",
  "ISSUE DATE": "جاری کی تاریخ",
  "DUE DATE": "آخری تاریخ",
  METHOD: "طریقہ",
  "RECEIPT NO.": "رسید نمبر",
  RECEIPT: "رسید",
  INVOICE: "انوائس",
  "Accounting overview": "اکاؤنٹنگ جائزہ",
  "ledger accounts and balances": "لیجر اکاؤنٹس اور بیلنس",
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
