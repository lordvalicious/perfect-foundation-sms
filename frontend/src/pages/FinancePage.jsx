import { useState } from "react";
import { Search, Wallet } from "lucide-react";
import { useApiList } from "./useApiList";
import {
  PageHeader,
  PanelHeader,
  StateArea,
  EmptyState,
  Pagination,
  StatusBadge,
} from "./ui";
import { formatCurrency, formatDate } from "./format";

const INVOICES_API_URL = "/api/finance/invoices/";
const PAYMENTS_API_URL = "/api/finance/payments/";
const CATEGORIES_API_URL = "/api/finance/categories/";

const INVOICE_STATUSES = [
  ["draft", "Draft"],
  ["issued", "Issued"],
  ["partial", "Partially Paid"],
  ["paid", "Paid"],
  ["overdue", "Overdue"],
  ["cancelled", "Cancelled"],
];

function buildParams(search, status, page) {
  const params = new URLSearchParams();

  params.append("page", page);

  if (search.trim()) {
    params.append("search", search.trim());
  }

  if (status) {
    params.append("status", status);
  }

  return params;
}

function Filters({ search, setSearch, status, setStatus, onSearch, onClear, statusOptions }) {
  return (
    <div className="panel students-filters">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          onSearch();
        }}
      >
        <div className="filter-row">
          <div className="filter-search">
            <Search size={18} />

            <input
              type="text"
              placeholder="Search by name, admission or number..."
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
            />
          </div>

          <select
            value={status}
            onChange={(event) => {
              setStatus(event.target.value);
              setTimeout(onSearch, 0);
            }}
          >
            <option value="">All statuses</option>

            {statusOptions.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>

          <button type="submit" className="primary-button">
            Search
          </button>

          <button
            type="button"
            className="secondary-button"
            onClick={onClear}
          >
            Clear
          </button>
        </div>
      </form>
    </div>
  );
}

export default function FinancePage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");

  const invoices = useApiList(INVOICES_API_URL);
  const payments = useApiList(PAYMENTS_API_URL);
  const categories = useApiList(CATEGORIES_API_URL);

  const applyInvoices = (pageNumber = 1) => {
    invoices.refresh(
      buildParams(search, status, pageNumber)
    );
  };

  const applyPayments = (pageNumber = 1) => {
    const params = new URLSearchParams();

    params.append("page", pageNumber);

    if (search.trim()) {
      params.append("search", search.trim());
    }

    payments.refresh(params);
  };

  const clearFilters = () => {
    setSearch("");
    setStatus("");
    applyInvoices(1);
    applyPayments(1);
  };

  return (
    <section className="content">
      <PageHeader
        crumb="Home / Finance"
        title="Finance"
        subtitle="Track invoices, payments and fee categories."
      />

      <Filters
        search={search}
        setSearch={setSearch}
        status={status}
        setStatus={setStatus}
        onSearch={() => {
          applyInvoices(1);
          applyPayments(1);
        }}
        onClear={clearFilters}
        statusOptions={INVOICE_STATUSES}
      />

      <div className="panel">
        <PanelHeader
          title="Invoices"
          subtitle="invoices found"
          count={invoices.count}
        />

        <StateArea
          loading={invoices.loading}
          error={invoices.error}
          onRetry={() => applyInvoices(invoices.page)}
        >
          {invoices.rows.length === 0 ? (
            <EmptyState
              icon={Wallet}
              title="No invoices found"
              message="No invoices match the current filters."
            />
          ) : (
            <>
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>INVOICE NO.</th>
                      <th>STUDENT</th>
                      <th>CLASS</th>
                      <th>ISSUE DATE</th>
                      <th>DUE DATE</th>
                      <th>TOTAL</th>
                      <th>PAID</th>
                      <th>BALANCE</th>
                      <th>STATUS</th>
                    </tr>
                  </thead>

                  <tbody>
                    {invoices.rows.map((invoice) => (
                      <tr key={invoice.id}>
                        <td>
                          <strong>
                            {invoice.invoice_number || "—"}
                          </strong>
                        </td>

                        <td>
                          <strong>
                            {invoice.student_name || "—"}
                          </strong>
                          <span className="cell-sub">
                            {invoice.admission_number || ""}
                          </span>
                        </td>

                        <td>{invoice.class_name || "—"}</td>

                        <td>
                          {formatDate(invoice.issue_date)}
                        </td>

                        <td>
                          {formatDate(invoice.due_date)}
                        </td>

                        <td>
                          {formatCurrency(
                            invoice.total_amount
                          )}
                        </td>

                        <td>
                          {formatCurrency(
                            invoice.paid_amount
                          )}
                        </td>

                        <td>
                          <strong>
                            {formatCurrency(invoice.balance)}
                          </strong>
                        </td>

                        <td>
                          <StatusBadge
                            status={invoice.status}
                            label={invoice.status_display}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <Pagination
                count={invoices.count}
                page={invoices.page}
                next={invoices.next}
                previous={invoices.previous}
                onPage={(pageNumber) =>
                  applyInvoices(pageNumber)
                }
              />
            </>
          )}
        </StateArea>
      </div>

      <div className="panel">
        <PanelHeader
          title="Payments"
          subtitle="payments recorded"
          count={payments.count}
        />

        <StateArea
          loading={payments.loading}
          error={payments.error}
          onRetry={() => applyPayments(payments.page)}
        >
          {payments.rows.length === 0 ? (
            <EmptyState
              icon={Wallet}
              title="No payments found"
              message="No payments match the current filters."
            />
          ) : (
            <>
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>RECEIPT NO.</th>
                      <th>STUDENT</th>
                      <th>INVOICE</th>
                      <th>DATE</th>
                      <th>METHOD</th>
                      <th>AMOUNT</th>
                      <th>STATUS</th>
                    </tr>
                  </thead>

                  <tbody>
                    {payments.rows.map((payment) => (
                      <tr key={payment.id}>
                        <td>
                          <strong>
                            {payment.receipt_number || "—"}
                          </strong>
                        </td>

                        <td>
                          <strong>
                            {payment.student_name || "—"}
                          </strong>
                        </td>

                        <td>
                          {payment.invoice_number || "—"}
                        </td>

                        <td>
                          {formatDate(payment.payment_date)}
                        </td>

                        <td>
                          {payment.payment_method_display ||
                            "—"}
                        </td>

                        <td>
                          <strong>
                            {formatCurrency(payment.amount)}
                          </strong>
                        </td>

                        <td>
                          <StatusBadge
                            status={payment.status}
                            label={payment.status_display}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <Pagination
                count={payments.count}
                page={payments.page}
                next={payments.next}
                previous={payments.previous}
                onPage={(pageNumber) =>
                  applyPayments(pageNumber)
                }
              />
            </>
          )}
        </StateArea>
      </div>

      <div className="panel">
        <PanelHeader
          title="Fee Categories"
          subtitle="categories configured"
          count={categories.count}
        />

        <StateArea
          loading={categories.loading}
          error={categories.error}
        >
          {categories.rows.length === 0 ? (
            <EmptyState
              icon={Wallet}
              title="No fee categories"
              message="No fee categories have been configured yet."
            />
          ) : (
            <div className="overview-list">
              {categories.rows.map((category) => (
                <div key={category.id}>
                  <span>
                    {category.name} ·{" "}
                    {category.frequency_display}
                  </span>

                  <StatusBadge
                    status={category.status}
                  />
                </div>
              ))}
            </div>
          )}
        </StateArea>
      </div>
    </section>
  );
}
