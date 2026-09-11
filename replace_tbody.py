with open("frontend/src/pages/PayrollPage.jsx", "r", encoding="utf-8") as f:
    content = f.read()

# Find the tbody section and replace it
old_tbody = """<tbody>
                  {tab === "structures" &&
                    rows.map((structure) => (
                      <tr key={structure.id}>
                        <td>
                          <strong>{structure.teacher_name || "—"}</strong>
                        </td>

                        <td>{formatCurrency(structure.basic_salary)}</td>

                        <td>{formatCurrency(structure.total_allowances)}</td>

                        <td>
                          <strong>{formatCurrency(structure.gross_salary)}</strong>
                        </td>

                        <td>{formatDate(structure.effective_date)}</td>

                        <td>
                          <span className={`status-badge ${structure.status === "active" ? "active" : "inactive"}`}>
                            {structure.status ? structure.status.charAt(0).toUpperCase() + structure.status.slice(1) : "—"}
                          </span>
                        </td>

                        <td>
                          <button
                            type="button"
                            className="table-action"
                            onClick={() => openStructureModal("edit", structure)}
                            title="Edit"
                          >
                            <Edit size={14} />
                          </button>
                          <button
                            type="button"
                            className="table-action danger"
                            onClick={() => handleDelete("structure", structure.id)}
                            title="Delete"
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  )}

                  {tab === "records" &&
                    rows.map((record) => (
                      <tr key={record.id}>
                        <td>
                          <strong>{record.teacher_name || "—"}</strong>
                        </td>

                        <td>{record.teacher_number || "—"}</td>

                        <td>
                          {record.month ? MONTHS[record.month - 1] : "—"} {record.year || ""}
                        </td>

                        <td>{record.working_days ?? "—"}</td>

                        <td>{record.paid_days ?? "—"}</td>

                        <td>{formatCurrency(record.gross_salary)}</td>

                        <td>{formatCurrency(record.total_deductions)}</td>

                        <td>
                          <strong>{formatCurrency(record.net_salary)}</strong>
                        </td>

                        <td>
                          <span className={`status-badge ${record.status === "paid" ? "active" : record.status === "approved" ? "warn" : record.status === "processed" ? "info" : "inactive"}`}>
                            {record.status ? record.status.charAt(0).toUpperCase() + record.status.slice(1) : "—"}
                          </span>
                        </td>

                        <td>
                          {record.status !== "paid" && (
                            <>
                              <button
                                type="button"
                                className="table-action"
                                onClick={() => openRecordModal("edit", record)}
                                title="Edit"
                              >
                                <Edit size={14} />
                              </button>
                              {record.status === "draft" && (
                                <button
                                  type="button"
                                  className="table-action"
                                  disabled={processing === record.id}
                                  onClick={() => handleProcess(record.id)}
                                  title="Process"
                                >
                                  {processing === record.id ? <Loader2 size={14} className="spin" /> : "Process"}
                                </button>
                              )}
                              {record.status === "processed" && (
                                <button
                                  type="button"
                                  className="table-action"
                                  disabled={processing === record.id}
                                  onClick={() => handleApprove(record.id)}
                                  title="Approve"
                                >
                                  {processing === record.id ? <Loader2 size={14} className="spin" /> : "Approve"}
                                </button>
                              )}
                              {record.status === "approved" && (
                                <button
                                  type="button"
                                  className="table-action"
                                  disabled={processing === record.id}
                                  onClick={() => handlePay(record.id)}
                                  title="Mark Paid"
                                >
                                  {processing === record.id ? <Loader2 size={14} className="spin" /> : "Pay"}
                                </button>
                              )}
                              {record.status === "paid" && (
                                <button
                                  type="button"
                                  className="table-action"
                                  onClick={() =>
                                    apiDownload(
                                      `${BASE}records/${record.id}/payslip.pdf`,
                                      `payslip_${record.teacher_number || record.id}_${record.year}_${String(record.month).padStart(2, "0")}.pdf`
                                    ).catch(() => alert("Could not download payslip."))
                              title="Download Payslip"
                            >
                              Payslip PDF
                            </button>
                          )}
                          {(record.status === "draft" || record.status === "processed") && (
                            <button
                              type="button"
                              className="table-action danger"
                              onClick={() => handleDelete("record", record.id)}
                              title="Delete"
                            >
                              <Trash2 size={14} />
                            </button>
                          )}
                        </>
                      </td>
                    </tr>
                  ))}
                )}

                  {tab === "payslips" &&
                    rows.map((payslip) => (
                      <tr key={payslip.id}>
                        <td>
                          <strong>{payslip.teacher_name || "—"}</strong>
                        </td>

                        <td>{payslip.period || "—"}</td>

                        <td>{formatDate(payslip.issued_at)}</td>
                      </tr>
                    ))}
                  )}
                </tbody>"""

new_tbody = """<tbody>
                  {tab === "structures" && renderStructures()}
                  {tab === "records" && renderRecords()}
                  {tab === "payslips" && renderPayslips()}
                </tbody>"""

if old_tbody in content:
    content = content.replace(old_tbody, new_tbody)
    print("Replaced")
else:
    print("Not found")
    # Debug: find the tbody
    idx = content.find("<tbody>")
    if idx >= 0:
        print(f"Found tbody at index {idx}")
        print(content[idx:idx+200])
    else:
        print("tbody not found")

with open("frontend/src/pages/PayrollPage.jsx", "w", encoding="utf-8") as f:
    f.write(content)

print("Done")