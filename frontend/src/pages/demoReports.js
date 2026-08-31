const C1 = "RS Campus";
const C2 = "Model Town Campus";

export const DEMO_REPORTS = {
  enrollment: {
    rowKeys: ["classes"],
    data: {
      total_students: 259,
      total_classes: 16,
      average_class_size: 16.2,
      classes: [
        { campus: C1, class: "Grade 1", total: 18, male: 10, female: 8 },
        { campus: C1, class: "Grade 2", total: 16, male: 9, female: 7 },
        { campus: C1, class: "Grade 3", total: 17, male: 8, female: 9 },
        { campus: C1, class: "Grade 4", total: 15, male: 7, female: 8 },
        { campus: C1, class: "Grade 5", total: 16, male: 9, female: 7 },
        { campus: C1, class: "Grade 6", total: 14, male: 6, female: 8 },
        { campus: C1, class: "Grade 7", total: 15, male: 8, female: 7 },
        { campus: C1, class: "Grade 8", total: 13, male: 7, female: 6 },
        { campus: C2, class: "Grade 1", total: 20, male: 11, female: 9 },
        { campus: C2, class: "Grade 2", total: 19, male: 10, female: 9 },
        { campus: C2, class: "Grade 3", total: 18, male: 9, female: 9 },
        { campus: C2, class: "Grade 4", total: 16, male: 8, female: 8 },
        { campus: C2, class: "Grade 5", total: 17, male: 9, female: 8 },
        { campus: C2, class: "Grade 6", total: 16, male: 8, female: 8 },
        { campus: C2, class: "Grade 7", total: 15, male: 8, female: 7 },
        { campus: C2, class: "Grade 8", total: 14, male: 7, female: 7 },
      ],
    },
  },

  attendance: {
    rowKeys: ["classes"],
    data: {
      overall_attendance_rate: 93.4,
      classes: [
        { campus: C1, class: "Grade 1", total_records: 270, present: 258, absent: 6, late: 3, leave: 3, attendance_rate: 95.6 },
        { campus: C1, class: "Grade 2", total_records: 240, present: 226, absent: 7, late: 4, leave: 3, attendance_rate: 94.2 },
        { campus: C1, class: "Grade 3", total_records: 255, present: 241, absent: 8, late: 3, leave: 3, attendance_rate: 94.5 },
        { campus: C1, class: "Grade 4", total_records: 225, present: 208, absent: 10, late: 4, leave: 3, attendance_rate: 92.4 },
        { campus: C1, class: "Grade 5", total_records: 240, present: 224, absent: 9, late: 5, leave: 2, attendance_rate: 93.3 },
        { campus: C2, class: "Grade 1", total_records: 300, present: 286, absent: 8, late: 4, leave: 2, attendance_rate: 95.3 },
        { campus: C2, class: "Grade 2", total_records: 285, present: 268, absent: 9, late: 5, leave: 3, attendance_rate: 94.0 },
        { campus: C2, class: "Grade 3", total_records: 270, present: 251, absent: 11, late: 5, leave: 3, attendance_rate: 93.0 },
        { campus: C2, class: "Grade 4", total_records: 240, present: 219, absent: 13, late: 6, leave: 2, attendance_rate: 91.3 },
        { campus: C2, class: "Grade 5", total_records: 255, present: 235, absent: 12, late: 6, leave: 2, attendance_rate: 92.2 },
      ],
    },
  },

  "chronic-absentee": {
    rowKeys: ["students"],
    data: {
      summary: { threshold: 75, students_tracked: 259, students_flagged: 6 },
      students: [
        { admission_number: "STU-0047", student: "Ali Raza", campus: C1, class: "Grade 4", total_days: 15, present: 9, absent: 5, leave: 1, attendance_rate: 60.0 },
        { admission_number: "STU-0089", student: "Sana Tariq", campus: C2, class: "Grade 5", total_days: 17, present: 10, absent: 6, leave: 1, attendance_rate: 58.8 },
        { admission_number: "STU-0123", student: "Hassan Mehmood", campus: C1, class: "Grade 6", total_days: 15, present: 10, absent: 4, leave: 1, attendance_rate: 66.7 },
        { admission_number: "STU-0156", student: "Ayesha Siddiqui", campus: C2, class: "Grade 3", total_days: 16, present: 11, absent: 4, leave: 1, attendance_rate: 68.8 },
        { admission_number: "STU-0198", student: "Bilal Ahmed", campus: C1, class: "Grade 7", total_days: 15, present: 10, absent: 4, leave: 1, attendance_rate: 66.7 },
        { admission_number: "STU-0221", student: "Fatima Noor", campus: C2, class: "Grade 2", total_days: 16, present: 11, absent: 5, leave: 0, attendance_rate: 68.8 },
      ],
    },
  },

  results: {
    rowKeys: ["students"],
    data: {
      summary: { total_students: 40, passed: 34, pass_rate: 85.0, average_percentage: 72.4, highest: 96.5, lowest: 38.0 },
      students: [
        { admission_number: "STU-0001", student: "Ahmed Khan", total_marks: 482, maximum_marks: 500, percentage: 96.5, grade: "A+", result: "Pass", position: 1 },
        { admission_number: "STU-0012", student: "Mariam Javed", total_marks: 466, maximum_marks: 500, percentage: 93.2, grade: "A+", result: "Pass", position: 2 },
        { admission_number: "STU-0023", student: "Usman Ghani", total_marks: 451, maximum_marks: 500, percentage: 90.2, grade: "A+", result: "Pass", position: 3 },
        { admission_number: "STU-0034", student: "Zainab Bibi", total_marks: 428, maximum_marks: 500, percentage: 85.6, grade: "A", result: "Pass", position: 4 },
        { admission_number: "STU-0047", student: "Ali Raza", total_marks: 397, maximum_marks: 500, percentage: 79.4, grade: "B+", result: "Pass", position: 5 },
        { admission_number: "STU-0055", student: "Hamza Malik", total_marks: 361, maximum_marks: 500, percentage: 72.2, grade: "B", result: "Pass", position: 6 },
        { admission_number: "STU-0061", student: "Laiba Shah", total_marks: 344, maximum_marks: 500, percentage: 68.8, grade: "B", result: "Pass", position: 7 },
        { admission_number: "STU-0073", student: "Daniyal Aslam", total_marks: 292, maximum_marks: 500, percentage: 58.4, grade: "C", result: "Pass", position: 8 },
        { admission_number: "STU-0089", student: "Sana Tariq", total_marks: 265, maximum_marks: 500, percentage: 53.0, grade: "C", result: "Pass", position: 9 },
        { admission_number: "STU-0094", student: "Rayyan Sheikh", total_marks: 190, maximum_marks: 500, percentage: 38.0, grade: "F", result: "Fail", position: 10 },
      ],
    },
  },

  subjects: {
    rowKeys: ["subjects"],
    data: {
      summary: { subjects: 8, results: 320, pass_rate: 86.3, average_percentage: 74.8 },
      subjects: [
        { subject: "English", students: 40, average_percentage: 78.5, pass_rate: 92.5, highest: 98, lowest: 42 },
        { subject: "Urdu", students: 40, average_percentage: 82.0, pass_rate: 95.0, highest: 99, lowest: 48 },
        { subject: "Mathematics", students: 40, average_percentage: 71.2, pass_rate: 82.5, highest: 97, lowest: 30 },
        { subject: "Science", students: 40, average_percentage: 74.6, pass_rate: 85.0, highest: 96, lowest: 35 },
        { subject: "Islamiat", students: 40, average_percentage: 86.4, pass_rate: 97.5, highest: 100, lowest: 52 },
        { subject: "Social Studies", students: 40, average_percentage: 76.9, pass_rate: 87.5, highest: 95, lowest: 40 },
        { subject: "Computer", students: 40, average_percentage: 80.3, pass_rate: 92.5, highest: 98, lowest: 44 },
        { subject: "General Knowledge", students: 40, average_percentage: 68.5, pass_rate: 78.0, highest: 94, lowest: 28 },
      ],
    },
  },

  "top-performers": {
    rowKeys: ["performers"],
    data: {
      summary: { classes: 6, students: 40, top_n: 5 },
      performers: [
        { position: 1, campus: C1, class: "Grade 8", admission_number: "STU-0001", student: "Ahmed Khan", percentage: 96.5, grade: "A+" },
        { position: 2, campus: C2, class: "Grade 7", admission_number: "STU-0012", student: "Mariam Javed", percentage: 93.2, grade: "A+" },
        { position: 3, campus: C1, class: "Grade 6", admission_number: "STU-0023", student: "Usman Ghani", percentage: 90.2, grade: "A+" },
        { position: 4, campus: C2, class: "Grade 5", admission_number: "STU-0034", student: "Zainab Bibi", percentage: 85.6, grade: "A" },
        { position: 5, campus: C1, class: "Grade 4", admission_number: "STU-0047", student: "Ali Raza", percentage: 79.4, grade: "B+" },
      ],
    },
  },

  "class-performance": {
    rowKeys: ["classes"],
    data: {
      summary: { total_students: 40, overall_pass_rate: 85.0, overall_average: 72.4 },
      classes: [
        { campus: C1, class: "Grade 3", total_students: 14, exams_covered: 2, passed: 13, failed: 1, pass_rate: 92.9, average_percentage: 81.5, highest: 96.0, lowest: 44.0 },
        { campus: C1, class: "Grade 4", total_students: 13, exams_covered: 2, passed: 11, failed: 2, pass_rate: 84.6, average_percentage: 73.8, highest: 94.5, lowest: 38.0 },
        { campus: C1, class: "Grade 5", total_students: 13, exams_covered: 2, passed: 10, failed: 3, pass_rate: 76.9, average_percentage: 68.2, highest: 91.0, lowest: 35.5 },
      ],
    },
  },

  "student-progress": {
    rowKeys: ["exams"],
    data: {
      summary: { total_exams: 3, average_percentage: 81.0, best_percentage: 88.2, worst_percentage: 74.5, trend: "improving" },
      exams: [
        { exam: "First Term Examination", exam_type: "Midterm", campus: C1, class: "Grade 5", percentage: 74.5, grade: "B", result: "Pass", position: 8 },
        { exam: "Second Term Examination", exam_type: "Final", campus: C1, class: "Grade 5", percentage: 80.3, grade: "A", result: "Pass", position: 6 },
        { exam: "Annual Examination", exam_type: "Annual", campus: C1, class: "Grade 5", percentage: 88.2, grade: "A+", result: "Pass", position: 3 },
      ],
    },
  },

  fees: {
    rowKeys: ["by_campus"],
    data: {
      summary: { total_invoiced: 6850000, total_collected: 6120000, total_outstanding: 730000, collection_rate: 89.3 },
      by_campus: [
        { campus: C1, invoiced: 3600000, collected: 3240000, outstanding: 360000 },
        { campus: C2, invoiced: 3250000, collected: 2880000, outstanding: 370000 },
      ],
    },
  },

  "fee-defaulters": {
    rowKeys: ["students"],
    data: {
      summary: { total_defaulters: 9, total_outstanding: 478500 },
      students: [
        { admission_number: "STU-0047", student: "Ali Raza", campus: C1, invoice_count: 3, total_invoiced: 45000, total_paid: 12000, total_outstanding: 33000 },
        { admission_number: "STU-0089", student: "Sana Tariq", campus: C2, invoice_count: 3, total_invoiced: 52000, total_paid: 19500, total_outstanding: 32500 },
        { admission_number: "STU-0123", student: "Hassan Mehmood", campus: C1, invoice_count: 2, total_invoiced: 38000, total_paid: 9000, total_outstanding: 29000 },
        { admission_number: "STU-0156", student: "Ayesha Siddiqui", campus: C2, invoice_count: 3, total_invoiced: 48000, total_paid: 22500, total_outstanding: 25500 },
        { admission_number: "STU-0198", student: "Bilal Ahmed", campus: C1, invoice_count: 2, total_invoiced: 35000, total_paid: 12000, total_outstanding: 23000 },
      ],
    },
  },

  "collection-trend": {
    rowKeys: ["months_data"],
    data: {
      summary: { total_invoiced: 6850000, total_collected: 6120000, collection_rate: 89.3, months: 6 },
      months_data: [
        { month: "2026-03", invoiced: 980000, collected: 902000, gap: 78000 },
        { month: "2026-04", invoiced: 1120000, collected: 1015000, gap: 105000 },
        { month: "2026-05", invoiced: 1080000, collected: 968000, gap: 112000 },
        { month: "2026-06", invoiced: 1150000, collected: 1042000, gap: 108000 },
        { month: "2026-07", invoiced: 1210000, collected: 1089000, gap: 121000 },
        { month: "2026-08", invoiced: 1310000, collected: 1104000, gap: 206000 },
      ],
    },
  },

  discounts: {
    rowKeys: ["by_campus", "invoices"],
    data: {
      summary: { invoices_affected: 54, total_discount: 148000, total_concession: 96500, total_reduction: 244500 },
      by_campus: [
        { campus: C1, invoices: 31, discounts: 86000, concessions: 53000 },
        { campus: C2, invoices: 23, discounts: 62000, concessions: 43500 },
      ],
      invoices: [
        { invoice_number: "INV-2026-0142", student: "Ali Raza", campus: C1, subtotal: 15000, discount: 2000, concession: 0, total_reduction: 2000 },
        { invoice_number: "INV-2026-0157", student: "Sana Tariq", campus: C2, subtotal: 18000, discount: 0, concession: 4500, total_reduction: 4500 },
        { invoice_number: "INV-2026-0183", student: "Usman Ghani", campus: C1, subtotal: 15000, discount: 2500, concession: 1500, total_reduction: 4000 },
        { invoice_number: "INV-2026-0201", student: "Mariam Javed", campus: C2, subtotal: 16000, discount: 1500, concession: 2000, total_reduction: 3500 },
        { invoice_number: "INV-2026-0216", student: "Ayesha Siddiqui", campus: C2, subtotal: 17000, discount: 0, concession: 5000, total_reduction: 5000 },
      ],
    },
  },

  staff: {
    rowKeys: ["groups"],
    data: {
      total_staff: 48,
      groups: [
        { campus: C1, designation: "Principal", count: 1 },
        { campus: C1, designation: "Vice Principal", count: 1 },
        { campus: C1, designation: "Teacher", count: 18 },
        { campus: C1, designation: "Accountant", count: 2 },
        { campus: C1, designation: "Librarian", count: 1 },
        { campus: C1, designation: "Office Assistant", count: 2 },
        { campus: C2, designation: "Principal", count: 1 },
        { campus: C2, designation: "Teacher", count: 16 },
        { campus: C2, designation: "Accountant", count: 1 },
        { campus: C2, designation: "Driver", count: 3 },
        { campus: C2, designation: "Security Guard", count: 2 },
      ],
    },
  },

  "teacher-workload": {
    rowKeys: ["teachers"],
    data: {
      summary: { total_teachers: 34, total_assignments: 52 },
      teachers: [
        { teacher: "Mr. Tariq Jameel", employee_number: "EMP-0021", campus: C1, assignments: 2, subjects: ["Mathematics", "Computer"], classes: 2, sections: 3 },
        { teacher: "Mrs. Naila Khan", employee_number: "EMP-0034", campus: C1, assignments: 1, subjects: ["English"], classes: 2, sections: 2 },
        { teacher: "Ms. Saba Akhtar", employee_number: "EMP-0042", campus: C2, assignments: 2, subjects: ["Science", "General Knowledge"], classes: 2, sections: 2 },
        { teacher: "Mr. Faisal Baig", employee_number: "EMP-0056", campus: C1, assignments: 1, subjects: ["Urdu"], classes: 3, sections: 3 },
        { teacher: "Ms. Hina Shah", employee_number: "EMP-0063", campus: C2, assignments: 2, subjects: ["Islamiat", "Social Studies"], classes: 2, sections: 2 },
      ],
    },
  },

  payments: {
    rowKeys: ["by_method", "by_campus"],
    data: {
      summary: { total_collected: 6120000, methods: 4 },
      by_method: [
        { method: "Bank Transfer", payments: 210, collected: 2860000 },
        { method: "JazzCash", payments: 165, collected: 1540000 },
        { method: "Easypaisa", payments: 98, collected: 920000 },
        { method: "Cash", payments: 140, collected: 800000 },
      ],
      by_campus: [
        { campus: C1, payments: 318, collected: 3240000 },
        { campus: C2, payments: 295, collected: 2880000 },
      ],
    },
  },

  "student-status": {
    rowKeys: ["rows"],
    data: {
      total_students: 259,
      statuses: [
        { status: "Active", count: 244 },
        { status: "Graduated", count: 11 },
        { status: "Transferred", count: 4 },
      ],
      rows: [
        { campus: C1, status: "Active", count: 124 },
        { campus: C1, status: "Graduated", count: 6 },
        { campus: C1, status: "Transferred", count: 2 },
        { campus: C2, status: "Active", count: 120 },
        { campus: C2, status: "Graduated", count: 5 },
        { campus: C2, status: "Transferred", count: 2 },
      ],
    },
  },

  "fee-categories": {
    rowKeys: ["by_category", "by_campus_category"],
    data: {
      summary: { total_invoiced: 6850000, categories: 6 },
      by_category: [
        { category: "Tuition Fee", invoiced: 4200000 },
        { category: "Admission Fee", invoiced: 260000 },
        { category: "Transport Fee", invoiced: 990000 },
        { category: "Exam Fee", invoiced: 480000 },
        { category: "Library Fee", invoiced: 220000 },
        { category: "Miscellaneous", invoiced: 700000 },
      ],
      by_campus_category: [
        { category: "Tuition Fee", campus: C1, invoiced: 2250000 },
        { category: "Tuition Fee", campus: C2, invoiced: 1950000 },
        { category: "Transport Fee", campus: C1, invoiced: 530000 },
        { category: "Transport Fee", campus: C2, invoiced: 460000 },
        { category: "Exam Fee", campus: C1, invoiced: 260000 },
        { category: "Exam Fee", campus: C2, invoiced: 220000 },
      ],
    },
  },

  "payroll-summary": {
    rowKeys: ["by_period", "by_campus"],
    data: {
      summary: { records: 96, total_gross: 6840000, total_deductions: 1240000, total_net: 5600000 },
      by_period: [
        { period: "2026-02", employees: 48, gross: 1120000, deductions: 208000, net: 912000 },
        { period: "2026-03", employees: 48, gross: 1135000, deductions: 206000, net: 929000 },
        { period: "2026-04", employees: 48, gross: 1135000, deductions: 209000, net: 926000 },
        { period: "2026-05", employees: 48, gross: 1150000, deductions: 207000, net: 943000 },
      ],
      by_campus: [
        { campus: C1, employees: 27, gross: 3920000, net: 3210000 },
        { campus: C2, employees: 21, gross: 2920000, net: 2390000 },
      ],
    },
  },

  library: {
    rowKeys: ["most_borrowed", "overdue"],
    data: {
      summary: { total_issues: 512, active_issues: 34, marked_overdue: 7, fines_outstanding: 6200, fines_collected: 18500 },
      most_borrowed: [
        { title: "Matilda", issues: 14, currently_out: 2 },
        { title: "Oxford Learner's Dictionary", issues: 12, currently_out: 1 },
        { title: "The Secret Garden", issues: 11, currently_out: 3 },
        { title: "Short Stories for Kids", issues: 10, currently_out: 2 },
        { title: "Encyclopedia for Children", issues: 9, currently_out: 1 },
      ],
      overdue: [
        { title: "Matilda", borrower: "Ali Raza", due_date: "2026-08-12", days_overdue: 9, fine: 450 },
        { title: "The Secret Garden", borrower: "Sana Tariq", due_date: "2026-08-15", days_overdue: 6, fine: 300 },
        { title: "Encyclopedia for Children", borrower: "Hamza Malik", due_date: "2026-08-18", days_overdue: 3, fine: 150 },
        { title: "Short Stories for Kids", borrower: "Ayesha Siddiqui", due_date: "2026-08-20", days_overdue: 1, fine: 50 },
      ],
    },
  },

  "route-utilization": {
    rowKeys: ["routes"],
    data: {
      summary: { routes: 5, total_capacity: 330, total_students: 296, average_utilization: 89.7, overloaded_routes: 1 },
      routes: [
        { route: "Route A - Model Town", campus: C2, vehicle: "Toyota Hiace AB-2341", driver: "Imran Yousaf", capacity: 70, students: 62, seats_free: 8, utilization: 88.6 },
        { route: "Route B - Gulberg", campus: C1, vehicle: "Hyundai County AB-3109", driver: "Asif Rana", capacity: 70, students: 71, seats_free: -1, utilization: 101.4 },
        { route: "Route C - Township", campus: C1, vehicle: "Toyota Coaster AB-1187", capacity: 55, students: 48, seats_free: 7, utilization: 87.3 },
        { route: "Route D - DHA", campus: C2, vehicle: "Toyota Hiace AB-4112", capacity: 65, students: 59, seats_free: 6, utilization: 90.8 },
        { route: "Route E - Johar Town", campus: C1, vehicle: "Hyundai County AB-2276", capacity: 70, students: 56, seats_free: 14, utilization: 80.0 },
      ],
    },
  },

  "inventory-value": {
    rowKeys: ["by_category", "by_campus"],
    data: {
      summary: {
        items: 84,
        quantity: 1240,
        total_value: 3890000,
        statuses: [
          { status: "In Stock", count: 71 },
          { status: "Low Stock", count: 9 },
          { status: "Out of Stock", count: 4 },
        ],
      },
      by_category: [
        { category: "Furniture", items: 22, quantity: 310, value: 1620000 },
        { category: "Laboratory Equipment", items: 18, quantity: 140, value: 1180000 },
        { category: "Sports Equipment", items: 14, quantity: 260, value: 480000 },
        { category: "Stationery", items: 30, quantity: 530, value: 610000 },
      ],
      by_campus: [
        { campus: C1, items: 46, quantity: 680, value: 2130000 },
        { campus: C2, items: 38, quantity: 560, value: 1760000 },
      ],
    },
  },

  "maintenance-due": {
    rowKeys: ["records"],
    data: {
      summary: { open_records: 6, scheduled_cost: 145000, in_progress_cost: 96000, assets_in_maintenance: 6 },
      records: [
        { asset: "Air Conditioner - Lab", code: "AC-014", campus: C1, status: "scheduled", date: "2026-09-04", cost: 28000, performed_by: "Livim SVC" },
        { asset: "Generator", code: "GEN-002", campus: C1, status: "in_progress", cost: 54000, performed_by: "PowerGen Services", date: "2026-08-28" },
        { asset: "Water Cooler - Corridor", code: "WC-007", campus: C2, status: "scheduled", date: "2026-09-06", cost: 16000, performed_by: "Aqua Tech" },
        { asset: "Projector - Hall", code: "PRJ-001", campus: C2, status: "in_progress", cost: 42000, performed_by: "AV Solutions", date: "2026-08-30" },
        { asset: "School Bus AB-1187 Engine", code: "BUS-003", campus: C1, status: "scheduled", date: "2026-09-08", cost: 89000, performed_by: "Hino Workshop" },
        { asset: "Fire Extinguishers", code: "FE-011", campus: C2, status: "scheduled", date: "2026-09-02", cost: 12000, performed_by: "SafeGuard Pvt Ltd" },
      ],
    },
  },

  "event-participation": {
    rowKeys: ["events"],
    data: {
      summary: { events: 4, total_responses: 316, attending: 271, participation_rate: 85.8 },
      events: [
        { event: "Independence Day Celebration", campus: C1, start: "2026-08-14", attending: 108, not_attending: 9, maybe: 7, responses: 124, participation_rate: 87.1 },
        { event: "Annual Sports Day", campus: C1, start: "2026-09-20", attending: 61, not_attending: 5, maybe: 3, responses: 69, participation_rate: 88.4 },
        { event: "Science Exhibition", campus: C2, start: "2026-10-05", attending: 52, not_attending: 9, maybe: 6, responses: 67, participation_rate: 77.6 },
        { event: "Parent-Teacher Meeting", campus: C2, start: "2026-11-02", attending: 50, not_attending: 4, maybe: 2, responses: 56, participation_rate: 89.3 },
      ],
    },
  },

  "sms-usage": {
    rowKeys: ["months_data"],
    data: {
      summary: { year: 2026, total_messages: 4820, sent: 4681, failed: 139, success_rate: 97.1 },
      months_data: [
        { month: "2026-03", sent: 720, failed: 18, queued: 0, total: 738, success_rate: 97.6 },
        { month: "2026-04", sent: 810, failed: 24, queued: 5, total: 839, success_rate: 96.5 },
        { month: "2026-05", sent: 840, failed: 22, queued: 0, total: 862, success_rate: 97.4 },
        { month: "2026-06", sent: 760, failed: 30, queued: 8, total: 798, success_rate: 95.3 },
        { month: "2026-07", sent: 535, failed: 12, queued: 0, total: 547, success_rate: 97.8 },
        { month: "2026-08", sent: 1016, failed: 33, queued: 10, total: 1059, success_rate: 96.0 },
      ],
    },
  },
};